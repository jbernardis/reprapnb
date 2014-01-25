import wx

class ShiftModelDlg(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Shift Model")
		
		self.app = parent
		self.model = self.app.model
		
		self.shiftx = 0
		self.shifty = 0
		
		self.minx = -self.model.xmin
		self.maxx = self.app.buildarea[0] - self.model.xmax
		self.miny = -self.model.ymin
		self.maxy = self.app.buildarea[1] - self.model.ymax
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		slidesizer = wx.GridSizer(rows=1, cols=2)
		btnsizer = wx.StdDialogButtonSizer()

		self.slideX = wx.Slider(
			self, wx.ID_ANY, 0, self.minx, self.maxx, size=(150, -1),
			style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
		self.slideX.Bind(wx.EVT_SCROLL_CHANGED, self.onSpinX)
		self.slideX.Bind(wx.EVT_MOUSEWHEEL, self.onMouseX)
		self.slideX.SetPageSize(1);

		b = wx.StaticBox(self, wx.ID_ANY, "X Axis")
		sbox = wx.StaticBoxSizer(b, wx.VERTICAL)
		sbox.Add(self.slideX, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
		slidesizer.Add(sbox, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
		
		self.slideY = wx.Slider(
			self, wx.ID_ANY, 0, self.miny, self.maxy, size=(-1, 150),
			style = wx.SL_VERTICAL | wx.SL_AUTOTICKS | wx.SL_LABELS | wx.SL_INVERSE)
		self.slideY.Bind(wx.EVT_SCROLL_CHANGED, self.onSpinY)
		self.slideY.Bind(wx.EVT_MOUSEWHEEL, self.onMouseY)
		self.slideY.SetPageSize(1);

		b = wx.StaticBox(self, wx.ID_ANY, "Y Axis")
		sbox = wx.StaticBoxSizer(b, wx.VERTICAL)
		sbox.Add(self.slideY, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5)
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
		
	def onSpinX(self, evt):
		self.shiftx = evt.EventObject.GetValue()
		self.app.setShift(self.shiftx, self.shifty)
	
	def onSpinY(self, evt):
		self.shifty = evt.EventObject.GetValue()
		self.app.setShift(self.shiftx, self.shifty)
	
	def onMouseX(self, evt):
		l = self.slideX.GetValue()
		if evt.GetWheelRotation() < 0:
			l -= 1
		else:
			l += 1
		if l >= self.minx and l <= self.maxx:
			self.shiftx = l
			self.slideX.SetValue(l)
			self.app.setShift(self.shiftx, self.shifty)	
	
	def onMouseY(self, evt):
		l = self.slideY.GetValue()
		if evt.GetWheelRotation() < 0:
			l -= 1
		else:
			l += 1
		if l >= self.miny and l <= self.maxy:
			self.shifty = l
			self.slideY.SetValue(l)
			self.app.setShift(self.shiftx, self.shifty)

