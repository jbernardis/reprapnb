'''
Created on Jun 20, 2013

@author: ejefber
'''
import os
import wx.html as html
import wx

class GCRef(wx.Dialog):
	def __init__(self, app):
		self.app = app
		
		pre = wx.PreDialog()
		pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
		pos = wx.DefaultPosition
		sz = wx.DefaultSize
		style = wx.DEFAULT_DIALOG_STYLE
		pre.Create(self.app, wx.ID_ANY, "G Code Reference", pos, sz, style)
		self.PostCreate(pre)

		self.cwd = os.getcwd()
		self.html = html.HtmlWindow(self, wx.ID_ANY)

		self.box = wx.BoxSizer(wx.VERTICAL)
		self.box.Add(self.html, 1, wx.GROW)

		btn = wx.Button(self, wx.ID_ANY, "Close")
		self.Bind(wx.EVT_BUTTON, self.onClose, btn)
		self.box.Add(btn, 1, wx.GROW | wx.ALL, 2)

		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.SetSizer(self.box)
		self.SetAutoLayout(True)

		self.html.LoadPage('gcode.html')

	def onClose(self, event):
		self.app.onGCRefExit()
		self.Destroy()






