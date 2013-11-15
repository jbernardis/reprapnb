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
import re
import wx.lib.newevent
from sdcard import SD_CARD_OK, SD_CARD_FAIL, SD_CARD_LIST

MAX_EXTRUDERS = 2

(RepRapEvent, EVT_REPRAP_UPDATE) = wx.lib.newevent.NewEvent()
(SDCardEvent, EVT_SD_CARD) = wx.lib.newevent.NewEvent()
(PrtMonEvent, EVT_PRT_MON) = wx.lib.newevent.NewEvent()

SD_PRINT_COMPLETE = 0
SD_PRINT_POSITION = 1

PRINT_COMPLETE = 1
PRINT_STOPPED = 2
PRINT_STARTED = 3
PRINT_RESUMED = 4
QUEUE_DRAINED = 5
RECEIVED_MSG = 10

CMD_GCODE = 1
CMD_STARTPRINT = 2
CMD_STOPPRINT = 3
CMD_DRAINQUEUE = 4
CMD_ENDOFPRINT = 5
CMD_RESUMEPRINT = 6

CACHE_SIZE = 50

# printer commands that are permissible while actively printing
allow_while_printing = [ "M0", "M1", "M20", "M21", "M22", "M23", "M25", "M27", "M30", "M31", "M42", "M82", "M83", "M85", "M92",
					"M104", "M105", "M106", "M107", "M114", "M115", "M117", "M119", "M140",
					"M200", "M201", "M202", "M203", "M204", "M205", "M206", "M207", "M208", "M209", "M220", "M221", "M240",
					"M301", "M302", "M303",
					"M500", "M501", "M502", "M503"]

class MsgCache:
	def __init__(self, size):
		self.cacheSize = size
		self.reinit()
		
	def reinit(self):
		self.cache = []
		self.lastKey = None
		
	def addMsg(self, key, msg):
		if self.lastKey is not None and key != self.lastKey+1:
			self.reinit()
			
		self.lastKey = key
		self.cache.append(msg)
		d = self.cacheSize - len(self.cache)
		if d < 0:
			self.cache = self.cache[-d:]
			
	def getMsg(self, key):
		l = len(self.cache)
		if key > self.lastKey or key <= self.lastKey - l:
			return None
		
		i = l - (self.lastKey - key) - 1
		if i < 0 or i >= self.cacheSize:
			return None
		
		return self.cache[i]

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
		self.sequence = 0
		self.okWait = False
		self.holdFan = False
		self.checksum = True
		self.resendFrom = None
		self.sentCache = MsgCache(CACHE_SIZE)
		thread.start_new_thread(self.Run, ())
		
	def kill(self):
		self.isRunning = False
		self.printer = None
		
	def endWait(self):
		self.okWait = False
		
	def isKilled(self):
		return self.endoflife
	
	def setResendFrom(self, n):
		self.resendFrom = n
	
	def getPrintIndex(self):
		return self.printIndex
	
	def setHoldFan(self, flag):
		self.holdFan = flag
		
	def setCheckSum(self, flag):
		self.checksum = flag
			
	def _checksum(self,command):
		return reduce(lambda x,y:x^y, map(ord,command))

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
					
				elif self.resendFrom is not None:
					string = self.sentCache.getMsg(self.resendFrom)
					if string is None:
						self.resendFrom = None
						self.sentCache.reinit()
					else:
						self.resendFrom += 1
						self.processCmd(CMD_GCODE, string, True)
					
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
				
	def processCmd(self, cmd, string, priQ):
		if cmd == CMD_GCODE:
			if string.startswith('@'):
				self.metaCommand(string)
			elif priQ:  # GCode off of the priority queue
				self.printer.write(str(string+"\n"))

			else:  # Gcode off of the main queue
				self.printIndex += 1
				try:
					verb = string.split()[0]
				except:
					verb = ""
				
				if (verb == "M106" or verb == "M107") and self.holdFan:
					return
				
				if self.checksum:
					prefix = "N" + str(self.sequence) + " " + string
					string = prefix + "*" + str(self._checksum(prefix))
					if verb != "M110":
						self.sentCache.addMsg(self.sequence, string)
					self.sequence += 1
					
				self.okWait = True
				self.printer.write(str(string+"\n"))
			
		elif cmd == CMD_STARTPRINT:
			string = "M110"
			if self.checksum:
				prefix = "N-1 " + string
				string = prefix + "*" + str(self._checksum(prefix))
				
			self.okWait = True

			self.printer.write(str(string+"\n"))
			self.printIndex = 0
			self.sequence = 0
			self.sentCache.reinit()
			self.resendFrom = None
			self.isPrinting = True
			evt = RepRapEvent(event = PRINT_STARTED)
			wx.PostEvent(self.win, evt)
			
		elif cmd == CMD_RESUMEPRINT:
			self.sentCache.reinit()
			self.resendFrom = None
			self.isPrinting = True
			evt = RepRapEvent(event = PRINT_RESUMED)
			wx.PostEvent(self.win, evt)
			
		elif cmd == CMD_STOPPRINT:
			self.isPrinting = False
			self.sentCache.reinit()
			self.resendFrom = None
			evt = RepRapEvent(event = PRINT_STOPPED)
			wx.PostEvent(self.win, evt)
			
		elif cmd == CMD_ENDOFPRINT:
			evt = RepRapEvent(event = PRINT_COMPLETE)
			self.sentCache.reinit()
			self.resendFrom = None
			wx.PostEvent(self.win, evt)
			
		elif cmd == CMD_DRAINQUEUE:
			self.sentCache.reinit()
			self.resendFrom = None
			while True:
				try:
					(cmd, string) = self.mainQ.get(False)
					if cmd == CMD_ENDOFPRINT:
						break
				except Queue.Empty:
					break
			evt = RepRapEvent(event = QUEUE_DRAINED)
			wx.PostEvent(self.win, evt)
	
	def metaCommand(self, cmd):
		print "Meta command: ", cmd
		l = cmd.split(" +")
		nl = len(l)
		
		if nl < 1:
			print "no terms"
			return
		
		nl -= 1
		verb = l[0]
		
		if verb.lower() == "@pause":
			if nl < 1:
				duration = 1
			else:
				try:
					duration = float(l[1])
				except:
					duration = 1
			print "pausing for ", duration, " seconds"
			time.sleep(duration)
			
			

class ListenThread:
	def __init__(self, win, printer, sender):
		self.win = win
		self.printer = printer
		self.isRunning = False
		self.endoflife = False
		self.sender = sender
		self.resendre = re.compile("resend: *([0-9]+)")
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
				llow = line.strip().lower()
				
				if llow.startswith("resend:"):
					m = self.resendre.search(llow)
					if m:
						t = m.groups()
						if len(t) >= 1:
							try:
								n = int(t[0])
							except:
								n = None
								
						if n:
							
							self.sender.setResendFrom(n)
				
				if llow.startswith("ok"):
					self.sender.endWait()

				if llow == "ok":
					continue
						
				if line.startswith("echo:"):
					line = line[5:]

				evt = RepRapEvent(event=RECEIVED_MSG, msg = line.rstrip(), state = 1)
				wx.PostEvent(self.win, evt)

		self.endoflife = True

class RepRapParser:
	'''
	Parse a REPRAP message
	'''
	def __init__(self, app):
		self.app = app
		self.firmware = self.app.firmware
		self.trpt1re = re.compile("ok *T: *([0-9\.]+) */ *([0-9\.]+) *B: *([0-9\.]+) */ *([0-9\.]+)")
		self.toolre = re.compile(".*?T([0-2]): *([0-9\.]+) */ *([0-9\.]+)")
		self.trpt2re = re.compile(" *T:([0-9\.]+) *E:([0-9\.]+) *B:([0-9\.]+)")
		self.trpt3re = re.compile(" *T:([0-9\.]+) *E:([0-9\.]+) *W:.*")
		self.locrptre = re.compile("^X:([0-9\.\-]+)Y:([0-9\.\-]+)Z:([0-9\.\-]+)E:([0-9\.\-]+) *Count")
		self.speedrptre = re.compile("Fan speed:([0-9]+) Feed Multiply:([0-9]+) Extrude Multiply:([0-9]+)")
		self.toolchgre = re.compile("Active tool is now T([0-9])")
		
		self.sdre = re.compile("SD printing byte *([0-9]+) *\/ *([0-9]+)")
		self.heaters = {}
		
		self.sd = None
		self.insideListing = False
		
	def setHandlers(self, sdhdlr, prtmonhdlr):
		self.app.Bind(EVT_SD_CARD, sdhdlr)
		self.app.Bind(EVT_PRT_MON, prtmonhdlr)
		
	def parseMsg(self, msg):
		if 'M92' in msg:
			X = self.parseG(msg, 'X')
			Y = self.parseG(msg, 'Y')
			Z = self.parseG(msg, 'Z')
			E = self.parseG(msg, 'E')
			self.firmware.m92(X, Y, Z, E)
			return False
		
		if 'M201' in msg:
			X = self.parseG(msg, 'X')
			Y = self.parseG(msg, 'Y')
			Z = self.parseG(msg, 'Z')
			E = self.parseG(msg, 'E')
			self.firmware.m201(X, Y, Z, E)
			return False
		
		if 'M203' in msg:
			X = self.parseG(msg, 'X')
			Y = self.parseG(msg, 'Y')
			Z = self.parseG(msg, 'Z')
			E = self.parseG(msg, 'E')
			self.firmware.m203(X, Y, Z, E)
			return False
		
		if 'M204' in msg:
			S = self.parseG(msg, 'S')
			T = self.parseG(msg, 'T')
			self.firmware.m204(S, T)
			return False
		
		if 'M205' in msg:
			S = self.parseG(msg, 'S')
			T = self.parseG(msg, 'T')
			B = self.parseG(msg, 'B')
			X = self.parseG(msg, 'X')
			Z = self.parseG(msg, 'Z')
			E = self.parseG(msg, 'E')
			self.firmware.m205(S, T, B, X, Z, E)
			return False
		
		if 'M206' in msg:
			X = self.parseG(msg, 'X')
			Y = self.parseG(msg, 'Y')
			Z = self.parseG(msg, 'Z')
			self.firmware.m206(X, Y, Z)
			return False
		
		if 'M301' in msg:
			P = self.parseG(msg, 'P')
			I = self.parseG(msg, 'I')
			D = self.parseG(msg, 'D')
			self.firmware.m301(P, I, D)
			return False
		
		if "SD card ok" in msg:
			evt = SDCardEvent(event = SD_CARD_OK)
			wx.PostEvent(self.app, evt)
			return False
		
		if "SD init fail" in msg:
			evt = SDCardEvent(event = SD_CARD_FAIL)
			wx.PostEvent(self.app, evt)
			return False
				
		if "Begin file list" in msg:
			self.insideListing = True
			self.sdfiles = []
			return False
		
		if "End file list" in msg:
			self.insideListing = False
			evt = SDCardEvent(event = SD_CARD_LIST, data=self.sdfiles)
			wx.PostEvent(self.app, evt)
			return False

		if self.insideListing:
			self.sdfiles.append(msg.strip())
			return False
		
		if "SD printing byte" in msg:
			m = self.sdre.search(msg)
			t = m.groups()
			if len(t) != 2: return
			gpos = int(t[0])
			gmax = int(t[1])
			if gmax == 0:
				evt = PrtMonEvent(event=SD_PRINT_COMPLETE)
			else:
				evt = PrtMonEvent(event=SD_PRINT_POSITION, pos=gpos, max=gmax)
			wx.PostEvent(self.app, evt)
			return False
			
		if "Done printing file" in msg:
			evt = PrtMonEvent(event=SD_PRINT_COMPLETE)
			wx.PostEvent(self.app, evt)
			return False

		m = self.trpt1re.search(msg)
		if m:
			gotHE = [False for i in range(MAX_EXTRUDERS)]
			HEtemp = [0 for i in range(MAX_EXTRUDERS)]
			HEtarget = [0 for i in range(MAX_EXTRUDERS)]
			t = m.groups()
			if len(t) >= 1:
				HEtemp[0] = float(t[0])
				gotHE[0] = True
			if len(t) >= 2:
				HEtarget[0] = float(t[1])
				gotHE[0] = True
			if len(t) >= 3:
				self.app.setBedTemp(float(t[2]))
			if len(t) >= 4:
				self.app.setBedTarget(float(t[3]))
				
			m = self.toolre.findall(msg)
			if m:
				for t in m:
					tool = int(t[0])
					if tool >= 0 and tool < MAX_EXTRUDERS:
						HEtemp[tool] = float(t[1])
						HEtarget[tool] = float(t[2])
						gotHE[tool] = True

			for i in range(MAX_EXTRUDERS):
				if gotHE[i]:
					self.app.setHETemp(i, HEtemp[i])
					self.app.setHETarget(i, HEtarget[i])
					
			if self.app.M105pending:
				self.app.M105pending = False
				return True
			else:
				return False
		
		m = self.trpt2re.search(msg)
		if m:
			t = m.groups()
			tool = 0
			gotHeTemp = False
			if len(t) >= 1:
				gotHeTemp = True
				HeTemp = float(t[0])
			if len(t) >= 2:
				tool = int(t[1])
			if len(t) >= 3:
				self.app.setBedTemp(float(t[2]))
				
			if gotHeTemp:
				self.app.setHETemp(tool, HeTemp)
			return False
		
		m = self.trpt3re.search(msg)
		if m:
			t = m.groups()
			tool = 0
			gotHeTemp = False
			if len(t) >= 1:
				HeTemp = float(t[0])
			if len(t) >= 2:
				tool = int(t[1])

			if gotHeTemp:
				self.app.setHETemp(tool, HeTemp)
			return False
		
		m = self.speedrptre.search(msg)
		if m:
			fan = None
			feed = None
			flow = None
			t = m.groups()
			if len(t) >= 1:
				fan = float(t[0])
			if len(t) >= 2:
				feed = float(t[1])
			if len(t) >= 3:
				flow = float(t[2])
				
			self.app.updateSpeeds(fan, feed, flow)
			return False
		
		m = self.toolchgre.search(msg)
		if m:
			tool = None
			t = m.groups()
			if len(t) >= 1:
				tool = int(t[0])
				
			if tool:
				self.app.setActiveTool(tool)
			return False
	
		return False
	
	def parseG(self, s, v):
		l = s.split()
		for p in l:
			if p.startswith(v):
				try:
					return float(p[1:])
				except:
					return None
		return None

class RepRap:
	def __init__(self, win, handler):
		self.win = win
		self.printer = None
		self.sender = None
		self.listener = None
		self.online = False
		self.printing = False
		self.holdFan = False
		self.restarting = False
		self.restartData = None
		win.Bind(EVT_REPRAP_UPDATE, handler)
		
	def setHoldFan(self, flag):
		self.holdFan = flag
		if self.sender is not None:
			self.sender.setHoldFan(flag)

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
			self.sender.setHoldFan(self.holdFan)
			self.sender.setCheckSum(True)
			self.listener = ListenThread(self.win, self.printer, self.sender)
			self.send_now("M105")
			self.online = True
				
	def addToAllowedCommands(self, cmd):
		allow_while_printing.append(cmd)

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
	
	def reset(self):
		self.clearPrint()
		if(self.printer):
			self.printer.setDTR(1)
			time.sleep(2)
			self.printer.setDTR(0)
	
	def startPrint(self, data):
		print "start print"
		self._sendCmd(CMD_STARTPRINT)
		for l in data:
			if l.raw.rstrip() != "":
				self._send(l.raw)

		self._sendCmd(CMD_ENDOFPRINT, priority=False)			
		self.printing = True
		self.paused = False
		
	def pausePrint(self):
		self._sendCmd(CMD_STOPPRINT)
		self.printing = False
		self.paused = True
		
	def resumePrint(self):
		print "resuming print"
		self._sendCmd(CMD_RESUMEPRINT)
		self.printing = True
		self.paused = False
		
	def restartPrint(self, data):
		print "restarting print"
		self.restarting = True
		self.restartData = data
		self._sendCmd(CMD_DRAINQUEUE)
		
	def clearPrint(self):
		self._sendCmd(CMD_DRAINQUEUE)
		
	def reprapEvent(self, evt):
		if evt.event == QUEUE_DRAINED:
			if self.restarting:
				self.startPrint(self.restartData)
				self.printing = True
				self.paused = False
				self.restarting = False
				self.restartData = None
			else:
				self.printing = False
				self.paused = False
		
	def printStopped(self):
		self.printing = False
		self.paused = True
		
	def printComplete(self):
		self.printing = False
		self.paused = False
				
	def send_now(self, cmd):
		verb = cmd.split()[0]
		if not self.printer:
			self.win.logger.LogWarning("Printer is off-line")
			return False
		elif self.printing and verb not in allow_while_printing:
			self.win.logger.LogWarning("Command not allowed while printing")
			return False
		else:
			return self._send(cmd, priority=True)
				
	def send(self, cmd):
		return self._send(cmd)

	def _send(self, command, priority=False):
		if not self.printer:
			return False
		
		if priority:		
			self.priQ.put((CMD_GCODE, command))
		else:
			self.mainQ.put((CMD_GCODE, command))
			
		return True
	
	def _sendCmd(self, cmd, priority=True):
		if priority:
			self.priQ.put((cmd, ""))
		else:
			self.mainQ.put((cmd, ""))
