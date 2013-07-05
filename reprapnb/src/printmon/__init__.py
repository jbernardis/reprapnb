import wx, os
from gcmframe import GcmFrame

BUTTONDIM = (64, 64)
#		t = wx.StaticText(self, -1, "(if connected) Start/Pause/Restart, SD printing, follow print progress, fan control, speed control", (60,60))
	
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

class PrintMonitor(wx.Panel):
	def __init__(self, parent, app):
		self.model = None
		self.app = app
		self.logger = self.app.logger
		self.printPos = 0
		self.appsettings = app.settings
		self.printersettings = self.app.printersettings
		self.settings = app.settings.printmon
		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(100, 100))
		self.SetBackgroundColour("white")
		
		self.gcFile = None

		self.sizerMain = wx.GridBagSizer()
		self.sizerMain.AddSpacer((20, 20), pos=(0,0))
		
		self.sizerBtns = wx.BoxSizer(wx.HORIZONTAL)
		self.sizerBtns.AddSpacer((20, 20))
		
		path = os.path.join(self.settings.cmdfolder, "images/print.png")
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		self.bTest = wx.BitmapButton(self, wx.ID_ANY, png, size=BUTTONDIM)
		self.bTest.SetToolTipString("")
		self.sizerBtns.Add(self.bTest)
		self.Bind(wx.EVT_BUTTON, self.test, self.bTest)
		


		self.sizerMain.Add(self.sizerBtns, pos=(1,1))
		self.sizerMain.AddSpacer((20,20), pos=(2,0))
		

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
		
		self.sizerMain.AddSpacer((20,20), pos=(3,2))

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

		self.SetSizer(self.sizerMain)
		
#FIXIT
		#self.app.setPrinterBusy(True)
		self.app.setPrinterBusy(False)
		
	def test(self, evt):
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
		
	# need to handle change printer, slicer, profile
		
	def enableButtons(self, flag=True):
		if flag:
			if self.model is not None:
				self.slideLayer.Enable(True)
			else:
				self.slideLayer.Enable(False)
		else:
			self.slideLayer.Enable(False)
