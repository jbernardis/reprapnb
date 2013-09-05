import wx
import os.path
from imagemap import ImageMap
from extruder import Extruder
from heater import Heater
from gcodeentry import GCodeEntry
from moveaxis import MoveAxis
	
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

		self.moveAxis = MoveAxis(self, self.app)				
		self.sizerMove = wx.BoxSizer(wx.VERTICAL)
		self.sizerMove.AddSpacer((20,20))
		self.sizerMove.Add(self.moveAxis)
		
		self.sizerExtrude = self.addExtruder()
		self.sizerHeat = self.addHeater()
		self.sizerGCode = self.addGCEntry()
		
		self.sizerMain = wx.GridBagSizer(hgap=5, vgap=5)
		self.sizerMain.AddSpacer((20,20), pos=(0,0))
		self.sizerMain.Add(self.sizerMove, pos=(1,1), span=(2,1))
		self.sizerMain.Add(self.sizerExtrude, pos=(1,3), span=(1,1))
		self.sizerMain.Add(self.sizerHeat, pos=(1,5), span=(1,1))
		self.sizerMain.Add(self.sizerGCode, pos=(2,3), span=(1,3))
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
		
		self.extWin = Extruder(self, self.app)
		t = wx.StaticText(self, wx.ID_ANY, "Extruder", style=wx.ALIGN_LEFT, size=(200, -1))
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD)
		t.SetFont(f)
		sizerExtrude.Add(t, flag=wx.LEFT)
		sizerExtrude.AddSpacer((10,10))
		sizerExtrude.Add(self.extWin)
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

		t = wx.StaticText(self, wx.ID_ANY, "Hot End", style=wx.ALIGN_LEFT, size=(200, -1))
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD)
		t.SetFont(f)
		sizerHeat.Add(t, flag=wx.LEFT)
		sizerHeat.AddSpacer((10,10))
		
		self.heWin = Heater(self, self.app, name="Hot End", shortname="HE", 
					target=185, trange=[20, 250], oncmd="M104")
		sizerHeat.Add(self.heWin)
		sizerHeat.AddSpacer((10,10))

		return sizerHeat

	def addGCEntry(self):
		sizerGCode = wx.BoxSizer(wx.VERTICAL)
		sizerGCode.AddSpacer((20,20))
		
		t = wx.StaticText(self, wx.ID_ANY, "G Code", style=wx.ALIGN_LEFT, size=(200, -1))
		f = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
		t.SetFont(f)
		self.GCELabel = t
		sizerGCode.Add(t, flag=wx.LEFT)
		
		sizerGCode.AddSpacer((10,10))

		self.GCEntry = GCodeEntry(self)	
		sizerGCode.Add(self.GCEntry)
		
		return sizerGCode
		
	def changePrinter(self, hetemps, bedtemps):
		self.heWin.setHeatTarget(hetemps[self.currentTool])
		self.bedWin.setHeatTarget(bedtemps[self.currentTool])

	def onClose(self, evt):
		return True
