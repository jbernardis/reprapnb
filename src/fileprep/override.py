import wx

class Override(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent, -1)

		box = wx.StaticBox(self, -1, "Slicer Overrides:")
		bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)

		t = wx.StaticText(self, -1, "Controls placed \"inside\" the box are really its siblings")
		bsizer.Add(t, 0, wx.TOP|wx.LEFT, 10)

		border = wx.BoxSizer()
		border.Add(bsizer, 1, wx.EXPAND|wx.ALL, 25)
		self.SetSizer(border)   
		
	def getOverrides(self):
		return {}     
