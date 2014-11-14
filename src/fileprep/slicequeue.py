#!/bin/env python
import os
import wx
from settings import BUTTONDIM
from stlview import StlViewer


wildcard = "STL (*.stl)|*.stl;*STL|AMF (*.amf.xml, *.amf)|*.amf.xml;*.AMF.XML;*.amf;*.AMF|All files (*.*)|*.*"

VISIBLEQUEUESIZE = 15

class SliceQueue(wx.Dialog):
	def __init__(self, parent, stllist, settings, images):
		self.parent = parent
		self.settings = settings
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Slicing Queue", size=(800, 804))
		self.SetBackgroundColour("white")
		
		self.stllist = stllist[:]
		self.stldisplay = [self.setDisplayName(x) for x in self.stllist]

		dsizer = wx.BoxSizer(wx.VERTICAL)
		dsizer.AddSpacer((10, 10))
		
		self.images = images
		
		f = wx.Font(12,  wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		dc = wx.ScreenDC()
		dc.SetFont(f)
		fontWidth, fontHeight = dc.GetTextExtent("X")
		
		lbsizer = wx.BoxSizer(wx.HORIZONTAL)
		lbsizer.AddSpacer((10, 10))
		self.lbQueue = wx.ListBox(self, wx.ID_ANY, size=(fontWidth * 90, fontHeight*VISIBLEQUEUESIZE+5), choices=self.stldisplay, style=wx.LB_EXTENDED)
		self.Bind(wx.EVT_LISTBOX, self.doQueueSelect, self.lbQueue)
		lbsizer.Add(self.lbQueue);
		lbsizer.AddSpacer((10, 10))
		self.lbQueue.SetFont(f)
		
		lbbtns = wx.BoxSizer(wx.VERTICAL)
		lbbtns.AddSpacer((10, 10))
		self.bAdd = wx.BitmapButton(self, wx.ID_ANY, self.images.pngAdd, size=BUTTONDIM)
		self.bAdd.SetToolTipString("Add new files to the slicing queue")
		self.Bind(wx.EVT_BUTTON, self.doAdd, self.bAdd)
		lbbtns.Add(self.bAdd)
		
		self.bDel = wx.BitmapButton(self, wx.ID_ANY, self.images.pngDel, size=BUTTONDIM)
		self.bDel.SetToolTipString("Remove selected file(s) from the queue")
		lbbtns.Add(self.bDel)
		self.Bind(wx.EVT_BUTTON, self.doDel, self.bDel)
		self.bDel.Enable(False)
		
		lbbtns.AddSpacer((20, 20))
		
		self.bUp = wx.BitmapButton(self, wx.ID_ANY, self.images.pngUp, size=BUTTONDIM)
		self.bUp.SetToolTipString("Move selected item up in queue")
		lbbtns.Add(self.bUp)
		self.Bind(wx.EVT_BUTTON, self.doUp, self.bUp)
		self.bUp.Enable(False)
		
		self.bDown = wx.BitmapButton(self, wx.ID_ANY, self.images.pngDown, size=BUTTONDIM)
		self.bDown.SetToolTipString("Move selected item down in queue")
		lbbtns.Add(self.bDown)
		self.Bind(wx.EVT_BUTTON, self.doDown, self.bDown)
		self.bDown.Enable(False)
		
		lbbtns.AddSpacer((20, 20))
		
		self.bView = wx.BitmapButton(self, wx.ID_ANY, self.images.pngView, size=BUTTONDIM)
		self.bView.SetToolTipString("View STL/AMF file")
		lbbtns.Add(self.bView)
		self.Bind(wx.EVT_BUTTON, self.stlView, self.bView)
		self.bView.Enable(True)
		
		lbsizer.Add(lbbtns)
		lbsizer.AddSpacer((10, 10))
		
		dsizer.Add(lbsizer)
		dsizer.AddSpacer((10,10))
		
		btnsizer = wx.BoxSizer(wx.HORIZONTAL)
		
		self.bSave = wx.BitmapButton(self, wx.ID_ANY, self.images.pngOk, size=BUTTONDIM)
		self.bSave.SetToolTipString("Save changes to queue")
		btnsizer.Add(self.bSave)
		self.Bind(wx.EVT_BUTTON, self.doSave, self.bSave)
		self.bSave.Enable(False)
		
		btnsizer.AddSpacer((20, 20))

		self.bCancel = wx.BitmapButton(self, wx.ID_ANY, self.images.pngCancel, size=BUTTONDIM)
		self.bCancel.SetToolTipString("Exit without saving")
		btnsizer.Add(self.bCancel)
		self.Bind(wx.EVT_BUTTON, self.doCancel, self.bCancel)
		
		btnsizer.AddSpacer((20, 20))
		
		self.cbBasename = wx.CheckBox(self, wx.ID_ANY, "Show basename only")
		self.cbBasename.SetToolTipString("Show only the basename of files")
		self.Bind(wx.EVT_CHECKBOX, self.checkBasename, self.cbBasename)
		self.cbBasename.SetValue(self.settings.showstlbasename)
		btnsizer.Add(self.cbBasename)
		
		dsizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

		self.SetSizer(dsizer)  
		dsizer.Fit(self)
			
	def setDisplayName(self, nm):
		if self.settings.showstlbasename:
			return os.path.basename(nm)
		else:
			return nm
	
	def checkBasename(self, evt):
		self.settings.showstlbasename = evt.IsChecked()
		self.settings.setModified()
		self.stldisplay = [self.setDisplayName(x) for x in self.stllist]
		self.lbQueue.SetItems(self.stldisplay)

		
	def doAdd(self, evt):
		dlg = wx.FileDialog(
						self, message="Choose a file",
						defaultDir=self.settings.laststldirectory, 
						defaultFile="",
						wildcard=wildcard,
						style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR)

		if dlg.ShowModal() == wx.ID_OK:
			paths = dlg.GetPaths()
			if len(paths) > 0:
				self.bSave.Enable(True)
				nd = os.path.split(paths[0])[0]
				if nd != self.settings.laststldirectory:
					self.settings.laststldirectory = nd
					self.settings.setModified()
				
			dups = []
			for path in paths:
				if path in self.stllist:
					dups.append(path)
				else:
					self.lbQueue.Append(self.setDisplayName(path))
					self.stllist.append(path)
					
			if len(dups) > 0:
				msg = "Duplicate files removed from queue:\n  " + ",\n  ".join(dups)
				dlg = wx.MessageDialog(self, msg, 'Duplicate files!', wx.OK | wx.ICON_INFORMATION)
				
				dlg.ShowModal()
				dlg.Destroy()
				
							
			if len(dups) != len(paths):
				self.bSave.Enable(True)

	def doDel(self, evt):
		ls = self.lbQueue.GetSelections()
		for l in ls[::-1]:
			self.lbQueue.Delete(l)
			del self.stllist[l]
			
		self.bDel.Enable(False)
		self.bUp.Enable(False)
		self.bDown.Enable(False)
		self.bSave.Enable(True)
		
	def doUp(self, evt):
		ls = self.lbQueue.GetSelections()
		if len(ls) != 1:
			return
		lx = ls[0]
		s = self.lbQueue.GetString(lx)
		self.lbQueue.Delete(lx)
		self.lbQueue.Insert(s, lx-1)
		self.lbQueue.SetSelection(lx-1)
		self.lbQueue.EnsureVisible(lx-1)
		
		sv = self.stllist[lx]
		del self.stllist[lx]
		self.stllist = self.stllist[:lx-1] + [sv] + self.stllist[lx-1:]
		
		self.bUp.Enable((lx-1) != 0)
		self.bDown.Enable(True)
		self.bSave.Enable(True)
		
	def doDown(self, evt):
		ls = self.lbQueue.GetSelections()
		if len(ls) != 1:
			return

		lx = ls[0]
		s = self.lbQueue.GetString(lx+1)
		self.lbQueue.Delete(lx+1)
		self.lbQueue.Insert(s, lx)
		
		sv = self.stllist[lx]
		del self.stllist[lx]
		self.stllist = self.stllist[:lx+1] + [sv] + self.stllist[lx+1:]

		self.lbQueue.SetSelection(lx+1)
		self.lbQueue.EnsureVisible(lx+1)
		self.bUp.Enable(True)
		self.bDown.Enable((lx+2) != self.lbQueue.GetCount())
		self.bSave.Enable(True)
		
	def doQueueSelect(self, evt):
		ls = self.lbQueue.GetSelections()
		if len(ls) == 0:
			self.bDel.Enable(False)
			self.bUp.Enable(False)
			self.bDown.Enable(False)
		else:
			self.bDel.Enable(True)
			
			if len(ls) != 1:
				self.bUp.Enable(False)
				self.bDown.Enable(False)
			else:
				if ls[0] == 0:
					self.bUp.Enable(False)
				else:
					self.bUp.Enable(True)
					
				if ls[0] == self.lbQueue.GetCount()-1:
					self.bDown.Enable(False)
				else:
					self.bDown.Enable(True)
		
	def stlView(self, evt):
		self.dlgView = StlViewer(self)
		self.dlgView.CenterOnScreen()
		self.dlgView.Show()
		
	def stlViewExit(self):
		self.dlgView = None
					
	def doSave(self, evt):
		self.EndModal(wx.ID_OK)
		
	def getSliceQueue(self):
		return self.stllist
		
	def doCancel(self, evt):
		if self.bSave.IsEnabled():
			dlg = wx.MessageDialog(self, "Exit without saving changes?",
					'Slicing Queue', wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION)
			
			rc = dlg.ShowModal()
			dlg.Destroy()

			if rc == wx.ID_YES:
				self.EndModal(wx.ID_CANCEL)
		else:
			self.EndModal(wx.ID_CANCEL)

		
