import os
import wx
import time

from settings import BUTTONDIM

VISIBLEQUEUESIZE = 21

class ViewSliceHistory(wx.Dialog):
	def __init__(self, parent, settings, images, sliceHistory, allowSlice, ch):
		self.parent = parent
		self.settings = settings
		self.closehandler = ch
		self.allowslice = allowSlice
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Slicing History", size=(800, 804))
		self.SetBackgroundColour("white")
		
		dsizer = wx.BoxSizer(wx.HORIZONTAL)
		dsizer.AddSpacer((10, 10))
		
		self.editDlg = None
		self.images = images

		leftsizer = wx.BoxSizer(wx.VERTICAL)
		leftsizer.AddSpacer((10, 10))
		
		self.lbHistory = SliceHistoryCtrl(self, sliceHistory, self.images,
				self.settings.showslicehistbasename, self.settings.showslicehisthidedupes)
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
		self.cbBase.SetValue(self.settings.showslicehistbasename)

		btnsizer.AddSpacer((30, 10))
		self.cbHideDupes = wx.CheckBox(self, wx.ID_ANY, "Hide Duplicates")
		btnsizer.Add(self.cbHideDupes, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
		self.cbHideDupes.SetToolTipString("Do not show duplicate filenames")
		self.Bind(wx.EVT_CHECKBOX, self.checkHideDupes, self.cbHideDupes)
		self.cbHideDupes.SetValue(self.settings.showslicehisthidedupes)

		leftsizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
		dsizer.Add(leftsizer)
		dsizer.AddSpacer((10,10))

		self.SetSizer(dsizer)  
		dsizer.Fit(self)
		
	def checkBasename(self, evt):
		self.settings.showslicehistbasename = evt.IsChecked()
		self.settings.setModified()
		self.lbHistory.setBaseNameOnly(evt.IsChecked())
		
	def checkHideDupes(self, evt):
		self.settings.showslicehisthidedupes = evt.IsChecked()
		self.settings.setModified()
		self.lbHistory.setHideDupes(evt.IsChecked())

	def getSelectedFile(self):
		return self.lbHistory.getSelectedFile()
	
	def UpdateDlg(self, exists):
		if self.allowslice:
			self.bSlice.Enable(exists)
		else:
			self.bSlice.Enable(False)
			
	def AllowSlicing(self, flag):
		self.allowslice = flag
		self.UpdateDlg(self.lbHistory.doesSelectedExist())
		
	def doExit(self, evt):
		self.closehandler(False)
		
	def doReslice(self, evt):
		self.closehandler(True)

class SliceHistoryCtrl(wx.ListCtrl):	
	def __init__(self, parent, slicehistory, images, basenameonly, hidedupes):
		
		f = wx.Font(8,  wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		dc = wx.ScreenDC()
		dc.SetFont(f)
		fontHeight = dc.GetTextExtent("Xy")[1]
		
		colWidths = [500, 130, 170, 120, 120, 120, 120, 120]
		colTitles = ["File", "Modified", "Config", "Filament", "Temperatures", "Slice Start", "Slice End", "Status"]
		
		totwidth = 20;
		for w in colWidths:
			totwidth += w
			
		self.attrModified = wx.ListItemAttr()
		self.attrModified.SetBackgroundColour(wx.Colour(135, 206, 236))

		self.attrDeleted = wx.ListItemAttr()
		self.attrDeleted.SetBackgroundColour(wx.Colour(255, 153, 153))
		
		wx.ListCtrl.__init__(self, parent, wx.ID_ANY, size=(totwidth, fontHeight*(VISIBLEQUEUESIZE+1)),
			style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES|wx.LC_SINGLE_SEL
			)

		self.parent = parent		
		self.slicehistory = slicehistory[::-1]
		self.basenameonly = basenameonly
		self.hidedupes = hidedupes
		self.selectedItem = None
		self.selectedExists = False
		self.il = wx.ImageList(16, 16)
		self.il.Add(images.pngSelected)
		self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

		self.SetFont(f)
		for i in range(len(colWidths)):
			self.InsertColumn(i, colTitles[i])
			self.SetColumnWidth(i, colWidths[i])
			
		self.fileFlags = []
		self.modTimes = []
		for h in self.slicehistory:
			try:
				mt = time.strftime('%y/%m/%d-%H:%M:%S', time.localtime(os.path.getmtime(h[0])))
				if mt > h[2]:
					self.fileFlags.append("mod")
				else:
					self.fileFlags.append("ok")
				self.modTimes.append(mt)
			except:
				self.modTimes.append("   <file not found>")
				self.fileFlags.append("del")
				
		self.setArraySize()
		
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.doListSelect)

	def setArraySize(self):		
		if self.hidedupes:
			# dups are based on contatenation of file name
			# and slice config (h[0] + h[1])
			mapFn = {}
			mapOrder = []
			mapFnOrder = []
			for i in range(len(self.slicehistory)):
				h = self.slicehistory[i]
				s = h[0] + ":" + h[1]
				if not s in mapOrder:
					mapFn[h[0]] = i
					mapOrder.append(s)
					mapFnOrder.append(h[0])
				
			self.itemIdx = []
			for m in mapFnOrder:
				self.itemIdx.append(mapFn[m])
		else:
			self.itemIdx = range(len(self.slicehistory))
			
		self.SetItemCount(len(self.itemIdx))
		
	def getSelectedFile(self):
		if self.selectedItem is None:
			return None
		
		return self.slicehistory[self.itemIdx[self.selectedItem]][0]
		
	def doListSelect(self, evt):
		x = self.selectedItem
		self.selectedItem = evt.m_itemIndex
		if x is not None:
			self.RefreshItem(x)
			
		fn = self.slicehistory[self.itemIdx[self.selectedItem]][0]
		if os.path.exists(fn):
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
		for i in range(len(self.itemIdx)):
			self.RefreshItem(i)
			
	def setHideDupes(self, flag):
		if self.hidedupes == flag:
			return
		
		self.hidedupes = flag
		self.setArraySize()
		for i in range(len(self.itemIdx)):
			self.RefreshItem(i)

	def OnGetItemText(self, item, col):
		idx = self.itemIdx[item]
		if col == 0:
			if self.basenameonly:
				return os.path.basename(self.slicehistory[idx][0])
			else:
				return self.slicehistory[idx][0]
		elif col == 1:
			return self.modTimes[idx]
		else:
			return str(self.slicehistory[idx][col-1])

	def OnGetItemImage(self, item):
		if item == self.selectedItem:
			return 0
		else:
			return -1
	
	def OnGetItemAttr(self, item):
		idx = self.itemIdx[item]
		if self.fileFlags[idx] == "mod":
			return self.attrModified
		elif self.fileFlags[idx] == "del":
			return self.attrDeleted
		else:
			return None


