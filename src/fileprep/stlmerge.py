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

		btnSizer = wx.BoxSizer(wx.HORIZONTAL)

		self.bAddStl = wx.Button(self, wx.ID_ANY, "Add STL", size=BUTTONDIM)
		self.bAddStl.SetToolTipString("Add an STL file to the merge")
		self.Bind(wx.EVT_BUTTON, self.onAddStl, self.bAddStl)
		btnSizer.Add(self.bAddStl)

		self.bDelStl = wx.Button(self, wx.ID_ANY, "Del STL", size=BUTTONDIM)
		self.bDelStl.SetToolTipString("Remove an STL file from the merge")
		self.Bind(wx.EVT_BUTTON, self.onDelStl, self.bDelStl)
		btnSizer.Add(self.bDelStl)

		self.bMerge = wx.Button(self, wx.ID_ANY, "Merge Files", size=BUTTONDIM)
		self.bMerge.SetToolTipString("Execute the merge")
		self.Bind(wx.EVT_BUTTON, self.onMerge, self.bMerge)
		btnSizer.Add(self.bMerge)

		self.bCancel = wx.Button(self, wx.ID_ANY, "Cancel", size=BUTTONDIM)
		self.bCancel.SetToolTipString("Exit without merging")
		self.Bind(wx.EVT_BUTTON, self.onCancel, self.bCancel)
		btnSizer.Add(self.bCancel)
		
		self.sizer.Add(btnSizer)

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
				
		dlg.Destroy()
		
	def onDelStl(self, event):
		pass
		
	def onMerge(self, event):
		pass
		
	def onCancel(self, event):
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
		
