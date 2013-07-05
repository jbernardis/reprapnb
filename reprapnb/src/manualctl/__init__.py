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
		self.logger = self.app.logger
		self.appsettings = app.settings
		self.settings = app.settings.manualctl
		self.printersettings = self.app.printersettings

		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(100, 100))
		self.SetBackgroundColour("white")

		self.moveAxis = MoveAxis(self, self.app)				
		self.sizerMove = wx.BoxSizer(wx.VERTICAL)
		self.sizerMove.AddSpacer((20,20))
		self.sizerMove.Add(self.moveAxis)
		
		self.sizerExtrude = self.addExtruders()
		self.sizerHeat = self.addHeaters()
		
		self.sizerGCode = self.addGCEntry()
		
		self.sizerMain = wx.GridBagSizer(hgap=5, vgap=5)
		self.sizerMain.AddSpacer((20,20), pos=(0,0))
		self.sizerMain.Add(self.sizerMove, pos=(1,1), span=(2,1))
		self.sizerMain.AddSpacer((10,10), pos=(0,2))
		self.sizerMain.Add(self.sizerExtrude, pos=(1,3))
		self.sizerMain.AddSpacer((10,10), pos=(0,4))
		self.sizerMain.Add(self.sizerHeat,pos=(1,5))
		self.sizerMain.Add(self.sizerGCode, pos=(2,3),span=(1,3))

		self.SetSizer(self.sizerMain)
		self.Layout()
		self.Fit()
		
	def addExtruders(self):
		sizerExtrude = wx.BoxSizer(wx.VERTICAL)
		sizerExtrude.AddSpacer((10,10))
		self.extruder = []
		self.extLabel = []
		
		maxExt = self.printersettings.settings['extruders']
		axes = self.printersettings.settings['axisletters']				
		for i in range(maxExt):
			ex = Extruder(self, self.app, axis=axes[i])
			self.extruder.append(ex)
			name = "Extruder"
			if maxExt > 1:
				name += " " + str(i)
			t = wx.StaticText(self, wx.ID_ANY, name, style=wx.ALIGN_LEFT, size=(200, -1))
			f = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
			t.SetFont(f)
			self.extLabel.append(t)
			sizerExtrude.Add(t, flag=wx.LEFT)
			sizerExtrude.AddSpacer((10,10))
			sizerExtrude.Add(ex)
			sizerExtrude.AddSpacer((10,10))
			
		return sizerExtrude
	
	def getProfileHeaterValue(self, idx=None):
		self.temperatures = self.app.slicer.type.getProfileTemps()
		maxExt = self.printersettings.settings['extruders']
		if len(self.temperatures) < 2:
			self.logger.LogError("No hot end temperatures configured in your profile")
		if len(self.temperatures) != maxExt+1:
			self.logger.LogWarning("Your profile does not have the same number of extruders configured")
			t = self.temperatures[1]
			ntemps = len(self.temperatures)
			for i in range(maxExt - ntemps + 1):
				self.temperatures.append(t)
		if idx is not None:
			return self.temperatures[idx]
			
	def addHeaters(self):
		sizerHeat = wx.BoxSizer(wx.VERTICAL)
		sizerHeat.AddSpacer((10,10))

		self.hotend = []
		self.heLabel = []		
		maxExt = self.printersettings.settings['extruders']
		self.getProfileHeaterValue()

		for i in range(maxExt):
			name = "Hot End"
			if maxExt > 1:
				name += " " + str(i)
			t = wx.StaticText(self, wx.ID_ANY, name, style=wx.ALIGN_LEFT, size=(200, -1))
			f = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
			t.SetFont(f)
			sizerHeat.Add(t, flag=wx.LEFT)
			self.heLabel.append(t)
			sizerHeat.AddSpacer((10,10))
		
			he = Heater(self, self.app, i+1, name="Hot End", target=self.temperatures[i+1], range=(20, 250), oncmd="G104")
			sizerHeat.Add(he)
			self.hotend.append(he)
			sizerHeat.AddSpacer((10,10))
		
		sizerHeat.AddSpacer((20,20))
		
		t = wx.StaticText(self, wx.ID_ANY, "Build Platform", style=wx.ALIGN_LEFT, size=(200, -1))
		f = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
		t.SetFont(f)
		sizerHeat.Add(t, flag=wx.LEFT)
		self.bpLabel = t
		
		sizerHeat.AddSpacer((10,10))
		
		self.BuildPlatform = Heater(self, self.app, 0, name="Build Platform", target=self.temperatures[0], range=(20, 130), oncmd="G140")
		sizerHeat.Add(self.BuildPlatform)
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

		
	def changePrinter(self):
		self.printersettings = self.app.printersettings

		item = self.sizerMain.FindItem(self.sizerExtrude)
		if item is None:
			self.logger.LogError("Unable to locate Extruder sizer")
			return False
		
		oldPos = item.GetPos()
		oldSpan = item.GetSpan()
		self.sizerMain.Detach(self.sizerExtrude)
		for ex in self.extruder:
			ex.Destroy()
		for exl in self.extLabel:
			exl.Destroy()
		self.sizerExtrude = self.addExtruders()
		self.sizerMain.Add(self.sizerExtrude, pos=oldPos, span=oldSpan)

		item = self.sizerMain.FindItem(self.sizerHeat)
		if item is None:
			self.logger.LogError("Unable to locate Heater sizer")
			return False
		
		oldPos = item.GetPos()
		oldSpan = item.GetSpan()
		self.sizerMain.Detach(self.sizerHeat)
		for he in self.hotend:
			he.Destroy()
		for hel in self.heLabel:
			hel.Destroy()
		self.BuildPlatform.Destroy()
		self.bpLabel.Destroy()
		self.sizerHeat = self.addHeaters()
		self.sizerMain.Add(self.sizerHeat, pos=oldPos, span=oldSpan)

		item = self.sizerMain.FindItem(self.sizerGCode)
		if item is None:
			self.logger.LogError("Unable to locate G Code sizer")
			return False
		
		oldPos = item.GetPos()
		oldSpan = item.GetSpan()
		self.sizerMain.Detach(self.sizerGCode)
		self.GCEntry.Destroy()
		self.GCELabel.Destroy()
		self.sizerGCode = self.addGCEntry()
		self.sizerMain.Add(self.sizerGCode, pos=oldPos, span=oldSpan)

		self.sizerMain.RecalcSizes()	
		self.Layout()
		self.Fit()
	
	#FIXIT need similar logic for slicer change and profile chnage

	def onClose(self, evt):
		return True
