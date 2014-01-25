import wx

class SaveLayerDlg(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Save Layer(s)")
		
		self.app = parent
		self.model = self.app.model
		self.layerText = self.getLayers()

		sizer = wx.BoxSizer(wx.VERTICAL)
		
		box = wx.BoxSizer(wx.HORIZONTAL)
		box.AddSpacer([10, 10])
		
		self.lbStart = wx.ListBox(self, wx.ID_ANY, choices=self.layerText, style=wx.LB_SINGLE)
		self.lbStart.SetSelection(0)
		b = wx.StaticBox(self, wx.ID_ANY, "Start Layer")
		sbox = wx.StaticBoxSizer(b, wx.VERTICAL)
		sbox.Add(self.lbStart)
		box.Add(sbox)
		
		self.lbEnd = wx.ListBox(self, wx.ID_ANY, choices=self.layerText, style=wx.LB_SINGLE)
		self.lbEnd.SetSelection(len(self.layerText)-1)
		b = wx.StaticBox(self, wx.ID_ANY, "End Layer")
		sbox = wx.StaticBoxSizer(b, wx.VERTICAL)
		sbox.Add(self.lbEnd)
		box.Add(sbox)
		
		b = wx.StaticBox(self, wx.ID_ANY, "Prefix")
		sbox = wx.StaticBoxSizer(b, wx.VERTICAL)
		
		self.cbPreE = wx.CheckBox(self, wx.ID_ANY, "E Axis Reset")
		self.cbPreE.SetValue(True)
		self.cbPreX = wx.CheckBox(self, wx.ID_ANY, "X Axis Home")
		self.cbPreY = wx.CheckBox(self, wx.ID_ANY, "Y Axis Home")
		self.cbPreZ = wx.CheckBox(self, wx.ID_ANY, "Z Axis Home")
		sbox.AddMany([self.cbPreE, (20, 20), self.cbPreX, (10, 10), self.cbPreY, (10, 10), self.cbPreZ])
		
		box.Add(sbox, 0, wx.GROW|wx.ALIGN_TOP)
		
		b = wx.StaticBox(self, wx.ID_ANY, "Suffix")
		sbox = wx.StaticBoxSizer(b, wx.VERTICAL)
		
		self.cbZLift = wx.CheckBox(self, wx.ID_ANY, "Add Z Lift (10mm)")
		self.cbZLift.SetValue(True)
		self.cbERetr = wx.CheckBox(self, wx.ID_ANY, "Add E retraction (2mm)")
		sbox.AddMany([self.cbZLift, (20, 20), self.cbERetr])
		
		box.Add(sbox, 0, wx.GROW|wx.ALIGN_TOP)
		box.AddSpacer([10, 10])

		sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

		line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
		sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

		btnsizer = wx.StdDialogButtonSizer()

		btn = wx.Button(self, wx.ID_OK)
		btn.SetHelpText("Save the chosen layer range")
		btn.SetDefault()
		btnsizer.AddButton(btn)

		btn = wx.Button(self, wx.ID_CANCEL)
		btn.SetHelpText("Exit without saving")
		btnsizer.AddButton(btn)
		btnsizer.Realize()

		sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

		self.SetSizer(sizer)
		sizer.Fit(self)
		
	def getValues(self):
		data = self.lbStart.GetSelection()
		try:
			slayer = int(data)
		except:
			slayer = 0
		
		data = self.lbEnd.GetSelection()
		try:
			elayer = int(data)
		except:
			elayer = 0
		
		return [slayer, elayer,
			self.cbPreE.GetValue(), self.cbPreX.GetValue(), self.cbPreY.GetValue(), self.cbPreZ.GetValue(),
			self.cbZLift.GetValue(), self.cbERetr.GetValue()]
		
	def getLayers(self):
		l = []
		lx = 0
		
		lyr = self.model.firstLayer()
		while lyr is not None:
			lx += 1
			l.append("%4d: %9.3f" % (lx, lyr.getLayerHeight()))
			lyr = self.model.nextLayer()
			
		return l

