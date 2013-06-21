'''
Created on Jan 27, 2013

@author: Jeff
'''

import wx

EXISTING = "existing"
NEW = "new"

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

		self.cbHomeX = wx.CheckBox(self, wx.ID_ANY, "X Axis Home")
		self.Bind(wx.EVT_CHECKBOX, self.updateDlg, self.cbHomeX)
		self.cbHomeY = wx.CheckBox(self, wx.ID_ANY, "Y Axis Home")
		self.Bind(wx.EVT_CHECKBOX, self.updateDlg, self.cbHomeY)
		self.cbHomeZ = wx.CheckBox(self, wx.ID_ANY, "Z Axis Home")
		self.Bind(wx.EVT_CHECKBOX, self.updateDlg, self.cbHomeZ)
		self.cbResetE = wx.CheckBox(self, wx.ID_ANY, "E Axis Reset")
		self.Bind(wx.EVT_CHECKBOX, self.updateDlg, self.cbResetE)
		sbox.AddMany([self.cbRetr, (10, 10), self.amtRetr, (20, 20),
					self.cbZLift, (10, 10), self.amtZLift, (20, 20),
					self.cbHomeX, (10, 10), self.cbHomeY, (10, 10), self.cbHomeZ, (20, 20),
					self.cbResetE])
		
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
		return self.newGCode
	
	def updateDlg(self, *arg):	
		hl = self.parent.hilite	
		e = self.model.findEValue(hl-1)
		z = self.layerInfo[0]

		self.newGCode = []
		
		try:
			retr = float(self.amtRetr.GetValue())
		except:
			retr = 2.0

		try:
			lift = float(self.amtZLift.GetValue())
		except:
			lift = 10.0

		restoreZ = False
		if self.cbRetr.GetValue():
			self.newGCode.append("G1 E%.3f" % (e - retr))
		if self.cbZLift.GetValue():
			self.newGCode.append("G1 Z%.3f" % (z + lift))
			restoreZ = True
			
		self.newGCode.append("M117 Change Filament")
		self.newGCode.append("M1")
			
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
				self.newGCode.append("G1 Z%.3f" % (z + 2))

		if self.cbResetE.GetValue():
			if self.cbRetr.GetValue():
				self.newGCode.append("G92 E%.3f" % (e - retr))
			else:
				self.newGCode.append("G92 E%.3f" % e)
			
		if self.cbRetr.GetValue():
			self.newGCode.append("G1 E%.3f" % e)
			
		if restoreZ:
			self.newGCode.append("G1 Z%.3f" % z)
	
		self.text.Clear()
		bg = self.text.GetBackgroundColour()
		
		if hl != 0:
			self.text.AppendText(self.model.lines[hl-1].orig+"\n")
		else:
			self.text.AppendText("<beginning of file>\n")
		v = self.text.GetInsertionPoint()
		self.text.SetStyle(0, v, wx.TextAttr("red", bg))
			
		for g in self.newGCode:
			self.text.AppendText(g+"\n")
			
		v = self.text.GetInsertionPoint()
		self.text.AppendText(self.model.lines[hl].orig+"\n")
		self.text.SetStyle(v, self.text.GetInsertionPoint(), wx.TextAttr("red", bg))
		
