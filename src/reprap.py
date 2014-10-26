from serial import Serial
import thread
import Queue
import time
import wx
import re
import wx.lib.newevent

TRACE = False

(RepRapEvent, EVT_REPRAP_UPDATE) = wx.lib.newevent.NewEvent()
(SDCardEvent, EVT_SD_CARD) = wx.lib.newevent.NewEvent()
(PrtMonEvent, EVT_PRINT_MONITOR) = wx.lib.newevent.NewEvent()

from settings import (MAX_EXTRUDERS, SD_PRINT_COMPLETE, SD_PRINT_POSITION, SD_CARD_OK, SD_CARD_FAIL, SD_CARD_LIST,
		PRINT_COMPLETE, PRINT_STOPPED, PRINT_AUTOSTOPPED, PRINT_STARTED, PRINT_RESUMED, PRINT_MESSAGE, QUEUE_DRAINED, RECEIVED_MSG, PRINT_ERROR,
		CMD_GCODE, CMD_STARTPRINT, CMD_STOPPRINT, CMD_DRAINQUEUE, CMD_ENDOFPRINT, CMD_RESUMEPRINT)

CACHE_SIZE = 50

# printer commands that are permissible while actively printing
allow_while_printing = [ "M0", "M1", "M20", "M21", "M22", "M23", "M25", "M27", "M29", "M30", "M31", "M42", "M82", "M83", "M85", "M92",
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
		self.resends = 0
		self.pendingPauseLayers = []
		self.sentCache = MsgCache(CACHE_SIZE)
		thread.start_new_thread(self.Run, ())
		
	def checkPendingPause(self, layer):
		for i in range(len(self.pendingPauseLayers)):
			ln = self.pendingPauseLayers[i][0]
			if ln == layer:
				return True
			
		return False
		
	def kill(self):
		self.isRunning = False
		
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
		
	def resetCounters(self):
		self.resends = 0
		
	def getCounters(self):
		return self.resends
			
	def _checksum(self,command):
		return reduce(lambda x,y:x^y, map(ord,command))

	def Run(self):
		self.isRunning = True
		while self.isRunning:
			if self.isPrinting:
				if not self.priQ.empty():
					try:
						(cmd, string) = self.priQ.get(True, 0.01)
						self.processCmd(cmd, string, False, False, True)
					except Queue.Empty:
						pass
					
				elif self.resendFrom is not None:
					string = self.sentCache.getMsg(self.resendFrom)
					if string is None:
						self.resendFrom = None
					else:
						self.resends += 1
						self.resendFrom += 1
						self.processCmd(CMD_GCODE, string, False, True, False)
					
				elif not self.okWait:
					if not self.mainQ.empty():
						try:
							(cmd, string, index) = self.mainQ.get(True, 0.01)
							self.processCmd(cmd, string, True, True, False, index=index)

						except Queue.Empty:
							pass
					else:
						time.sleep(0.001)
				else:
					time.sleep(0.001)

			else:
				try:
					(cmd, string) = self.priQ.get(True, 0.01)
					self.processCmd(cmd, string, False, False, True)
				except Queue.Empty:
					time.sleep(0.01)
		self.endoflife = True
		self.printer = None
				
	def processCmd(self, cmd, string, calcCS, setOK, PriQ, index=None):
		if cmd == CMD_GCODE:
			if string.startswith('@'):
				cl = self.metaCommand(string)
			else: 
				cl = [string]
				
			for st in cl: 
				if calcCS:
					if index is not None:
						self.printIndex = index
					try:
						verb = st.split()[0]
					except:
						verb = ""
					
					if (verb == "M106" or verb == "M107") and self.holdFan:
						return
					
					if self.checksum:
						prefix = "N" + str(self.sequence) + " " + st
						st = prefix + "*" + str(self._checksum(prefix))
						if verb != "M110":
							self.sentCache.addMsg(self.sequence, st)
						self.sequence += 1
					
				if setOK: self.okWait = True
				if TRACE:
					print "==>", self.okWait, st
					
				evt = RepRapEvent(event = PRINT_MESSAGE, msg = st, primary=PriQ, immediate=False)
				wx.PostEvent(self.win, evt)
					
				try:
					self.printer.write(str(st+"\n"))
				except:
					evt = RepRapEvent(event = PRINT_ERROR, msg="Unable to write to printer")
					wx.PostEvent(self.win, evt)
					self.kill()
			
		elif cmd == CMD_STARTPRINT:
			string = "M110"
			if self.checksum:
				prefix = "N-1 " + string
				string = prefix + "*" + str(self._checksum(prefix))
				
			self.okWait = True

			try:
				self.printer.write(str(string+"\n"))
			except:
				evt = RepRapEvent(event = PRINT_ERROR, msg="Unable to write to printer")
				wx.PostEvent(self.win, evt)
				self.kill()
				
			if TRACE:
				print "==>", self.okWait, string
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
					(cmd, string, index) = self.mainQ.get(False)
					if cmd == CMD_ENDOFPRINT:
						break
				except Queue.Empty:
					break
			evt = RepRapEvent(event = QUEUE_DRAINED)
			wx.PostEvent(self.win, evt)
	
	def metaCommand(self, cmd):
		l = cmd.split()
		nl = len(l)
		
		if nl < 1:
			return []
		
		nl -= 1
		verb = l[0]
		l = l[1:]
		
		values = {}
		
		for term in l:
			try:
				name, val = term.split("=")
				values[name.lower()] = val
			except:
				pass
		
		if verb.lower() == "@pause":
			if 'layer' in values.keys():
				try:
					x = int(values['layer'])
					lift = None
					if 'lift' in values.keys():
						lift = float(values['lift'])
					self.pendingPauseLayers.append((x, lift))

				except:
					pass
				return []
			else:
				self.isPrinting = False
				self.sentCache.reinit()
				self.resendFrom = None
				evt = RepRapEvent(event = PRINT_AUTOSTOPPED, msg="pause meta command")
				wx.PostEvent(self.win, evt)
				
				if 'lift' in values.keys():
					return [ "G91", "G1 Z%s F500" % values['lift'], "G90" ]
				else:
					return []
			
		elif verb.lower() == "@layerchange":
			print "Layer change layer number = %s" % values['layer']
			try:
				thisLayer = int(values['layer'])
			except:
				thisLayer = -1
			for i in range(len(self.pendingPauseLayers)):
				ln, lift = self.pendingPauseLayers[i]
				if ln == thisLayer:
					self.isPrinting = False
					self.sentCache.reinit()
					self.resendFrom = None
					evt = RepRapEvent(event = PRINT_AUTOSTOPPED, msg="matching layer number")
					wx.PostEvent(self.win, evt)
					del self.pendingPauseLayers[i]
					if lift is not None:
						return [ "G91", "G1 Z%.3f F500" % lift, "G90" ]
					else:
						return []
			return []
		
		return []

class ListenThread:
	def __init__(self, win, printer, sender):
		self.win = win
		self.printer = printer
		self.isRunning = False
		self.endoflife = False
		self.sender = sender
		self.eatOK = 0
		self.resendRequests = 0
		self.resendre = re.compile("resend: *([0-9]+)")
		thread.start_new_thread(self.Run, ())
		
	def kill(self):
		self.isRunning = False
		
	def resetCounters(self):
		self.resendRequests = 0
		
	def getCounters(self):
		return self.resendRequests
		
	def isKilled(self):
		return self.endoflife
	
	def setEatOk(self):
		self.eatOK = 1
		
	def Run(self):
		self.isRunning = True
		while self.isRunning:
			if(not self.printer or not self.printer.isOpen):
				break
			try:
				line=self.printer.readline()
			except:
				evt = RepRapEvent(event = PRINT_ERROR, msg="Unable to read from printer")
				wx.PostEvent(self.win, evt)
				self.kill()
				break

			if(len(line)>1):
				if TRACE:
					print "<==", line
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
							self.resendRequests += 1
							self.sender.setResendFrom(n)
				
				if llow.startswith("ok"):
					if self.eatOK > 0:
						if TRACE:
							print "EATEN"
						self.eatOK -= 1
					else:
						self.sender.endWait()

				if llow == "ok":
					continue
						
				if line.startswith("echo:"):
					line = line[5:]

				evt = RepRapEvent(event=RECEIVED_MSG, msg = line.rstrip(), state = 1)
				wx.PostEvent(self.win, evt)

		self.endoflife = True
		self.printer = None

class RepRapParser:
	def __init__(self, app):
		self.app = app
		self.firmware = None
		self.manctl = None
		self.printmon = None
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

	def config(self, pm, mc):
		self.printmon = pm
		self.manctl = mc
		self.firmware = mc.firmware
		pm.Bind(EVT_SD_CARD, pm.sdcard.sdEvent)
		pm.Bind(EVT_PRINT_MONITOR, pm.prtMonEvent)
		
	def parseMsg(self, msg):
		if 'M92' in msg:
			X = self.parseG(msg, 'X')
			Y = self.parseG(msg, 'Y')
			Z = self.parseG(msg, 'Z')
			E = self.parseG(msg, 'E')
			if self.firmware is not None:
				self.firmware.m92(X, Y, Z, E)
			return False
		
		if 'M201' in msg:
			X = self.parseG(msg, 'X')
			Y = self.parseG(msg, 'Y')
			Z = self.parseG(msg, 'Z')
			E = self.parseG(msg, 'E')
			if self.firmware is not None:
				self.firmware.m201(X, Y, Z, E)
			return False
		
		if 'M203' in msg:
			X = self.parseG(msg, 'X')
			Y = self.parseG(msg, 'Y')
			Z = self.parseG(msg, 'Z')
			E = self.parseG(msg, 'E')
			if self.firmware is not None:
				self.firmware.m203(X, Y, Z, E)
			return False
		
		if 'M204' in msg:
			S = self.parseG(msg, 'S')
			T = self.parseG(msg, 'T')
			if self.firmware is not None:
				self.firmware.m204(S, T)
			return False
		
		if 'M205' in msg:
			S = self.parseG(msg, 'S')
			T = self.parseG(msg, 'T')
			B = self.parseG(msg, 'B')
			X = self.parseG(msg, 'X')
			Z = self.parseG(msg, 'Z')
			E = self.parseG(msg, 'E')
			if self.firmware is not None:
				self.firmware.m205(S, T, B, X, Z, E)
			return False
		
		if 'M206' in msg:
			X = self.parseG(msg, 'X')
			Y = self.parseG(msg, 'Y')
			Z = self.parseG(msg, 'Z')
			if self.firmware is not None:
				self.firmware.m206(X, Y, Z)
			return False
		
		if 'M301' in msg:
			P = self.parseG(msg, 'P')
			I = self.parseG(msg, 'I')
			D = self.parseG(msg, 'D')
			if self.firmware is not None:
				self.firmware.m301(P, I, D)
			return False
		
		if "SD card ok" in msg:
			evt = SDCardEvent(event = SD_CARD_OK)
			wx.PostEvent(self.printmon, evt)
			return False
		
		if "SD init fail" in msg:
			evt = SDCardEvent(event = SD_CARD_FAIL)
			wx.PostEvent(self.printmon, evt)
			return False
				
		if "Begin file list" in msg:
			self.insideListing = True
			self.sdfiles = []
			return False
		
		if "End file list" in msg:
			self.insideListing = False
			evt = SDCardEvent(event = SD_CARD_LIST, data=self.sdfiles)
			wx.PostEvent(self.printmon, evt)
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
			evt = PrtMonEvent(event=SD_PRINT_POSITION, pos=gpos, max=gmax)
			wx.PostEvent(self.printmon, evt)
			if self.printmon.M27pending:
				self.printmon.M27pending = False
				return True
			else:
				return False
			
		if "Done printing file" in msg:
			evt = PrtMonEvent(event=SD_PRINT_COMPLETE)
			wx.PostEvent(self.printmon, evt)
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
				self.setBedTemp(float(t[2]))
			if len(t) >= 4:
				self.setBedTarget(float(t[3]))
				
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
					self.setHETemp(i, HEtemp[i])
					self.setHETarget(i, HEtarget[i])
	
			if self.printmon.M105pending:
				self.printmon.M105pending = False
				return True
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
				self.setBedTemp(float(t[2]))
				
			if gotHeTemp:
				self.setHETemp(tool, HeTemp)
			return False
		
		m = self.trpt3re.search(msg)
		if m:
			t = m.groups()
			tool = 0
			gotHeTemp = False
			if len(t) >= 1:
				gotHeTemp = True
				HeTemp = float(t[0])
			if len(t) >= 2:
				tool = int(t[1])

			if gotHeTemp:
				self.setHETemp(tool, HeTemp)
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
				
			if self.manctl is not None:
				self.manctl.updateSpeeds(fan, feed, flow)
			return False
		
		m = self.toolchgre.search(msg)
		if m:
			tool = None
			t = m.groups()
			if len(t) >= 1:
				tool = int(t[0])
				
			if tool is not None and self.manualctl is not None:
				self.manualctl.setActiveTool(tool)
			return False
	
		return False

	def setHETarget(self, tool, val):
		if self.printmon is not None:
			self.printmon.setHETarget(tool, val)
		if self.manctl is not None:
			self.manctl.setHETarget(tool, val)
	
	def setHETemp(self, tool, val):
		if self.printmon is not None:
			self.printmon.setHETemp(tool, val)
		if self.manctl is not None:
			self.manctl.setHETemp(tool, val)
	
	def setBedTarget(self, val):
		if self.printmon is not None:
			self.printmon.setBedTarget(val)
		if self.manctl is not None:
			self.manctl.setBedTarget(val)
	
	def setBedTemp(self, val):
		if self.printmon is not None:
			self.printmon.setBedTemp(val)
		if self.manctl is not None:
			self.manctl.setBedTemp(val)
	
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
	def __init__(self, app):
		self.app = app
		self.printer = None
		self.sender = None
		self.listener = None
		self.online = False
		self.printing = False
		self.holdFan = False
		self.restarting = False
		self.restartData = None
		
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
			self.printer = Serial(self.port, self.baud, timeout=2)
		
	def bind(self, win, handler):
		win.Bind(EVT_REPRAP_UPDATE, handler)
		self.sender = SendThread(win, self.printer, self.priQ, self.mainQ)
		self.sender.setHoldFan(self.holdFan)
		self.sender.setCheckSum(True)
		self.listener = ListenThread(win, self.printer, self.sender)
		self.online = True
		
	def checkPendingPause(self, layer):
		if self.sender is None:
			return False
		
		return self.sender.checkPendingPause(layer)

	def addToAllowedCommands(self, cmd):
		allow_while_printing.append(cmd)
		
	def setEatOk(self):
		self.listener.setEatOk()

	def getPrintPosition(self):
		if self.sender and self.sender.isPrinting:
			return self.sender.getPrintIndex()
		else:
			return None

	def disconnect(self):
		if self.listener and not self.listener.isKilled():
			self.listener.kill()
		if self.sender and not self.sender.isKilled():
			self.sender.kill()
	
	def checkDisconnection(self):
		if self.listener is None and self.sender is None:
			return True
		if self.listener and not self.listener.isKilled():
			return False
		if self.sender and not self.sender.isKilled():
			return False
		
		if(self.printer):
			self.printer.close()
			
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
		self.sender.resetCounters()
		self.listener.resetCounters()
		self._sendCmd(CMD_STARTPRINT)
		idx = -1
		layerIdx = -1
		endline = -1
		self._send("@layerchange layer=0")
		for l in data:
			idx += 1
			if idx > endline:
				layerIdx += 1
				linfo = data.getLayerInfo(layerIdx)
				z = linfo[0]
				startline = linfo[4][0]
				endline = linfo[4][1]
				print "New Layer at line %d new s/e=(%d,%d) new z = %.3f, layernumber=%s" % (idx, startline, endline, z, layerIdx)
				self._send("@layerchange layer=%d" % (layerIdx+1))
				
			if l.raw.rstrip() != "":
				self._send(l.raw, index=idx)

		self._sendCmd(CMD_ENDOFPRINT, priority=False)			
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
		
	def getCounters(self):
		return self.sender.getCounters(), self.listener.getCounters()
		
	def restartPrint(self, data):
		self.sender.resetCounters()
		self.listener.resetCounters()
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
			self.app.logger.LogWarning("Printer is off-line")
			return False
		elif self.printing and verb not in allow_while_printing:
			self.app.logger.LogWarning("Command not allowed while printing")
			return False
		else:
			return self._send(cmd, priority=True)
				
	def send(self, cmd):
		return self._send(cmd)

	def _send(self, command, priority=False, index=None):
		if not self.printer:
			return False
		
		if priority:		
			self.priQ.put((CMD_GCODE, command))
		else:
			self.mainQ.put((CMD_GCODE, command, index))
			
		return True
	
	def _sendCmd(self, cmd, priority=True):
		if priority:
			self.priQ.put((cmd, ""))
		else:
			self.mainQ.put((cmd, "", None))
