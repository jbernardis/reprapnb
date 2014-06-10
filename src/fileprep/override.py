import wx

class Override(wx.Panel):
	def __init__(self, parent):
		self.parent = parent
		self.logger = parent.logger
		wx.Panel.__init__(self, parent, -1)
		self.SetBackgroundColour("white")

		box = wx.StaticBox(self, -1, "Slicer Overrides:")
		box.SetBackgroundColour("white")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)

		bgrid = wx.GridBagSizer()
		bgrid.AddSpacer((10, 10), pos=(0,0))
		bgrid.AddSpacer((10, 10), pos=(0,2))
		bgrid.AddSpacer((10, 10), pos=(0,4))
		
		self.controls = {}

		ln = 1
		self.cbOvLH = wx.CheckBox(self, wx.ID_ANY, "Layer Height")
		self.Bind(wx.EVT_CHECKBOX, self.checkLH, self.cbOvLH)
		bgrid.Add(self.cbOvLH, pos=(ln, 1))
		self.teOvLH = wx.TextCtrl(self, wx.ID_ANY, "0.2", style=wx.TE_RIGHT)
		self.teOvLH.Enable(False)
		self.controls["layerheight"] = self.teOvLH
		bgrid.Add(self.teOvLH, pos=(ln,3))
		
		ln += 1
		self.cbOvExWid = wx.CheckBox(self, wx.ID_ANY, "Extrusion Width")
		self.Bind(wx.EVT_CHECKBOX, self.checkEW, self.cbOvExWid)
		bgrid.Add(self.cbOvExWid, pos=(ln, 1))
		self.teOvExWid = wx.TextCtrl(self, wx.ID_ANY, "2.8", style=wx.TE_RIGHT)
		self.teOvExWid.Enable(False)
		self.controls["extrusionwidth"] = self.teOvExWid
		bgrid.Add(self.teOvExWid, pos=(ln,3))
		
		ln += 1
		self.cbOvInfill = wx.CheckBox(self, wx.ID_ANY, "Infill Density")
		self.Bind(wx.EVT_CHECKBOX, self.checkInfill, self.cbOvInfill)
		bgrid.Add(self.cbOvInfill, pos=(ln, 1))
		self.teOvInfill = wx.TextCtrl(self, wx.ID_ANY, "0.4", style=wx.TE_RIGHT)
		self.teOvInfill.Enable(False)
		self.controls["infilldensity"] = self.teOvInfill
		bgrid.Add(self.teOvInfill, pos=(ln,3))
		
		ln += 1
		self.cbOvBedTmp1 = wx.CheckBox(self, wx.ID_ANY, "Bed Temperature First Layer")
		self.Bind(wx.EVT_CHECKBOX, self.checkBedTmp1, self.cbOvBedTmp1)
		bgrid.Add(self.cbOvBedTmp1, pos=(ln, 1))
		self.teOvBedTmp1 = wx.TextCtrl(self, wx.ID_ANY, "60", style=wx.TE_RIGHT)
		self.teOvBedTmp1.Enable(False)
		self.controls["layer1bedtemperature"] = self.teOvBedTmp1
		bgrid.Add(self.teOvBedTmp1, pos=(ln,3))
		
		ln += 1
		self.cbOvBedTmp = wx.CheckBox(self, wx.ID_ANY, "Bed Temperature")
		self.Bind(wx.EVT_CHECKBOX, self.checkBedTmp, self.cbOvBedTmp)
		bgrid.Add(self.cbOvBedTmp, pos=(ln, 1))
		self.teOvBedTmp = wx.TextCtrl(self, wx.ID_ANY, "55", style=wx.TE_RIGHT)
		self.teOvBedTmp.Enable(False)
		self.controls["bedtemperature"] = self.teOvBedTmp
		bgrid.Add(self.teOvBedTmp, pos=(ln,3))
		
		ln += 1
		self.cbOvTmp1 = wx.CheckBox(self, wx.ID_ANY, "Temperature(s) First Layer")
		self.Bind(wx.EVT_CHECKBOX, self.checkTmp1, self.cbOvTmp1)
		bgrid.Add(self.cbOvTmp1, pos=(ln, 1))
		self.teOvTmp1 = wx.TextCtrl(self, wx.ID_ANY, "185", style=wx.TE_RIGHT)
		self.teOvTmp1.Enable(False)
		self.controls["layer1temperature"] = self.teOvTmp1
		bgrid.Add(self.teOvTmp1, pos=(ln,3))
		
		ln += 1
		self.cbOvTmp = wx.CheckBox(self, wx.ID_ANY, "Temperature(s)")
		self.Bind(wx.EVT_CHECKBOX, self.checkTmp, self.cbOvTmp)
		bgrid.Add(self.cbOvTmp, pos=(ln, 1))
		self.teOvTmp = wx.TextCtrl(self, wx.ID_ANY, "185", style=wx.TE_RIGHT)
		self.teOvTmp.Enable(False)
		self.controls["temperature"] = self.teOvTmp
		bgrid.Add(self.teOvTmp, pos=(ln,3))
		
		ln += 1
		self.cbOvPrSpd = wx.CheckBox(self, wx.ID_ANY, "Print Speed")
		self.Bind(wx.EVT_CHECKBOX, self.checkPrSpd, self.cbOvPrSpd)
		bgrid.Add(self.cbOvPrSpd, pos=(ln, 1))
		self.teOvPrSpd = wx.TextCtrl(self, wx.ID_ANY, "60", style=wx.TE_RIGHT)
		self.teOvPrSpd.Enable(False)
		self.controls["printspeed"] = self.teOvPrSpd
		bgrid.Add(self.teOvPrSpd, pos=(ln,3))
		
		ln += 1
		self.cbOvTrSpd = wx.CheckBox(self, wx.ID_ANY, "Travel Speed")
		self.Bind(wx.EVT_CHECKBOX, self.checkTrSpd, self.cbOvTrSpd)
		bgrid.Add(self.cbOvTrSpd, pos=(ln, 1))
		self.teOvTrSpd = wx.TextCtrl(self, wx.ID_ANY, "120", style=wx.TE_RIGHT)
		self.teOvTrSpd.Enable(False)
		self.controls["travelspeed"] = self.teOvTrSpd
		bgrid.Add(self.teOvTrSpd, pos=(ln,3))
		
		ln += 1
		self.cbOvPr1Spd = wx.CheckBox(self, wx.ID_ANY, "First Layer Speed")
		self.Bind(wx.EVT_CHECKBOX, self.checkPr1Spd, self.cbOvPr1Spd)
		bgrid.Add(self.cbOvPr1Spd, pos=(ln, 1))
		self.teOvPr1Spd = wx.TextCtrl(self, wx.ID_ANY, "30", style=wx.TE_RIGHT)
		self.teOvPr1Spd.Enable(False)
		self.controls["print1speed"] = self.teOvPr1Spd
		bgrid.Add(self.teOvPr1Spd, pos=(ln,3))
		
		ln += 1
		self.cbOvSpt = wx.CheckBox(self, wx.ID_ANY, "Support")
		self.Bind(wx.EVT_CHECKBOX, self.checkSpt, self.cbOvSpt)
		bgrid.Add(self.cbOvSpt, pos=(ln, 1))
		self.teOvSpt = wx.CheckBox(self, wx.ID_ANY, "Enabled")
		self.teOvSpt.Enable(False)
		self.controls["support"] = self.teOvSpt
		bgrid.Add(self.teOvSpt, pos=(ln,3))
		
		ln += 1
		self.cbOvSkt = wx.CheckBox(self, wx.ID_ANY, "Skirt")
		self.Bind(wx.EVT_CHECKBOX, self.checkSkt, self.cbOvSkt)
		bgrid.Add(self.cbOvSkt, pos=(ln, 1))
		self.teOvSkt = wx.CheckBox(self, wx.ID_ANY, "Enabled")
		self.teOvSkt.Enable(False)
		self.controls["skirt"] = self.teOvSkt
		bgrid.Add(self.teOvSkt, pos=(ln,3))

		ln += 1
		self.cbOvAdh = wx.CheckBox(self, wx.ID_ANY, "Adhesion")
		self.Bind(wx.EVT_CHECKBOX, self.checkAdh, self.cbOvAdh)
		bgrid.Add(self.cbOvAdh, pos=(ln, 1))
		self.teOvAdh = wx.ListBox(self, wx.ID_ANY, (-1, -1),  (270, 120), ["None", "Raft", "Brim"], wx.LB_SINGLE)
		self.teOvAdh.SetSelection(0)
		self.teOvAdh.Enable(False)
		self.controls["adhesion"] = self.teOvAdh
		bgrid.Add(self.teOvAdh, pos=(ln,3))

		ln += 1
		bgrid.AddSpacer((10, 10), pos=(ln,0))

		bsizer.Add(bgrid)
		border = wx.BoxSizer()
		border.Add(bsizer, 1, wx.EXPAND|wx.ALL, 10)
		self.SetSizer(border)  
		
	def setHelpText(self, ht):
		if ht is None:
			return
		
		for ck in self.controls.keys():
			if ck in ht.keys():
				self.controls[ck].SetToolTipString(ht[ck])
			else:
				self.controls[ck].SetToolTipString("")
		
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
		if self.cbOvLH.IsChecked():
			r['layerheight'] = self.teOvLH.GetValue()
			self.logger.LogMessage("Overriding layer height to: %s" % r['layerheight'])
			
		if self.cbOvExWid.IsChecked():
			r['extrusionwidth'] = self.teOvExWid.GetValue()
			self.logger.LogMessage("Overriding extrusion width to: %s" % r['extrusionwidth'])
			
		if self.cbOvInfill.IsChecked():
			r['infilldensity'] = self.teOvInfill.GetValue()
			self.logger.LogMessage("Overriding infill density to: %s" % r['infilldensity'])
			
		if self.cbOvBedTmp1.IsChecked():
			r['layer1bedtemperature'] = self.teOvBedTmp1.GetValue()
			self.logger.LogMessage("Overriding layer 1 bed temperature to: %s" % r['layer1bedtemperature'])
			
		if self.cbOvBedTmp.IsChecked():
			r['bedtemperature'] = self.teOvBedTmp.GetValue()
			self.logger.LogMessage("Overriding bed temperature to: %s" % r['bedtemperature'])
			
		if self.cbOvTmp1.IsChecked():
			r['layer1temperature'] = self.teOvTmp1.GetValue()
			self.logger.LogMessage("Overriding layer 1 temperature to: %s" % r['layer1temperature'])
			
		if self.cbOvTmp.IsChecked():
			r['temperature'] = self.teOvTmp.GetValue()
			self.logger.LogMessage("Overriding temperature to: %s" % r['temperature'])
			
		if self.cbOvPrSpd.IsChecked():
			r['printspeed'] = self.teOvPrSpd.GetValue()
			self.logger.LogMessage("Overriding print speed to: %s" % r['printspeed'])
			
		if self.cbOvTrSpd.IsChecked():
			r['travelspeed'] = self.teOvTrSpd.GetValue()
			self.logger.LogMessage("Overriding travel speed to: %s" % r['travelspeed'])
			
		if self.cbOvPr1Spd.IsChecked():
			r['print1speed'] = self.teOvPr1Spd.GetValue()
			self.logger.LogMessage("Overriding first layer print speed to: %s" % r['print1speed'])
			
		if self.cbOvSkt.IsChecked():
			if self.teOvSkt.IsChecked():
				r['skirt'] = 'True'
			else:
				r['skirt'] = 'False'
			self.logger.LogMessage("Overriding skirt enable to: %s" % r['skirt'])
			
		if self.cbOvSpt.IsChecked():
			if self.teOvSpt.IsChecked():
				r['support'] = 'True'
			else:
				r['support'] = 'False'
			self.logger.LogMessage("Overriding support enable to: %s" % r['support'])
			
		if self.cbOvAdh.IsChecked():
			r['adhesion'] = self.teOvAdh.GetString(self.teOvAdh.GetSelection())

		return r
