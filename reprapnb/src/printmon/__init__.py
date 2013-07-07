import wx, os
from gcmframe import GcmFrame
from tempgraph import TempGraph

BUTTONDIM = (64, 64)
#Start/Pause/Restart, SD printing, follow print progress, fan control, speed control",
	
myRed = wx.Colour(254, 142, 82, 179)
myBlue = wx.Colour(51, 115, 254, 179)
myGreen = wx.Colour(94, 190, 82, 179)
myYellow = wx.Colour(219, 242, 37, 179)

bedIntervals = {
			"PLA": [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70],
			"ABS": [20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130]}
bedColors = {
			"PLA": [[39, wx.BLUE], [59, wx.Colour(255, 255, 0)], [999, wx.RED]],
			"ABS": [[59, wx.BLUE], [109, wx.Colour(255, 255, 0)], [999, wx.RED]]}

PAUSE_MODE_PAUSE = 1
PAUSE_MODE_RESUME = 2

PRINT_MODE_PRINT = 1
PRINT_MODE_RESTART = 2

class PrintMonitor(wx.Panel):
	def __init__(self, parent, app):
		self.model = None
		self.app = app
		self.logger = self.app.logger
		self.printPos = 0
		self.printing = False
		self.paused = False
		self.printersettings = self.app.printersettings
		self.settings = app.settings.printmon
		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(100, 100))
		self.SetBackgroundColour("white")
		self.targets = {}
		self.temps = {}
		self.tempData = {}

		self.sizerMain = wx.GridBagSizer()
		self.sizerMain.AddSpacer((10,10), pos=(0,0))
		
		self.sizerBtns = wx.BoxSizer(wx.HORIZONTAL)
		self.sizerBtns.AddSpacer((10,10))
		
		path = os.path.join(self.settings.cmdfolder, "images/restart.png")
		self.pngRestart = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(self.pngRestart, wx.BLUE)
		self.pngRestart.SetMask(mask)
		
		path = os.path.join(self.settings.cmdfolder, "images/print.png")
		self.pngPrint = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(self.pngPrint, wx.BLUE)
		self.pngPrint.SetMask(mask)
		
		self.bPrint = wx.BitmapButton(self, wx.ID_ANY, self.pngPrint, size=BUTTONDIM)
		self.setPrintMode(PRINT_MODE_PRINT)
		self.sizerBtns.Add(self.bPrint)
		self.Bind(wx.EVT_BUTTON, self.doPrint, self.bPrint)
		
		path = os.path.join(self.settings.cmdfolder, "images/pause.png")
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		self.bPause = wx.BitmapButton(self, wx.ID_ANY, png, size=BUTTONDIM)
		self.setPauseMode(PAUSE_MODE_PAUSE)
		self.sizerBtns.Add(self.bPause)
		self.Bind(wx.EVT_BUTTON, self.doPause, self.bPause)
		self.bPause.Enable(False)
		
		self.sizerBtns.AddSpacer((10,10))
	
		path = os.path.join(self.settings.cmdfolder, "images/zoomin.png")	
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		self.bZoomIn = wx.BitmapButton(self, wx.ID_ANY, png, size=BUTTONDIM)
		self.bZoomIn.SetToolTipString("Zoom the view in")
		self.sizerBtns.Add(self.bZoomIn)
		self.Bind(wx.EVT_BUTTON, self.viewZoomIn, self.bZoomIn)
		
		path = os.path.join(self.settings.cmdfolder, "images/zoomout.png")	
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		self.bZoomOut = wx.BitmapButton(self, wx.ID_ANY, png, size=BUTTONDIM)
		self.bZoomOut.SetToolTipString("Zoom the view out")
		self.sizerBtns.Add(self.bZoomOut)
		self.Bind(wx.EVT_BUTTON, self.viewZoomOut, self.bZoomOut)

		self.sizerMain.Add(self.sizerBtns, pos=(1,1))
		self.sizerMain.AddSpacer((10,10), pos=(2,0))

		self.gcf = GcmFrame(self, self.model, self.settings, self.printersettings.settings['buildarea'])
		self.sizerMain.Add(self.gcf, pos=(3,1))
		
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
		sz = self.printersettings.settings['buildarea'][0] * self.settings.gcodescale
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

		sz = self.printersettings.settings['buildarea'][1] * self.settings.gcodescale
		
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

		self.app.setPrinterBusy(False)

		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)        
		self.timer.Start(1000)

	def setPrintMode(self, mode):
		if mode == PRINT_MODE_PRINT:
			self.bPrint.SetToolTipString("Start the print")
			self.bPrint.SetBitmapLabel(self.pngPrint)
		elif mode == PRINT_MODE_RESTART:
			self.bPrint.SetToolTipString("Restart the print")
			self.bPrint.SetBitmapLabel(self.pngRestart)

	def setPauseMode(self, mode):
		if mode == PAUSE_MODE_PAUSE:
			self.bPause.SetToolTipString("Pause the print")
		elif mode == PAUSE_MODE_RESUME:
			self.bPause.SetToolTipString("Resume the print from the paused point")

		
	def doPrint(self, evt):
		#FIXIT
		self.printPos = 0
		self.printing = True
		self.paused = False
		self.setPrintMode(PRINT_MODE_PRINT)
		self.setPauseMode(PAUSE_MODE_PAUSE)
		self.bPrint.Enable(False)
		self.bPause.Enable(True)
		self.app.setPrinterBusy(True)
		
	def doPause(self, evt):
		#FIXIT
		if self.paused:
			self.paused = False
			self.printing = True
			self.setPrintMode(PRINT_MODE_PRINT)
			self.setPauseMode(PAUSE_MODE_PAUSE)
			self.bPrint.Enable(False)
			self.app.setPrinterBusy(True)
		else:
			self.paused = True
			self.printing = False
			self.setPrintMode(PRINT_MODE_RESTART)
			self.setPauseMode(PAUSE_MODE_RESUME)
			self.bPrint.Enable(True)
			self.app.setPrinterBusy(False)
		
	def test(self):
		self.printPos += 10
		self.gcf.setPrintPosition(self.printPos)
		
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
			zh = self.model.getLayerHeight(l)
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
		self.tName.SetLabel(name)
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
		
	def changePrinter(self, heaters, extruders):
		self.targets = {}
		self.temps = {}
		self.tempData = {}
		self.knownHeaters = [h[0] for h in heaters]
		for h in self.knownHeaters:
			self.temps[h] = None
			self.targets[h] = 0
			self.tempData[h] = []

		self.gTemp.setHeaters(self.knownHeaters)			
		self.gTemp.setTemps(self.tempData)
		self.gTemp.setTargets({})
			
		
	#FIXIT need to handle change printer, slicer, profile
	#FIXIT target temps should come from the printer
	def setHeatTarget(self, name, temp):
		if name not in self.knownHeaters:
			self.logger.LogWarning("Ignoring target temperature for unknown heater: %s" % name)
			return
		self.targets[name] = temp
		self.gTemp.setTargets(self.targets)
		
	def setHeatTemp(self, name, temp):
		if name not in self.knownHeaters:
			self.logger.LogWarning("Ignoring temperature for unknown heater: %s" % name)
			return
		self.temps[name] = temp
		
	def onTimer(self, evt):
		for h in self.knownHeaters:
			self.tempData[h].append(self.temps[h])
			l = len(self.tempData[h])
			if l > 240: # 4 minutes data
				self.tempData[h] = self.tempData[h][l-240:]
		self.gTemp.setTemps(self.tempData)
		
	def enableButtons(self, flag=True):
		if flag:
			if self.model is not None:
				self.slideLayer.Enable(True)
			else:
				self.slideLayer.Enable(False)
		else:
			self.slideLayer.Enable(False)
