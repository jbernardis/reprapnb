import os
import wx

from settings import BUTTONDIM

VISIBLEQUEUESIZE = 21

class ViewSliceHistory(wx.Dialog):
	def __init__(self, parent, settings, images, sliceHistory, ch):
		self.parent = parent
		self.settings = settings
		self.closehandler = ch
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Slicing History", size=(800, 804))
		self.SetBackgroundColour("white")
		
		dsizer = wx.BoxSizer(wx.HORIZONTAL)
		dsizer.AddSpacer((10, 10))
		
		self.editDlg = None
		self.images = images

		leftsizer = wx.BoxSizer(wx.VERTICAL)
		leftsizer.AddSpacer((10, 10))
		
		self.lbHistory = SliceHistoryCtrl(self, sliceHistory, self.images, self.settings.showhistbasename)
		leftsizer.Add(self.lbHistory);
		leftsizer.AddSpacer((10, 10))

		btnsizer = wx.BoxSizer(wx.HORIZONTAL)		
		btnsizer.AddSpacer((5,5))

		self.bExit = wx.BitmapButton(self, wx.ID_ANY, self.images.pngExit, size=BUTTONDIM)
		self.bExit.SetToolTipString("Exit")
		btnsizer.Add(self.bExit)
		self.Bind(wx.EVT_BUTTON, self.doExit, self.bExit)
		btnsizer.AddSpacer((5,5))

		self.bSlice = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSlice, size=BUTTONDIM)
		self.bSlice.SetToolTipString("Re-Slice file")
		btnsizer.Add(self.bSlice)
		self.Bind(wx.EVT_BUTTON, self.doReslice, self.bSlice)
		self.bSlice.Enable(False)
		
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
		self.bSlice.Enable(exists)
		
	def doExit(self, evt):
		self.closehandler(False)
		
	def doReslice(self, evt):
		self.closehandler(True)

class SliceHistoryCtrl(wx.ListCtrl):	
	def __init__(self, parent, slicehistory, images, basenameonly):
		
		f = wx.Font(8,  wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		dc = wx.ScreenDC()
		dc.SetFont(f)
		fontWidth, fontHeight = dc.GetTextExtent("Xy")
		
		colWidths = [500, 150, 120, 120, 100]
		colTitles = ["File", "Config", "Start Time", "End Time", "Status"]
		
		totwidth = 0;
		for w in colWidths:
			totwidth += w
		
		wx.ListCtrl.__init__(self, parent, wx.ID_ANY, size=(totwidth, fontHeight*(VISIBLEQUEUESIZE+1)),
			style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES|wx.LC_SINGLE_SEL
			)

		self.parent = parent		
		self.slicehistory = slicehistory
		self.basenameonly = basenameonly
		self.selectedItem = None
		self.il = wx.ImageList(16, 16)
		self.il.Add(images.pngSelected)
		self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

		self.SetFont(f)
		for i in range(len(colWidths)):
			self.InsertColumn(i, colTitles[i])
			self.SetColumnWidth(i, colWidths[i])
		
		self.SetItemCount(len(self.slicehistory))
		
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.doListSelect)
		
	def getSelectedFile(self):
		if self.selectedItem is None:
			return None
		
		return self.slicehistory[self.selectedItem][0]
		
	def doListSelect(self, evt):
		x = self.selectedItem
		self.selectedItem = evt.m_itemIndex
		if x is not None:
			self.RefreshItem(x)
			
		fn = self.slicehistory[self.selectedItem][0]
		if os.path.exists(fn):
			exists = True
		else:
			exists = False
		print fn, " exists ", exists
		self.parent.UpdateDlg(exists)
			
	def setBaseNameOnly(self, flag):
		if self.basenameonly == flag:
			return
		
		self.basenameonly = flag
		for i in range(len(self.slicehistory)):
			self.RefreshItem(i)

	def OnGetItemText(self, item, col):
		if col == 0 and self.basenameonly:
			return os.path.basename(self.slicehistory[item][0])
		else:
			return self.slicehistory[item][col]

	def OnGetItemImage(self, item):
		if item == self.selectedItem:
			return 0
		else:
			return -1
	
	def OnGetItemAttr(self, item):
		return None


