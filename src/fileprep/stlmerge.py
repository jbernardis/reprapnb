import os
import wx

BUTTONDIM = (48, 48)

class StlMergeDlg(wx.Dialog):
	def __init__(self, parent):
		self.parent = parent
		self.settings = self.parent.settings
		self.app = parent.app
		self.logger = parent.logger
		self.fileList = []
		
		pre = wx.PreDialog()
		pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
		pos = wx.DefaultPosition
		sz = (420, 280)
		style = wx.DEFAULT_DIALOG_STYLE
		pre.Create(self.app, wx.ID_ANY, "STL File Merge", pos, sz, style)
		self.PostCreate(pre)
		
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.sizer.AddSpacer((20, 20))

		btnSizer1 = wx.BoxSizer(wx.HORIZONTAL)
		btnSizer2 = wx.BoxSizer(wx.HORIZONTAL)
		
		btnSizer1.AddSpacer((20, 20))

		self.bAddStl = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngAdd, size=BUTTONDIM)
		self.bAddStl.SetToolTipString("Add an STL file to the merge")
		self.Bind(wx.EVT_BUTTON, self.onAddStl, self.bAddStl)
		btnSizer1.Add(self.bAddStl)

		btnSizer1.AddSpacer((20, 20))
		
		self.bDelStl = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngDel, size=BUTTONDIM)
		self.bDelStl.SetToolTipString("Remove an STL file from the merge")
		self.Bind(wx.EVT_BUTTON, self.onDelStl, self.bDelStl)
		self.bDelStl.Enable(False)
		btnSizer1.Add(self.bDelStl)
		
		self.sizer.Add(btnSizer1)

		self.lb = wx.ListBox(self, wx.ID_ANY, (-1, -1), (400, 120), [], wx.LB_SINGLE)
		self.sizer.Add(self.lb, 0, wx.ALL, 10)

		btnSizer2.AddSpacer((20, 20))

		self.bMerge = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngMerge, size=BUTTONDIM)
		self.bMerge.SetToolTipString("Execute the merge")
		self.Bind(wx.EVT_BUTTON, self.onMerge, self.bMerge)
		self.bMerge.Enable(False)
		btnSizer2.Add(self.bMerge)

		self.cbXML = wx.CheckBox(self, wx.ID_ANY, "Add .XML file extension")
		self.cbXML.SetToolTipString("Add .XML to the file extension (req'd by Slic3r)")
		self.cbXML.SetValue(False)
		self.cbXML.Enable(False)
		btnSizer2.Add(self.cbXML, flag=wx.EXPAND | wx.ALL, border=10)

		btnSizer2.AddSpacer((90, 20))

		self.bCancel = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngCancel, size=BUTTONDIM)
		self.bCancel.SetToolTipString("Exit without merging")
		self.Bind(wx.EVT_BUTTON, self.onCancel, self.bCancel)
		btnSizer2.Add(self.bCancel)
		
		self.sizer.Add(btnSizer2)

		self.Bind(wx.EVT_CLOSE, self.onCancel)

		self.SetSizer(self.sizer)
		self.SetAutoLayout(True)
		
	def onAddStl(self, event):
		dlg = wx.FileDialog(
			self, message="Choose an STL file",
			defaultDir=self.settings.laststldirectory, 
			defaultFile="",
			wildcard="STL (*.stl)|*.[sS][tT][lL]",
			style=wx.FD_OPEN | wx.FD_CHANGE_DIR
			)
		
		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()
			self.settings.laststldirectory = os.path.dirname(path)
			self.settings.setModified()
			self.fileList.append(path)
			self.lb.Append(path)
			self.lb.SetSelection(len(self.fileList)-1)
				
		dlg.Destroy()
		if len(self.fileList) > 0:
			self.bDelStl.Enable(True)
		if len(self.fileList) > 1:
			self.bMerge.Enable(True)
			self.cbXML.Enable(True)
		
	def onDelStl(self, event):
		n = self.lb.GetSelection()
		if n != -1:
			self.lb.Delete(n)
			del(self.fileList[n])
			
		if len(self.fileList) <= 0:
			self.bDelStl.Enable(False)
			self.lb.Clear()
		else:
			if n >= len(self.fileList):
				n = len(self.fileList)-1

			self.lb.SetSelection(n)
			if len(self.fileList) <= 1:
				self.bMerge.Enable(False)
				self.cbXML.Enable(False)
			
	def onMerge(self, event):
		fn = os.path.splitext(self.fileList[0])[0]
		if self.cbXML.IsChecked():
			wildcard = "AMF XML (*.amf.xml)|*.[aA][mM][fF].[xX][mM][lL]"
			ext = ".amf.xml"
		else:
			wildcard = "AMF (*.amf)|*.[aA][mM][fF]"
			ext = ".amf"
			
		dlg = wx.FileDialog(
			self, message="Save as ...", defaultDir=self.settings.laststldirectory, 
			defaultFile=fn+ext, wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
			)
		
		val = dlg.ShowModal()

		if val != wx.ID_OK:
			dlg.Destroy()
			return
		
		path = dlg.GetPath()
		dlg.Destroy()
		
		# do merge here
		print self.fileList, " ==> ", path
		

		dlg = wx.MessageDialog(self, "Merge Completed",
					'Merges', wx.OK | wx.ICON_INFORMATION)
			
		dlg.ShowModal()
		self.parent.dlgMergeClosed()
		self.Destroy()
		
	def onCancel(self, event):
		if len(self.fileList) > 0:
			dlg = wx.MessageDialog(self, "Are you sure you want to exit without merging?",
					'Cancel Merge', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_INFORMATION)
			
			rc = dlg.ShowModal()
			dlg.Destroy()

			if rc != wx.ID_YES:
				return

		self.parent.dlgMergeClosed()
		self.Destroy()
