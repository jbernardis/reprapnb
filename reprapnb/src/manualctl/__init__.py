import wx
import os.path
from imagemap import ImageMap
from extruder import Extruder
from heater import Heater
from gcodeentry import GCodeEntry
from moveaxis import MoveAxis
	
# G code ref

class ManualControl(wx.Panel): 
	def __init__(self, parent, app):
		self.model = None
		self.parent = parent
		self.app = app
		self.appsettings = app.settings
		self.settings = app.settings.manualctl

		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(100, 100))
		self.SetBackgroundColour("white")
		

		self.moveAxis = MoveAxis(self, self.app)				
		sizerMove = wx.BoxSizer(wx.VERTICAL)
		sizerMove.AddSpacer((20,20))
		sizerMove.Add(self.moveAxis)



		
		self.extruder = Extruder(self, self.app)
		sizerExtrude = wx.BoxSizer(wx.VERTICAL)
		
		sizerExtrude.AddSpacer((10,10))
		
		t = wx.StaticText(self, wx.ID_ANY, "Extruder", style=wx.ALIGN_LEFT, size=(200, -1))
		f = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
		t.SetFont(f)
		sizerExtrude.Add(t, flag=wx.LEFT)
		
		sizerExtrude.AddSpacer((10,10))
		
		sizerExtrude.Add(self.extruder)
		
		
		
		sizerHeat = wx.BoxSizer(wx.VERTICAL)
		sizerHeat.AddSpacer((10,10))
		
		t = wx.StaticText(self, wx.ID_ANY, "Hot End", style=wx.ALIGN_LEFT, size=(200, -1))
		f = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
		t.SetFont(f)
		sizerHeat.Add(t, flag=wx.LEFT)
		
		sizerHeat.AddSpacer((10,10))
		
		self.HotEnd = Heater(self, self.app, name="Hot End", range=(20, 250), oncmd="G104")
		sizerHeat.Add(self.HotEnd)
		
		sizerHeat.AddSpacer((30,30))
		
		t = wx.StaticText(self, wx.ID_ANY, "Build Platform", style=wx.ALIGN_LEFT, size=(200, -1))
		f = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
		t.SetFont(f)
		sizerHeat.Add(t, flag=wx.LEFT)
		
		sizerHeat.AddSpacer((10,10))
		
		self.BuildPlatform = Heater(self, self.app, name="Build Platform", range=(20, 130), oncmd="G140")
		sizerHeat.Add(self.BuildPlatform)



		self.GCEntry = GCodeEntry(self)	
			
		sizerGCode = wx.BoxSizer(wx.VERTICAL)
		sizerGCode.AddSpacer((20,20))
		
		t = wx.StaticText(self, wx.ID_ANY, "G Code", style=wx.ALIGN_LEFT, size=(200, -1))
		f = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
		t.SetFont(f)
		sizerGCode.Add(t, flag=wx.LEFT)
		
		sizerGCode.AddSpacer((10,10))
		
		sizerGCode.Add(self.GCEntry)


		
		sizerMain = wx.GridBagSizer(hgap=5, vgap=5)
		sizerMain.AddSpacer((20,20), pos=(0,0))
		sizerMain.Add(sizerMove, pos=(1,1), span=(2,1))
		sizerMain.AddSpacer((20,20), pos=(0,2))
		sizerMain.Add(sizerExtrude, pos=(1,3))
		sizerMain.AddSpacer((20,20), pos=(0,4))
		sizerMain.Add(sizerHeat,pos=(1,5))
		sizerMain.Add(sizerGCode, pos=(2,3),span=(1,3))

		self.SetSizer(sizerMain)
		self.Layout()
		self.Fit()

	def onClose(self, evt):
		return True
