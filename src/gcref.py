import os
import wx.html as html
import wx

from settings import BUTTONDIM

class GCRef(wx.Panel):
	def __init__(self, parent, app, folder):
		self.parent = parent
		self.app = app
		
		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(400, 250))
		self.SetBackgroundColour("white")
		
		self.cwd = os.getcwd()
		self.html = html.HtmlWindow(self, wx.ID_ANY)

		self.box = wx.BoxSizer(wx.VERTICAL)
		self.box.Add(self.html, 1, wx.GROW)

		btnSizer = wx.BoxSizer(wx.HORIZONTAL)

		btn = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngContents, size=BUTTONDIM)
		btn.SetToolTipString("Scroll to Table of Contents")
		self.Bind(wx.EVT_BUTTON, self.onTOC, btn)
		btnSizer.Add(btn, 1, wx.ALL, 5)
		
		self.box.Add(btnSizer)

		self.SetSizer(self.box)
		self.SetAutoLayout(True)

		self.html.LoadPage(os.path.join(folder, 'gcode.html'))
		
	def onTOC(self, event):
		self.html.ScrollToAnchor("TOC")
