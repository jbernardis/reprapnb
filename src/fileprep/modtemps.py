import wx

MINBED = -100
MAXBED = 100
MINHE = -200
MAXHE = 200

class ModifyTempsDlg(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Modify Temperatures")
		
		ipfont = wx.Font(16,  wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

		self.app = parent
		self.model = self.app.model
		
		self.bed, self.hotends = self.model.getTemps()

		self.bedDelta = 0
		self.heDelta = [0, 0]
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		slidesizer = wx.GridSizer(rows=1, cols=4)
		profbtnsizer = wx.BoxSizer(wx.HORIZONTAL)
		btnsizer = wx.StdDialogButtonSizer()

		self.modBed = wx.Slider(
			self, wx.ID_ANY, 0, MINBED, MAXBED, size=(150, -1),
			style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
		self.modBed.Bind(wx.EVT_SCROLL_CHANGED, self.onSpinBed)
		self.modBed.Bind(wx.EVT_MOUSEWHEEL, self.onMouseBed)
		self.modBed.SetPageSize(1);

		b = wx.StaticBox(self, wx.ID_ANY, "Bed Temperature Delta")
		sbox = wx.StaticBoxSizer(b, wx.VERTICAL)
		sbox.Add(self.modBed, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
		slidesizer.Add(sbox, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
		
		self.bedTemp = wx.StaticText(self, wx.ID_ANY, "");
		self.bedTemp.SetFont(ipfont)
		slidesizer.Add(self.bedTemp, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 40)

		self.modHE0 = wx.Slider(
			self, wx.ID_ANY, 0, MINHE, MAXHE, size=(150, -1),
			style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
		self.modHE0.Bind(wx.EVT_SCROLL_CHANGED, self.onSpinHE0)
		self.modHE0.Bind(wx.EVT_MOUSEWHEEL, self.onMouseHE0)
		self.modHE0.SetPageSize(1);

		b = wx.StaticBox(self, wx.ID_ANY, "Hot End 0 Delta")
		sbox = wx.StaticBoxSizer(b, wx.VERTICAL)
		sbox.Add(self.modHE0, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
		slidesizer.Add(sbox, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)

		self.he0Temp = wx.StaticText(self, wx.ID_ANY, "");
		self.he0Temp.SetFont(ipfont)
		slidesizer.Add(self.he0Temp, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 40)
		
		if len(self.hotends) > 1:
			self.modHE1 = wx.Slider(
				self, wx.ID_ANY, 0, MINHE, MAXHE, size=(150, -1),
				style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
			self.modHE1.Bind(wx.EVT_SCROLL_CHANGED, self.onSpinHE1)
			self.modHE1.Bind(wx.EVT_MOUSEWHEEL, self.onMouseHE1)
			self.modHE1.SetPageSize(1);
	
			b = wx.StaticBox(self, wx.ID_ANY, "Hot End 1 Delta")
			sbox = wx.StaticBoxSizer(b, wx.VERTICAL)
			sbox.Add(self.modHE1, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
			slidesizer.Add(sbox, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
	
			self.he1Temp = wx.StaticText(self, wx.ID_ANY, "");
			self.he1Temp.SetFont(ipfont)
			slidesizer.Add(self.he1Temp, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 40)

		btn = wx.Button(self, wx.ID_ANY, "PLA->ABS")
		btn.SetHelpText("Change from PLA profile to ABS")
		self.Bind(wx.EVT_BUTTON, self.profilePLA2ABS, btn)
		profbtnsizer.Add(btn);

		btn = wx.Button(self, wx.ID_ANY, "ABS->PLA")
		btn.SetHelpText("Change from ABS profile to PLA")
		self.Bind(wx.EVT_BUTTON, self.profileABS2PLA, btn)
		profbtnsizer.Add(btn);
		
		self.btnOK = wx.Button(self, wx.ID_OK)
		self.btnOK.SetHelpText("Save the changes")
		self.btnOK.SetDefault()
		btnsizer.AddButton(self.btnOK)
		self.btnOK.Enable(False)

		self.btnCancel = wx.Button(self, wx.ID_CANCEL)
		self.btnCancel.SetHelpText("Exit without saving")
		self.btnCancel.SetLabel("Close")
		btnsizer.AddButton(self.btnCancel)
		btnsizer.Realize()

		self.showTemps()

		sizer.Add(slidesizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
		sizer.Add(profbtnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
		sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

		self.SetSizer(sizer)
		sizer.Fit(self)

	def profilePLA2ABS(self, evt):
		self.bedDelta = 50
		self.heDelta = [40, 40]
		self.showTemps()

	def profileABS2PLA(self, evt):
		self.bedDelta = -50
		self.heDelta = [-40, -40]
		self.showTemps()

	def showTemps(self):
		changes = False
		if self.bed is None:
			s = "?? / ??"
		else:
			if self.bedDelta != 0:
				changes = True
			s = "%.1f / %.1f" % (self.bed, self.bed+self.bedDelta)
		self.bedTemp.SetLabel(s)
		self.modBed.SetValue(self.bedDelta)

		if self.hotends[0] is None:
			s = "?? / ??"
		else:
			if self.heDelta[0] != 0:
				changes = True
			s = "%.1f / %.1f" % (self.hotends[0], self.hotends[0]+self.heDelta[0])
		self.he0Temp.SetLabel(s)
		self.modHE0.SetValue(self.heDelta[0])

		if len(self.hotends) > 1:
			if self.heDelta[1] != 0:
				changes = True
			s = "%.1f / %.1f" % (self.hotends[1], self.hotends[1]+self.heDelta[1])
			self.he1Temp.SetLabel(s)
			self.modHE1.SetValue(self.heDelta[1])

		if changes:
			self.btnOK.Enable(True)
			self.btnCancel.SetLabel("Cancel")
		else:
			self.btnOK.Enable(False)
			self.btnCancel.SetLabel("Close")
		
	def onSpinBed(self, evt):
		self.bedDelta = evt.EventObject.GetValue()
		self.showTemps()
	
	def onSpinHE0(self, evt):
		self.heDelta[0] = evt.EventObject.GetValue()
		self.showTemps()
	
	def onSpinHE1(self, evt):
		self.heDelta[1] = evt.EventObject.GetValue()
		self.showTemps()
	
	def onMouseBed(self, evt):
		l = self.modBed.GetValue()
		if evt.GetWheelRotation() < 0:
			l -= 1
		else:
			l += 1
		if l >= MINBED and l <= MAXBED:
			self.bedDelta = l
			self.showTemps()
	
	def onMouseHE0(self, evt):
		l = self.modHE0.GetValue()
		if evt.GetWheelRotation() < 0:
			l -= 1
		else:
			l += 1
		if l >= MINHE and l <= MAXHE:
			self.heDelta[0] = l
			self.showTemps()
	
	def onMouseHE1(self, evt):
		l = self.modHE1.GetValue()
		if evt.GetWheelRotation() < 0:
			l -= 1
		else:
			l += 1
		if l >= MINHE and l <= MAXHE:
			self.heDelta[1] = l
			self.showTemps()
			
	def getResult(self):
		return (self.bedDelta, self.heDelta)

