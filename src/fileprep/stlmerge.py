import os, thread
import wx
import wx.lib.newevent

import stltool

(MergeEvent, EVT_MERGE_UPDATE) = wx.lib.newevent.NewEvent()
MERGE_RUNNING = 1
MERGE_FINISHED = 2

class MergeThread:
	def __init__(self, win, fn, flist):
		self.win = win
		self.fn = fn
		self.fileList = flist
		self.running = False
		self.cancelled = False

	def Start(self):
		self.running = True
		self.cancelled = False
		thread.start_new_thread(self.Run, ())

	def Stop(self):
		self.cancelled = True

	def IsRunning(self):
		return self.running
	
	def getStlObj(self):
		return self.stlObj

	def Run(self):
		evt = MergeEvent(msg = "Merging...", state = MERGE_RUNNING)
		wx.PostEvent(self.win, evt)
		
		a = amf(cb=self.mergeStlEvent)
		for s in self.fileList:
			a.addStl(s)

		evt = MergeEvent(msg = "Saving AMF output file " + self.fn, state = MERGE_RUNNING)
		wx.PostEvent(self.win, evt)
		try:
			f=open(self.fn,"w")
		except:
			evt = MergeEvent(msg = "Unable to open output file " + self.fn, state = MERGE_FINISHED)
			wx.PostEvent(self.win, evt)
			return
	
		f.write(a.merge())
		f.close()
		
		evt = MergeEvent(msg = "completed", state = MERGE_FINISHED)
		wx.PostEvent(self.win, evt)	
		self.running = False
		
	def mergeStlEvent(self, message):
		evt = MergeEvent(msg = message, state = MERGE_RUNNING)
		wx.PostEvent(self.win, evt)

class volume:
	def __init__(self, fn, startIdx, zzero, xoffset, yoffset, cb=None):
		self.vertexMap = {}
		self.vertexVal = []
		self.vertexIdx = startIdx
		self.triangles = []
		self.name = fn
		self.cb = cb
		
		self.stl = stltool.stl(cb = cb, filename=fn, zZero=zzero, xOffset=xoffset, yOffset=yoffset)
		if cb:
			cb("Processing facets for AMF formatting...")
			
		fx = 0
		for f in self.stl.facets:
			triangle = [None, None, None]
			for px in range(3):
				key = str(f[1][px][0]) + ";" + str(f[1][px][1]) + ";" + str(f[1][px][2])
				if key not in self.vertexMap.keys():
					self.vertexMap[key] = self.vertexIdx
					self.vertexVal.append(key)
					self.vertexIdx += 1
			
				triangle[px] = self.vertexMap[key]
	
			self.triangles.append(triangle)
			if cb:
				fx += 1
				if fx % 10000 == 0:
					cb("Processed %d facets" % fx)
			
	def maxVertexIdx(self):
		return self.vertexIdx
	
	def getName(self):
		return self.name
	
	def getVertices(self):
		result = ""
		vx = 0
		for v in self.vertexVal:
			x, y, z = v.split(";")
			result += "        <vertex>\n"
			result += "          <coordinates>\n"
			result += "            <x>%s</x>\n" % x
			result += "            <y>%s</y>\n" % y
			result += "            <z>%s</z>\n" % z
			result += "          </coordinates>\n"
			result += "        </vertex>\n"	
			if self.cb:
				vx += 1
				if vx % 10000 == 0:
					self.cb("%d vertices processed" % vx)

		if self.cb:
			self.cb("%d total vertices in volume" % vx)
		return result
	
	def getTriangles(self):
		result = ""
		tx = 0
		for t in self.triangles:
			result += "        <triangle>\n"
			result += "          <v1>%s</v1>\n" % t[0]
			result += "          <v2>%s</v2>\n" % t[1]
			result += "          <v3>%s</v3>\n" % t[2]
			result += "        </triangle>\n"
			if self.cb:
				tx += 1
				if tx % 10000 == 0:
					self.cb("%d triangles processed" % tx)
		
		if self.cb:
			self.cb("%d total triangles in volume" % tx)
		return result
			
class amf:
	def __init__(self, cb=None):
		self.volumes = []
		self.vIdx = 0
		self.cb = cb
		
	def addStl(self, fn, zZero=False, xOffset=0, yOffset=0):
		v = volume(fn, self.vIdx, zZero, xOffset, yOffset, cb=self.cb)
		self.vIdx = v.maxVertexIdx()
		self.volumes.append(v)

	def merge(self):
		result = ""
		
		result += "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
		result += "<amf unit=\"millimeter\">\n"
		result += "  <metadata type=\"cad\">stlmerge.py</metadata>\n"
		
		vx = 0
		if self.cb:
			self.cb("Merging volumes...")
		for v in self.volumes:
			if self.cb:
				self.cb("Volume %d" % (vx+1))
			result += "  <material id=\"%d\">\n" % vx
			vx += 1
			result += "    <metadata type=\"Name\">%s</metadata>\n" % v.getName()
			result += "  </material>\n"
		
		result += "  <object id=\"0\">\n"
		result += "    <mesh>\n"
		result += "      <vertices>\n"

		if self.cb:
			self.cb("Merging vertices...")		
		for v in self.volumes:
			result += v.getVertices()
			
		result += "      </vertices>\n"
		
		if self.cb:
			self.cb("Merging triangles...")		
		vx = 0
		for v in self.volumes:
			result += "      <volume materialid=\"%d\">\n" % vx
			result += v.getTriangles()
			result += "      </volume>\n"
			vx += 1

		result += "    </mesh>\n"
		result += "  </object>\n"
		result += "</amf>"
		if self.cb:
			self.cb("Merge completed")
		return result


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
		self.Bind(EVT_MERGE_UPDATE, self.mergeUpdate)
		
	def onAddStl(self, event):
		dlg = wx.FileDialog(
			self, message="Choose an STL file",
			defaultDir=self.settings.laststldirectory, 
			defaultFile="",
			wildcard="STL (*.stl)|*.stl;*.STL",
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
			wildcard = "AMF XML (*.amf.xml)|*.amf.xml;*.AMF.XML"
			ext = ".amf.xml"
		else:
			wildcard = "AMF (*.amf)|*.amf;*.AMF"
			ext = ".amf"
			
		dlg = wx.FileDialog(
			self, message="Save as ...", defaultDir=self.settings.laststldirectory, 
			defaultFile=fn+ext, wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
			)
		
		val = dlg.ShowModal()

		if val != wx.ID_OK:
			dlg.Destroy()
			return
		
		amfFn = dlg.GetPath()
		dlg.Destroy()

		self.logger.LogMessage("Beginning merge")
				
		self.mergeThread = MergeThread(self, amfFn, self.fileList)
		self.mergeThread.Start()
	
	def mergeUpdate(self, evt):
		if evt.state == MERGE_RUNNING:
			if evt.msg is not None:
				self.logger.LogMessage(evt.msg)
				
		elif evt.state == MERGE_FINISHED:
			if evt.msg is not None:
				self.logger.LogMessage(evt.msg)

			self.continueMerge()

	def continueMerge(self):		
		dlg = wx.MessageDialog(self, "Merge Completed",
					'Merged', wx.OK | wx.ICON_INFORMATION)
			
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
