import wx

ovKeyOrder = ['filamentdiam', 'extrusionmult', 'layerheight', 'extrusionwidth', 'infilldensity',
			'layer1bedtemperature', 'bedtemperature', 'layer1temperature', 'temperature',
			'printspeed', 'travelspeed', 'print1speed',
			'support', 'skirt', 'skirtheight', 'adhesion']

ovUserKeyMap = {'filamentdiam': "Filament Diameter",
			'extrusionmult': "Extrusion Multiplier",
			'layerheight': "Layer Height",
			'extrusionwidth' : "Extrusion Width",
			'infilldensity' : "Infill Density",
			'layer1bedtemperature' : "Layer 1 Bed Temperature",
			'bedtemperature' : "Bed Temperature",
			'layer1temperature' : "Layer 1 Extrusion Temperature",
			'temperature' : "Extrusion Temperature",
			'printspeed' : "Normal Print Speed",
			'travelspeed' : "Travel Speed",
			'print1speed' : "Print Speed for Layer 1",
			'support' : "Support",
			'skirt' : "Skirt",
			'skirtheight' : "Skirt Height",
			'adhesion' : "Adhesion Method"}


class Override(wx.Dialog):
	def __init__(self, parent, values, helptext):
		self.parent = parent
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Slicer Overrides", size=(800, 804))
		self.SetBackgroundColour("white")
		
		dsizer = wx.BoxSizer(wx.VERTICAL)

		bgrid = wx.GridBagSizer()
		bgrid.AddSpacer((10, 10), pos=(0,0))
		bgrid.AddSpacer((10, 10), pos=(0,2))
		bgrid.AddSpacer((10, 10), pos=(0,4))
		
		self.controls = {}

		ln = 1
		value = "2.95"
		key = "filamentdiam"
		self.cbOvFilDia = wx.CheckBox(self, wx.ID_ANY, "Filament Diameter")
		self.Bind(wx.EVT_CHECKBOX, self.checkFilDia, self.cbOvFilDia)
		bgrid.Add(self.cbOvFilDia, pos=(ln, 1))
		self.teOvFilDia = wx.TextCtrl(self, wx.ID_ANY, value, style=wx.TE_RIGHT)
		self.teOvFilDia.Enable(False)
		self.controls[key] = self.teOvFilDia
		if key in values.keys():
			self.teOvFilDia.SetValue(values[key])
			self.teOvFilDia.Enable(True)
			self.cbOvFilDia.SetValue(True)
			
		bgrid.Add(self.teOvFilDia, pos=(ln,3))
		
		h = self.teOvFilDia.GetSize()[1]
		
		ln += 1
		value = "0.95"
		key = "extrusionmult"
		self.cbOvExtMlt = wx.CheckBox(self, wx.ID_ANY, "Extrusion Multiplier")
		self.Bind(wx.EVT_CHECKBOX, self.checkExtMlt, self.cbOvExtMlt)
		bgrid.Add(self.cbOvExtMlt, pos=(ln, 1))
		self.teOvExtMlt = wx.TextCtrl(self, wx.ID_ANY, value, style=wx.TE_RIGHT)
		self.teOvExtMlt.Enable(False)
		self.controls[key] = self.teOvExtMlt
		if key in values.keys():
			self.teOvExtMlt.SetValue(values[key])
			self.teOvExtMlt.Enable(True)
			self.cbOvExtMlt.SetValue(True)
			
		bgrid.Add(self.teOvExtMlt, pos=(ln,3))
		
		ln += 1
		value = "0.2"
		key = "layerheight"
		self.cbOvLH = wx.CheckBox(self, wx.ID_ANY, "Layer Height")
		self.Bind(wx.EVT_CHECKBOX, self.checkLH, self.cbOvLH)
		bgrid.Add(self.cbOvLH, pos=(ln, 1))
		self.teOvLH = wx.TextCtrl(self, wx.ID_ANY, value, style=wx.TE_RIGHT)
		self.teOvLH.Enable(False)
		self.controls[key] = self.teOvLH
		if key in values.keys():
			self.teOvLH.SetValue(values[key])
			self.teOvLH.Enable(True)
			self.cbOvLH.SetValue(True)
			
		bgrid.Add(self.teOvLH, pos=(ln,3))
		
		ln += 1
		value = "2.8"
		key = "extrusionwidth"
		self.cbOvExWid = wx.CheckBox(self, wx.ID_ANY, "Extrusion Width")
		self.Bind(wx.EVT_CHECKBOX, self.checkEW, self.cbOvExWid)
		bgrid.Add(self.cbOvExWid, pos=(ln, 1))
		self.teOvExWid = wx.TextCtrl(self, wx.ID_ANY, value, style=wx.TE_RIGHT)
		self.teOvExWid.Enable(False)
		self.controls[key] = self.teOvExWid
		if key in values.keys():
			self.teOvExWid.SetValue(values[key])
			self.teOvExWid.Enable(True)
			self.cbOvExWid.SetValue(True)
			
		bgrid.Add(self.teOvExWid, pos=(ln,3))
		
		ln += 1
		value = "0.4"
		key = "infilldensity"
		self.cbOvInfill = wx.CheckBox(self, wx.ID_ANY, "Infill Density")
		self.Bind(wx.EVT_CHECKBOX, self.checkInfill, self.cbOvInfill)
		bgrid.Add(self.cbOvInfill, pos=(ln, 1))
		self.teOvInfill = wx.TextCtrl(self, wx.ID_ANY, value, style=wx.TE_RIGHT)
		self.teOvInfill.Enable(False)
		self.controls[key] = self.teOvInfill
		if key in values.keys():
			self.teOvInfill.SetValue(values[key])
			self.teOvInfill.Enable(True)
			self.cbOvInfill.SetValue(True)

		bgrid.Add(self.teOvInfill, pos=(ln,3))
		
		ln += 1
		value = "60"
		key = "layer1bedtemperature"
		self.cbOvBedTmp1 = wx.CheckBox(self, wx.ID_ANY, "Bed Temperature First Layer")
		self.Bind(wx.EVT_CHECKBOX, self.checkBedTmp1, self.cbOvBedTmp1)
		bgrid.Add(self.cbOvBedTmp1, pos=(ln, 1))
		self.teOvBedTmp1 = wx.TextCtrl(self, wx.ID_ANY, value, style=wx.TE_RIGHT)
		self.teOvBedTmp1.Enable(False)
		self.controls[key] = self.teOvBedTmp1
		if key in values.keys():
			self.teOvBedTmp1.SetValue(values[key])
			self.teOvBedTmp1.Enable(True)
			self.cbOvBedTmp1.SetValue(True)

		bgrid.Add(self.teOvBedTmp1, pos=(ln,3))
		
		ln += 1
		value = "55"
		key = "bedtemperature"
		self.cbOvBedTmp = wx.CheckBox(self, wx.ID_ANY, "Bed Temperature")
		self.Bind(wx.EVT_CHECKBOX, self.checkBedTmp, self.cbOvBedTmp)
		bgrid.Add(self.cbOvBedTmp, pos=(ln, 1))
		self.teOvBedTmp = wx.TextCtrl(self, wx.ID_ANY, value, style=wx.TE_RIGHT)
		self.teOvBedTmp.Enable(False)
		self.controls[key] = self.teOvBedTmp
		if key in values.keys():
			self.teOvBedTmp.SetValue(values[key])
			self.teOvBedTmp.Enable(True)
			self.cbOvBedTmp.SetValue(True)

		bgrid.Add(self.teOvBedTmp, pos=(ln,3))
		
		ln += 1
		value = "185"
		key = "layer1temperature"
		self.cbOvTmp1 = wx.CheckBox(self, wx.ID_ANY, "Temperature(s) First Layer")
		self.Bind(wx.EVT_CHECKBOX, self.checkTmp1, self.cbOvTmp1)
		bgrid.Add(self.cbOvTmp1, pos=(ln, 1))
		self.teOvTmp1 = wx.TextCtrl(self, wx.ID_ANY, value, style=wx.TE_RIGHT)
		self.teOvTmp1.Enable(False)
		self.controls[key] = self.teOvTmp1
		if key in values.keys():
			self.teOvTmp1.SetValue(values[key])
			self.teOvTmp1.Enable(True)
			self.cbOvTmp1.SetValue(True)

		bgrid.Add(self.teOvTmp1, pos=(ln,3))
		
		ln += 1
		value = "185"
		key = "temperature"
		self.cbOvTmp = wx.CheckBox(self, wx.ID_ANY, "Temperature(s)")
		self.Bind(wx.EVT_CHECKBOX, self.checkTmp, self.cbOvTmp)
		bgrid.Add(self.cbOvTmp, pos=(ln, 1))
		self.teOvTmp = wx.TextCtrl(self, wx.ID_ANY, value, style=wx.TE_RIGHT)
		self.teOvTmp.Enable(False)
		self.controls[key] = self.teOvTmp
		if key in values.keys():
			self.teOvTmp.SetValue(values[key])
			self.teOvTmp.Enable(True)
			self.cbOvTmp.SetValue(True)

		bgrid.Add(self.teOvTmp, pos=(ln,3))
		
		ln += 1
		value = "60"
		key = "printspeed"
		self.cbOvPrSpd = wx.CheckBox(self, wx.ID_ANY, "Print Speed")
		self.Bind(wx.EVT_CHECKBOX, self.checkPrSpd, self.cbOvPrSpd)
		bgrid.Add(self.cbOvPrSpd, pos=(ln, 1))
		self.teOvPrSpd = wx.TextCtrl(self, wx.ID_ANY, value, style=wx.TE_RIGHT)
		self.teOvPrSpd.Enable(False)
		self.controls[key] = self.teOvPrSpd
		if key in values.keys():
			self.teOvPrSpd.SetValue(values[key])
			self.teOvPrSpd.Enable(True)
			self.cbOvPrSpd.SetValue(True)

		bgrid.Add(self.teOvPrSpd, pos=(ln,3))
		
		ln += 1
		value = "120"
		key = "travelspeed"
		self.cbOvTrSpd = wx.CheckBox(self, wx.ID_ANY, "Travel Speed")
		self.Bind(wx.EVT_CHECKBOX, self.checkTrSpd, self.cbOvTrSpd)
		bgrid.Add(self.cbOvTrSpd, pos=(ln, 1))
		self.teOvTrSpd = wx.TextCtrl(self, wx.ID_ANY, value, style=wx.TE_RIGHT)
		self.teOvTrSpd.Enable(False)
		self.controls[key] = self.teOvTrSpd
		if key in values.keys():
			self.teOvTrSpd.SetValue(values[key])
			self.teOvTrSpd.Enable(True)
			self.cbOvTrSpd.SetValue(True)

		bgrid.Add(self.teOvTrSpd, pos=(ln,3))
		
		ln += 1
		value = "30"
		key = "print1speed"
		self.cbOvPr1Spd = wx.CheckBox(self, wx.ID_ANY, "First Layer Speed")
		self.Bind(wx.EVT_CHECKBOX, self.checkPr1Spd, self.cbOvPr1Spd)
		bgrid.Add(self.cbOvPr1Spd, pos=(ln, 1))
		self.teOvPr1Spd = wx.TextCtrl(self, wx.ID_ANY, value, style=wx.TE_RIGHT)
		self.teOvPr1Spd.Enable(False)
		self.controls[key] = self.teOvPr1Spd
		if key in values.keys():
			self.teOvPr1Spd.SetValue(values[key])
			self.teOvPr1Spd.Enable(True)
			self.cbOvPr1Spd.SetValue(True)

		bgrid.Add(self.teOvPr1Spd, pos=(ln,3))
		
		ln += 1
		value = "False"
		key = "support"
		self.cbOvSpt = wx.CheckBox(self, wx.ID_ANY, "Support")
		self.Bind(wx.EVT_CHECKBOX, self.checkSpt, self.cbOvSpt)
		bgrid.Add(self.cbOvSpt, pos=(ln, 1))
		self.teOvSpt = wx.CheckBox(self, wx.ID_ANY, "Enabled", size=(-1, h))
		self.teOvSpt.SetValue(False)
		self.teOvSpt.Enable(False)
		self.controls[key] = self.teOvSpt
		if key in values.keys():
			self.teOvSpt.SetValue(values[key] == "True")
			self.teOvSpt.Enable(True)
			self.cbOvSpt.SetValue(True)
			
		bgrid.Add(self.teOvSpt, pos=(ln,3))
		
		ln += 1
		value = "False"
		key = "skirt"
		self.cbOvSkt = wx.CheckBox(self, wx.ID_ANY, "Skirt")
		self.Bind(wx.EVT_CHECKBOX, self.checkSkt, self.cbOvSkt)
		bgrid.Add(self.cbOvSkt, pos=(ln, 1))
		self.teOvSkt = wx.CheckBox(self, wx.ID_ANY, "Enabled", size=(-1, h))
		self.teOvSkt.SetValue(False)
		self.teOvSkt.Enable(False)
		self.controls[key] = self.teOvSkt
		if key in values.keys():
			self.teOvSkt.SetValue(values[key] == "True")
			self.teOvSkt.Enable(True)
			self.cbOvSkt.SetValue(True)
			
		bgrid.Add(self.teOvSkt, pos=(ln,3))
		
		ln += 1
		value = "1"
		key = "skirtheight"
		self.cbOvSktHt = wx.CheckBox(self, wx.ID_ANY, "Skirt")
		self.Bind(wx.EVT_CHECKBOX, self.checkSktHt, self.cbOvSktHt)
		bgrid.Add(self.cbOvSktHt, pos=(ln, 1))
		self.teOvSktHt= wx.TextCtrl(self, wx.ID_ANY, value, style=wx.TE_RIGHT)
		self.teOvSktHt.Enable(False)
		self.controls[key] = self.teOvSktHt
		if key in values.keys():
			self.teOvSktHt.SetValue(values[key])
			self.teOvSktHt.Enable(True)
			self.cbOvSktHt.SetValue(True)
			
		bgrid.Add(self.teOvSktHt, pos=(ln,3))

		ln += 1
		value = "None"
		key = "adhesion"
		self.cbOvAdh = wx.CheckBox(self, wx.ID_ANY, "Adhesion")
		self.Bind(wx.EVT_CHECKBOX, self.checkAdh, self.cbOvAdh)
		bgrid.Add(self.cbOvAdh, pos=(ln, 1))
		self.teOvAdh = wx.ComboBox(self, wx.ID_ANY, "", (-1, -1),  (120, -1), ["None", "Raft", "Brim"], wx.CB_DROPDOWN | wx.CB_READONLY)
		self.teOvAdh.SetSelection(0)
		self.teOvAdh.Enable(False)
		self.controls[key] = self.teOvAdh
		if key in values.keys():
			if values[key] == "Raft":
				self.teOvAdh.SetSelection(1)
			elif values[key] == "Brim":
				self.teOvAdh.SetSelection(2)
			else:
				self.teOvAdh.SetSelection(0)
			self.teOvAdh.Enable(True)
			self.cbOvAdh.SetValue(True)

		bgrid.Add(self.teOvAdh, pos=(ln,3))

		ln += 1
		dsizer.Add(bgrid)
		
		btnsizer = wx.StdDialogButtonSizer()
		
		btn = wx.Button(self, wx.ID_OK)
		btn.SetHelpText("Save the changes")
		btn.SetDefault()
		btnsizer.AddButton(btn)

		btn = wx.Button(self, wx.ID_CANCEL)
		btn.SetHelpText("Exit without saving")
		btnsizer.AddButton(btn)
		btnsizer.Realize()
		
		dsizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

		self.setHelpText(helptext)

		self.SetSizer(dsizer)  
		dsizer.Fit(self)
		
	def setHelpText(self, ht):
		if ht is None:
			return
		
		for ck in self.controls.keys():
			if ck in ht.keys():
				self.controls[ck].SetToolTipString(ht[ck])
			else:
				self.controls[ck].SetToolTipString("")
		
	def checkFilDia(self, evt):
		if self.cbOvFilDia.IsChecked():
			self.teOvFilDia.Enable(True)
		else:
			self.teOvFilDia.Enable(False)
		
	def checkExtMlt(self, evt):
		if self.cbOvExtMlt.IsChecked():
			self.teOvExtMlt.Enable(True)
		else:
			self.teOvExtMlt.Enable(False)
		
	def checkLH(self, evt):
		if self.cbOvLH.IsChecked():
			self.teOvLH.Enable(True)
		else:
			self.teOvLH.Enable(False)
		
	def checkEW(self, evt):
		if self.cbOvExWid.IsChecked():
			self.teOvExWid.Enable(True)
		else:
			self.teOvExWid.Enable(False)
		
	def checkInfill(self, evt):
		if self.cbOvInfill.IsChecked():
			self.teOvInfill.Enable(True)
		else:
			self.teOvInfill.Enable(False)
		
	def checkBedTmp1(self, evt):
		if self.cbOvBedTmp1.IsChecked():
			self.teOvBedTmp1.Enable(True)
		else:
			self.teOvBedTmp1.Enable(False)
		
	def checkBedTmp(self, evt):
		if self.cbOvBedTmp.IsChecked():
			self.teOvBedTmp.Enable(True)
		else:
			self.teOvBedTmp.Enable(False)
		
	def checkTmp1(self, evt):
		if self.cbOvTmp1.IsChecked():
			self.teOvTmp1.Enable(True)
		else:
			self.teOvTmp1.Enable(False)
		
	def checkTmp(self, evt):
		if self.cbOvTmp.IsChecked():
			self.teOvTmp.Enable(True)
		else:
			self.teOvTmp.Enable(False)
		
	def checkPrSpd(self, evt):
		if self.cbOvPrSpd.IsChecked():
			self.teOvPrSpd.Enable(True)
		else:
			self.teOvPrSpd.Enable(False)
		
	def checkTrSpd(self, evt):
		if self.cbOvTrSpd.IsChecked():
			self.teOvTrSpd.Enable(True)
		else:
			self.teOvTrSpd.Enable(False)
		
	def checkPr1Spd(self, evt):
		if self.cbOvPr1Spd.IsChecked():
			self.teOvPr1Spd.Enable(True)
		else:
			self.teOvPr1Spd.Enable(False)
		
	def checkSkt(self, evt):
		if self.cbOvSkt.IsChecked():
			self.teOvSkt.Enable(True)
		else:
			self.teOvSkt.Enable(False)
		
	def checkSktHt(self, evt):
		if self.cbOvSktHt.IsChecked():
			self.teOvSktHt.Enable(True)
		else:
			self.teOvSktHt.Enable(False)
		
	def checkSpt(self, evt):
		if self.cbOvSpt.IsChecked():
			self.teOvSpt.Enable(True)
		else:
			self.teOvSpt.Enable(False)
			
	def checkAdh(self, evt):
		if self.cbOvAdh.IsChecked():
			self.teOvAdh.Enable(True)
		else:
			self.teOvAdh.Enable(False)

	def getOverrides(self):
		r = {}     
		if self.cbOvFilDia.IsChecked():
			r['filamentdiam'] = self.teOvFilDia.GetValue()
			
		if self.cbOvExtMlt.IsChecked():
			r['extrusionmult'] = self.teOvExtMlt.GetValue()
			
		if self.cbOvLH.IsChecked():
			r['layerheight'] = self.teOvLH.GetValue()
			
		if self.cbOvExWid.IsChecked():
			r['extrusionwidth'] = self.teOvExWid.GetValue()
			
		if self.cbOvInfill.IsChecked():
			r['infilldensity'] = self.teOvInfill.GetValue()
			
		if self.cbOvBedTmp1.IsChecked():
			r['layer1bedtemperature'] = self.teOvBedTmp1.GetValue()
			
		if self.cbOvBedTmp.IsChecked():
			r['bedtemperature'] = self.teOvBedTmp.GetValue()
			
		if self.cbOvTmp1.IsChecked():
			r['layer1temperature'] = self.teOvTmp1.GetValue()
			
		if self.cbOvTmp.IsChecked():
			r['temperature'] = self.teOvTmp.GetValue()
			
		if self.cbOvPrSpd.IsChecked():
			r['printspeed'] = self.teOvPrSpd.GetValue()
			
		if self.cbOvTrSpd.IsChecked():
			r['travelspeed'] = self.teOvTrSpd.GetValue()
			
		if self.cbOvPr1Spd.IsChecked():
			r['print1speed'] = self.teOvPr1Spd.GetValue()
			
		if self.cbOvSkt.IsChecked():
			if self.teOvSkt.IsChecked():
				r['skirt'] = 'True'
			else:
				r['skirt'] = 'False'
			
		if self.cbOvSktHt.IsChecked():
			r['skirtheight'] = self.teOvSktHt.GetValue()
			
		if self.cbOvSpt.IsChecked():
			if self.teOvSpt.IsChecked():
				r['support'] = 'True'
			else:
				r['support'] = 'False'
			
		if self.cbOvAdh.IsChecked():
			r['adhesion'] = self.teOvAdh.GetValue()

		return r
