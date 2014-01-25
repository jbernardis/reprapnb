import wx

from settings import BUTTONDIM

class GCodeEntry(wx.Window): 
	def __init__(self, parent, app, name=""):
		self.parent = parent
		self.app = app
		self.reprap = self.parent.reprap
		self.name = name
		wx.Window.__init__(self, parent, wx.ID_ANY, size=(-1, -1), style=wx.SIMPLE_BORDER)		
		sizerGCode = wx.BoxSizer(wx.HORIZONTAL)
		self.tGCode = wx.TextCtrl(self, wx.ID_ANY, "", size=(300, -1), style=wx.TE_LEFT | wx.TE_PROCESS_ENTER)
		self.tGCode.Bind(wx.EVT_TEXT_ENTER, self.evtGCodeSend)
		f = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		self.tGCode.SetFont(f)
		
		self.bSend = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngSend, size=BUTTONDIM)
		self.bSend.SetToolTipString("Send a G Code command to the printer")
		self.Bind(wx.EVT_BUTTON, self.evtGCodeSend, self.bSend)

		self.bClear = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngClear, size=BUTTONDIM)
		self.bClear.SetToolTipString("Clear the G Code entry field")
		self.Bind(wx.EVT_BUTTON, self.onClear, self.bClear)

		sizerGCode.AddSpacer((10, 10))
		sizerGCode.Add(self.tGCode, flag=wx.TOP, border=20)
		sizerGCode.AddSpacer((10, 10))
		sizerGCode.Add(self.bSend, flag=wx.TOP | wx.BOTTOM, border=10)
		sizerGCode.AddSpacer((10, 10))
		sizerGCode.Add(self.bClear, flag=wx.TOP | wx.BOTTOM, border=10)
		sizerGCode.AddSpacer((10, 10))
		self.SetSizer(sizerGCode)
		self.Layout()
		self.Fit()
		
	def evtGCodeSend(self, evt):
		cmd = self.tGCode.GetValue()
		self.reprap.send_now(cmd)
		
	def onClear(self, evt):
		self.tGCode.SetValue("")
