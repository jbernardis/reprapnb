'''
Created on Jul 3, 2013

@author: Jeff
'''
import os
import wx
import time
import string

BUTTONDIM = (48, 48)

class Logger(wx.Panel):
	def __init__(self, parent, app):
		self.parent = parent
		self.app = app
		self.settings = app.settings
		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(400, 250))
		self.SetBackgroundColour("white")

		sz = wx.BoxSizer(wx.VERTICAL)
		
		self.t = wx.TextCtrl(self, wx.ID_ANY, size=(300, 600), style=wx.TE_MULTILINE|wx.TE_RICH2|wx.TE_READONLY)
		sz.Add(self.t, flag=wx.EXPAND | wx.ALL, border=10)
		
		bsz = wx.BoxSizer(wx.HORIZONTAL)
				
		self.bClear = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngClearlog, size=BUTTONDIM)
		self.bClear.SetToolTipString("Clear the log")
		bsz.Add(self.bClear, flag=wx.ALL, border=10)
		self.Bind(wx.EVT_BUTTON, self.doClear, self.bClear)
				
		self.bSave = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngSavelog, size=BUTTONDIM)
		self.bSave.SetToolTipString("Save the log to a file")
		bsz.Add(self.bSave, flag=wx.ALL, border=10)
		self.Bind(wx.EVT_BUTTON, self.doSave, self.bSave)

		sz.Add(bsz, flag=wx.EXPAND | wx.ALL, border=10)

		self.SetSizer(sz)
		self.Layout()
		self.Fit()
		
	def doClear(self, evt):
		self.t.Clear()
		
	def doSave(self, evt):
		wildcard = "Log File |*.log"
		dlg = wx.FileDialog(
			self, message="Save as ...", defaultDir=self.settings.lastlogdirectory, 
			defaultFile="", wildcard=wildcard, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
		
		val = dlg.ShowModal()

		if val == wx.ID_OK:
			path = dlg.GetPath()
	
			if self.t.SaveFile(path):
				self.LogMessage("Log successfully saved to %s" % path)
				self.settings.lastlogdirectory = os.path.dirname(path)
				self.settings.setModified()
			else:
				self.LogError("Save of log to %s failed" % path)
				
		dlg.Destroy()


	def setTraceLevel(self, l):
		self.traceLevel = l
		
	def LogTrace(self, level, text):
		if level <= self.traceLevel:
			self.LogMessage(("Trace[%d] - " % level) +string.rstrip(text)+"\n")

	def LogMessage(self, text):
		s = time.strftime('%H:%M:%S', time.localtime(time.time()))
		try:
			self.t.AppendText(s+" - " +string.rstrip(text)+"\n")
		except:
			print "Unable to add (%s) to log" % text

	def LogError(self, text):
		self.LogMessage("Error - " +string.rstrip(text)+"\n")

	def LogWarning(self, text):
		self.LogMessage("Warning - " +string.rstrip(text)+"\n")
