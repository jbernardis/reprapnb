import os
import wx
import time
import string
import toaster as TB

from settings import BUTTONDIM

class Logger(wx.Panel):
	def __init__(self, parent, app):
		self.parent = parent
		self.app = app
		self.settings = app.settings
		
		self.setTraceLevel(99)
		
		self.logCommands = False
		self.logGCode = False
		
		self.nLines = 0
		self.maxLines = self.settings.maxloglines;
		self.chunk = 100;
		if self.maxLines is not None and self.chunk > self.maxLines:
			self.chunk = self.maxLines/2
		
		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(400, 250))
		self.SetBackgroundColour("white")
		
		self.toaster = TB.Toaster()
		self.toaster.SetPositionByCorner(self.settings.popuplocation)
		self.toaster.SetShowTime(2000)

		self.hiLiteTabTimer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.onHiLiteTabTimer, self.hiLiteTabTimer)
		
		sz = wx.BoxSizer(wx.VERTICAL)
		
		self.t = wx.TextCtrl(self, wx.ID_ANY, size=(300, 600), style=wx.TE_MULTILINE|wx.TE_RICH2|wx.TE_READONLY)
		sz.Add(self.t, flag=wx.EXPAND | wx.ALL, border=10)
		
		bsz = wx.BoxSizer(wx.HORIZONTAL)
				
		self.bClear = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngClearlog, size=BUTTONDIM)
		self.bClear.SetToolTipString("Clear the log")
		bsz.Add(self.bClear, flag=wx.ALL, border=10)
		self.Bind(wx.EVT_BUTTON, self.doClear, self.bClear)
				
		self.bSave = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngSavelog, size=BUTTONDIM)
		self.bSave.SetToolTipString("Save the log to a file")
		bsz.Add(self.bSave, flag=wx.ALL, border=10)
		self.Bind(wx.EVT_BUTTON, self.doSave, self.bSave)
		
		bsz.AddSpacer((20, 60))
		
		self.cbUsePopup = wx.CheckBox(self, wx.ID_ANY, "Use Popup Display")
		self.cbUsePopup.SetToolTipString("Display log messages in a popup display")
		self.Bind(wx.EVT_CHECKBOX, self.checkUsePopup, self.cbUsePopup)
		self.cbUsePopup.SetValue(self.settings.usepopup)
		bsz.Add(self.cbUsePopup, 0, wx.TOP, 10)
		
		bsz.AddSpacer((20, 60))
		
		self.cbLogCmds = wx.CheckBox(self, wx.ID_ANY, "Log Commands")
		self.cbLogCmds.SetToolTipString("Log G Code commands entered interactively")
		self.Bind(wx.EVT_CHECKBOX, self.checkLogCmds, self.cbLogCmds)
		self.cbLogCmds.SetValue(self.logCommands)
		bsz.Add(self.cbLogCmds, 0, wx.TOP, 10)
		
		bsz.AddSpacer((20, 20))
		
		self.cbLogGCode = wx.CheckBox(self, wx.ID_ANY, "Log G Code")
		self.cbLogGCode.SetToolTipString("Log G Code from printed file")
		self.Bind(wx.EVT_CHECKBOX, self.checkLogGCode, self.cbLogGCode)
		self.cbLogGCode.SetValue(self.logGCode)
		bsz.Add(self.cbLogGCode, 0, wx.TOP, 10)


		sz.Add(bsz, flag=wx.EXPAND | wx.ALL, border=10)

		self.SetSizer(sz)
		self.Layout()
		self.Fit()
		
	def checkUsePopup(self, evt):
		self.settings.usepopup = evt.IsChecked()
		self.settings.setModified()
		
	def hideToaster(self):
		self.toaster.Hide()
		
	def checkShowToaster(self):
		self.toaster.checkShow()
		
	def checkLogCmds(self, evt):
		self.logCommands = evt.IsChecked()
		
	def checkLogGCode(self, evt):
		self.logGCode = evt.IsChecked()

	def onHiLiteTabTimer(self, evt):
		self.app.hiLiteLogTab(False)
		
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
		onLoggerPage = self.app.onLoggerPage()
		try:
			msg = s+" - "+string.rstrip(text)
			if self.settings.usepopup:
				self.toaster.Append(msg, onLoggerPage)
				
			self.t.AppendText(msg+"\n")
			self.nLines += 1
			if self.maxLines is not None and self.nLines > self.maxLines:
				self.t.Remove(0L, self.t.XYToPosition(0, self.chunk))
				self.nLines -= self.chunk
		except:
			print "Unable to add (%s) to log" % text
			
		if not onLoggerPage:
			self.hiLiteTabTimer.Start(3000, True)
			self.app.hiLiteLogTab(True)

	def LogCMessage(self, text):
		if self.logCommands:
			self.LogMessage("(c) - " + text)

	def LogGMessage(self, text):
		if self.logGCode:
			self.LogMessage("(g) - " + text)

	def LogMessageCR(self, text):
		self.LogMessage(text)

	def LogError(self, text):
		self.LogMessage("Error - " +string.rstrip(text))

	def LogWarning(self, text):
		self.LogMessage("Warning - " +string.rstrip(text))
		
	def close(self):
		if self.toaster is not None:
			self.toaster.Close()
