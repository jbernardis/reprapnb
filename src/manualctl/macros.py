import os
import wx

from managemacros import ManageMacros

BASE_ID = 2000

class MacroDialog(wx.Dialog):
	def __init__(self, parent, reprap):
		self.parent = parent
		self.app = self.parent.app
		self.reprap = reprap
		self.logger = self.app.logger
		self.settings = self.app.settings
		self.mmdlg = None
		self.macroList = MacroList(self.app.settings)
		
		pre = wx.PreDialog()
		pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
		pos = wx.DefaultPosition
		sz = wx.DefaultSize
		style = wx.DEFAULT_DIALOG_STYLE
		pre.Create(self.app, wx.ID_ANY, "Macros", pos, sz, style)
		self.PostCreate(pre)
		
		self.Bind(wx.EVT_CLOSE, self.onClose)
		sizer = wx.BoxSizer(wx.VERTICAL)
		hsizer = None

		i = 0
		self.macroMap = []		
		for k in self.macroList:
			if (i % 3) == 0:
				if hsizer:
					sizer.Add(hsizer)
				hsizer = wx.BoxSizer(wx.HORIZONTAL)
				
			self.macroMap.append(k)
			b = wx.Button(self, BASE_ID + i, k)
			i += 1
			self.Bind(wx.EVT_BUTTON, self.runMacro, b)
			hsizer.Add(b)
			
		sizer.Add(hsizer)
		
		sizer.AddSpacer((30, 30))
		self.bManage = wx.Button(self, wx.ID_ANY, "Manage Macros")
		sizer.Add(self.bManage)
		self.Bind(wx.EVT_BUTTON, self.manageMacros, self.bManage)

		self.SetSizer(sizer)
		sizer.Fit(self)
		
	def manageMacros(self, evt):
		if self.mmdlg is None:
			self.mmdlg = ManageMacros(self, self.settings, self.parent.images, self.settings.macroOrder, self.settings.macroList, self.manageDone)
			self.mmdlg.Show()
			self.bManage.Enable(False)

	def manageDone(self, rc):
		if rc:
			mo, mfn = self.mmdlg.getData()
		self.mmdlg.Destroy()
		self.mmdlg = None
		self.bManage.Enable(True)
		if rc:
			self.settings.macroOrder = mo
			self.settings.macroList = mfn
			self.settings.setModified()
			self.parent.onMacroExit(True)
		
	def onClose(self, evt):
		self.parent.onMacroExit()
		
	def runMacro(self, evt):
		kid = evt.GetId() - BASE_ID
		if kid < 0 or kid >= len(self.macroMap):
			print "Invalid ID in runmacro: ", kid
			return
	
		mn = self.macroMap[kid]	
		self.logger.LogMessage("Running macro \"%s\"" % mn)

		fn = self.macroList.getFileName(mn)		
		try:
			l = list(open(fn))
		except:
			self.logger.LogMessage("Unable to open macro file: " + fn)
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
	


