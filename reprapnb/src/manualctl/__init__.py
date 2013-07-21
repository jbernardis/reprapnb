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
		self.htrWin = []
		self.htrLabel = []	
		self.heaters = []	
		self.extWin = []
		self.extLabel = []
		self.extruders = []
		self.htrMap = {}	

		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(100, 100))
		self.SetBackgroundColour("white")

		self.moveAxis = MoveAxis(self, self.app)				
		self.sizerMove = wx.BoxSizer(wx.VERTICAL)
		self.sizerMove.AddSpacer((20,20))
		self.sizerMove.Add(self.moveAxis)
		
		self.sizerExtrude = None
		self.sizerHeat = None
		self.sizerGCode = None
		
		self.sizerMain = wx.GridBagSizer(hgap=5, vgap=5)
		self.sizerMain.AddSpacer((20,20), pos=(0,0))
		self.sizerMain.Add(self.sizerMove, pos=(1,1), span=(2,1))
		self.sizerMain.AddSpacer((10,10), pos=(0,2))
		self.sizerMain.AddSpacer((10,10), pos=(0,4))

		self.SetSizer(self.sizerMain)
		self.Layout()
		self.Fit()
		
	def setHeatTarget(self, name, temp):
		if name not in self.htrMap.keys():
			self.logger.LogError("Unknown heater name: %s" % name)
			return
		
		self.htrMap[name].setHeatTarget(temp)
		
	def setHeatTemp(self, name, temp):
		if name not in self.htrMap.keys():
			self.logger.LogError("Unknown heater name: %s" % name)
			return
		
		self.htrMap[name].setHeatTemp(temp)
		
	def addExtruders(self):
		sizerExtrude = wx.BoxSizer(wx.VERTICAL)
		sizerExtrude.AddSpacer((10,10))
		self.extWin = []
		self.extLabel = []
		
		for e in self.extruders:
			ex = Extruder(self, self.app, axis=e[2])
			self.extWin.append(ex)
			t = wx.StaticText(self, wx.ID_ANY, e[1], style=wx.ALIGN_LEFT, size=(200, -1))
			f = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
			t.SetFont(f)
			self.extLabel.append(t)
			sizerExtrude.Add(t, flag=wx.LEFT)
			sizerExtrude.AddSpacer((10,10))
			sizerExtrude.Add(ex)
			sizerExtrude.AddSpacer((10,10))
			
		return sizerExtrude
			
	def addHeaters(self):
		sizerHeat = wx.BoxSizer(wx.VERTICAL)
		sizerHeat.AddSpacer((10,10))

		self.htrWin = []
		self.htrLabel = []	
		
		self.htrMap = {}	

		for h in self.heaters:
			t = wx.StaticText(self, wx.ID_ANY, h[1], style=wx.ALIGN_LEFT, size=(200, -1))
			f = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
			t.SetFont(f)
			sizerHeat.Add(t, flag=wx.LEFT)
			self.htrLabel.append(t)
			sizerHeat.AddSpacer((10,10))
		
			he = Heater(self, self.app, name=h[1], shortname=h[0], 
					target=h[2], trange=h[3], oncmd=h[4])
			sizerHeat.Add(he)
			self.htrWin.append(he)
			self.htrMap[h[0]] = he
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
		
	def changePrinter(self, heaters, extruders):
		self.heaters = heaters
		self.extruders = extruders

		oldPos = (1,3)
		oldSpan = (1,1)
		if self.sizerExtrude is not None:
			item = self.sizerMain.FindItem(self.sizerExtrude)
			if item is not None:
				oldPos = item.GetPos()
				oldSpan = item.GetSpan()
				self.sizerMain.Detach(self.sizerExtrude)
				for ex in self.extWin:
					ex.Destroy()
				for exl in self.extLabel:
					exl.Destroy()
				
		self.sizerExtrude = self.addExtruders()
		self.sizerMain.Add(self.sizerExtrude, pos=oldPos, span=oldSpan)

		oldPos = (1,5)
		oldSpan = (1,1)
		if self.sizerHeat is not None:
			item = self.sizerMain.FindItem(self.sizerHeat)
			if item is not None:
				oldPos = item.GetPos()
				oldSpan = item.GetSpan()
				self.sizerMain.Detach(self.sizerHeat)
				for he in self.htrWin:
					he.Destroy()
				for hel in self.htrLabel:
					hel.Destroy()
			
		self.sizerHeat = self.addHeaters()
		self.sizerMain.Add(self.sizerHeat, pos=oldPos, span=oldSpan)

		oldPos = (2,3)
		oldSpan = (1,3)
		if self.sizerGCode is not None:
			item = self.sizerMain.FindItem(self.sizerGCode)
			if item is not None:
				oldPos = item.GetPos()
				oldSpan = item.GetSpan()
				self.sizerMain.Detach(self.sizerGCode)
				self.GCEntry.Destroy()
				self.GCELabel.Destroy()
			
		self.sizerGCode = self.addGCEntry()
		self.sizerMain.Add(self.sizerGCode, pos=oldPos, span=oldSpan)

		self.Layout()
		self.Fit()
	
	#FIXIT need similar logic for slicer change and profile chnage

	def onClose(self, evt):
		return True
