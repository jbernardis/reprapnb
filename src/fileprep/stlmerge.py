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
		sz = (400, 400)
		style = wx.DEFAULT_DIALOG_STYLE
		pre.Create(self.app, wx.ID_ANY, "STL File Merge", pos, sz, style)
		self.PostCreate(pre)
		
		self.sizer = wx.BoxSizer(wx.VERTICAL)

		btnSizer1 = wx.BoxSizer(wx.HORIZONTAL)
		btnSizer2 = wx.BoxSizer(wx.HORIZONTAL)

		self.bAddStl = wx.Button(self, wx.ID_ANY, "Add STL", size=BUTTONDIM)
		self.bAddStl.SetToolTipString("Add an STL file to the merge")
		self.Bind(wx.EVT_BUTTON, self.onAddStl, self.bAddStl)
		btnSizer1.Add(self.bAddStl)

		self.bDelStl = wx.Button(self, wx.ID_ANY, "Del STL", size=BUTTONDIM)
		self.bDelStl.SetToolTipString("Remove an STL file from the merge")
		self.Bind(wx.EVT_BUTTON, self.onDelStl, self.bDelStl)
		self.bDelStl.Enable(False)
		btnSizer1.Add(self.bDelStl)
		
		self.sizer.Add(btnSizer1)

		self.lb = wx.ListBox(self, wx.ID_ANY, size=(90, 120), [], wx.LB_SINGLE)
		self.Bind(wx.EVT_LISTBOX, self.EvtListBox, self.lb)
		self.sizer.Add(self.lb, 0, wx.ALL, 10)

		self.bMerge = wx.Button(self, wx.ID_ANY, "Merge Files", size=BUTTONDIM)
		self.bMerge.SetToolTipString("Execute the merge")
		self.Bind(wx.EVT_BUTTON, self.onMerge, self.bMerge)
		self.bMerge.Enable(False)
		btnSizer2.Add(self.bMerge)

		self.bCancel = wx.Button(self, wx.ID_ANY, "Cancel", size=BUTTONDIM)
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
			wildcard="STL (*.stl)|*.stl*.STL",
			style=wx.FD_OPEN | wx.FD_CHANGE_DIR
			)
		
		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()
			self.settings.laststldirectory = os.path.dirname(path)
			self.settings.setModified()
			self.fileList.append(path)
			self.lb.Append(path)
				
		dlg.Destroy()
		if len(self.fileList) > 0:
			self.bDelStl.Enable(True)
		if len(self.fileList) > 1:
			self.bMerge.Enable(True)
		
	def onDelStl(self, event):
		print "selection = ", self.lb.GetSelection()
		if len(self.fileList) <= 0:
			self.bDelStl.Enable(False)
		if len(self.fileList) <= 1:
			self.bMerge.Enable(False)
		
	def onMerge(self, event):
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
		
			
		
	def onSaveProf(self, event):
		dlg = wx.FileDialog(
			self, message="Save merged file as...",
			defaultDir=os.getcwd(), 
			defaultFile="",
			wildcard="AMF (*.amf)|*.amf|AMF XML (*.amf.xml)|*.amf.xml",
			style=wx.FD_SAVE | wx.FD_CHANGE_DIR | wx.FD_OVERWRITE_PROMPT
			)
		
		v = dlg.ShowModal()
		if v != wx.ID_OK:
			dlg.Destroy()
			return
		
		path = dlg.GetPath()
		dlg.Destroy()
		
		ext = os.path.splitext(os.path.basename(path))[1]
		if ext == "":
			path += ".amf"
		
