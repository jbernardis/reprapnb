import wx
import os
import time
import re

from gcmframe import GcmFrame
from tempgraph import TempGraph, MAXX
from infopane import InfoPane, MODE_NORMAL, MODE_TO_SD, MODE_FROM_SD
from images import Images
from settings import (TEMPFILELABEL, BUTTONDIM, BUTTONDIMWIDE, PMSTATUS_NOT_READY, PMSTATUS_READY, PMSTATUS_PRINTING, PMSTATUS_PAUSED,
					PRINT_COMPLETE, PRINT_STOPPED, PRINT_STARTED, PRINT_MESSAGE, QUEUE_DRAINED,
					PRINT_RESUMED, PRINT_ERROR, SD_PRINT_COMPLETE, SD_PRINT_POSITION)
from sdcard import SDCard
from tools import formatElapsed

SCANTHRESHOLD = 100
	
myRed = wx.Colour(254, 142, 82, 179) 
myBlue = wx.Colour(51, 115, 254, 179)
myGreen = wx.Colour(94, 190, 82, 179)
myYellow = wx.Colour(219, 242, 37, 179)

PAUSE_MODE_PAUSE = 1
PAUSE_MODE_RESUME = 2

PRINT_MODE_PRINT = 1
PRINT_MODE_RESTART = 2

TEMPINTERVAL = 3
POSITIONINTERVAL = 1
M27Interval = 2000

gcRegex = re.compile("[-]?\d+[.]?\d*")
def _get_float(l, which):
	return float(gcRegex.findall(l.split(which)[1])[0])

class PrintMonitor(wx.Panel):
	def __init__(self, parent, app, prtname, reprap):
		self.model = None
		self.app = app
		self.buildarea = self.app.settings.printersettings[prtname].buildarea
		self.prtname = prtname
		self.reprap = reprap
		self.manctl = None

		self.M105pending = False
		self.suspendM105 = False
		self.cycle = 0
		self.skipCycles = 5
		self.logger = self.app.logger
		self.printPos = 0
		self.printing = False
		self.paused = False
		self.sdpaused = False
		self.sdprintingfrom = False
		self.settings = app.settings.printmon
		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(100, 100))
		self.SetBackgroundColour("white")
		self.knownHeaters = ['HE0', 'Bed']
		self.targets = {}
		self.temps = {}
		self.tempData = {}
		for h in self.knownHeaters:
			self.temps[h] = None
			self.targets[h] = 0
			self.tempData[h] = []
		self.startTime = None
		self.endTime = None
		self.gcFile = None
		self.printMode = None
		self.origEta = None
		self.countGLines = None
		self.syncPrint = True
		self.holdFan = False
		self.status = PMSTATUS_NOT_READY
				
		self.sdcard = SDCard(self.app, self, self.reprap, self.logger)
		
		self.M27Timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.onM27Timer, self.M27Timer)
		self.printingfrom = False

		self.sizerMain = wx.BoxSizer(wx.HORIZONTAL)
		self.sizerLeft = wx.BoxSizer(wx.VERTICAL)
		self.sizerRight = wx.BoxSizer(wx.VERTICAL)
		self.sizerLeft.AddSpacer((10,10))
		
		self.sizerBtns = wx.BoxSizer(wx.HORIZONTAL)
		self.sizerBtns.AddSpacer((10,10))

		self.images = Images(os.path.join(self.settings.cmdfolder, "images"))		
		
		self.bPull = wx.BitmapButton(self, wx.ID_ANY, self.images.pngPull, size=BUTTONDIMWIDE)
		self.sizerBtns.Add(self.bPull)
		self.bPull.SetToolTipString("Pull model from file preparation")
		self.Bind(wx.EVT_BUTTON, self.doPull, self.bPull)
		self.bPull.Enable(self.app.currentPullStatus())
		
		self.sizerBtns.AddSpacer((20, 20))
		
		self.bPrint = wx.BitmapButton(self, wx.ID_ANY, self.images.pngPrint, size=BUTTONDIM)
		self.setPrintMode(PRINT_MODE_PRINT)
		self.sizerBtns.Add(self.bPrint)
		self.Bind(wx.EVT_BUTTON, self.doPrint, self.bPrint)
		self.bPrint.Enable(False)
		
		self.bPause = wx.BitmapButton(self, wx.ID_ANY, self.images.pngPause, size=BUTTONDIM)
		self.setPauseMode(PAUSE_MODE_PAUSE)
		self.sizerBtns.Add(self.bPause)
		self.Bind(wx.EVT_BUTTON, self.doPause, self.bPause)
		self.bPause.Enable(False)

		self.sizerBtns.AddSpacer(BUTTONDIM)
		
		self.bSDPrintFrom = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSdprintfrom, size=BUTTONDIMWIDE)
		self.bSDPrintFrom.SetToolTipString("Print from SD Card")
		self.sizerBtns.Add(self.bSDPrintFrom)
		self.Bind(wx.EVT_BUTTON, self.doSDPrintFrom, self.bSDPrintFrom)
		self.bSDPrintFrom.Enable(True)
		
		self.bSDPrintTo = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSdprintto, size=BUTTONDIMWIDE)
		self.bSDPrintTo.SetToolTipString("Print to SD Card")
		self.sizerBtns.Add(self.bSDPrintTo)
		self.Bind(wx.EVT_BUTTON, self.doSDPrintTo, self.bSDPrintTo)
		self.bSDPrintTo.Enable(False)
		
		self.bSDDelete = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSddelete, size=BUTTONDIM)
		self.bSDDelete.SetToolTipString("Delete a file from SD Card")
		self.sizerBtns.Add(self.bSDDelete)
		self.Bind(wx.EVT_BUTTON, self.doSDDelete, self.bSDDelete)
		self.bSDDelete.Enable(True)
		
		self.sizerBtns.AddSpacer(BUTTONDIM)
	
		self.bZoomIn = wx.BitmapButton(self, wx.ID_ANY, self.images.pngZoomin, size=BUTTONDIM)
		self.bZoomIn.SetToolTipString("Zoom the view in")
		self.sizerBtns.Add(self.bZoomIn)
		self.Bind(wx.EVT_BUTTON, self.viewZoomIn, self.bZoomIn)
		
		self.bZoomOut = wx.BitmapButton(self, wx.ID_ANY, self.images.pngZoomout, size=BUTTONDIM)
		self.bZoomOut.SetToolTipString("Zoom the view out")
		self.sizerBtns.Add(self.bZoomOut)
		self.Bind(wx.EVT_BUTTON, self.viewZoomOut, self.bZoomOut)

		self.sizerLeft.Add(self.sizerBtns)
		self.sizerLeft.AddSpacer((10,10))
		
		self.sizerGCM = wx.BoxSizer(wx.HORIZONTAL)

		self.gcf = GcmFrame(self, self.model, self.settings, self.buildarea)
		self.sizerGCM.Add(self.gcf)
		
		sz = self.buildarea[1] * self.settings.gcodescale
		
		self.slideLayer = wx.Slider(
			self, wx.ID_ANY, 1, 1, 9999, size=(80, sz),
			style = wx.SL_VERTICAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
		self.slideLayer.Bind(wx.EVT_SCROLL_CHANGED, self.onSpinLayer)
		self.slideLayer.Bind(wx.EVT_MOUSEWHEEL, self.onMouseLayer)
		self.slideLayer.SetRange(1, 10)
		self.slideLayer.SetValue(1)
		self.slideLayer.SetPageSize(1);
		self.slideLayer.Disable()
		self.sizerGCM.Add(self.slideLayer)
		
		self.sizerLeft.Add(self.sizerGCM)

		self.sizerLeft.AddSpacer((10,10))

		self.sizerOpts = wx.BoxSizer(wx.HORIZONTAL)
				
		self.cbPrevious = wx.CheckBox(self, wx.ID_ANY, "Show Previous Layer")
		self.cbPrevious.SetToolTipString("Turn on/off drawing of the previous layer in the background")
		self.Bind(wx.EVT_CHECKBOX, self.checkPrevious, self.cbPrevious)
		self.cbPrevious.SetValue(self.settings.showprevious)
		self.sizerOpts.Add(self.cbPrevious)
		
		self.sizerOpts.AddSpacer((10, 10))

		self.cbMoves = wx.CheckBox(self, wx.ID_ANY, "Show Moves")
		self.cbMoves.SetToolTipString("Turn on/off the drawing of non-extrusion moves")
		self.Bind(wx.EVT_CHECKBOX, self.checkMoves, self.cbMoves)
		self.cbMoves.SetValue(self.settings.showmoves)
		self.sizerOpts.Add(self.cbMoves)
		
		self.sizerOpts.AddSpacer((10, 10))

		self.cbBuffDC = wx.CheckBox(self, wx.ID_ANY, "Use Buffered DC")
		self.Bind(wx.EVT_CHECKBOX, self.checkBuffDC, self.cbBuffDC)
		self.cbBuffDC.SetValue(self.settings.usebuffereddc)
		self.sizerOpts.Add(self.cbBuffDC)
		
		self.sizerOpts.AddSpacer((10, 10))

		self.cbSync = wx.CheckBox(self, wx.ID_ANY, "Sync with print")
		self.Bind(wx.EVT_CHECKBOX, self.checkSync, self.cbSync)
		self.cbSync.SetValue(True)
		self.sizerOpts.Add(self.cbSync)

		self.sizerLeft.AddSpacer((5, 5))		
		self.sizerLeft.Add(self.sizerOpts)

		self.sizerOpts2 = wx.BoxSizer(wx.HORIZONTAL)
				
		self.cbHoldFan = wx.CheckBox(self, wx.ID_ANY, "Hold Fan Speed")
		self.cbHoldFan.SetToolTipString("Maintain fan speed at its manual setting")
		self.Bind(wx.EVT_CHECKBOX, self.checkHoldFan, self.cbHoldFan)
		self.cbHoldFan.SetValue(self.holdFan)
		self.sizerOpts2.Add(self.cbHoldFan)

		self.sizerLeft.AddSpacer((5, 5))		
		self.sizerLeft.Add(self.sizerOpts2)

		self.sizerLeft.AddSpacer((10,10))
		
		self.sizerRight.AddSpacer((40,40))

		self.gTemp = TempGraph(self, self.settings)
		self.sizerRight.Add(self.gTemp)

		self.sizerRight.AddSpacer((20, 20))
		
		self.infoPane = InfoPane(self, self.app)
		self.sizerRight.Add(self.infoPane, flag=wx.EXPAND)
		
		self.sizerMain.AddSpacer((50,50))
		self.sizerMain.Add(self.sizerLeft)
		self.sizerMain.Add(self.sizerRight)

		self.SetSizer(self.sizerMain)

		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)        
		self.timer.Start(1000)
		self.reprap.setHoldFan(self.holdFan)
		
		self.infoPane.setMode(MODE_NORMAL)
		self.setSDTargetFile(None)
		
	def setManCtl(self, mc):
		self.manctl = mc;

	def assertAllowPulls(self, flag):
		self.bPull.Enable(flag)

	def tick(self):
		if self.skipCycles >= 0:
			self.skipCycles -= 1
			return
		
		self.cycle += 1

		if self.cycle % TEMPINTERVAL == 0:
			if self.suspendM105:
				self.M105pending = False
			elif not self.M105pending:
				self.M105pending = True
				self.reprap.setEatOk()
				self.reprap.send_now("M105")
				
		if self.cycle % POSITIONINTERVAL == 0:
			n = self.reprap.getPrintPosition()
			if n is not None:
				self.printPosition = n
				self.updatePrintPosition(n)
				
	def suspendTempProbe(self, flag):
		self.suspendM105 = flag
		
	def prtMonEvent(self, evt):
		if evt.event == SD_PRINT_POSITION:
			if self.sdprintingfrom:
				if evt.pos < evt.max:
					self.infoPane.setSDPrintInfo(evt.pos, evt.max)
					self.M27Timer.Start(M27Interval, True)
				else:
					self.sdprintingfrom = False
					self.setPrintMode(PRINT_MODE_PRINT)
					self.bPrint.Enable(self.hasFileLoaded())
					self.bPull.Enable(True)
					self.setPauseMode(PAUSE_MODE_PAUSE)
					self.bPause.Enable(False)
					self.bSDPrintFrom.Enable(True)
					self.bSDPrintTo.Enable(self.hasFileLoaded())
					self.bSDDelete.Enable(True)
					self.infoPane.setSDPrintComplete()
			return

		if evt.event == SD_PRINT_COMPLETE:
			return
	
	def setStatus(self, s):
		print "printmon set status to ", s
		self.status = s
		self.app.updatePrintMonStatus(self.prtname, s)
		
	def isPrinting(self):
		return self.printing or self.sdprintingfrom
		
	def getStatus(self):
		if self.printing or self.sdprintingfrom:
			status = self.infoPane.getStatus()
			status['printing'] = "True"
		else:
			status = {}
			status['printing'] = "False"
			
		return status
		
	def hasFileLoaded(self):
		return self.model is not None
	
	def getBedGCode(self):
		if not self.hasFileLoaded():
			return None;
		
		i = 0
		for l in self.model:
			if l.raw.startswith("M140 ") or l.raw.startswith("M190 "):
				if "S" in l.raw:
					temp = _get_float(l.raw, "S")
					return temp

			i += 1
			if i >= SCANTHRESHOLD:
				return None
	
	def getHEGCode(self, tool):
		if not self.hasFileLoaded():
			return None;
		
		i = 0
		for l in self.model:
			if l.raw.startswith("M104 ") or l.raw.startswith("M109 "):
				t = 1
				if "T" in l.raw:
					t = _get_float(l.raw, "T")
					
				if (t-1) == tool:
					if "S" in l.raw:
						temp = _get_float(l.raw, "S")
						return temp

			i += 1
			if i >= SCANTHRESHOLD:
				return None
	
	def printerReset(self):
		self.printPos = 0
		self.skipCycles = 5
		self.M105pending = False
		self.printing = False
		self.paused = False
		self.sdpaused = False
		self.sdprintingfrom = False
		print "printer reset status to ready"
		self.setStatus(PMSTATUS_READY)
		self.setPrintMode(PRINT_MODE_PRINT)
		self.setPauseMode(PAUSE_MODE_PAUSE)
		self.bPrint.Enable(self.hasFileLoaded())
		self.bPull.Enable(True)
		self.bPause.Enable(False)
		
	def doSDPrintFrom(self, evt):
		self.sdcard.startPrintFromSD()
		
	def resumeSDPrintFrom(self, fn):
		self.reprap.send_now("M23 " + fn[1].lower())
		self.reprap.send_now("M24")
		self.sdprintingfrom = True
		self.M27Timer.Start(M27Interval, True)
		self.bPrint.Enable(False)
		self.bPull.Enable(False)
		self.bSDPrintFrom.Enable(False)
		self.bSDPrintTo.Enable(False)
		self.bSDDelete.Enable(False)
		self.setPauseMode(PAUSE_MODE_PAUSE)
		self.bPause.Enable(True)
		self.sdpaused = False
		self.infoPane.setMode(MODE_FROM_SD)
		self.infoPane.setSDStartTime(time.time())
		
	def doSDPrintTo(self, evt):
		self.sdcard.startPrintToSD()
		
	def resumeSDPrintTo(self, tfn):
		self.setSDTargetFile(tfn[1].lower())
		self.suspendTempProbe(True)
		self.reprap.send_now("M28 %s" % self.sdTargetFile)
		self.printPos = 0
		self.startTime = time.time()
		self.endTime = None
		self.reprap.startPrint(self.model)
		self.logger.LogMessage("Print to SD: %s started at %s" % (self.sdTargetFile, time.strftime('%H:%M:%S', time.localtime(self.startTime))))
		self.origEta = self.startTime + self.model.duration
		self.countGLines = len(self.model)
		self.infoPane.setMode(MODE_TO_SD)
		self.infoPane.setStartTime(self.startTime)
		self.bPrint.Enable(False)
		self.bPull.Enable(False)
		self.bPause.Enable(False)
		
	def setSDTargetFile(self, tfn):
		self.sdTargetFile = tfn
		self.infoPane.setSDTargetFile(tfn)
		
	def doSDDelete(self, evt):
		self.sdcard.startDeleteFromSD()
		
	def reprapEvent(self, evt):
		if evt.event in [ PRINT_STARTED, PRINT_RESUMED ]:
			self.printing = True
			print "reprapevent started/resumed status printing"
			self.setStatus(PMSTATUS_PRINTING)
			self.paused = False
			self.setPrintMode(PRINT_MODE_PRINT)
			self.setPauseMode(PAUSE_MODE_PAUSE)
			self.bPrint.Enable(False)
			self.bPull.Enable(False)
			self.bPause.Enable(True)
			self.bSDPrintFrom.Enable(False)
			self.bSDPrintTo.Enable(False)
			self.bSDDelete.Enable(False)
			
		elif evt.event == PRINT_STOPPED:
			self.paused = True
			print "reprapevent stopped status paused"
			self.setStatus(PMSTATUS_PAUSED)
			self.printing = False
			self.reprap.printStopped()
			self.setPrintMode(PRINT_MODE_RESTART)
			self.setPauseMode(PAUSE_MODE_RESUME)
			self.bPrint.Enable(True)
			self.bPull.Enable(True)
			self.bPause.Enable(True)
			self.bSDPrintFrom.Enable(True)
			self.bSDPrintTo.Enable(True)
			self.bSDDelete.Enable(True)
			
		elif evt.event == PRINT_COMPLETE:
			
			self.endTime = time.time()
			self.infoPane.setPrintComplete()
			if self.sdTargetFile is not None:
				self.reprap.send_now("M29 %s" % self.sdTargetFile)
				self.suspendTempProbe(False)
				self.setSDTargetFile(None)

			self.printing = False
			self.paused = False
			print "reprapevent complete - status ready"
			self.setStatus(PMSTATUS_READY)
			self.reprap.printComplete()
			self.setPrintMode(PRINT_MODE_PRINT)
			self.setPauseMode(PAUSE_MODE_PAUSE)
			self.bPrint.Enable(True)
			self.bPull.Enable(True)
			self.bPause.Enable(False)
			self.bSDPrintFrom.Enable(True)
			self.bSDPrintTo.Enable(True)
			self.bSDDelete.Enable(True)
			self.logger.LogMessage("Print completed at %s" % time.strftime('%H:%M:%S', time.localtime(self.endTime)))
			self.logger.LogMessage("Total elapsed time: %s" % formatElapsed(self.endTime - self.startTime))
			rs, rq = self.reprap.getCounters()
			if rs + rq != 0:
				self.logger.LogMessage("Resend Requests: %d, messages retransmitted: %d" % (rq, rs))
			self.updatePrintPosition(0)
			
		elif evt.event == PRINT_ERROR:
			self.logger.LogError(evt.msg)
# 			self.paused = False
# 			self.setStatus(PMSTATUS_NOT_READY)
# 			self.printing = False
# 			self.reprap.printComplete()
# 			self.setPrintMode(PRINT_MODE_PRINT)
# 			self.setPauseMode(PAUSE_MODE_PAUSE)
# 			self.bPrint.Enable(True)
# 			self.bPull.Enable(True)
# 			self.bPause.Enable(True)
# 			self.bSDPrintFrom.Enable(True)
# 			self.bSDPrintTo.Enable(True)
# 			self.bSDDelete.Enable(True)
			self.app.doPrinterError(self.prtname)
			
		elif evt.event == PRINT_MESSAGE:
			if evt.primary:
				self.logger.LogCMessage(evt.msg)
			else:
				self.logger.LogGMessage(evt.msg)

		elif evt.event == QUEUE_DRAINED:
			self.logger.LogMessage("Print Queue drained")
			self.reprap.reprapEvent(evt)
		else:
			self.reprap.reprapEvent(evt)
			
	def getPrintTimes(self):
		return self.startTime, self.endTime
	
	def onM27Timer(self, evt):
		if not self.app.M27Pending:
			self.app.M27Pending = True
			self.reprap.send_now("M27")

	def setPrintMode(self, mode):
		self.printMode = mode
		if mode == PRINT_MODE_PRINT:
			self.bPrint.SetToolTipString("Start the print")
			self.bPrint.SetBitmapLabel(self.images.pngPrint)
		elif mode == PRINT_MODE_RESTART:
			self.bPrint.SetToolTipString("Restart the print")
			self.bPrint.SetBitmapLabel(self.images.pngRestart)

	def setPauseMode(self, mode):
		if mode == PAUSE_MODE_PAUSE:
			self.bPause.SetToolTipString("Pause the print")
		elif mode == PAUSE_MODE_RESUME:
			self.bPause.SetToolTipString("Resume the print from the paused point")
		
	def doPrint(self, evt):
		if self.sdpaused:
			self.reprap.send_now("M26 S0")
			self.setPauseMode(PAUSE_MODE_PAUSE)
			self.setPrintMode(PRINT_MODE_PRINT)
			self.bPrint.Enable(False)
			self.bPull.Enable(False)
			self.sdprintingfrom = True
			self.reprap.send_now("M24")
			self.infoPane.setSDStartTime(time.time())
			self.M27Timer.Start(M27Interval, True)
		else:
			self.printPos = 0
			self.startTime = time.time()
			self.endTime = None
			if self.printMode == PRINT_MODE_RESTART:
				action = "restarted"
				self.reprap.restartPrint(self.model)
			else:
				action = "started"
				self.reprap.startPrint(self.model)
			self.logger.LogMessage("Print %s at %s" % (action, time.strftime('%H:%M:%S', time.localtime(self.startTime))))
			self.origEta = self.startTime + self.model.duration
			self.logger.LogMessage("ETA at %s (%s)" % (time.strftime('%H:%M:%S', time.localtime(self.startTime+self.model.duration)), formatElapsed(self.model.duration)))
			self.countGLines = len(self.model)
			self.infoPane.setMode(MODE_NORMAL)
			self.infoPane.setStartTime(self.startTime)
			self.bPrint.Enable(False)
			self.bPull.Enable(False)
			self.bPause.Enable(False)
			self.setSDTargetFile(None)
		
	def doPause(self, evt):
		if self.sdTargetFile is not None:
			msgdlg = wx.MessageDialog(self.app, "Are you sure you want to terminate this job",
					'Confirm', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
			rc = msgdlg.ShowModal()
			msgdlg.Destroy()
			
			if rc == wx.ID_YES:
				self.stopPrintToSD()
		
		elif self.sdprintingfrom or self.sdpaused:
			if self.sdpaused:
				self.reprap.send_now("M24")
				self.setPauseMode(PAUSE_MODE_PAUSE)
				self.setPrintMode(PRINT_MODE_PRINT)
				self.bPrint.Enable(False)
				self.bPull.Enable(False)
				self.sdprintingfrom = True
				self.M27Timer.Start(M27Interval, True)
				self.sdpaused = False
			else:
				self.stopPrintFromSD()

		else:
			if self.paused:
				self.bPause.Enable(False)
				self.bPrint.Enable(False)
				self.bPull.Enable(False)
				self.reprap.resumePrint()
			else:
				self.stopPrintNormal()
				
	def stopPrint(self):
		result = {}
		if self.sdTargetFile is not None:
			self.stopPrintToSD()
			result['result'] = "Success - Print to SD stopped"
			
		elif self.sdprintingfrom:
			self.stopPrintFromSD()
			self.stopMotorsAndHeaters()
			result['result'] = "Success - Print from SD stopped"
			
		else:
			self.stopPrintNormal()
			self.stopMotorsAndHeaters()
			result['result'] = "Success - Print stopped"
			
		return result
			
	def stopPrintToSD(self):
		self.reprap.pausePrint()
		self.reprap.send_now("M29 %s" % self.sdTargetFile)
		self.setPauseMode(PAUSE_MODE_PAUSE)
		self.bPause.Enable(False)
		self.setPrintMode(PRINT_MODE_PRINT)
		self.bPrint.Enable(self.hasFileLoaded())
		self.bPull.Enable(True)
		self.bSDPrintFrom(True)
		self.bSDPrintTo(True)
		self.bSDDelete(True)
		self.setSDTargetFile(None)
		self.suspendTempProbe(False)
		
	def stopPrintFromSD(self):
		self.reprap.send_now("M25")
		self.setPauseMode(PAUSE_MODE_RESUME)
		self.setPrintMode(PRINT_MODE_RESTART)
		self.bPrint.Enable(self.hasFileLoaded())
		self.bPull.Enable(True)
		self.sdprintingfrom = False
		self.sdpaused = True
		
	def stopPrintNormal(self):
		self.bPause.Enable(False)
		self.bPrint.Enable(False)
		self.bPull.Enable(False)
		self.reprap.pausePrint()
		
	def stopMotorsAndHeaters(self):
		self.reprap.send_now("M84")
		self.reprap.send_now("M106 S0")
		self.reprap.send_now("M140 S0")
		for h in self.knownHeaters:
			if h.startswith("HE"):
				self.reprap.send_now("M104 S0 T" + h[2])
		
	def updatePrintPosition(self, pos):
		if self.printing:
			if pos != self.printPos:
				self.printPos = pos
				self.gcf.setPrintPosition(self.printPos, self.syncPrint)
				
			l = self.model.findLayerByLine(pos)
			gcl = None
			lt = None
			if l is not None:
				gcl = self.model.layerlines[l]
				lt = self.model.layer_time[l]
			self.infoPane.setPrintInfo(pos, l, gcl, lt)
		
	def onMouseLayer(self, evt):
		l = self.slideLayer.GetValue()-1
		if evt.GetWheelRotation() < 0:
			l += 1
		else:
			l -= 1
		if l >= 0 and l < self.layerCount:
			self.gcf.setLayer(l)
			self.setLayer(l)

	def onSpinLayer(self, evt):
		l = evt.EventObject.GetValue()-1
		self.gcf.setLayer(l)
		self.setLayer(l)
		
	def setLayer(self, l):
		if l >=0 and l < self.layerCount:
			self.slideLayer.SetValue(l+1)
			(zh, xymin, xymax, filament, glines, time, filstart) = self.model.getLayerInfo(l)
			self.infoPane.setLayerInfo(l, zh, xymin, xymax, filament, filstart, time, glines)

	def onClose(self, evt):
		return True
		
	def viewZoomIn(self, evt):
		self.gcf.zoomIn()
		
	def viewZoomOut(self, evt):
		self.gcf.zoomOut()
		
	def checkSync(self, evt):
		self.syncPrint = evt.IsChecked()
		
	def checkBuffDC(self, evt):
		self.settings.usebuffereddc = evt.IsChecked()
		self.settings.setModified()
		self.gcf.redrawCurrentLayer()
		
	def checkHoldFan(self, evt):
		self.holdFan = evt.IsChecked()
		self.reprap.setHoldFan(self.holdFan)
		
	def checkPrevious(self, evt):
		self.settings.showprevious = evt.IsChecked()
		self.settings.setModified()
		self.gcf.redrawCurrentLayer()
		
	def checkMoves(self, evt):
		self.settings.showmoves = evt.IsChecked()
		self.settings.setModified()
		self.gcf.redrawCurrentLayer()
		
	def doPull(self, evt):
		self.app.pullGCode(self)
	
	def forwardModel(self, model, name=""):
		self.setSDTargetFile(None)
		
		print "starting forward - status not ready"
		self.setStatus(PMSTATUS_NOT_READY)
		self.reprap.clearPrint()
		self.model = model
		self.name = name
		if self.name == TEMPFILELABEL:
			self.gcFile = None
		elif len(self.name) > 40:
			self.gcFile = self.name
			self.name = os.path.basename(self.gcFile)
		else:
			self.gcFile = self.name
			
		layer = 0

		self.layerCount = self.model.countLayers()
		
		self.layerInfo = self.model.getLayerInfo(layer)
		if self.layerInfo is None:
			return
		
		self.slideLayer.SetRange(1, self.layerCount)
		n = int(self.layerCount/20)
		if n<1: n=1
		self.slideLayer.SetTickFreq(n, 1)
		self.slideLayer.SetPageSize(1);
		self.slideLayer.Enable()
		self.slideLayer.Refresh()
		
		self.gcf.loadModel(self.model, layer=layer)
		self.enableButtons()
		
		self.printPos = 0
		self.printing = False
		self.paused = False

		self.setPrintMode(PRINT_MODE_PRINT)
		self.setPauseMode(PAUSE_MODE_PAUSE)
		self.bPrint.Enable(self.hasFileLoaded())
		self.bPull.Enable(True)
		self.bPause.Enable(False)
		self.bSDPrintFrom.Enable(True)
		self.bSDPrintTo.Enable(self.hasFileLoaded())
		self.bSDDelete.Enable(True)
		self.sdprintingfrom = False
		self.sdpaused = False
		
		self.bPull.Enable(True)
		print "ending forward status ready"
		self.setStatus(PMSTATUS_READY)
		self.infoPane.setFileInfo(self.name, self.model.duration, len(self.model), self.layerCount, self.model.total_e, self.model.layer_time)
		self.setLayer(layer)
		
	def disconnect(self):
		print "disconnect - status not ready"
		self.setStatus(PMSTATUS_NOT_READY)
		self.targets = {}
		self.temps = {}
		self.tempData = {}
		for h in self.knownHeaters:
			self.temps[h] = None
			self.targets[h] = 0
			self.tempData[h] = []

		self.gTemp.setTemps(self.tempData)
		self.gTemp.setTargets({})
		
	def setHETarget(self, tool, temp):
		key = 'HE' + str(tool)
		self.targets[key] = temp
		self.gTemp.setTargets(self.targets)
		
	def setHETemp(self, tool, temp):
		key = 'HE' + str(tool)
		self.temps[key] = temp
			
	def setBedTarget(self, temp):
		self.targets['Bed'] = temp
		self.gTemp.setTargets(self.targets)
		
	def setBedTemp(self, temp):
		self.temps['Bed'] = temp
		
	def getTemps(self):
		temps = {}
		temps['temps'] = self.temps
		temps['targets'] = self.targets
		return temps
		
	def onTimer(self, evt):
		for h in self.knownHeaters:
			if h in self.temps.keys():
				self.tempData[h].append(self.temps[h])
			else:
				self.tempData[h].append(None)
			l = len(self.tempData[h])
			if l > MAXX: # 4 minutes data
				self.tempData[h] = self.tempData[h][l-MAXX:]
		self.gTemp.setTemps(self.tempData)
		
	def enableButtons(self, flag=True):
		if flag:
			if self.model is not None:
				self.slideLayer.Enable(True)
			else:
				self.slideLayer.Enable(False)
		else:
			self.slideLayer.Enable(False)
