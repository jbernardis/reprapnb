#!/bin/env python
import os
import wx
from images import Images
from settings import BUTTONDIM


wildcard = "STL files (*.stl)|*.stl|"  "All files (*.*)|*.*"

VISIBLEQUEUESIZE = 15

class SliceQueue(wx.Dialog):
	def __init__(self, parent, stllist, settings, images):
		self.parent = parent
		self.settings = settings
		wx.Dialog.__init__(self, parent, wx.ID_ANY, "Slicing Queue", size=(800, 804))
		self.SetBackgroundColour("white")
		
		dsizer = wx.BoxSizer(wx.VERTICAL)
		dsizer.AddSpacer((10, 10))
		
		self.images = images
		
		f = wx.Font(12,  wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		dc = wx.ScreenDC()
		dc.SetFont(f)
		fontWidth, fontHeight = dc.GetTextExtent("Xy")

		lbsizer = wx.BoxSizer(wx.HORIZONTAL)
		lbsizer.AddSpacer((10, 10))
		self.lbQueue = wx.ListBox(self, wx.ID_ANY, size=(300, fontHeight*VISIBLEQUEUESIZE+5), choices=stllist, style=wx.LB_EXTENDED)
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
		
		lbsizer.Add(lbbtns)
		lbsizer.AddSpacer((10, 10))
		
		dsizer.Add(lbsizer)
		dsizer.AddSpacer((10,10))
		
		btnsizer = wx.BoxSizer(wx.HORIZONTAL)
		
		self.bSlice = wx.BitmapButton(self, wx.ID_ANY, self.images.pngOk, size=BUTTONDIM)
		self.bSlice.SetToolTipString("Save changes to queue")
		btnsizer.Add(self.bSlice)
		self.Bind(wx.EVT_BUTTON, self.doSlice, self.bSlice)
		self.bSlice.Enable(False)
		
		btnsizer.AddSpacer((20, 20))

		self.bCancel = wx.BitmapButton(self, wx.ID_ANY, self.images.pngCancel, size=BUTTONDIM)
		self.bCancel.SetToolTipString("Exit without saving")
		btnsizer.Add(self.bCancel)
		self.Bind(wx.EVT_BUTTON, self.doCancel, self.bCancel)
		
		dsizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

		self.SetSizer(dsizer)  
		dsizer.Fit(self)
		
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
				self.bSlice.Enable(True)
				self.settings.laststldirectory = os.path.split(paths[0])[0]
				self.settings.setModified()
			for path in paths:
				self.lbQueue.Append(path)

	def doDel(self, evt):
		ls = self.lbQueue.GetSelections()
		for l in ls[::-1]:
			self.lbQueue.Delete(l)
			
		self.bDel.Enable(False)
		self.bUp.Enable(False)
		self.bDown.Enable(False)
		
		if self.lbQueue.GetCount() == 0:
			self.bSlice.Enable(False)
		
	def doUp(self, evt):
		ls = self.lbQueue.GetSelections()
		if len(ls) != 1:
			return
		lx = ls[0]
		s = self.lbQueue.GetString(lx)
		self.lbQueue.Delete(lx)
		self.lbQueue.Insert(s, lx-1)
		self.lbQueue.SetSelection(lx-1)
		self.bUp.Enable((lx-1) != 0)
		self.bDown.Enable(True)
		
	def doDown(self, evt):
		ls = self.lbQueue.GetSelections()
		if len(ls) != 1:
			return
		lx = ls[0]+1
		s = self.lbQueue.GetString(lx)
		self.lbQueue.Delete(lx)
		self.lbQueue.Insert(s, lx-1)
		self.lbQueue.SetSelection(lx)
		self.lbQueue.EnsureVisible(lx+1)
		self.bUp.Enable(True)
		self.bDown.Enable((lx+1) != self.lbQueue.GetCount())
		minFirst = lx+1-VISIBLEQUEUESIZE
		if minFirst >= 0:
			self.lbQueue.SetFirstItem(minFirst)
		
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
					
	def doSlice(self, evt):
		self.EndModal(wx.ID_OK)
		
	def getSliceQueue(self):
		return self.lbQueue.GetItems()
		
	def doCancel(self, evt):
		self.EndModal(wx.ID_CANCEL)
		
