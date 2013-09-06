import wx
import os
import time
from gcmframe import GcmFrame
from tempgraph import TempGraph, MAXX
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

		self.sizerMain = wx.GridBagSizer()
		self.sizerMain.AddSpacer((10,10), pos=(0,0))
		
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

		self.sizerMain.Add(self.sizerBtns, pos=(1,1))
		self.sizerMain.AddSpacer((10,10), pos=(2,0))

		self.gcf = GcmFrame(self, self.model, self.settings, self.buildarea)
		self.sizerMain.Add(self.gcf, pos=(3,1))
		
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
		sz = self.buildarea[0] * self.settings.gcodescale
		self.tName = wx.StaticText(self, wx.ID_ANY, "", size=(sz, -1), style=wx.ST_NO_AUTORESIZE | wx.ALIGN_CENTER_HORIZONTAL)
		self.tName.SetFont(f)
		self.sizerMain.Add(self.tName, pos=(4,1), flag=wx.EXPAND | wx.ALL)

		self.tHeight = wx.StaticText(self, wx.ID_ANY, "", size=(sz, -1), style=wx.ST_NO_AUTORESIZE | wx.ALIGN_CENTER_HORIZONTAL)
		self.tHeight.SetFont(f)
		self.sizerMain.Add(self.tHeight, pos=(5,1), flag=wx.EXPAND | wx.ALL)
		
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

		self.sizerMain.AddSpacer((10,10), pos=(6,1))		
		self.sizerMain.Add(self.sizerOpts, pos=(7, 1), flag=wx.EXPAND | wx.ALL)
		
		self.sizerMain.AddSpacer((10,10), pos=(3,2))

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
		self.sizerMain.Add(self.slideLayer, pos=(3,3), flag=wx.ALIGN_RIGHT)
		
		self.sizerMain.AddSpacer((10,10), pos=(3,4))

		self.gTemp = TempGraph(self, self.settings)
		self.sizerMain.Add(self.gTemp, pos=(3,5))

		self.sizerMain.AddSpacer((10,10), pos=(3,6))

		self.SetSizer(self.sizerMain)

		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)        
		self.timer.Start(1000)
		
	def reprapEvent(self, evt):
		if evt.event in [ PRINT_STARTED, PRINT_RESUMED ]:
			self.printing = True
			self.paused = False
			self.setPrintMode(PRINT_MODE_PRINT)
			self.setPauseMode(PAUSE_MODE_PAUSE)
			self.bPrint.Enable(False)
			self.bPause.Enable(True)
			self.app.setPrinterBusy(True)
			
		elif evt.event == PRINT_STOPPED:
			self.paused = True
			self.printing = False
			self.setPrintMode(PRINT_MODE_RESTART)
			self.setPauseMode(PAUSE_MODE_RESUME)
			self.bPrint.Enable(True)
			self.bPause.Enable(True)
			self.app.setPrinterBusy(False)
			
		elif evt.event == PRINT_COMPLETE:
			self.printing = False
			self.paused = False
			self.setPrintMode(PRINT_MODE_PRINT)
			self.setPauseMode(PAUSE_MODE_PAUSE)
			self.bPrint.Enable(True)
			self.bPause.Enable(True)
			self.app.setPrinterBusy(False)
			self.endTime = time.time()
			self.logger.LogMessage("Print completed at %s" % time.strftime('%H:%M:%S', time.localtime(self.endTime)))
			self.logger.LogMessage("Total elapsed time: %s" % formatElapsed(self.endTime - self.startTime))
			self.updatePrintPosition(0)
			
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
		self.logger.LogMessage("ETA at %s (%s)" % (time.strftime('%H:%M:%S', time.localtime(self.startTime+self.model.duration))), formatElapsed(self.model.duration))
		self.countGLines = len(self.model)
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
		self.gcf.setPrintPosition(self.printPos)
		print "Line position = %d/%d (%f)" % (pos, self.countGLines, float(pos)/float(self.countGLines))
		elapsed = time.time() - self.startTime
		print "Time %% = %f" % (float(elapsed)/float(self.model.duration))
		
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
			print "z=", zh
			print "min=", xymin
			print "max=", xymax
			print "filament=", filament
			print "G code lines=", glines
			print "time=", time
			print "filstart=", filstart
			print "Layer %d/%d" % (l+1, self.layerCount)
			if zh is None:
				self.tHeight.SetLabel("")
			else:
				self.tHeight.SetLabel("Z: %.3f" % zh)

	def onClose(self, evt):
		return True
		
	def viewZoomIn(self, evt):
		self.gcf.zoomIn()
		
	def viewZoomOut(self, evt):
		self.gcf.zoomOut()
		
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
		self.model = model
		self.name = name
		if self.name == TEMPFILELABEL:
			self.gcFile = None
		elif len(self.name) > 40:
			self.gcFile = self.name
			self.name = os.path.basename(self.gcFile)
		else:
			self.gcFile = self.name
			
		self.tName.SetLabel(self.name)
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
