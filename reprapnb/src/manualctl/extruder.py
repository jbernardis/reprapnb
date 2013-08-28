import wx
import os.path

from images import Images

BUTTONDIM = (64, 64)

class Extruder(wx.Window): 
	def __init__(self, parent, app, name="", axis="E"):
		self.parent = parent
		self.app = app
		self.logger = self.app.logger

		self.name = name
		self.axis = axis
		wx.Window.__init__(self, parent, wx.ID_ANY, size=(-1, -1), style=wx.SIMPLE_BORDER)		
		sizerExtrude = wx.GridBagSizer()

		t = wx.StaticText(self, wx.ID_ANY, "%s Speed (mm/min):" % self.axis, style=wx.ALIGN_RIGHT, size=(200, -1))
		f = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
		t.SetFont(f)
		sizerExtrude.Add(t, pos=(1,0), span=(1,3))
		self.tESpeed = wx.TextCtrl(self, wx.ID_ANY, str(self.parent.settings.espeed), size=(80, -1), style=wx.TE_RIGHT)
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
		self.tESpeed.SetFont(f)
		sizerExtrude.Add(self.tESpeed, pos=(1,3))
		self.tESpeed.Bind(wx.EVT_KILL_FOCUS, self.evtESpeedKillFocus)

		sizerExtrude.AddSpacer((10,10), pos=(2,1))
		
		t = wx.StaticText(self, wx.ID_ANY, "%s Distance (mm):" % self.axis, style=wx.ALIGN_RIGHT, size=(200, -1))
		f = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
		t.SetFont(f)
		sizerExtrude.Add(t, pos=(3,0), span=(1,3))
		
		self.tEDistance = wx.TextCtrl(self, wx.ID_ANY, str(self.parent.settings.edistance), size=(80, -1), style=wx.TE_RIGHT)
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
		self.tEDistance.SetFont(f)
		sizerExtrude.Add(self.tEDistance, pos=(3,3))
		self.tEDistance.Bind(wx.EVT_KILL_FOCUS, self.evtEDistanceKillFocus)
		
		sizerExtrude.AddSpacer((10,10), pos=(4,0))
		sizerExtrude.AddSpacer((64, 64), pos=(5,0))
		
		self.images = Images(os.path.join(self.parent.settings.cmdfolder, "images"))
				
		self.bExtrude = wx.BitmapButton(self, wx.ID_ANY, self.images.pngExtrude, size=BUTTONDIM)
		self.bExtrude.SetToolTipString("Extrude filament")
		sizerExtrude.Add(self.bExtrude, pos=(5,1))
		self.Bind(wx.EVT_BUTTON, self.doExtrude, self.bExtrude)
				
		self.bRetract = wx.BitmapButton(self, wx.ID_ANY, self.images.pngRetract, size=BUTTONDIM)
		self.bRetract.SetToolTipString("Retract filament")
		sizerExtrude.Add(self.bRetract, pos=(5,2))
		self.Bind(wx.EVT_BUTTON, self.doRetract, self.bRetract)

		self.SetSizer(sizerExtrude)
		self.Layout()
		self.Fit()
		
	def evtESpeedKillFocus(self, evt):
		try:
			v = float(self.tESpeed.GetValue())
		except:
			self.logger.LogError("Invalid value for E Speed: %s" % self.tESpeed.GetValue())
		
	def evtEDistanceKillFocus(self, evt):
		try:
			v = float(self.tEDistance.GetValue())
		except:
			self.logger.LogError("Invalid value for E Distance: %s" % self.tEDistance.GetValue())
			
	def doExtrude(self, evt):
		try:
			sp = float(self.tESpeed.GetValue())
		except:
			self.logger.LogError("Invalid value for E Speed: %s" % self.tESpeed.GetValue())
			sp = 0
		try:
			dst = float(self.tEDistance.GetValue())
		except:
			self.logger.LogError("Invalid value for E Distance: %s" % self.tEDistance.GetValue())
			dst = 0
		self.app.reprap.send_now("G91")
		self.app.reprap.send_now("G1 %s%.3f F%.3f" % (self.axis.upper(), dst, sp))
		self.app.reprap.send_now("G90")
		
	def doRetract(self, evt):
		try:
			sp = float(self.tESpeed.GetValue())
		except:
			self.logger.LogError("Invalid value for E Speed: %s" % self.tESpeed.GetValue())
			sp = 0
		try:
			dst = float(self.tEDistance.GetValue())
		except:
			self.logger.LogError("Invalid value for E Distance: %s" % self.tEDistance.GetValue())
			dst = 0
		self.app.reprap.send_now("G91")
		self.app.reprap.send_now("G1 %s-%.3f F%.3f" % (self.axis.upper(), dst, sp))
		self.app.reprap.send_now("G90")
		

