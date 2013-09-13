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
		sizerExtrude = wx.BoxSizer(wx.HORIZONTAL)
		
		szLeft = wx.BoxSizer(wx.VERTICAL)
		szLeft.AddSpacer((10, 10))
		szCenter = wx.BoxSizer(wx.VERTICAL)
		szCenter.AddSpacer((10, 10))
		szRight = wx.BoxSizer(wx.VERTICAL)

		dc = wx.WindowDC(self)
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
		dc.SetFont(f)

		text1 = "%s Speed (mm/min):" % self.axis
		w, h = dc.GetTextExtent(text1)
		text2 = "%s Distance (mm):" % self.axis
		w2, h2 = dc.GetTextExtent(text2)
		if w2 > w: w = w2
		if h2 > h: h = h2
		
		t = wx.StaticText(self, wx.ID_ANY, text1, style=wx.ALIGN_RIGHT, size=(w, h))
		t.SetFont(f)
		szLeft.Add(t, flag=wx.ALIGN_RIGHT | wx.ALL, border=10)
		
		self.tESpeed = wx.TextCtrl(self, wx.ID_ANY, str(self.parent.settings.espeed), size=(80, -1), style=wx.TE_RIGHT)
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
		self.tESpeed.SetFont(f)
		szCenter.Add(self.tESpeed, flag=wx.ALL, border=5)
		self.tESpeed.Bind(wx.EVT_KILL_FOCUS, self.evtESpeedKillFocus)
		
		t = wx.StaticText(self, wx.ID_ANY, text2, style=wx.ALIGN_RIGHT, size=(w, h))
		t.SetFont(f)
		szLeft.Add(t, flag=wx.ALIGN_RIGHT | wx.ALL, border=10)
		
		self.tEDistance = wx.TextCtrl(self, wx.ID_ANY, str(self.parent.settings.edistance), size=(80, -1), style=wx.TE_RIGHT)
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
		self.tEDistance.SetFont(f)
		szCenter.Add(self.tEDistance, flag=wx.ALL, border=5)
		self.tEDistance.Bind(wx.EVT_KILL_FOCUS, self.evtEDistanceKillFocus)
		
		self.bExtrude = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngExtrude, size=BUTTONDIM)
		self.bExtrude.SetToolTipString("Extrude filament")
		szRight.Add(self.bExtrude, flag=wx.ALL, border=10)
		self.Bind(wx.EVT_BUTTON, self.doExtrude, self.bExtrude)
				
		self.bRetract = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngRetract, size=BUTTONDIM)
		self.bRetract.SetToolTipString("Retract filament")
		szRight.Add(self.bRetract, flag=wx.ALL, border=10)
		self.Bind(wx.EVT_BUTTON, self.doRetract, self.bRetract)
		
		sizerExtrude.Add(szLeft)
		sizerExtrude.Add(szCenter)
		sizerExtrude.AddSpacer((20, 20))
		sizerExtrude.Add(szRight, flag=wx.ALIGN_RIGHT)

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
		

