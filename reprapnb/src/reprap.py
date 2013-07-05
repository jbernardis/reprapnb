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

CMD_GCODE = 1
CMD_STARTPRINT = 2
CMD_STOPPRINT = 3
CMD_DRAINQUEUE = 4
CMD_ENDOFPRINT = 5

class SendThread:
	def __init__(self, win, printer, priQ, mainQ):
		self.priQ = priQ
		self.mainQ = mainQ
		self.isPrinting = False
		self.win = win
		self.printer = printer
		self.isRunning = False
		thread.start_new_thread(self.Run, ())
		
	def kill(self):
		self.isRunning = False
		self.printer = None
	
	def Run(self):
		self.isRunning = True
		while self.isRunning:
			if self.isPrinting:
				if not self.priQ.empty():
					try:
						(cmd, string) = self.priQ.get(True, 0.01)
						print "got ", cmd, " from pri q"
						self.processCmd(cmd, string)
					except Queue.Empty:
						pass
					
				elif not self.mainQ.empty():
					try:
						(cmd, string) = self.mainQ.get(True, 0.01)
						print "got ", cmd, string, " from main q"
						self.processCmd(cmd, string)
					except Queue.Empty:
						pass
				else:
					time.sleep(0.001)

			else:
				try:
					(cmd, string) = self.priQ.get(True, 0.01)
					print "got ", cmd, " from pri q"
					self.processCmd(cmd, string)
				except Queue.Empty:
					time.sleep(0.01)
		print "sender ending"
				
	def processCmd(self, cmd, string):
		if cmd == CMD_GCODE:
			self.printer.write(str(string+"\n"))
		elif cmd == CMD_STARTPRINT:
			self.isPrinting = True
			evt = RepRapEvent(event = PRINT_STARTED)
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
	def __init__(self, win, printer):
		self.win = win
		self.printer = printer
		self.isRunning = False
		thread.start_new_thread(self.Run, ())
		
	def kill(self):
		self.isRunning = False
		self.printer = None
		
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
				print "RECV: ",line.rstrip()
		print "listener ending"

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
		
		if self.port is not None and self.baud is not None:
			self.priQ = Queue.Queue(0)
			self.mainQ = Queue.Queue(0)
			self.printer = Serial(self.port, self.baud, timeout=5)
			self.listener = ListenThread(self.win, self.printer)
			self.sender = SendThread(self.win, self.printer, self.priQ, self.mainQ)
			self.send_now("M105")
			self.online = True

	def disconnect(self):
		if(self.printer):
			self.printer.close()
		if self.listener and self.listener.isRunning:
			self.listener.kill()
			
		self.listener = None
		if self.sender and self.sender.isRunning:
			self.sender.kill()
			
		self.sender = None
		self.printer = None
		self.online = False
		self.printing = False
		
	def _checksum(self,command):
		return reduce(lambda x,y:x^y, map(ord,command))
	
	def startPrint(self, data):
		ln = 0
		for l in data:
			self._send(l, ln, checksum=True)
			ln += 1

		self._sendCmd(CMD_ENDOFPRINT, priority=False)			
		self._sendCmd(CMD_STARTPRINT)
				
	def send_now(self, cmd):
		return self._send(cmd, priority=True)
				
	def send(self, cmd):
		return self._send(cmd)

	def _send(self, command, lineno=0, checksum=False, priority=False):
		self.logger.LogMessage("Sending (%s)" % command)
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
			self.priQ((cmd, ""))
		else:
			self.mainQ((cmd, ""))
