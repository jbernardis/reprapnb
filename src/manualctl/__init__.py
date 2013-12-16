import wx
import os.path
from imagemap import ImageMap
from extruder import Extruder
from hotbed import HotBed
from gcodeentry import GCodeEntry
from moveaxis import MoveAxis
from hotend import HotEnd
from images import Images

#FIXIT  G code ref
BUTTONDIMWIDE = (96, 48)

class ManualControl(wx.Panel): 
	def __init__(self, parent, app, nExtr, heTemps, bedTemp):
		self.model = None
		self.parent = parent
		self.app = app
		self.logger = self.app.logger
		self.appsettings = app.settings
		self.settings = app.settings.manualctl
		self.currentTool = 0

		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(100, 100))
		self.SetBackgroundColour("white")

		self.images = Images(os.path.join(self.settings.cmdfolder, "images"))

		self.slFeedTimer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.onFeedSpeedChanged, self.slFeedTimer)
		self.slFanTimer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.onFanSpeedChanged, self.slFanTimer)

		self.moveAxis = MoveAxis(self, self.app)				
		self.sizerMove = wx.BoxSizer(wx.VERTICAL)
		self.sizerMove.AddSpacer((20,20))
		self.sizerMove.Add(self.moveAxis)
		
		self.sizerExtrude = self.addExtruder(heTemps, nExtr)
		self.sizerBed = self.addBed(bedTemp)
		self.sizerSpeed = self.addSpeedControls(self.appsettings.speedcommand)
		self.sizerGCode = self.addGCEntry()
		
		self.sizerMain = wx.BoxSizer(wx.HORIZONTAL)
		sizerLeft = wx.BoxSizer(wx.VERTICAL)
		sizerRight = wx.BoxSizer(wx.VERTICAL)
		
		sizerLeft.AddSpacer((20,20))
		sizerLeft.Add(self.sizerMove)
		sizerLeft.Add(self.sizerGCode)
		
		sizerRight.AddSpacer((20, 20))
		sizerRight.Add(self.sizerExtrude)
		sizerBedSpd = wx.BoxSizer(wx.HORIZONTAL)
		sizerBedSpd.Add(self.sizerBed)
		sizerBedSpd.AddSpacer((10, 10))
		sizerBedSpd.Add(self.sizerSpeed)
		sizerRight.Add(sizerBedSpd)
		
		self.sizerMain.AddSpacer((20, 20))
		self.sizerMain.Add(sizerLeft)
		self.sizerMain.AddSpacer((20, 20))
		self.sizerMain.Add(sizerRight)
		self.sizerMain.AddSpacer((20, 20))

		self.SetSizer(self.sizerMain)
		self.Layout()
		self.Fit()
		
	def setBedTarget(self, temp):
		self.bedWin.setHeatTarget(temp)
		
	def setHETarget(self, tool, temp):
		self.heWin.setHeatTarget(tool, temp)
		
	def setBedTemp(self, temp):
		self.bedWin.setHeatTemp(temp)
		
	def setHETemp(self, tool, temp):
		self.heWin.setHeatTemp(tool, temp)
		
	def setActiveTool(self, tool):
		self.heWin.setActiveTool(tool)
		
	def addExtruder(self, startTemps, nExtr):
		sizerExtrude = wx.BoxSizer(wx.VERTICAL)
		sizerExtrude.AddSpacer((10,10))

		self.font12bold = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		self.font16 = wx.Font(16, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

		t = wx.StaticText(self, wx.ID_ANY, "Hot End(s)", style=wx.ALIGN_LEFT, size=(200, -1))
		t.SetFont(self.font12bold)
		sizerExtrude.Add(t, flag=wx.LEFT)
		sizerExtrude.AddSpacer((10,10))
		
		self.heWin = HotEnd(self, self.app, name=("Hot End 0", "Hot End 1", "Hot End 2"), shortname=("HE0", "HE1", "HE2"), 
					target=startTemps, trange=((20, 250), (20, 250), (20, 250)), nextr=nExtr)
		sizerExtrude.Add(self.heWin, flag=wx.LEFT | wx.EXPAND)
		sizerExtrude.AddSpacer((10,10))

		t = wx.StaticText(self, wx.ID_ANY, "Extruder", style=wx.ALIGN_LEFT, size=(200, -1))
		t.SetFont(self.font12bold)
		sizerExtrude.Add(t, flag=wx.LEFT)
		sizerExtrude.AddSpacer((10,10))
		
		self.extWin = Extruder(self, self.app)
		sizerExtrude.Add(self.extWin, flag=wx.LEFT)
		sizerExtrude.AddSpacer((10,10))
			
		return sizerExtrude
			
	def addBed(self, startTemp):
		sizerBed = wx.BoxSizer(wx.VERTICAL)
		sizerBed.AddSpacer((10,10))

		t = wx.StaticText(self, wx.ID_ANY, "Heated Print Bed", style=wx.ALIGN_LEFT, size=(200, -1))
		t.SetFont(self.font12bold)
		sizerBed.Add(t, flag=wx.LEFT)
		sizerBed.AddSpacer((10,10))
		
		self.bedWin = HotBed(self, self.app, name="Heated Print Bed", shortname="Bed", 
					target=startTemp, trange=[20, 150])
		sizerBed.Add(self.bedWin)
		sizerBed.AddSpacer((10,10))

		return sizerBed
	
	def addSpeedControls(self, speedcommand):
		sizerSpeed = wx.BoxSizer(wx.VERTICAL)
		sizerSpeed.AddSpacer((10, 10))

		t = wx.StaticText(self, wx.ID_ANY, "Feed Speed", style=wx.ALIGN_CENTER, size=(-1, -1))
		t.SetFont(self.font12bold)
		sizerSpeed.Add(t, flag=wx.ALL)

		self.slFeedSpeed = wx.Slider(
			self, wx.ID_ANY, 100, 50, 200, size=(320, -1), 
			style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS 
			)
		self.slFeedSpeed.SetTickFreq(5, 1)
		self.slFeedSpeed.SetPageSize(1)
		self.slFeedSpeed.Bind(wx.EVT_SCROLL_CHANGED, self.onFeedSpeedChanged)
		self.slFeedSpeed.Bind(wx.EVT_MOUSEWHEEL, self.onFeedSpeedWheel)
		sizerSpeed.Add(self.slFeedSpeed)
		sizerSpeed.AddSpacer((10, 10))

		t = wx.StaticText(self, wx.ID_ANY, "Fan Speed", style=wx.ALIGN_CENTER, size=(-1, -1))
		t.SetFont(self.font12bold)
		sizerSpeed.Add(t, flag=wx.ALL)
		
		self.slFanSpeed = wx.Slider(
			self, wx.ID_ANY, 0, 0, 255, size=(320, -1), 
			style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS 
			)
		self.slFanSpeed.SetTickFreq(5, 1)
		self.slFanSpeed.SetPageSize(1)
		self.slFanSpeed.Bind(wx.EVT_SCROLL_CHANGED, self.onFanSpeedChanged)
		self.slFanSpeed.Bind(wx.EVT_MOUSEWHEEL, self.onFanSpeedWheel)
		sizerSpeed.Add(self.slFanSpeed)
	
		if speedcommand is not None:			
			self.bSpeedQuery = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSpeedquery, size=BUTTONDIMWIDE)
			self.bSpeedQuery.SetToolTipString("Retrieve current feed and fan speeds from printer")
			sizerSpeed.Add(self.bSpeedQuery, flag=wx.ALIGN_CENTER | wx.ALL, border=10)
			self.Bind(wx.EVT_BUTTON, self.doSpeedQuery, self.bSpeedQuery)
		
		return sizerSpeed
	
	def doSpeedQuery(self, evt):
		self.app.reprap.send_now(self.appsettings.speedcommand)
		
	def updateSpeeds(self, fan, feed, flow):
		if feed is not None:
			self.slFeedSpeed.SetValue(feed)
		if fan is not None:
			self.slFanSpeed.SetValue(fan)
	
	def onFeedSpeedChanged(self, evt):
		self.setFeedSpeed(self.slFeedSpeed.GetValue())
	
	def onFeedSpeedWheel(self, evt):
		self.slFeedTimer.Start(500, True)
		l = self.slFeedSpeed.GetValue()
		if evt.GetWheelRotation() < 0:
			l -= 1
		else:
			l += 1
		if l >= 50 and l <= 200:
			self.slFeedSpeed.SetValue(l)
			
	def setFeedSpeed(self, spd):
		self.app.reprap.send_now("M220 S%d" % spd)
		
	def onFanSpeedChanged(self, evt):
		self.setFanSpeed(self.slFanSpeed.GetValue())
	
	def onFanSpeedWheel(self, evt):
		self.slFanTimer.Start(500, True)
		l = self.slFanSpeed.GetValue()
		if evt.GetWheelRotation() < 0:
			l -= 1
		else:
			l += 1
		if l >= 0 and l <= 255:
			self.slFanSpeed.SetValue(l)
		
	def setFanSpeed(self, spd):
		self.app.reprap.send_now("M106 S%d" % spd)

	def addGCEntry(self):
		sizerGCode = wx.BoxSizer(wx.VERTICAL)
		sizerGCode.AddSpacer((20,20))
		
		t = wx.StaticText(self, wx.ID_ANY, "G Code", style=wx.ALIGN_LEFT, size=(200, -1))
		t.SetFont(self.font12bold)
		self.GCELabel = t
		sizerGCode.Add(t, flag=wx.LEFT)
		
		sizerGCode.AddSpacer((10,10))

		self.GCEntry = GCodeEntry(self, self.app)	
		sizerGCode.Add(self.GCEntry)
		
		return sizerGCode
		
	def changePrinter(self, hetemps, bedtemp):
		self.bedWin.setProfileTarget(bedtemp)
		self.heWin.changePrinter(hetemps)

	def onClose(self, evt):
		return True
