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

		ln = 1
		self.cbOvLH = wx.CheckBox(self, wx.ID_ANY, "Layer Height")
		self.Bind(wx.EVT_CHECKBOX, self.checkLH, self.cbOvLH)
		bgrid.Add(self.cbOvLH, pos=(ln, 1))
		self.teOvLH = wx.TextCtrl(self, wx.ID_ANY, "0.2", style=wx.TE_RIGHT)
		self.teOvLH.Enable(False)
		bgrid.Add(self.teOvLH, pos=(ln,3))
		
		ln += 1
		self.cbOvBedTmp1 = wx.CheckBox(self, wx.ID_ANY, "Bed Temperature First Layer")
		self.Bind(wx.EVT_CHECKBOX, self.checkBedTmp1, self.cbOvBedTmp1)
		bgrid.Add(self.cbOvBedTmp1, pos=(ln, 1))
		self.teOvBedTmp1 = wx.TextCtrl(self, wx.ID_ANY, "60", style=wx.TE_RIGHT)
		self.teOvBedTmp1.Enable(False)
		bgrid.Add(self.teOvBedTmp1, pos=(ln,3))
		
		ln += 1
		self.cbOvBedTmp = wx.CheckBox(self, wx.ID_ANY, "Bed Temperature")
		self.Bind(wx.EVT_CHECKBOX, self.checkBedTmp, self.cbOvBedTmp)
		bgrid.Add(self.cbOvBedTmp, pos=(ln, 1))
		self.teOvBedTmp = wx.TextCtrl(self, wx.ID_ANY, "55", style=wx.TE_RIGHT)
		self.teOvBedTmp.Enable(False)
		bgrid.Add(self.teOvBedTmp, pos=(ln,3))
		
		ln += 1
		self.cbOvTmp1 = wx.CheckBox(self, wx.ID_ANY, "Temperature(s) First Layer")
		self.Bind(wx.EVT_CHECKBOX, self.checkTmp1, self.cbOvTmp1)
		bgrid.Add(self.cbOvTmp1, pos=(ln, 1))
		self.teOvTmp1 = wx.TextCtrl(self, wx.ID_ANY, "185", style=wx.TE_RIGHT)
		self.teOvTmp1.Enable(False)
		bgrid.Add(self.teOvTmp1, pos=(ln,3))
		
		ln += 1
		self.cbOvTmp = wx.CheckBox(self, wx.ID_ANY, "Temperature(s)")
		self.Bind(wx.EVT_CHECKBOX, self.checkTmp, self.cbOvTmp)
		bgrid.Add(self.cbOvTmp, pos=(ln, 1))
		self.teOvTmp = wx.TextCtrl(self, wx.ID_ANY, "185", style=wx.TE_RIGHT)
		self.teOvTmp.Enable(False)
		bgrid.Add(self.teOvTmp, pos=(ln,3))
		
		ln += 1
		self.cbOvPrSpd = wx.CheckBox(self, wx.ID_ANY, "Print Speed")
		self.Bind(wx.EVT_CHECKBOX, self.checkPrSpd, self.cbOvPrSpd)
		bgrid.Add(self.cbOvPrSpd, pos=(ln, 1))
		self.teOvPrSpd = wx.TextCtrl(self, wx.ID_ANY, "60", style=wx.TE_RIGHT)
		self.teOvPrSpd.Enable(False)
		bgrid.Add(self.teOvPrSpd, pos=(ln,3))
		
		ln += 1
		self.cbOvTrSpd = wx.CheckBox(self, wx.ID_ANY, "Travel Speed")
		self.Bind(wx.EVT_CHECKBOX, self.checkTrSpd, self.cbOvTrSpd)
		bgrid.Add(self.cbOvTrSpd, pos=(ln, 1))
		self.teOvTrSpd = wx.TextCtrl(self, wx.ID_ANY, "120", style=wx.TE_RIGHT)
		self.teOvTrSpd.Enable(False)
		bgrid.Add(self.teOvTrSpd, pos=(ln,3))
		
		ln += 1
		self.cbOvPr1Spd = wx.CheckBox(self, wx.ID_ANY, "First Layer Speed")
		self.Bind(wx.EVT_CHECKBOX, self.checkPr1Spd, self.cbOvPr1Spd)
		bgrid.Add(self.cbOvPr1Spd, pos=(ln, 1))
		self.teOvPr1Spd = wx.TextCtrl(self, wx.ID_ANY, "30", style=wx.TE_RIGHT)
		self.teOvPr1Spd.Enable(False)
		bgrid.Add(self.teOvPr1Spd, pos=(ln,3))
		
		ln += 1
		self.cbOvSkt = wx.CheckBox(self, wx.ID_ANY, "Skirt")
		self.Bind(wx.EVT_CHECKBOX, self.checkSkt, self.cbOvSkt)
		bgrid.Add(self.cbOvSkt, pos=(ln, 1))
		self.teOvSkt = wx.CheckBox(self, wx.ID_ANY, "Enabled")
		self.teOvSkt.Enable(False)
		bgrid.Add(self.teOvSkt, pos=(ln,3))

		ln += 1
		bgrid.AddSpacer((10, 10), pos=(ln,0))

		bsizer.Add(bgrid)
		border = wx.BoxSizer()
		border.Add(bsizer, 1, wx.EXPAND|wx.ALL, 10)
		self.SetSizer(border)  
		
	def checkLH(self, evt):
		if self.cbOvLH.IsChecked():
			self.teOvLH.Enable(True)
		else:
			self.teOvLH.Enable(False)
		
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
		
	def getOverrides(self):
		r = {}     
		if self.cbOvLH.IsChecked():
			r['layerheight'] = self.teOvLH.GetValue()
			self.logger.LogMessage("Overriding layer height to: %s" % r['layerheight'])
			
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

		return r
