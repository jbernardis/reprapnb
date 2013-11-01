import wx

BUTTONDIM = (48, 48)

orange = wx.Colour(237, 139, 33)


class HotEnd(wx.Window): 
	def __init__(self, parent, app,
				name=("", "", ""), shortname=("", "", ""),
				target=(20, 20, 20), trange=((0, 100), (0,100), (0, 100)), nextr=1):
		self.parent = parent
		self.app = app
		self.logger = self.app.logger
		self.currentSelection = 0
		self.name = name
		self.shortname = shortname
		self.profileTarget = target
		self.trange = trange
		self.currentTemp = [0.0, 0.0, 0.0]
		self.currentTarget = [0.0, 0.0, 0.0]
		self.currentTempColor = [None, None, None]

		self.nextr = nextr
		wx.Window.__init__(self, parent, wx.ID_ANY, size=(-1, -1), style=wx.SIMPLE_BORDER)		
		sizerHE = wx.BoxSizer(wx.VERTICAL)

		dc = wx.WindowDC(self)
		f = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		dc.SetFont(f)

		self.rbTools = []
		self.btnOn = []
		self.btnOff = []
		self.txtTemp = []
		self.txtTarget = []
		self.sliders = []
		self.btnImport = []
		
		for i in range(3):
			sizerRow = wx.BoxSizer(wx.HORIZONTAL)
			if i == 0:
				style = wx.RB_GROUP
			else:
				style = 0
			rb = wx.RadioButton(self, wx.ID_ANY, " Tool %d " % (i+1), style = style)
			self.rbTools.append(rb)
			sizerRow.Add(rb, flag=wx.TOP | wx.BOTTOM, border=5)
			sizerRow.AddSpacer((10, 10))
			self.Bind(wx.EVT_RADIOBUTTON, self.onToolChange, rb )
			rb.Enable(i<self.nextr)

			btn = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngHeaton, size=BUTTONDIM)
			btn.SetToolTipString("Turn hot end %d on" % i)
			sizerRow.Add(btn)
			self.Bind(wx.EVT_BUTTON, self.heaterOn, btn)
			btn.Enable(i<self.nextr)
			self.btnOn.append(btn)
				
			btn = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngHeatoff, size=BUTTONDIM)
			btn.SetToolTipString("Turn hot end %d off" % i)
			sizerRow.Add(btn)
			self.Bind(wx.EVT_BUTTON, self.heaterOff, btn)
			btn.Enable(i<self.nextr)
			self.btnOff.append(btn)

			txt = wx.TextCtrl(self, wx.ID_ANY, "???", size=(60, -1), style=wx.TE_RIGHT | wx.TE_READONLY)
			txt.SetFont(f)
			txt.SetBackgroundColour("blue")
			txt.SetForegroundColour(wx.Colour(255, 255, 255))
			sizerRow.Add(txt)
			self.txtTemp.append(txt)
	
			txt = wx.TextCtrl(self, wx.ID_ANY, "", size=(60, -1), style=wx.TE_RIGHT | wx.TE_READONLY)
			txt.SetFont(f)
			txt.SetBackgroundColour(wx.Colour(0, 0, 0))
			txt.SetForegroundColour(wx.Colour(255, 255, 255))
			sizerRow.Add(txt)
			self.txtTarget.append(txt)

			sldr = wx.Slider(
				self, wx.ID_ANY, target[i], self.trange[i][0], self.trange[i][1], size=(320, -1), 
				style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS 
				)
			sldr.SetTickFreq(5, 1)
			sldr.SetPageSize(1)
			sldr.Bind(wx.EVT_SCROLL_CHANGED, self.onTargetChanged)
			sldr.Bind(wx.EVT_MOUSEWHEEL, self.onTargetWheel)
			sizerRow.Add(sldr)
			self.sliders.append(sldr)

			btn = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngProfile, size=BUTTONDIM)
			btn.SetToolTipString("Import from profile")
			sizerRow.Add(btn)
			self.Bind(wx.EVT_BUTTON, self.importProfile, btn)
			sizerRow.Add(btn)
			self.btnImport.append(btn)
			
			sizerHE.Add(sizerRow)

		self.rbTools[0].SetValue(True)

		self.SetSizer(sizerHE)
		self.Layout()
		self.Fit()
		
	def onToolChange(self, evt):
		tc_sel = evt.GetEventObject()

		for i in range(3):
			if tc_sel is self.rbTools[i]:
				self.currentSelection = i
				break
		
	def changePrinter(self, nextr):
		self.nextr = nextr
		for i in range(3):
			self.rbTools[i].Enable(i<self.nextr)
			self.btnOn[i].Enable(i<self.nextr)
			self.btnOff[i].Enable(i<self.nextr)
			self.txtTemp[i].Enable(i<self.nextr)
			self.txtTarget[i].Enable(i<self.nextr)
			self.sliders[i].Enable(i<self.nextr)
			self.btnImport[i].Enable(i<self.nextr)
			
		if self.currentSelection >= self.nextr:
			self.currentSelection = 0
			self.rbTools[0].SetValue(True)

	def importProfile(self, evt):
		tc_sel = evt.GetEventObject()
		sel = None
		for i in range(self.nextr):
			if tc_sel is self.btnImport[i]:
				sel = i
				break

		if sel is None:
			return
		
		self.slTarget[sel].SetValue(self.profileTarget[sel])
			
	def setProfileTarget(self, t):
		self.profileTarget = t
		
	def setHeatTarget(self, tool, temp):
		if tool < 0 or tool >- self.nextr:
			self.logger.LogError("Tool number out of range")
			return
		
		if temp is None or temp == 0:
			self.txtTarget[tool].SetBackgroundColour("black")
			self.txtTarget[tool].SetValue("")
			self.currentTarget[tool] = 0
			return
		
		try:
			ft = float(temp)
		except:
			self.logger.LogError("Invalid value for %s temperature: '%s'" % (self.name, temp))
			return
		
		self.txtTarget[tool].SetValue("%.1f" % ft)
		self.currentTarget[tool] = ft

	def setHeatTemp(self, tool, temp):
		if tool < 0 or tool >- self.nextr:
			self.logger.LogError("Tool number out of range")
			return
		
		if temp is None:
			self.txtTemp[tool].SetBackgroundColour("black")
			self.txtTemp[tool].SetValue("???")
			return
		
		try:
			ft = float(temp)
		except:
			self.logger.LogError("Invalid value for %s temperature: '%s'" % (self.name, temp))
			return
		
		self.currentTemp[tool] = ft

		c = self.currentTempColor[tool]
		if self.currentTarget[tool] != 0:
			if self.currentTemp[tool] < self.currentTarget[tool]:
				c = orange
			else:
				c = "red"
		else:
			if self.currentTemp[tool] < 30.0:
				c = "blue"
			else:
				c = "green"
				
		if c != self.currentTempColor[tool]:
			self.currentTempColor[tool] = c
			self.txtTemp[tool].SetBackgroundColour(c)
			
		self.txtTemp[tool].SetValue("%.1f" % ft)

	def onTargetChanged(self, evt):
		pass
	
	def onTargetWheel(self, evt):
		tc_sel = evt.GetEventObject()
		sel = None
		for i in range(self.nextr):
			if tc_sel is self.sliders[i]:
				sel = i
				break

		if sel is None:
			return
					
		l = self.sliders[i].GetValue()
		if evt.GetWheelRotation() < 0:
			l -= 1
		else:
			l += 1
		if l >= self.trange[i][0] and l <= self.trange[i][1]:
			self.sliders[i].SetValue(l)

	
	def heaterOn(self, evt):
		tc_sel = evt.GetEventObject()
		sel = None
		for i in range(self.nextr):
			if tc_sel is self.btnOn[i]:
				sel = i
				break

		if sel is None:
			return
					
		t = self.sliders[i].GetValue()
		cmd = "M104 S%d" % t
		if self.nextr > 1:
			cmd += " T" + str(sel)
		self.app.reprap.send_now(cmd)
		
	def heaterOff(self, evt):
		tc_sel = evt.GetEventObject()
		sel = None
		for i in range(self.nextr):
			if tc_sel is self.btnOff[i]:
				sel = i
				break

		if sel is None:
			return
					
		cmd = "M104 S0"
		if self.nextr > 1:
			cmd += " T" + str(sel)
		self.app.reprap.send_now(cmd)


