import wx

from settings import BUTTONDIM

orange = wx.Colour(237, 139, 33)

class HotBed(wx.Window):
	def __init__(self, parent, app, reprap, name="", shortname="", target=[0, 20, 20], trange=(0, 100)):
		self.parent = parent
		self.app = app
		self.reprap = reprap
		self.logger = self.app.logger
		self.name = name
		self.shortname = shortname
		self.trange = trange
		self.currentTemp = 0.0
		self.currentTarget = 0.0
		self.currentTempColor = None
		wx.Window.__init__(self, parent, wx.ID_ANY, size=(-1, -1), style=wx.SIMPLE_BORDER)		
		sizerHB = wx.GridBagSizer(vgap=10, hgap=10)
		
		sizerHB.AddSpacer((5, 5), pos=(0,0))
		sizerHB.AddSpacer((5, 5), pos=(4,6))

		dc = wx.WindowDC(self)
		f = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		dc.SetFont(f)

		text = "Current: "
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w, h))
		t.SetFont(f)
		sizerHB.Add(t, pos=(1,3), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL) 
		
		self.tTemp = wx.TextCtrl(self, wx.ID_ANY, "???", size=(60, -1), style=wx.TE_RIGHT | wx.TE_READONLY)
		self.tTemp.SetFont(f)
		self.tTemp.SetBackgroundColour("blue")
		self.tTemp.SetForegroundColour(wx.Colour(255, 255, 255))
		sizerHB.Add(self.tTemp, pos=(1,4))

		text = "Target: "
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w, h))
		t.SetFont(f)
		sizerHB.Add(t, pos=(2,3), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER)
		
		self.tTarget = wx.TextCtrl(self, wx.ID_ANY, "", size=(60, -1), style=wx.TE_RIGHT | wx.TE_READONLY)
		self.tTarget.SetFont(f)
		self.tTarget.SetBackgroundColour(wx.Colour(0, 0, 0))
		self.tTarget.SetForegroundColour(wx.Colour(255, 255, 255))
		sizerHB.Add(self.tTarget, pos=(2,4))
		
		self.slTarget = wx.Slider(
			self, wx.ID_ANY, target[1], self.trange[0], self.trange[1], size=(320, -1), 
			style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS 
			)
		self.slTarget.SetTickFreq(5, 1)
		self.slTarget.SetPageSize(1)
		self.slTarget.Bind(wx.EVT_SCROLL_CHANGED, self.onTargetChanged)
		self.slTarget.Bind(wx.EVT_MOUSEWHEEL, self.onTargetWheel)
		sizerHB.Add(self.slTarget, pos=(3,1), span=(1,5))

		self.bHeatOn = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngHeaton, size=BUTTONDIM)
		self.bHeatOn.SetToolTipString("Turn %s heater on" % self.name)
		sizerHB.Add(self.bHeatOn, pos=(1,1),span=(2,1))
		self.Bind(wx.EVT_BUTTON, self.heaterOn, self.bHeatOn)
				
		self.bHeatOff = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngHeatoff, size=BUTTONDIM)
		self.bHeatOff.SetToolTipString("Turn %s heater off" % self.name)
		sizerHB.Add(self.bHeatOff, pos=(1,2),span=(2,1))
		self.Bind(wx.EVT_BUTTON, self.heaterOff, self.bHeatOff)
				
		self.bProfile = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngProfile, size=BUTTONDIM)
		self.bProfile.SetToolTipString("Import from G Code")
		sizerHB.Add(self.bProfile, pos=(1,5),span=(2,1))
		self.Bind(wx.EVT_BUTTON, self.importProfile, self.bProfile)

		self.SetSizer(sizerHB)
		self.Layout()
		self.Fit()
		
	def setRange(self, trange):
		self.trange = trange
		self.slTarget.SetRange(trange[0], trange[1])
		
	def importProfile(self, evt):
		temp = self.parent.getBedGCode()
		if temp is None:
			self.logger.LogMessage("Unable to obtain temperature from G Code")
			return
		
		self.slTarget.SetValue(temp)
		
	def setHeatTarget(self, t):
		if t is None or t == 0:
			self.tTarget.SetBackgroundColour("black")
			self.tTarget.SetValue("")
			self.currentTarget = 0
			return
		
		try:
			ft = float(t)
		except:
			self.logger.LogError("Invalid value for %s temperature: '%s'" % (self.name, t))
			return
		
		self.tTarget.SetValue("%.1f" % ft)
		self.currentTarget = ft

	def setHeatTemp(self, t):
		if t is None:
			self.tTemp.SetBackgroundColour("black")
			self.tTemp.SetValue("???")
			return
		
		try:
			ft = float(t)
		except:
			self.logger.LogError("Invalid value for %s temperature: '%s'" % (self.name, t))
			return
		
		self.currentTemp = ft

		c = self.currentTempColor
		if self.currentTarget != 0:
			if self.currentTemp < self.currentTarget:
				c = orange
			else:
				c = "red"
		else:
			if self.currentTemp < 30.0:
				c = "blue"
			else:
				c = "green"
				
		if c != self.currentTempColor:
			self.currentTempColor = c
			self.tTemp.SetBackgroundColour(c)
			
		self.tTemp.SetValue("%.1f" % ft)

	def onTargetChanged(self, evt):
		pass
	
	def onTargetWheel(self, evt):
		l = self.slTarget.GetValue()
		if evt.GetWheelRotation() < 0:
			l -= 1
		else:
			l += 1
		if l >= self.trange[0] and l <= self.trange[1]:
			self.slTarget.SetValue(l)

	
	def heaterOn(self, evt):
		t = self.slTarget.GetValue()
		self.heaterTemp(t)
		
	def heaterOff(self, evt):
		self.heaterTemp(0)
		
	def heaterTemp(self, temp):
		self.reprap.send_now("M140 S%d" % temp)
		

