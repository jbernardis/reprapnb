'''
Created on Jun 23, 2013

@author: Jeff
'''
from serial import Serial, SerialException
import thread
from select import error as SelectError
import Queue
import time
import wx
import wx.lib.newevent

(RepRapEvent, EVT_REPRAP_UPDATE) = wx.lib.newevent.NewEvent()
PRINT_COMPLETE = 1
PRINT_STOPPED = 2
PRINT_STARTED = 3
PRINT_RESUMED = 4
RECEIVED_MSG = 10

CMD_GCODE = 1
CMD_STARTPRINT = 2
CMD_STOPPRINT = 3
CMD_DRAINQUEUE = 4
CMD_ENDOFPRINT = 5
CMD_RESUMEPRINT = 6

class SendThread:
	def __init__(self, win, printer, priQ, mainQ):
		self.priQ = priQ
		self.mainQ = mainQ
		self.isPrinting = False
		self.win = win
		self.printer = printer
		self.isRunning = False
		self.endoflife = False
		self.printIndex = 0
		self.okWait = False
		thread.start_new_thread(self.Run, ())
		
	def kill(self):
		self.isRunning = False
		self.printer = None
		
	def endWait(self):
		print "end wait"
		self.okWait = False
		
	def isKilled(self):
		return self.endoflife
	
	def getPrintIndex(self):
		return self.printIndex
	
	def Run(self):
		self.isRunning = True
		while self.isRunning:
			if self.isPrinting:
				if not self.priQ.empty():
					try:
						(cmd, string) = self.priQ.get(True, 0.01)
						self.processCmd(cmd, string, True)
					except Queue.Empty:
						pass
					
				elif not self.okWait:
					if not self.mainQ.empty():
						try:
							(cmd, string) = self.mainQ.get(True, 0.01)
							self.processCmd(cmd, string, False)
						except Queue.Empty:
							pass
					else:
						time.sleep(0.001)
				else:
					time.sleep(0.001)

			else:
				try:
					(cmd, string) = self.priQ.get(True, 0.01)
					self.processCmd(cmd, string, True)
				except Queue.Empty:
					time.sleep(0.01)
		self.endoflife = True
				
	def processCmd(self, cmd, string, pflag):
		if cmd == CMD_GCODE:
			if not pflag:
				self.printIndex += 1
				self.okWait = True
			self.printer.write(str(string+"\n"))
			
		elif cmd == CMD_STARTPRINT:
			self.isPrinting = True
			self.printIndex = 0
			evt = RepRapEvent(event = PRINT_STARTED)
			wx.PostEvent(self.win, evt)
			
		elif cmd == CMD_RESUMEPRINT:
			self.isPrinting = True
			evt = RepRapEvent(event = PRINT_RESUMED)
			wx.PostEvent(self.win, evt)
			
		elif cmd == CMD_STOPPRINT:
			self.isPrinting = False
			evt = RepRapEvent(event = PRINT_STOPPED)
			wx.PostEvent(self.win, evt)
			
		elif cmd == CMD_ENDOFPRINT:
			evt = RepRapEvent(event = PRINT_COMPLETE)
			wx.PostEvent(self.win, evt)
			
		elif cmd == CMD_DRAINQUEUE:
			while True:
				try:
					(cmd, string) = self.mainQ.get(False)
					if cmd == CMD_ENDOFPRINT:
						break
				except Queue.Empty:
					break

class ListenThread:
	def __init__(self, win, printer, sender):
		self.win = win
		self.printer = printer
		self.isRunning = False
		self.endoflife = False
		self.sender = sender
		thread.start_new_thread(self.Run, ())
		
	def kill(self):
		self.isRunning = False
		self.printer = None
		
	def isKilled(self):
		return self.endoflife
		
	def Run(self):
		self.isRunning = True
		while self.isRunning:
			if(not self.printer or not self.printer.isOpen):
				break
			try:
				line=self.printer.readline()
			except SelectError, e:
				if 'Bad file descriptor' in e.args[1]:
					print "Can't read from printer (disconnected?)."
					break
				else:
					raise
				
			except SerialException, e:
				print "Can't read from printer (disconnected?)."
				break
			except OSError, e:
				print "Can't read from printer (disconnected?)."
				break

			if(len(line)>1):
				if line.strip().lower() == "ok":
					self.sender.endWait()
					continue
						
				if line.startswith("echo:"):
					line = line[5:]

				evt = RepRapEvent(event=RECEIVED_MSG, msg = line.rstrip(), state = 1)
				wx.PostEvent(self.win, evt)

		self.endoflife = True

class RepRap:
	def __init__(self, win, handler):
		self.win = win
		self.logger = self.win.logger
		self.printer = None
		self.online = False
		self.printing = False
		win.Bind(EVT_REPRAP_UPDATE, handler)

	def connect(self, port, baud):
		if(self.printer is not None):
			self.disconnect()

		self.port = port
		self.baud = baud
		
		self.printing = False
		self.paused = False
		
		if self.port is not None and self.baud is not None:
			self.priQ = Queue.Queue(0)
			self.mainQ = Queue.Queue(0)
			self.printer = Serial(self.port, self.baud, timeout=5)
			self.sender = SendThread(self.win, self.printer, self.priQ, self.mainQ)
			self.listener = ListenThread(self.win, self.printer, self.sender)
			self.send_now("M105")
			self.online = True
			
	def getPrintPosition(self):
		if self.sender and self.sender.isPrinting:
			return self.sender.getPrintIndex()
		else:
			return None

	def disconnect(self):
		if(self.printer):
			self.printer.close()
		if self.listener and self.listener.isRunning:
			self.listener.kill()
			
		if self.sender and self.sender.isRunning:
			self.sender.kill()
	
	def checkDisconnection(self):
		if self.listener is None or self.sender is None:
			return True
				
		if not self.listener.isKilled() or not self.sender.isKilled():
			return False
		self.listener = None
		self.sender = None
		self.printer = None
		self.online = False
		self.printing = False
		self.paused = False
		
		return True
		
	def _checksum(self,command):
		return reduce(lambda x,y:x^y, map(ord,command))
	
	def startPrint(self, data):
		ln = 0
		self._send("M110", lineno=-1, checksum=True)
		for l in data:
			if l.raw.rstrip() != "":
				self._send(l.raw, lineno=ln, checksum=True)
				ln += 1

		self._sendCmd(CMD_ENDOFPRINT, priority=False)			
		self._sendCmd(CMD_STARTPRINT)
		self.printing = True
		self.paused = False
		
	def pausePrint(self):
		self._sendCmd(CMD_STOPPRINT)
		self.printing = False
		self.paused = True
		
	def resumePrint(self):
		self._sendCmd(CMD_RESUMEPRINT)
		self.printing = True
		self.paused = False
		
	def restartPrint(self, data):
		self._sendCmd(CMD_DRAINQUEUE)
		self.startPrint(data)
		self.printing = True
		self.paused = False
		
	def resetPrint(self):
		self._sendCmd(CMD_DRAINQUEUE)
		self.printing = False
		self.paused = False
				
	def send_now(self, cmd):
		if not self.printer:
			self.logger.LogWarning("Printer is off-line")
			return False
		else:
			return self._send(cmd, priority=True)
				
	def send(self, cmd):
		return self._send(cmd)

	def _send(self, command, lineno=0, checksum=False, priority=False):
		if not self.printer:
			return False
		
		if priority:		
			self.priQ.put((CMD_GCODE, command))
		else:
			if checksum:
				prefix = "N" + str(lineno) + " " + command
				command = prefix + "*" + str(self._checksum(prefix))
			self.mainQ.put((CMD_GCODE, command))
			
		return True
	
	def _sendCmd(self, cmd, priority=True):
		if priority:
			self.priQ.put((cmd, ""))
		else:
			self.mainQ.put((cmd, ""))
