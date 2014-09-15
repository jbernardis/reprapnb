import wx

MINBED = -100
MAXBED = 100
MINHE = -200
MAXHE = 200

class ModifyTempsDlg(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Modify Temperatures")
		
		self.app = parent
		self.model = self.app.model
		
		self.bed = 0
		self.hotends = [0, 0]
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		slidesizer = wx.GridSizer(rows=1, cols=2)
		btnsizer = wx.StdDialogButtonSizer()

		self.modBed = wx.Slider(
			self, wx.ID_ANY, 0, MINBED, MAXBED, size=(150, -1),
			style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
		self.modBed.Bind(wx.EVT_SCROLL_CHANGED, self.onSpinBed)
		self.modBed.Bind(wx.EVT_MOUSEWHEEL, self.onMouseBed)
		self.modBed.SetPageSize(1);

		b = wx.StaticBox(self, wx.ID_ANY, "Bed Temperature")
		sbox = wx.StaticBoxSizer(b, wx.VERTICAL)
		sbox.Add(self.modBed, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
		slidesizer.Add(sbox, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
		
		self.modHE0 = wx.Slider(
			self, wx.ID_ANY, 0, MINHE, MAXHE, size=(-1, 150),
			style = wx.SL_VERTICAL | wx.SL_AUTOTICKS | wx.SL_LABELS | wx.SL_INVERSE)
		self.modHE0.Bind(wx.EVT_SCROLL_CHANGED, self.onSpinHE0)
		self.modHE0.Bind(wx.EVT_MOUSEWHEEL, self.onMouseHE0)
		self.modHE0.SetPageSize(1);

		b = wx.StaticBox(self, wx.ID_ANY, "Hot End 0")
		sbox = wx.StaticBoxSizer(b, wx.VERTICAL)
		sbox.Add(self.modHE0, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
		slidesizer.Add(sbox, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
		
		self.modHE1 = wx.Slider(
			self, wx.ID_ANY, 0, MINHE, MAXHE, size=(-1, 150),
			style = wx.SL_VERTICAL | wx.SL_AUTOTICKS | wx.SL_LABELS | wx.SL_INVERSE)
		self.modHE1.Bind(wx.EVT_SCROLL_CHANGED, self.onSpinHE1)
		self.modHE1.Bind(wx.EVT_MOUSEWHEEL, self.onMouseHE1)
		self.modHE1.SetPageSize(1);

		b = wx.StaticBox(self, wx.ID_ANY, "Hot End 1")
		sbox = wx.StaticBoxSizer(b, wx.VERTICAL)
		sbox.Add(self.modHE1, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
		slidesizer.Add(sbox, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
		
		btn = wx.Button(self, wx.ID_OK)
		btn.SetHelpText("Save the changes")
		btn.SetDefault()
		btnsizer.AddButton(btn)

		btn = wx.Button(self, wx.ID_CANCEL)
		btn.SetHelpText("Exit without saving")
		btnsizer.AddButton(btn)
		btnsizer.Realize()

		sizer.Add(slidesizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
		sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

		self.SetSizer(sizer)
		sizer.Fit(self)
		
	def onSpinBed(self, evt):
		self.bed = evt.EventObject.GetValue()
	
	def onSpinHE0(self, evt):
		self.hotends[0] = evt.EventObject.GetValue()
	
	def onSpinHE1(self, evt):
		self.hotends[1] = evt.EventObject.GetValue()
	
	def onMouseBed(self, evt):
		l = self.modBed.GetValue()
		if evt.GetWheelRotation() < 0:
			l -= 1
		else:
			l += 1
		if l >= MINBED and l <= MAXBED:
			self.bed = l
			self.modBed.SetValue(l)
	
	def onMouseHE0(self, evt):
		l = self.modHE0.GetValue()
		if evt.GetWheelRotation() < 0:
			l -= 1
		else:
			l += 1
		if l >= MINHE and l <= MAXHE:
			self.hotends[0] = l
			self.modHE0.SetValue(l)
	
	def onMouseHE1(self, evt):
		l = self.modHE1.GetValue()
		if evt.GetWheelRotation() < 0:
			l -= 1
		else:
			l += 1
		if l >= MINHE and l <= MAXHE:
			self.hotends[1] = l
			self.modHE1.SetValue(l)
			
	def getResults(self):
		return (self.bed, self.hotends)

