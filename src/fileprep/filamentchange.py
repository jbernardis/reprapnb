import wx

EXISTING = "existing"
NEW = "new"

FMT = "%.5f"

class FilamentChangeDlg(wx.Dialog):
	def __init__(self, parent):
		self.parent = parent
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Add Filament Change")
		
		self.model = self.parent.model
		self.layerInfo = self.parent.layerInfo
		self.newGCode = []

		sizer = wx.BoxSizer(wx.VERTICAL)
		box = wx.BoxSizer(wx.HORIZONTAL)
		box.AddSpacer([10, 10])
	
		b = wx.StaticBox(self, wx.ID_ANY, "Parameters")
		sbox = wx.StaticBoxSizer(b, wx.VERTICAL)
		
		self.cbRetr = wx.CheckBox(self, wx.ID_ANY, "Add Retraction")
		self.Bind(wx.EVT_CHECKBOX, self.updateDlg, self.cbRetr)
		self.amtRetr = wx.TextCtrl(self, wx.ID_ANY, "2", size=(125, -1))
		self.amtRetr.Bind(wx.EVT_KILL_FOCUS, self.updateDlg)

		self.cbZLift = wx.CheckBox(self, wx.ID_ANY, "Add Z Lift")
		self.Bind(wx.EVT_CHECKBOX, self.updateDlg, self.cbZLift)
		self.amtZLift = wx.TextCtrl(self, wx.ID_ANY, "10", size=(125, -1))
		self.amtZLift.Bind(wx.EVT_KILL_FOCUS, self.updateDlg)
		
		scMessage = wx.StaticText(self, wx.ID_ANY, "LCD Message")
		self.txtLcd = wx.TextCtrl(self, wx.ID_ANY, "Change Filament", size=(125, -1))
		self.txtLcd.Bind(wx.EVT_KILL_FOCUS, self.updateDlg)

		self.cbHomeX = wx.CheckBox(self, wx.ID_ANY, "X Axis Home")
		self.Bind(wx.EVT_CHECKBOX, self.updateDlg, self.cbHomeX)
		self.cbHomeY = wx.CheckBox(self, wx.ID_ANY, "Y Axis Home")
		self.Bind(wx.EVT_CHECKBOX, self.updateDlg, self.cbHomeY)
		self.cbHomeZ = wx.CheckBox(self, wx.ID_ANY, "Z Axis Home")
		self.Bind(wx.EVT_CHECKBOX, self.updateDlg, self.cbHomeZ)
		self.cbResetE = wx.CheckBox(self, wx.ID_ANY, "E Axis Reset")
		self.Bind(wx.EVT_CHECKBOX, self.updateDlg, self.cbResetE)

		self.cbEExtra = wx.CheckBox(self, wx.ID_ANY, "Extra filament")
		self.amtEExtra = wx.TextCtrl(self, wx.ID_ANY, "0.5", size=(125, -1))
		self.amtEExtra.Bind(wx.EVT_KILL_FOCUS, self.updateDlg)
		self.Bind(wx.EVT_CHECKBOX, self.updateDlg, self.cbEExtra)
		
		scText = wx.StaticText(self, wx.ID_ANY, "Lines of Context")
		self.scContext = wx.SpinCtrl(self, wx.ID_ANY, "")
		self.scContext.SetRange(1, 10)
		self.scContext.SetValue(5)
		self.Bind(wx.EVT_SPINCTRL, self.updateDlg, self.scContext)
		
		self.cbFirstLastGC = wx.CheckBox(self, wx.ID_ANY, "Use First GCode line")
		self.cbFirstLastGC.SetValue(True)
		self.Bind(wx.EVT_CHECKBOX, self.updateDlg, self.cbFirstLastGC)

		sbox.AddMany([self.cbRetr, (10, 10), self.amtRetr, (20, 20),
					self.cbZLift, (10, 10), self.amtZLift, (20, 20),
					scMessage, self.txtLcd, (20, 20),
					self.cbHomeX, (10, 10), self.cbHomeY, (10, 10), self.cbHomeZ, (20, 20),
					self.cbEExtra, (10, 10), self.amtEExtra, (20, 20),
					self.cbResetE, (20, 20), 
					scText, self.scContext, self.cbFirstLastGC])
		
		box.Add(sbox, 0, wx.GROW|wx.ALIGN_TOP)
		
		self.text = wx.TextCtrl(self, -1, "", size=(300, 100), style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH2)
		box.Add(self.text, 0, wx.GROW|wx.ALIGN_LEFT, 5)
		box.AddSpacer([10, 10])

		sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

		btnsizer = wx.StdDialogButtonSizer()

		btn = wx.Button(self, wx.ID_OK)
		btn.SetHelpText("Insert the new code")
		btn.SetDefault()
		btnsizer.AddButton(btn)

		btn = wx.Button(self, wx.ID_CANCEL)
		btn.SetHelpText("Exit without changing code")
		btnsizer.AddButton(btn)
		btnsizer.Realize()

		sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

		self.SetSizer(sizer)
		sizer.Fit(self)
		
		self.updateDlg()
		
	def getValues(self):
		return self.newGCode, self.insertPoint
	
	def updateDlg(self, *arg):
		if self.cbFirstLastGC.IsChecked():
			hl = self.parent.drawGCFirst
		else:	
			hl = self.parent.drawGCLast	
		self.insertPoint = hl
		e = self.model.findEValue(hl-1)
		z = self.layerInfo[0]

		self.newGCode = []
		
		try:
			contextLines = int(self.scContext.GetValue())
		except:
			contextLines = 1
		
		try:
			retr = float(self.amtRetr.GetValue())
		except:
			retr = 2.0

		try:
			eextra = float(self.amtEExtra.GetValue())
		except:
			eextra = 0.5

		try:
			lift = float(self.amtZLift.GetValue())
		except:
			lift = 10.0

		restoreZ = False
		if self.cbRetr.GetValue():
			self.newGCode.append("G1 E" + FMT % (e - retr))
		if self.cbZLift.GetValue():
			self.newGCode.append("G1 Z" + FMT % (z + lift))
			restoreZ = True
			
		self.newGCode.append("M117 %s" % self.txtLcd.GetValue())
		self.newGCode.append("@pause")
		self.newGCode.append("M117 Proceeding...")
			
		fX = self.cbHomeX.GetValue()
		fY = self.cbHomeY.GetValue()
		fZ = self.cbHomeZ.GetValue()
		if fX or fY or fZ:
			axes = ""
			if fX:
				axes += " X0"
			if fY:
				axes += " Y0"
			if fZ:
				axes += " Z0"
			self.newGCode.append("G28%s" % axes)
			if fZ:
				restoreZ = True
				self.newGCode.append("G1 Z" + FMT % (z + 2))
				
		if self.cbEExtra.IsChecked():
			self.newGCode.append("G92 E0")
			self.newGCode.append("G1 E" + FMT % eextra)
			if not self.cbResetE.IsChecked():
				self.newGCode.append("G92 E" + FMT % e)

		if self.cbResetE.GetValue():
			if self.cbRetr.GetValue():
				self.newGCode.append("G92 E" + FMT % (e - retr))
			else:
				self.newGCode.append("G92 E" + FMT % e)
			
		if self.cbRetr.GetValue():
			self.newGCode.append("G1 E" + FMT % e)
			
		if restoreZ:
			self.newGCode.append("G1 Z" + FMT % z)
	
		self.text.Clear()
		bg = self.text.GetBackgroundColour()
		
		for dl in range(contextLines):
			l = hl - contextLines + dl
			if l < -1:
				pass
			elif l == -1:
				self.text.AppendText("<beginning of file>\n")
			else:
				self.text.AppendText(self.model.lines[l].orig+"\n")
				
		v = self.text.GetInsertionPoint()
		self.text.SetStyle(0, v, wx.TextAttr("red", bg))
			
		for g in self.newGCode:
			self.text.AppendText(g+"\n")
			
		v = self.text.GetInsertionPoint()

		nlines = len(self.model.lines)		
		for dl in range(contextLines):
			if hl+dl == nlines:
				self.text.appendText("<end of file>\n")
			elif hl+dl > nlines:
				pass
			else:
				self.text.AppendText(self.model.lines[hl+dl].orig+"\n")
			
		self.text.SetStyle(v, self.text.GetInsertionPoint(), wx.TextAttr("red", bg))
		
