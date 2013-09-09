import wx

BUTTONDIM = (48, 48)

class ToolChange(wx.Window): 
	def __init__(self, parent, app, nextr=1):
		self.parent = parent
		self.app = app
		self.logger = self.app.logger
		self.currentSelection = 0

		self.nextr = nextr
		wx.Window.__init__(self, parent, wx.ID_ANY, size=(-1, -1), style=wx.SIMPLE_BORDER)		
		sizerToolChange = wx.BoxSizer(wx.HORIZONTAL)

		self.rbTools = []
		sizerToolChange.AddSpacer((20, 10))
		for i in range(3):
			if i == 0:
				style = wx.RB_GROUP
			else:
				style = 0
			rb = wx.RadioButton(self, wx.ID_ANY, " Tool %d " % (i+1), style = style)
			self.rbTools.append(rb)
			sizerToolChange.Add(rb, flag=wx.TOP | wx.BOTTOM, border=5)
			sizerToolChange.AddSpacer((20, 10))
			self.Bind(wx.EVT_RADIOBUTTON, self.onToolChange, rb )
			rb.Enable(i<self.nextr)

		self.rbTools[0].SetValue(True)

		self.SetSizer(sizerToolChange)
		self.Layout()
		self.Fit()
		
	def onToolChange(self, evt):
		tc_sel = evt.GetEventObject()

		for i in range(3):
			if tc_sel is self.rbTools[i]:
				self.currentSelection = i
				print "Selected tool ", i
				break
		
	def changePrinter(self, nextr):
		self.nextr = nextr
		for i in range(3):
			self.rbTools[i].Enable(i<self.nextr)
			
		if self.currentSelection >= self.nextr:
			self.currentSelection = 0
			self.rbTools[0].SetValue(True)
