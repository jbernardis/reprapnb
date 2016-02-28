import wx
import os
import shlex, subprocess

class ToolBar(wx.Frame):
	def __init__(self, app, settings, images):
		wx.Frame.__init__(self, None, title="Toolbar")
		self.SetBackgroundColour("white")
		self.buttonMap = {}
		fsizer = wx.BoxSizer(wx.HORIZONTAL)
		
		self.Bind(wx.EVT_CLOSE, self.hideToolBar)
		
		self.settings = settings
		self.app = app
		self.logger = self.app.logger
		
		cGroup = None
		sizer = None
		bsizer = None
		fsizer.AddSpacer((5,5))
		
		for t in self.settings.toolOrder:
			if self.settings.tools[t][0] != cGroup:
				if sizer is not None:
					bsizer.Add(sizer)
					fsizer.Add(bsizer)
					fsizer.AddSpacer((10,90))

				box = wx.StaticBox(self, -1, self.settings.tools[t][0])
				box.SetBackgroundColour("white")
				bsizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
				
				sizer = wx.BoxSizer(wx.HORIZONTAL)
				cGroup = self.settings.tools[t][0]
		
			b = wx.BitmapButton(self, wx.ID_ANY, images.getByName(t), size=(64,64))
			b.SetToolTipString(self.settings.tools[t][1])
			self.buttonMap[t] = b
			self.Bind(wx.EVT_BUTTON, self.bTool, b)
			sizer.Add(b)
		
		bsizer.Add(sizer)
		fsizer.Add(bsizer)
		fsizer.AddSpacer((5,5))

		self.SetSizer(fsizer)
		self.Fit()
		
	def hideToolBar(self, evt):
		self.Hide()
	
	def bTool(self, evt):
		b = evt.GetEventObject()
		for t in self.buttonMap.keys():
			if b == self.buttonMap[t]:
				s = self.settings.tools[t][2]
				cmd = os.path.expandvars(os.path.expanduser(self.app.replace(s)))
				self.logger.LogMessage("Executing: %s" % cmd)

				args = shlex.split(str(cmd))
				try:
					subprocess.Popen(args, shell=False, stdin=None, stdout=None, stderr=None, close_fds=True)

				except:
					self.logger.LogError("Exception occurred trying to spawn tool process")
					return

