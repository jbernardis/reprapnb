'''
Created on Jul 3, 2013

@author: Jeff
'''
import wx
import time
import string

class Logger(wx.Panel):
	def __init__(self, parent, app):
		self.parent = parent
		self.app = app
		self.settings = app.settings
		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(400, 250))
		self.SetBackgroundColour("white")

		sz = wx.BoxSizer(wx.VERTICAL)
		
		self.t = wx.TextCtrl(self, wx.ID_ANY, size=(300, 600), style=wx.TE_MULTILINE|wx.TE_RICH2)
		sz.Add(self.t, flag=wx.EXPAND | wx.ALL, border=10)

		self.SetSizer(sz)
		self.Layout()
		self.Fit()

	def setTraceLevel(self, l):
		self.traceLevel = l
		
	def LogTrace(self, level, text):
		if level > self.traceLevel:
			return
		
		self.LogMessage(("Trace[%d] - " % level) +string.rstrip(text)+"\n")

	def LogMessage(self, text):
		s = time.strftime('%H:%M:%S', time.localtime(time.time()))
		try:
			self.t.AppendText(s+" - " +string.rstrip(text)+"\n")
		except:
			pass

	def LogError(self, text):
		self.LogMessage("Error - " +string.rstrip(text)+"\n")

	def LogWarning(self, text):
		self.LogMessage("Warning - " +string.rstrip(text)+"\n")
