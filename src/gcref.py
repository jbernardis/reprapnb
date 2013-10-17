'''
Created on Jun 20, 2013

@author: ejefber
'''
import os
import wx.html as html
import wx

BUTTONDIM = (64, 64)

class GCRef(wx.Dialog):
	def __init__(self, app, folder):
		self.app = app
		
		pre = wx.PreDialog()
		pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
		pos = wx.DefaultPosition
		style = wx.DEFAULT_DIALOG_STYLE
		pre.Create(self.app, wx.ID_ANY, "G Code Reference", pos, [500, 500], style)
		self.PostCreate(pre)

		self.cwd = os.getcwd()
		self.html = html.HtmlWindow(self, wx.ID_ANY)

		self.box = wx.BoxSizer(wx.VERTICAL)
		self.box.Add(self.html, 1, wx.GROW)

		btnSizer = wx.BoxSizer(wx.HORIZONTAL)

		btn = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngExit, size=BUTTONDIM)
		btn.SetToolTipString("Close Dialog")
		self.Bind(wx.EVT_BUTTON, self.onClose, btn)
		btnSizer.Add(btn, 1, wx.ALL, 5)

		btn = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngContents, size=BUTTONDIM)
		btn.SetToolTipString("Scroll to Table of Contents")
		self.Bind(wx.EVT_BUTTON, self.onTOC, btn)
		btnSizer.Add(btn, 1, wx.ALL, 5)
		
		self.box.Add(btnSizer)

		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.SetSizer(self.box)
		self.SetAutoLayout(True)

		self.html.LoadPage(os.path.join(folder, 'gcode.html'))
		
	def onTOC(self, event):
		self.html.ScrollToAnchor("TOC")

	def onClose(self, event):
		self.app.onGCRefExit()
		self.Destroy()






