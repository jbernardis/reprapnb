import wx
import os.path

from images import Images

BUTTONDIM = (48, 48)

class Extruder(wx.Window): 
	def __init__(self, parent, app, name="", axis="E"):
		self.parent = parent
		self.app = app
		self.logger = self.app.logger

		self.name = name
		self.axis = axis
		wx.Window.__init__(self, parent, wx.ID_ANY, size=(-1, -1), style=wx.SIMPLE_BORDER)		
		sizerExtrude = wx.GridBagSizer(vgap=10, hgap=10)
		
		sizerExtrude.AddSpacer((5, 5), pos=(0,0))
		sizerExtrude.AddSpacer((5, 5), pos=(5,5))

		dc = wx.WindowDC(self)
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
		dc.SetFont(f)

		text = "%s Speed (mm/min):" % self.axis
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w, h))
		t.SetFont(f)
		sizerExtrude.Add(t, pos=(1,1), span=(1,3), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
		
		self.tESpeed = wx.TextCtrl(self, wx.ID_ANY, str(self.parent.settings.espeed), size=(80, -1), style=wx.TE_RIGHT)
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
		self.tESpeed.SetFont(f)
		sizerExtrude.Add(self.tESpeed, pos=(1,4))
		self.tESpeed.Bind(wx.EVT_KILL_FOCUS, self.evtESpeedKillFocus)

		sizerExtrude.AddSpacer((4,4), pos=(2,1))
		
		text = "%s Distance (mm):" % self.axis
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w, h))
		t.SetFont(f)
		sizerExtrude.Add(t, pos=(3,1), span=(1,3), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
		
		self.tEDistance = wx.TextCtrl(self, wx.ID_ANY, str(self.parent.settings.edistance), size=(80, -1), style=wx.TE_RIGHT)
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
		self.tEDistance.SetFont(f)
		sizerExtrude.Add(self.tEDistance, pos=(3,4))
		self.tEDistance.Bind(wx.EVT_KILL_FOCUS, self.evtEDistanceKillFocus)
		
		self.bExtrude = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngExtrude, size=BUTTONDIM)
		self.bExtrude.SetToolTipString("Extrude filament")
		sizerExtrude.Add(self.bExtrude, pos=(4,4))
		self.Bind(wx.EVT_BUTTON, self.doExtrude, self.bExtrude)
				
		self.bRetract = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngRetract, size=BUTTONDIM)
		self.bRetract.SetToolTipString("Retract filament")
		sizerExtrude.Add(self.bRetract, pos=(4,5))
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
		

