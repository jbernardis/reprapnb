import wx

class ModifySpeedDlg(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Modify Speeds")
		
		self.app = parent
		self.model = self.app.model
		
		self.extSpeed = 100
		self.moveSpeed = 100
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		slidesizer = wx.GridSizer(rows=1, cols=2)
		btnsizer = wx.StdDialogButtonSizer()

		self.modExt = wx.Slider(
			self, wx.ID_ANY, 100, 25, 200, size=(150, -1),
			style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
		self.modExt.Bind(wx.EVT_SCROLL_CHANGED, self.onSpinExt)
		self.modExt.Bind(wx.EVT_MOUSEWHEEL, self.onMouseExt)
		self.modExt.SetPageSize(1);

		b = wx.StaticBox(self, wx.ID_ANY, "Extrusion Speed Percent")
		sbox = wx.StaticBoxSizer(b, wx.VERTICAL)
		sbox.Add(self.modExt, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
		slidesizer.Add(sbox, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
		
		self.modMove = wx.Slider(
			self, wx.ID_ANY, 100, 25, 200, size=(150, -1),
			style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
		self.modMove.Bind(wx.EVT_SCROLL_CHANGED, self.onSpinMove)
		self.modMove.Bind(wx.EVT_MOUSEWHEEL, self.onMouseMove)
		self.modMove.SetPageSize(1);

		b = wx.StaticBox(self, wx.ID_ANY, "Movement Speed Percent")
		sbox = wx.StaticBoxSizer(b, wx.VERTICAL)
		sbox.Add(self.modMove, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)
		slidesizer.Add(sbox, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 5)

		self.btnOK = wx.Button(self, wx.ID_OK)
		self.btnOK.SetHelpText("Save the changes")
		self.btnOK.SetDefault()
		self.btnOK.Enable(False)
		btnsizer.AddButton(self.btnOK)

		self.btnCancel = wx.Button(self, wx.ID_CANCEL)
		self.btnCancel.SetHelpText("Exit without saving")
		self.btnCancel.SetLabel("Close")
		btnsizer.AddButton(self.btnCancel)

		btnsizer.Realize()

		sizer.Add(slidesizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
		sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

		self.SetSizer(sizer)
		sizer.Fit(self)

	def checkStatus(self):
		if self.extSpeed == 100 and self.moveSpeed == 100:
			self.btnOK.Enable(False)
			self.btnCancel.SetLabel("Close")
		else:
			self.btnOK.Enable(True)
			self.btnCancel.SetLabel("Cancel")
		
	def onSpinExt(self, evt):
		self.extSpeed = evt.EventObject.GetValue()
		self.checkStatus()
	
	def onSpinMove(self, evt):
		self.moveSpeed = evt.EventObject.GetValue()
		self.checkStatus()
	
	def onMouseExt(self, evt):
		l = self.modExt.GetValue()
		if evt.GetWheelRotation() < 0:
			l -= 1
		else:
			l += 1
		if l >= 25 and l <= 200:
			self.extSpeed = l
			self.modExt.SetValue(self.extSpeed)
			self.checkStatus()
	
	def onMouseMove(self, evt):
		l = self.modMove.GetValue()
		if evt.GetWheelRotation() < 0:
			l -= 1
		else:
			l += 1
		if l >= 25 and l <= 200:
			self.moveSpeed = l
			self.modMove.SetValue(self.moveSpeed)
			self.checkStatus()
	
	def getResult(self):
		return (self.extSpeed, self.moveSpeed)

