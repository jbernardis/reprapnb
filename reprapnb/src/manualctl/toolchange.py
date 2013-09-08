import wx

BUTTONDIM = (48, 48)

class ToolChange(wx.Window): 
	def __init__(self, parent, app, nextr=1):
		self.parent = parent
		self.app = app
		self.logger = self.app.logger

		self.nextr = nextr
		wx.Window.__init__(self, parent, wx.ID_ANY, size=(-1, -1), style=wx.SIMPLE_BORDER)		
		sizerToolChange = wx.BoxSizer(wx.HORIZONTAL)

		self.rbTools = []
		self.rbTools.append(wx.RadioButton(self, wx.ID_ANY, " Tool 1 ", style = wx.RB_GROUP ))
		self.rbTools.apoend(wx.RadioButton(self, wx.ID_ANY, " Tool 2 ", ))
		self.rbTools.append(wx.RadioButton(self, wx.ID_ANY, " Tool 3 ", ))
		for i in self.rbTools:
			sizerToolChange.Add(i)
			self.Bind(wx.EVT_RADIOBUTTON, self.OnToolChange, i )
			i.Enable(i<self.nextr)

		self.Bind(wx.EVT_BUTTON, self.doRetract, self.bRetract)

		self.SetSizer(sizerToolChange)
		self.Layout()
		self.Fit()
		
	def onToolChange(self, evt):
		tc_sel = evt.GetEventObject()

		for i in range(3):
			if tc_sel is self.rbTools[i]:
				print "Selected tool ", i
				break
		
	def changePrinter(self, nextr):
		self.nextr = nextr
		for i in self.rbTools:
			i.Enable(i<self.nextr)
