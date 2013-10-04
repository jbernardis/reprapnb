'''
Created on Jun 20, 2013

@author: ejefber
'''
import os
import wx

BUTTONDIM = (48, 48)
BASE_ID = 2000

class MacroDialog(wx.Dialog):
	def __init__(self, app, reprap):
		self.app = app
		self.reprap = reprap
		self.logger = self.app.logger
		self.settings = self.app.settings
		self.path = os.path.join(self.settings.cmdfolder, "macros")
		self.macroList = MacroList(self.settings)
		
		pre = wx.PreDialog()
		pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
		pos = wx.DefaultPosition
		sz = wx.DefaultSize
		style = wx.DEFAULT_DIALOG_STYLE
		pre.Create(self.app, wx.ID_ANY, "Macros", pos, sz, style)
		self.PostCreate(pre)
		
		self.Bind(wx.EVT_CLOSE, self.onClose)
		sizer = wx.BoxSizer(wx.VERTICAL)

		i = 0
		self.macroMap = []		
		for k in self.macroList:
			self.macroMap.append(k)
			b = wx.Button(self, BASE_ID + i, k)
			i += 1
			self.Bind(wx.EVT_BUTTON, self.runMacro, b)
			sizer.Add(b)

		self.SetSizer(sizer)
		sizer.Fit(self)
		
	def onClose(self, evt):
		self.app.onMacroExit()
		self.Destroy()
		
	def runMacro(self, evt):
		kid = evt.GetId() - BASE_ID
		if kid < 0 or kid >= len(self.macroMap):
			print "Invalid ID in runmacro: ", kid
			return
	
		mn = self.macroMap[kid]	
		self.logger.LogMessage("Running macro \"%s\"" % mn)

		fn = os.path.join(self.path. self.macroList.getFileName(mn))		
		try:
			l = list(open(fn))
		except:
			self.logger.LogMessage("Unable to open macro file: ", fn)
			return
		
		for ln in l:
			self.reprap.send_now(ln)

		
class MacroList:
	def __init__(self, settings):
		self.ml = settings.macroList
		self.keyList = settings.macroOrder
				
	def __iter__(self):
		self.__mindex__ = 0
		return self
	
	def next(self):
		if self.__mindex__ < self.__len__():
			i = self.__mindex__
			self.__mindex__ += 1
			return self.keyList[i]

		raise StopIteration
	
	def __len__(self):
		return len(self.keyList)
	
	def getFileName(self, key):
		if key in self.ml.keys():
			return self.ml[key]
		else:
			return None
	


