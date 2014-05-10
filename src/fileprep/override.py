import wx

class Override(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent, -1)
		self.SetBackgroundColour("white")

		box = wx.StaticBox(self, -1, "Slicer Overrides:")
		box.SetBackgroundColour("white")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)

		bgrid = wx.GridBagSizer()
		bgrid.AddSpacer((10, 10), pos=(0,0))
		bgrid.AddSpacer((10, 10), pos=(0,2))
		bgrid.AddSpacer((10, 10), pos=(0,4))

		self.cbOvLH = wx.CheckBox(self, wx.ID_ANY, "Layer Height")
		self.Bind(wx.EVT_CHECKBOX, self.checkLH, self.cbOvLH)
		bgrid.Add(self.cbOvLH, pos=(1, 1))
		self.teOvLH = wx.TextCtrl(self, wx.ID_ANY, "0.2", style=wx.TE_RIGHT)
		self.teOvLH.Enable(False)
		bgrid.AddSpacer((10, 10), pos=(2,0))

		bgrid.Add(self.teOvLH, pos=(1,3))


		bsizer.Add(bgrid)
		border = wx.BoxSizer()
		border.Add(bsizer, 1, wx.EXPAND|wx.ALL, 10)
		self.SetSizer(border)   
	def checkLH(self, evt):
		if self.cbOvLH.IsChecked():
			self.teOvLH.Enable(True)
		else:
			self.teOvLH.Enable(False)
		
	def getOverrides(self):
		r = {}     
		if self.cbOvLH.IsChecked():
			r['layerheight'] = self.teOvLH.GetValue()

		print "get ovr returning ", r
		return r
