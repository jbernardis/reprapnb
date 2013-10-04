import wx
import os
import time
from gcmframe import GcmFrame
from tempgraph import TempGraph, MAXX
from infopane import InfoPane
from images import Images
from settings import TEMPFILELABEL
from reprap import (PRINT_COMPLETE, PRINT_STOPPED, PRINT_STARTED,
					PRINT_RESUMED)
from tools import formatElapsed

BUTTONDIM = (48, 48)
#FIXIT Start/Pause/Restart, SD printing, follow print progress, fan control, speed control",
	
myRed = wx.Colour(254, 142, 82, 179) 
myBlue = wx.Colour(51, 115, 254, 179)
myGreen = wx.Colour(94, 190, 82, 179)
myYellow = wx.Colour(219, 242, 37, 179)

PAUSE_MODE_PAUSE = 1
PAUSE_MODE_RESUME = 2

PRINT_MODE_PRINT = 1
PRINT_MODE_RESTART = 2

PMSTATUS_NOT_READY = 0
PMSTATUS_READY = 1
PMSTATUS_PRINTING = 2
PMSTATUS_PAUSED = 3

class PrintMonitor(wx.Panel):
	def __init__(self, parent, app, reprap):
		self.model = None
		self.app = app
		self.buildarea = self.app.buildarea
		self.reprap = reprap
		self.logger = self.app.logger
		self.printPos = 0
		self.printing = False
		self.paused = False
		self.settings = app.settings.printmon
		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(100, 100))
		self.SetBackgroundColour("white")
		self.knownHeaters = ['HE', 'Bed']
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
		self.status = PMSTATUS_NOT_READY

		self.sizerMain = wx.BoxSizer(wx.HORIZONTAL)
		self.sizerLeft = wx.BoxSizer(wx.VERTICAL)
		self.sizerRight = wx.BoxSizer(wx.VERTICAL)
		self.sizerLeft.AddSpacer((10,10))
		
		self.sizerBtns = wx.BoxSizer(wx.HORIZONTAL)
		self.sizerBtns.AddSpacer((10,10))

		self.images = Images(os.path.join(self.settings.cmdfolder, "images"))		
		
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
		
		self.sizerBtns.AddSpacer((10,10))
	
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

		self.sizerLeft.AddSpacer((10,10))		
		self.sizerLeft.Add(self.sizerOpts)
		
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
		
	def setStatus(self, s):
		self.status = s
		self.app.updatePrintMonStatus(s)
		
	def getStatus(self):
		if self.printing:
			status = self.infoPane.getStatus()
			status['printing'] = "True"
		else:
			status = {}
			status['printing'] = "False"
			
		return status
		
	def hasFileLoaded(self):
		return self.model is not None
		
	def reprapEvent(self, evt):
		if evt.event in [ PRINT_STARTED, PRINT_RESUMED ]:
			self.printing = True
			self.setStatus(PMSTATUS_PRINTING)
			self.paused = False
			self.setPrintMode(PRINT_MODE_PRINT)
			self.setPauseMode(PAUSE_MODE_PAUSE)
			self.bPrint.Enable(False)
			self.bPause.Enable(True)
			self.app.setPrinterBusy(True)
			
		elif evt.event == PRINT_STOPPED:
			self.paused = True
			self.setStatus(PMSTATUS_PAUSED)
			self.printing = False
			self.reprap.printStopped()
			self.setPrintMode(PRINT_MODE_RESTART)
			self.setPauseMode(PAUSE_MODE_RESUME)
			self.bPrint.Enable(True)
			self.bPause.Enable(True)
			self.app.setPrinterBusy(False)
			
		elif evt.event == PRINT_COMPLETE:
			self.printing = False
			self.paused = False
			self.setStatus(PMSTATUS_READY)
			self.reprap.printComplete()
			self.setPrintMode(PRINT_MODE_PRINT)
			self.setPauseMode(PAUSE_MODE_PAUSE)
			self.bPrint.Enable(True)
			self.bPause.Enable(True)
			self.app.setPrinterBusy(False)
			self.endTime = time.time()
			self.logger.LogMessage("Print completed at %s" % time.strftime('%H:%M:%S', time.localtime(self.endTime)))
			self.logger.LogMessage("Total elapsed time: %s" % formatElapsed(self.endTime - self.startTime))
			self.updatePrintPosition(0)
			self.infoPane.setPrintComplete()
			
	def getPrintTimes(self):
		return self.startTime, self.endTime

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
		self.infoPane.setStartTime(self.startTime)
		self.bPrint.Enable(False)
		self.bPause.Enable(False)
		
	def doPause(self, evt):
		if self.paused:
			self.bPause.Enable(False)
			self.bPrint.Enable(False)
			self.reprap.resumePrint()
		else:
			self.bPause.Enable(False)
			self.bPrint.Enable(False)
			self.reprap.pausePrint()
		
	def updatePrintPosition(self, pos):
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
		
	def checkPrevious(self, evt):
		self.settings.showprevious = evt.IsChecked()
		self.settings.setModified()
		self.gcf.redrawCurrentLayer()
		
	def checkMoves(self, evt):
		self.settings.showmoves = evt.IsChecked()
		self.settings.setModified()
		self.gcf.redrawCurrentLayer()
	
	def forwardModel(self, model, name=""):
		self.reprap.resetPrint()
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
		self.setLayer(layer)
		
		self.printPos = 0
		self.printing = False
		self.paused = False

		self.setPrintMode(PRINT_MODE_PRINT)
		self.setPauseMode(PAUSE_MODE_PAUSE)
		self.bPrint.Enable(True)
		self.bPause.Enable(False)
		
		self.app.setPrinterBusy(False)
		self.setStatus(PMSTATUS_READY)
		self.infoPane.setFileInfo(self.name, self.model.duration, len(self.model), self.layerCount, self.model.total_e, self.model.layer_time)
		
	def changePrinter(self, hetemps, bedtemps):
		self.targets = {}
		self.temps = {}
		self.tempData = {}
		for h in self.knownHeaters:
			self.temps[h] = None
			self.targets[h] = 0
			self.tempData[h] = []

		self.gTemp.setTemps(self.tempData)
		self.gTemp.setTargets({})
		
	def disconnect(self):
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
		
	def setHETarget(self, temp):
		self.targets['HE'] = temp
		self.gTemp.setTargets(self.targets)
		
	def setHETemp(self, temp):
		self.temps['HE'] = temp
			
	def setBedTarget(self, temp):
		self.targets['Bed'] = temp
		self.gTemp.setTargets(self.targets)
		
	def setBedTemp(self, temp):
		self.temps['Bed'] = temp
		
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
