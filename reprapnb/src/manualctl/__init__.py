import wx
import os.path
from imagemap import ImageMap
from extruder import Extruder
from heater import Heater
from gcodeentry import GCodeEntry
from moveaxis import MoveAxis
from toolchange import ToolChange

#FIXIT  G code ref

class ManualControl(wx.Panel): 
	def __init__(self, parent, app):
		self.model = None
		self.parent = parent
		self.app = app
		self.logger = self.app.logger
		self.appsettings = app.settings
		self.settings = app.settings.manualctl
		self.currentTool = 0

		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(100, 100))
		self.SetBackgroundColour("white")

		self.slFeedTimer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.onFeedSpeedChanged, self.slFeedTimer)
		self.slFanTimer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.onFanSpeedChanged, self.slFanTimer)

		self.moveAxis = MoveAxis(self, self.app)				
		self.sizerMove = wx.BoxSizer(wx.VERTICAL)
		self.sizerMove.AddSpacer((20,20))
		self.sizerMove.Add(self.moveAxis)
		
		self.sizerExtrude = self.addExtruder()
		self.sizerHeat = self.addHeater()
		self.sizerSpeed = self.addSpeedControls()
		self.sizerGCode = self.addGCEntry()
		
		self.sizerMain = wx.GridBagSizer(hgap=5, vgap=5)
		self.sizerMain.AddSpacer((20,20), pos=(0,0))
		self.sizerMain.Add(self.sizerMove, pos=(1,1), span=(3,1))
		self.sizerMain.Add(self.sizerExtrude, pos=(1,3), span=(2,1))
		self.sizerMain.Add(self.sizerHeat, pos=(1,5), span=(1,1))
		self.sizerMain.Add(self.sizerSpeed, pos=(2,5), span=(1,1))
		self.sizerMain.Add(self.sizerGCode, pos=(3,3), span=(1,3))
		self.sizerMain.AddSpacer((10,10), pos=(0,2))
		self.sizerMain.AddSpacer((10,10), pos=(0,4))

		self.SetSizer(self.sizerMain)
		self.Layout()
		self.Fit()
		
	def setBedTarget(self, temp):
		self.bedWin.setHeatTarget(temp)
		
	def setHETarget(self, temp):
		self.heWin.setHeatTarget(temp)
		
	def setBedTemp(self, temp):
		self.bedWin.setHeatTemp(temp)
		
	def setHETemp(self, temp):
		self.heWin.setHeatTemp(temp)
		
	def addExtruder(self):
		sizerExtrude = wx.BoxSizer(wx.VERTICAL)
		sizerExtrude.AddSpacer((10,10))

		t = wx.StaticText(self, wx.ID_ANY, "Current Tool", style=wx.ALIGN_LEFT, size=(200, -1))
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD)
		t.SetFont(f)
		sizerExtrude.Add(t, flag=wx.LEFT)
		sizerExtrude.AddSpacer((10,10))
		
		self.toolChange = ToolChange(self, self.app, 1)
		sizerExtrude.Add(self.toolChange, flag=wx.ALIGN_LEFT | wx.EXPAND)
		sizerExtrude.AddSpacer((10, 10))

		t = wx.StaticText(self, wx.ID_ANY, "Hot End", style=wx.ALIGN_LEFT, size=(200, -1))
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD)
		t.SetFont(f)
		sizerExtrude.Add(t, flag=wx.LEFT)
		sizerExtrude.AddSpacer((10,10))
		
		self.heWin = Heater(self, self.app, name="Hot End", shortname="HE", 
					target=185, trange=[20, 250], oncmd="M104")
		sizerExtrude.Add(self.heWin, flag=wx.LEFT | wx.EXPAND)
		sizerExtrude.AddSpacer((10,10))

		self.extWin = Extruder(self, self.app)
		t = wx.StaticText(self, wx.ID_ANY, "Extruder", style=wx.ALIGN_LEFT, size=(200, -1))
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD)
		t.SetFont(f)
		sizerExtrude.Add(t, flag=wx.LEFT)
		sizerExtrude.AddSpacer((10,10))
		sizerExtrude.Add(self.extWin, flag=wx.LEFT | wx.EXPAND)
		sizerExtrude.AddSpacer((10,10))
			
		return sizerExtrude
			
	def addHeater(self):
		sizerHeat = wx.BoxSizer(wx.VERTICAL)
		sizerHeat.AddSpacer((10,10))

		t = wx.StaticText(self, wx.ID_ANY, "Heated Print Bed", style=wx.ALIGN_LEFT, size=(200, -1))
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD)
		t.SetFont(f)
		sizerHeat.Add(t, flag=wx.LEFT)
		sizerHeat.AddSpacer((10,10))
		
		self.bedWin = Heater(self, self.app, name="Heated Print Bed", shortname="Bed", 
					target=60, trange=[20, 150], oncmd="M140")
		sizerHeat.Add(self.bedWin)
		sizerHeat.AddSpacer((10,10))

		return sizerHeat
	
	def addSpeedControls(self):
		sizerSpeed = wx.BoxSizer(wx.VERTICAL)
		sizerSpeed.AddSpacer((10, 10))

		t = wx.StaticText(self, wx.ID_ANY, "Feed Speed", style=wx.ALIGN_CENTER, size=(-1, -1))
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD)
		t.SetFont(f)
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
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD)
		t.SetFont(f)
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
		
		return sizerSpeed
	
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
		f = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
		t.SetFont(f)
		self.GCELabel = t
		sizerGCode.Add(t, flag=wx.LEFT)
		
		sizerGCode.AddSpacer((10,10))

		self.GCEntry = GCodeEntry(self, self.app)	
		sizerGCode.Add(self.GCEntry)
		
		return sizerGCode
		
	def changePrinter(self, hetemps, bedtemps):
		print "chg prt: he: ", hetemps[self.currentTool]
		print "chg prt: bed: ", bedtemps[self.currentTool]
		self.heWin.setProfileTarget(hetemps[self.currentTool])
		self.bedWin.setProfileTarget(bedtemps[self.currentTool])
		self.toolChange.changePrinter(len(hetemps))

	def onClose(self, evt):
		return True
