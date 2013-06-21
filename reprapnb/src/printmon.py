import wx
from gauge import Gauge
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
		self.settings = app.settings
		
		self.gcFile = None
		
		self.polymer = "ABS"

		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(100, 100))
		self.SetBackgroundColour("white")

		self.gBed = Gauge(self)
		self.gBed.setThresholds([[35, myGreen], [59, myYellow], [999, myRed]])
		self.gBed.setRange(20, 90)
		self.gBed.setTarget(60)
		self.gBed.setValue(20)

		self.gExt = Gauge(self)
		self.gExt.setThresholds([[35, myGreen], [109, myYellow], [999, myRed]])
		self.gExt.setRange(20, 140)
		self.gExt.setTarget(110)
		self.gExt.setValue(20)
		
		sizerMain = wx.BoxSizer(wx.HORIZONTAL)
		sizerMain.Add(self.gBed)
		sizerMain.Add(self.gExt)
		self.SetSizer(sizerMain)

	def onClose(self, evt):
		return True
	
