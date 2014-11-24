#!/bin/env python
import os
import wx
from images import Images
from __builtin__ import file
from editgcode import EditGCodeDlg


wildcard = "G Code files (*.gcode)|*.gcode|"  "All files (*.*)|*.*"

BUTTONDIM = (64, 64)
VISIBLEQUEUESIZE = 17

class ManageMacros(wx.Dialog):
	def __init__(self, parent, settings, images, macroOrder, macroFiles, closehandler):
		self.parent = parent
		self.settings = settings
		self.macroOrder = macroOrder
		self.macroFiles = macroFiles
		self.closehandler = closehandler
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Manage Macros", size=(800, 804))
		self.SetBackgroundColour("white")
		
		dsizer = wx.BoxSizer(wx.HORIZONTAL)
		dsizer.AddSpacer((10, 10))
		
		self.editDlg = None
		self.images = images

		leftsizer = wx.BoxSizer(wx.VERTICAL)
		leftsizer.AddSpacer((10, 10))
		
		self.lbQueue = MacroListCtrl(self, macroOrder, macroFiles, self.images)
		leftsizer.Add(self.lbQueue);
		leftsizer.AddSpacer((10, 10))
		
		lbbtns = wx.BoxSizer(wx.VERTICAL)
		lbbtns.AddSpacer((10, 10))
		self.bAdd = wx.BitmapButton(self, wx.ID_ANY, self.images.pngAdd, size=BUTTONDIM)
		self.bAdd.SetToolTipString("Add new macros")
		self.Bind(wx.EVT_BUTTON, self.doAdd, self.bAdd)
		lbbtns.Add(self.bAdd)
		
		self.bDel = wx.BitmapButton(self, wx.ID_ANY, self.images.pngDel, size=BUTTONDIM)
		self.bDel.SetToolTipString("Delete a macro")
		lbbtns.Add(self.bDel)
		self.Bind(wx.EVT_BUTTON, self.doDel, self.bDel)
		self.bDel.Enable(False)
		
		lbbtns.AddSpacer((20, 20))
		
		self.bUp = wx.BitmapButton(self, wx.ID_ANY, self.images.pngUp, size=BUTTONDIM)
		self.bUp.SetToolTipString("Move selected macro up in list")
		lbbtns.Add(self.bUp)
		self.Bind(wx.EVT_BUTTON, self.doUp, self.bUp)
		self.bUp.Enable(False)
		
		self.bDown = wx.BitmapButton(self, wx.ID_ANY, self.images.pngDown, size=BUTTONDIM)
		self.bDown.SetToolTipString("Move selected macro down in list")
		lbbtns.Add(self.bDown)
		self.Bind(wx.EVT_BUTTON, self.doDown, self.bDown)
		self.bDown.Enable(False)
		
		lbbtns.AddSpacer((20, 20))
		
		self.bEditSel = wx.BitmapButton(self, wx.ID_ANY, self.images.pngEdit, size=BUTTONDIM)
		self.bEditSel.SetToolTipString("Edit the selected macro file")
		lbbtns.Add(self.bEditSel)
		self.Bind(wx.EVT_BUTTON, self.doEditSelected, self.bEditSel)
		self.bEditSel.Enable(False)
		
		self.bNewFile = wx.BitmapButton(self, wx.ID_ANY, self.images.pngNewfile, size=BUTTONDIM)
		self.bNewFile.SetToolTipString("New G Code file")
		lbbtns.Add(self.bNewFile)
		self.Bind(wx.EVT_BUTTON, self.doNewFile, self.bNewFile)
		
		
		btnsizer = wx.BoxSizer(wx.HORIZONTAL)
		
		self.bSave = wx.BitmapButton(self, wx.ID_ANY, self.images.pngOk, size=BUTTONDIM)
		self.bSave.SetToolTipString("Save Changes")
		btnsizer.Add(self.bSave)
		self.Bind(wx.EVT_BUTTON, self.doSave, self.bSave)
		self.bSave.Enable(False)
		
		btnsizer.AddSpacer((5,5))

		self.bCancel = wx.BitmapButton(self, wx.ID_ANY, self.images.pngCancel, size=BUTTONDIM)
		self.bCancel.SetToolTipString("Exit without saving")
		btnsizer.Add(self.bCancel)
		self.Bind(wx.EVT_BUTTON, self.doCancel, self.bCancel)

		leftsizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
		dsizer.Add(leftsizer)
		dsizer.AddSpacer((10,10))

		dsizer.Add(lbbtns)

		self.SetSizer(dsizer)  
		dsizer.Fit(self)

		
	def doAdd(self, evt):
		dlg = wx.TextEntryDialog(
				self, 'Enter Macro Name:',
				'Macro Name', '')
		name = None
		if dlg.ShowModal() == wx.ID_OK:
			name = dlg.GetValue()

		dlg.Destroy()
		if name is None:
			return
		
		if name in self.lbQueue.getMacroNames():
			dlg = wx.MessageDialog(self, 'Macro name already in use', 'Error', wx.OK | wx.ICON_INFORMATION)
			dlg.ShowModal()
			dlg.Destroy()
			return

		dlg = wx.FileDialog(
			self, message="Choose a file",
			defaultDir=self.settings.lastmacrodirectory, 
			defaultFile="",
			wildcard=wildcard,
			style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR)

		if dlg.ShowModal() == wx.ID_OK:
			paths = dlg.GetPaths()
			if len(paths) > 0:
				self.bSave.Enable(True)
				mdir = os.path.split(paths[0])[0]
				if mdir != self.settings.lastmacrodirectory:
					self.settings.lastmacrodirectory = mdir
					self.settings.setModified()
					
				path = paths[0]
				if self.lbQueue.addMacro(name, path):
					self.bSave.Enable(True)

	def doDel(self, evt):
		if self.lbQueue.deleteSelected():
			self.bSave.Enable(True)
		
	def doUp(self, evt):
		if self.lbQueue.moveSelectedUp():
			self.bSave.Enable(True)
		
	def doDown(self, evt):
		if self.lbQueue.moveSelectedDown():
			self.bSave.Enable(True)
			
	def doNewFile(self, evt):
		self.bNewFile.Enable(False)
		self.editDlg = EditGCodeDlg(self, [""], "<new macro file>", self.closeNewFile)
		self.editDlg.Show()
	
	def closeNewFile(self, rc):
		if rc:
			data = self.editDlg.getData()

		self.editDlg.Destroy();
		self.bNewFile.Enable(True)
		if not rc:
			return
		
		dlg = wx.FileDialog(
			self, message="Save as ...", defaultDir=self.settings.lastmacrodirectory, 
			defaultFile="", wildcard=wildcard, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
		
		val = dlg.ShowModal()

		if val != wx.ID_OK:
			dlg.Destroy()
			return
		
		path = dlg.GetPath()
		mdir = os.path.split(path)[0]
		if mdir != self.settings.lastmacrodirectory:
			self.settings.lastmacrodirectory = mdir
			self.settings.setModified()
			
		dlg.Destroy()

		ext = os.path.splitext(os.path.basename(path))[1]
		if ext == "":
			path += ".gcode"
			
		fp = file(path, 'w')
		
		for ln in data:
			fp.write("%s\n" % ln.rstrip())
			
		fp.close()
		
	def doEditSelected(self, evt):
		fn = self.lbQueue.getSelectedFile()
		self.bEditSel.Enable(False)
		if not fn:
			return
		
		try:
			data = list(open(fn))
			
		except:
			dlg = wx.MessageDialog(self, "Unable to open Macro file\n" + fn,
					'File Open Error', wx.OK | wx.ICON_INFORMATION)
			dlg.ShowModal()
			dlg.Destroy()
			return

		self.editFileName = fn		
		self.editDlg = EditGCodeDlg(self, data, fn, self.closeEditSelected)
		self.editDlg.Show()
	
	def closeEditSelected(self, rc):
		if rc:
			data = self.editDlg.getData()
			
		self.editDlg.Destroy();
		self.bEditSel.Enable(True)
		
		if not rc:
			return
			
		fp = file(self.editFileName, 'w')
		
		for ln in data:
			fp.write("%s\n" % ln.rstrip())
			
		fp.close()

	def getData(self):
		return self.lbQueue.getData()
		
	def updateDlg(self, nMacros, nSelected):
		if nMacros == 0:
			self.bDel.Enable(False)
			self.bUp.Enable(False)
			self.bDown.Enable(False)
			self.bEditSel.Enable(False)
		else:
			
			if nSelected is None:
				self.bDel.Enable(False)
				self.bUp.Enable(False)
				self.bDown.Enable(False)
				self.bEditSel.Enable(False)
			else:
				self.bEditSel.Enable(True)
				self.bDel.Enable(True)
				if nSelected == 0:
					self.bUp.Enable(False)
				else:
					self.bUp.Enable(True)
					
				if nSelected == nMacros-1:
					self.bDown.Enable(False)
				else:
					self.bDown.Enable(True)
					
	def doSave(self, evt):
		self.closehandler(True)
		
	def doCancel(self, evt):
		if self.bSave.IsEnabled():
			dlg = wx.MessageDialog(self, "Exit without saving changes?",
					'Macro Management', wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION)
			
			rc = dlg.ShowModal()
			dlg.Destroy()

			if rc == wx.ID_YES:
				self.closehandler(False)
		else:
			self.closehandler(False)

class MacroListCtrl(wx.ListCtrl):	
	def __init__(self, parent, macroOrder, macroFiles, images):
		
		f = wx.Font(12,  wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		dc = wx.ScreenDC()
		dc.SetFont(f)
		fontWidth, fontHeight = dc.GetTextExtent("Xy")
		
		wx.ListCtrl.__init__(self, parent, wx.ID_ANY, size=(680, fontHeight*(VISIBLEQUEUESIZE+1)),
			style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES|wx.LC_SINGLE_SEL
			)

		self.parent = parent		
		self.macroOrder = macroOrder
		self.macroFiles = macroFiles
		self.selectedItem = None
		self.il = wx.ImageList(16, 16)
		self.il.Add(images.pngSelected)
		self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

		self.SetFont(f)
		self.InsertColumn(0, "Name")
		self.InsertColumn(1, "File")
		self.SetColumnWidth(0, 175)
		self.SetColumnWidth(1, 500)
		
		self.SetItemCount(len(self.macroOrder))
		
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.doQueueSelect)
		
	def doQueueSelect(self, evt):
		x = self.selectedItem
		self.selectedItem = evt.m_itemIndex
		if x is not None:
			self.RefreshItem(x)
		self.updateParent()
		
	def updateParent(self):
		self.parent.updateDlg(len(self.macroOrder), self.selectedItem)
		
	def addMacro(self, name, filename):
		if name in self.macroOrder:
			return False
		self.macroOrder.append(name)
		self.macroFiles[name] = filename
		self.SetItemCount(len(self.macroOrder))
		self.updateParent()
		return True
	
	def deleteSelected(self):
		if self.selectedItem is None:
			return False
		
		if self.selectedItem < 0 or self.selectedItem >= len(self.macroOrder):
			return False
		
		n = self.macroOrder[self.selectedItem]
		del self.macroOrder[self.selectedItem]
		del self.macroFiles[n]
		self.SetItemCount(len(self.macroOrder))
		self.Select(self.selectedItem, False)
		self.RefreshItems(self.selectedItem, len(self.macroFiles)-1)
		
		self.selectedItem = None
		self.updateParent()
		return True
	
	def moveSelectedUp(self):
		if self.selectedItem is None:
			return False
		
		if self.selectedItem < 1 or self.selectedItem >= len(self.macroOrder):
			return False
		
		n = self.selectedItem
		self.selectedItem -= 1
		
		tn = self.macroOrder[n]
		self.macroOrder[n] = self.macroOrder[self.selectedItem]
		self.macroOrder[self.selectedItem] = tn
		self.RefreshItems(n-1, n)
		self.updateParent()
		return True
	
	def moveSelectedDown(self):
		if self.selectedItem is None:
			return False
		
		if self.selectedItem < 0 or self.selectedItem >= len(self.macroOrder)-1:
			return False
		
		n = self.selectedItem
		self.selectedItem += 1
		
		tn = self.macroOrder[n]
		self.macroOrder[n] = self.macroOrder[self.selectedItem]
		self.macroOrder[self.selectedItem] = tn
		self.RefreshItems(n, n+1)
		self.updateParent()
		return True
	
	def getSelectedFile(self):
		if self.selectedItem is None:
			return None
		
		if self.selectedItem < 0 or self.selectedItem >= len(self.macroOrder):
			return None
		
		return self.macroFiles[self.macroOrder[self.selectedItem]]	
		
	
	def getMacroNames(self):
		return self.macroOrder[:]
	
	def getData(self):
		return self.macroOrder[:], self.macroFiles.copy()

	def OnGetItemText(self, item, col):
		if col == 0:
			return self.macroOrder[item]
		
		elif col == 1:
			k = self.macroOrder[item]
			return self.macroFiles[k]

	def OnGetItemImage(self, item):
		if item == self.selectedItem:
			return 0
		else:
			return -1
	
	def OnGetItemAttr(self, item):
		return None

