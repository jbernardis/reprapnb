'''
Created on Apr 10, 2013

@author: Jeff
'''
import wx

class InfoPane (wx.Window):
	def __init__(self, parent, app):
		self.parent = parent
		self.app = app
		self.logger = self.app.logger

		wx.Window.__init__(self, parent, wx.ID_ANY, size=(-1, -1), style=wx.SIMPLE_BORDER)		
		sizerInfo = wx.GridBagSizer(vgap=2, hgap=10)
		
		dc = wx.WindowDC(self)
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
		dc.SetFont(f)

		self.SetSizer(sizerInfo)
		self.Layout()
		self.Fit()
