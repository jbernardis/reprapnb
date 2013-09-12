import wx
	
class GCodeEntry(wx.Window): 
	def __init__(self, parent, app, name=""):
		self.parent = parent
		self.app = app
		self.name = name
		wx.Window.__init__(self, parent, wx.ID_ANY, size=(-1, -1), style=wx.SIMPLE_BORDER)		
		sizerGCode = wx.BoxSizer(wx.HORIZONTAL)
		self.tGCode = wx.TextCtrl(self, wx.ID_ANY, "", size=(550, -1), style=wx.TE_LEFT | wx.TE_PROCESS_ENTER)
		self.tGCode.Bind(wx.EVT_KILL_FOCUS, self.evtGCodeSend)
		self.tGCode.Bind(wx.EVT_TEXT_ENTER, self.evtGCodeSend)
		f = wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL)
		self.tGCode.SetFont(f)
		sizerGCode.AddSpacer((10, 10))
		sizerGCode.Add(self.tGCode, 0, wx.ALL, 10)
		sizerGCode.AddSpacer((10, 10))
		self.SetSizer(sizerGCode)
		self.Layout()
		self.Fit()
		
	def evtGCodeSend(self, evt):
		cmd = self.tGCode.GetValue().upper()
		self.app.reprap.send_now(cmd)