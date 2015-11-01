import os
import wx

from settings import BUTTONDIM

VISIBLEQUEUESIZE = 21

class ViewPrintHistory(wx.Dialog):
	def __init__(self, parent, settings, images, printHistory, allowLoad, ch):
		self.parent = parent
		self.settings = settings
		self.closehandler = ch
		self.allowload = allowLoad
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Printing History", size=(800, 804))
		self.SetBackgroundColour("white")
		
		dsizer = wx.BoxSizer(wx.HORIZONTAL)
		dsizer.AddSpacer((10, 10))
		
		self.images = images

		leftsizer = wx.BoxSizer(wx.VERTICAL)
		leftsizer.AddSpacer((10, 10))
		
		self.lbHistory = PrintHistoryCtrl(self, printHistory, self.images, self.settings.showhistbasename)
		leftsizer.Add(self.lbHistory);
		leftsizer.AddSpacer((10, 10))

		btnsizer = wx.BoxSizer(wx.HORIZONTAL)		
		btnsizer.AddSpacer((5,5))

		self.bExit = wx.BitmapButton(self, wx.ID_ANY, self.images.pngExit, size=BUTTONDIM)
		self.bExit.SetToolTipString("Exit")
		btnsizer.Add(self.bExit)
		self.Bind(wx.EVT_BUTTON, self.doExit, self.bExit)
		btnsizer.AddSpacer((5,5))

		self.bLoad = wx.BitmapButton(self, wx.ID_ANY, self.images.pngFileopen, size=BUTTONDIM)
		self.bLoad.SetToolTipString("Re-load G Code file")
		btnsizer.Add(self.bLoad)
		self.Bind(wx.EVT_BUTTON, self.doReload, self.bLoad)
		self.bLoad.Enable(False)
		
		btnsizer.AddSpacer((30, 10))
		self.cbBase = wx.CheckBox(self, wx.ID_ANY, "Show basename only")
		btnsizer.Add(self.cbBase, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
		self.cbBase.SetToolTipString("Show only basename of filenames")
		self.Bind(wx.EVT_CHECKBOX, self.checkBasename, self.cbBase)
		self.cbBase.SetValue(self.settings.showhistbasename)


		leftsizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
		dsizer.Add(leftsizer)
		dsizer.AddSpacer((10,10))

		self.SetSizer(dsizer)  
		dsizer.Fit(self)
		
	def checkBasename(self, evt):
		self.settings.showhistbasename = evt.IsChecked()
		self.settings.setModified()
		self.lbHistory.setBaseNameOnly(evt.IsChecked())

	def getSelectedFile(self):
		return self.lbHistory.getSelectedFile()
	
	def UpdateDlg(self, exists):
		if self.allowload:
			self.bLoad.Enable(exists)
		else:
			self.bLoad.Enable(False)
			
	def AllowLoading(self, flag):
		self.allowload = flag
		self.UpdateDlg(self.lbHistory.doesSelectedExist())
		
	def doExit(self, evt):
		self.closehandler(False)
		
	def doReload(self, evt):
		self.closehandler(True)

class PrintHistoryCtrl(wx.ListCtrl):	
	def __init__(self, parent, printhistory, images, basenameonly):
		
		f = wx.Font(8,  wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		dc = wx.ScreenDC()
		dc.SetFont(f)
		fontHeight = dc.GetTextExtent("Xy")[1]
		
		colWidths = [500, 80, 120, 120, 80]
		colTitles = ["File", "Printer", "Start Time", "End Time", "Type"]
		
		totwidth = 20;
		for w in colWidths:
			totwidth += w
		
		wx.ListCtrl.__init__(self, parent, wx.ID_ANY, size=(totwidth, fontHeight*(VISIBLEQUEUESIZE+1)),
			style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES|wx.LC_SINGLE_SEL
			)

		self.parent = parent		
		self.printhistory = printhistory[::-1]
		self.basenameonly = basenameonly
		self.selectedItem = None
		self.selectedExists = False
		self.il = wx.ImageList(16, 16)
		self.il.Add(images.pngSelected)
		self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

		self.SetFont(f)
		for i in range(len(colWidths)):
			self.InsertColumn(i, colTitles[i])
			self.SetColumnWidth(i, colWidths[i])
		
		self.SetItemCount(len(self.printhistory))
		
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.doListSelect)
		
	def getSelectedFile(self):
		if self.selectedItem is None:
			return None
		
		return self.printhistory[self.selectedItem][0]
		
	def doListSelect(self, evt):
		x = self.selectedItem
		self.selectedItem = evt.m_itemIndex
		if x is not None:
			self.RefreshItem(x)
			
		fn = self.printhistory[self.selectedItem][0]
		if fn and  os.path.exists(fn):
			self.selectedExists = True
		else:
			self.selectedExists = False
		self.parent.UpdateDlg(self.selectedExists)
		
	def doesSelectedExist(self):
		return self.selectedExists
			
	def setBaseNameOnly(self, flag):
		if self.basenameonly == flag:
			return
		
		self.basenameonly = flag
		for i in range(len(self.printhistory)):
			self.RefreshItem(i)

	def OnGetItemText(self, item, col):
		if col == 0:
			if not self.printhistory[item][0]:
				return "<temporary file>"
			elif self.printhistory[item][0].startswith("SD:"):
				return self.printhistory[item][0]
			else:
				if self.basenameonly:
					return os.path.basename(self.printhistory[item][0])
				else:
					return self.printhistory[item][0]
		else:
			return self.printhistory[item][col]

	def OnGetItemImage(self, item):
		if item == self.selectedItem:
			return 0
		else:
			return -1
	
	def OnGetItemAttr(self, item):
		return None


