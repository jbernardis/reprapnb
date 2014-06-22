import wx
import os
import time
from images import Images

class ToolBar(wx.Frame):
	def __init__(self, settings):
		wx.Frame.__init__(self, None, title="Toolbar")
		self.SetBackgroundColour("white")
		self.buttonMap = {}
		fsizer = wx.BoxSizer(wx.HORIZONTAL)
		
		self.settings = settings
		images = Images(os.path.join(".", "tbimages"))
		
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
	
	def bTool(self, evt):
		b = evt.GetEventObject()
		for t in self.buttonMap.keys():
			if b == self.buttonMap[t]:
				print "command line: ", self.settings.tools[t][2]
				return
