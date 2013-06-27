import os
import sys, inspect
import tempfile, random

cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
if cmd_folder not in sys.path:
	sys.path.insert(0, cmd_folder)

import wx
	
from stlframe import StlFrame
import stltool

wildcard = "STL (*.stl)|*.stl"


TITLETEXT = "Plater"
BUTTONDIM = (64,64)
BUTTONDIMWIDE = (96,64)

class Plater(wx.Panel):
	def __init__(self, parent, app):
		self.parent = parent
		self.app = app
		self.appsettings = app.settings
		self.printersettings = self.app.printersettings
		self.settings = app.settings.plater
		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(400, 250))
		self.SetBackgroundColour("white")

		self.sizerMain = wx.GridBagSizer()
		
		self.objNumber = 1
		
		self.modified = False
		
		self.lbMap = []
		self.lbModified = []
		self.lbSelection = None
		self.sizerMain = wx.GridBagSizer()
		self.sizerMain.AddSpacer((20,20), pos=(0,0))

		
		self.stlFrame =  StlFrame(self, scale=self.settings.stlscale, buildarea=self.printersettings.settings['buildarea'])
		self.sizerMain.Add(self.stlFrame, pos=(1, 1), span=(6,1))

		self.sizerBtn = wx.BoxSizer(wx.HORIZONTAL)
		
		path = os.path.join(self.settings.cmdfolder, "images/add.png")	
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		self.bAdd = wx.BitmapButton(self, wx.ID_ANY, png, size=BUTTONDIM)
		self.bAdd.SetToolTipString("Add an STL file to the plate")
		self.sizerBtn.Add(self.bAdd)
		self.Bind(wx.EVT_BUTTON, self.doAdd, self.bAdd)
		
		path = os.path.join(self.settings.cmdfolder, "images/clone.png")	
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		self.bClone = wx.BitmapButton(self, wx.ID_ANY, png, size=BUTTONDIM)
		self.bClone.SetToolTipString("Create a copy of the currently selected object")
		self.sizerBtn.Add(self.bClone)
		self.Bind(wx.EVT_BUTTON, self.doClone, self.bClone)
		self.bClone.Enable(False)

		path = os.path.join(self.settings.cmdfolder, "images/arrange.png")	
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		self.bArrange = wx.BitmapButton(self, wx.ID_ANY, png, size=BUTTONDIM)
		self.bArrange.SetToolTipString("Arrange objects so they fit on the plate")
		self.sizerBtn.Add(self.bArrange)
		self.Bind(wx.EVT_BUTTON, self.doArrange, self.bArrange)
		self.bArrange.Enable(False)		

		self.sizerBtn.AddSpacer((20, 20))
				
		self.cbAutoArrange = wx.CheckBox(self, wx.ID_ANY, "Auto Arrange")
		self.cbAutoArrange.SetToolTipString("Automatically arrange the plate when adding or cloning")
		self.Bind(wx.EVT_CHECKBOX, self.checkAutoArrange, self.cbAutoArrange)
		self.cbAutoArrange.SetValue(self.settings.autoarrange)
		self.sizerBtn.Add(self.cbAutoArrange, 1, wx.EXPAND)

		self.sizerBtn.AddSpacer((20, 20))
				
		path = os.path.join(self.settings.cmdfolder, "images/del.png")	
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		self.bDel = wx.BitmapButton(self, wx.ID_ANY, png, size=BUTTONDIM)
		self.bDel.SetToolTipString("Delete the currently selected object from the plate")
		self.sizerBtn.Add(self.bDel)
		self.Bind(wx.EVT_BUTTON, self.doDelete, self.bDel)
		self.bDel.Enable(False)

		path = os.path.join(self.settings.cmdfolder, "images/delall.png")	
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		self.bDelAll = wx.BitmapButton(self, wx.ID_ANY, png, size=BUTTONDIM)
		self.bDelAll.SetToolTipString("Delete all objects from the plate")
		self.sizerBtn.Add(self.bDelAll)
		self.Bind(wx.EVT_BUTTON, self.doDelAll, self.bDelAll)
		self.bDelAll.Enable(False)

		self.sizerMain.AddSpacer((20,20), pos=(1,3))		
		self.sizerMain.Add(self.sizerBtn, pos=(1,4))
		
		t = wx.StaticText(self, wx.ID_ANY, "STL File List:")
		f = wx.Font(14, wx.SWISS, wx.NORMAL, wx.NORMAL)
		t.SetFont(f)
		self.sizerMain.Add(t, pos=(3,4))
		
		self.lb = wx.ListBox(self, wx.ID_ANY, size=(400, 200))
		self.Bind(wx.EVT_LISTBOX, self.onLbClick, self.lb)
		self.sizerMain.AddSpacer((20,20), pos=(2,4))		
		self.sizerMain.Add(self.lb, pos=(4,4))

		self.sizerBtn2 = wx.BoxSizer(wx.HORIZONTAL)
		
		path = os.path.join(self.settings.cmdfolder, "images/rotCW.png")	
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		self.bRotate45CW = wx.BitmapButton(self, wx.ID_ANY, png, size=BUTTONDIM)
		self.bRotate45CW.SetToolTipString("Rotate the selected object 45 degrees Clockwise")
		self.sizerBtn2.Add(self.bRotate45CW)
		self.Bind(wx.EVT_BUTTON, self.doRotate45CW, self.bRotate45CW)
		self.bRotate45CW.Enable(False)
		
		path = os.path.join(self.settings.cmdfolder, "images/rotCCW.png")	
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		self.bRotate45CCW = wx.BitmapButton(self, wx.ID_ANY, png, size=BUTTONDIM)
		self.bRotate45CCW.SetToolTipString("Rotate the selected object 45 degrees Counter-Clockwise")
		self.sizerBtn2.Add(self.bRotate45CCW)
		self.Bind(wx.EVT_BUTTON, self.doRotate45CCW, self.bRotate45CCW)
		self.bRotate45CCW.Enable(False)
		
		path = os.path.join(self.settings.cmdfolder, "images/rotate.png")	
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		self.bRotate = wx.BitmapButton(self, wx.ID_ANY, png, size=BUTTONDIM)
		self.bRotate.SetToolTipString("Rotate the selected object a specified amount")
		self.sizerBtn2.Add(self.bRotate)
		self.Bind(wx.EVT_BUTTON, self.doRotate, self.bRotate)
		self.bRotate.Enable(False)
		
		path = os.path.join(self.settings.cmdfolder, "images/scale.png")	
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		self.bScale = wx.BitmapButton(self, wx.ID_ANY, png, size=BUTTONDIM)
		self.bScale.SetToolTipString("Scale the selected object by specified percent")
		self.sizerBtn2.Add(self.bScale)
		self.Bind(wx.EVT_BUTTON, self.doScale, self.bScale)
		self.bScale.Enable(False)
		
		self.sizerBtn2.AddSpacer((20, 20))
		
		path = os.path.join(self.settings.cmdfolder, "images/export.png")	
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		self.bExport = wx.BitmapButton(self, wx.ID_ANY, png, size=BUTTONDIMWIDE)
		self.bExport.SetToolTipString("Export the plate to a single STL file")
		self.sizerBtn2.Add(self.bExport)
		self.Bind(wx.EVT_BUTTON, self.doExport, self.bExport)
		self.bExport.Enable(False)
		
		path = os.path.join(self.settings.cmdfolder, "images/export2prep.png")	
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		self.bExport2Prep = wx.BitmapButton(self, wx.ID_ANY, png, size=BUTTONDIMWIDE)
		self.bExport2Prep.SetToolTipString("Export the plate to the file preparation tab")
		self.sizerBtn2.Add(self.bExport2Prep)
		self.Bind(wx.EVT_BUTTON, self.doExport2Prep, self.bExport2Prep)
		self.bExport2Prep.Enable(False)

		self.sizerMain.AddSpacer((20,20), pos=(5,4))		
		self.sizerMain.Add(self.sizerBtn2, pos=(6,4))
		
		self.SetSizer(self.sizerMain)
		
	def enableButtons(self, flag):
		self.bDel.Enable(flag)
		self.bDelAll.Enable(flag)
		self.bExport.Enable(flag)
		self.bExport2Prep.Enable(flag)
		self.bArrange.Enable(flag)
		self.bClone.Enable(flag)
		self.bRotate45CW.Enable(flag)
		self.bRotate45CCW.Enable(flag)
		self.bRotate.Enable(flag)
		self.bScale.Enable(flag)

	def checkModified(self, message='Exit without saving changes?'):
		if self.modified:
			dlg = wx.MessageDialog(self, message,
					'Plater', wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION)
			
			rc = dlg.ShowModal()
			dlg.Destroy()

			if rc != wx.ID_YES:
				return True

		return False
	
	def doRotate45CW(self, evt):
		if self.lbSelection is None:
			return
		
		self.lbModified[self.lbSelection] = True
		self.setModified()
		
		self.stlFrame.doRotate(-45)
		
	def doRotate45CCW(self, evt):
		if self.lbSelection is None:
			return
		
		self.lbModified[self.lbSelection] = True
		self.setModified()
		
		self.stlFrame.doRotate(45)
		
	def doRotate(self, evt):
		if self.lbSelection is None:
			return
		
		dlg = wx.TextEntryDialog(
				self, 'Enter number of degrees (0-360)',
				'Degrees of rotation', '0')
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		
		v = dlg.GetValue().strip()
		dlg.Destroy()
		
		try:
			angle = int(v)
		except:
			angle = None

		if angle is not None:
			if angle >= 0 and angle <= 360:
				self.lbModified[self.lbSelection] = True
				self.setModified()
				self.stlFrame.doRotate(angle)
				return

		dlg = wx.MessageDialog(self, 'Invalid value for angle (0-360)',
							   'Invalid value',
							   wx.OK | wx.ICON_INFORMATION
							   )
		dlg.ShowModal()
		dlg.Destroy()
			
	def doScale(self, evt):
		if self.lbSelection is None:
			return
		
		dlg = wx.TextEntryDialog(
				self, 'Enter scaling factor as a percent',
				'Scale percent', '0')
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		
		v = dlg.GetValue().strip()
		dlg.Destroy()
		
		try:
			factor = float(v)/100.0
		except:
			factor = None

		if factor is not None:
			self.lbModified[self.lbSelection] = True
			self.setModified()
			self.stlFrame.scaleStl(factor)
			return

		dlg = wx.MessageDialog(self, 'Invalid value for scaling percent',
							   'Invalid value',
							   wx.OK | wx.ICON_INFORMATION
							   )
		dlg.ShowModal()
		dlg.Destroy()
				
	def onClose(self, evt):
		if self.checkModified():
			return False
		
		return True
	
	def onLbClick(self, evt):
		self.lbSelection = self.lb.GetSelection()
		self.stlFrame.setSelection(self.lbMap[self.lbSelection][1])
		
	def checkAutoArrange(self, evt):
		self.settings.autoarrange = evt.IsChecked()
		self.settings.setModified()
		
	def onFrameClick(self, itemId):
		for i in range(len(self.lbMap)):
			if itemId == self.lbMap[i][1]:
				self.lbSelection = i
				self.lb.SetSelection(i)
				return

		self.lbSelection = None
	
	def doAdd(self, evt):
		dlg = wx.FileDialog(
			self, message="Choose an STL file",
			defaultDir=self.settings.lastdirectory, 
			defaultFile="",
			wildcard=wildcard,
			style=wx.FD_OPEN | wx.FD_CHANGE_DIR
			)
		
		if dlg.ShowModal() == wx.ID_OK:
			paths = dlg.GetPaths()
			if len(paths) == 1:
				self.loadFile(paths[0])

		dlg.Destroy()
		
	def loadFile(self, fn):
		if len(self.lbMap) != 0:
			self.setModified()
		self.filename = fn
		self.settings.lastdirectory = os.path.dirname(fn)
		self.settings.setModified()
			
		name = "OBJECT%03d" % self.objNumber
		self.objNumber += 1
		stlFile = stltool.stl(filename=fn, name=name)
		self.stlFrame.addStl(stlFile, highlight=True)
		itemId = self.stlFrame.getSelection()
		self.enableButtons(True)

		self.lbMap.append([fn, itemId])
		self.lbModified.append(False)
		self.lbSelection = len(self.lbMap)-1
		self.lb.Append(fn)
		self.lb.SetSelection(self.lbSelection)
		
		if self.settings.autoarrange:
			self.doArrange(None)
			
	def doClone(self, evt):
		stlObj = self.stlFrame.getSelectedStl()
		if stlObj is None:
			return
		
		if self.lbSelection is None:
			return
		
		self.setModified()
		
		fn = self.lbMap[self.lbSelection][0]
		name = "OBJECT%03d" % self.objNumber
		self.objNumber += 1
		s = stlObj.clone(name=name)
		self.stlFrame.addStl(s, highlight=True)
		itemid = self.stlFrame.getSelection()
		self.lbMap.append([fn, itemid])
		self.lbModified.append(False)
		self.lb.Append(fn)
		self.lbSelection = len(self.lbMap)-1
		self.lb.SetSelection(self.lbSelection)
		
		if self.settings.autoarrange:
			self.doArrange(None)
			
	def doDelete(self, evt):
		if self.lbSelection is None:
			return
		if self.lbModified[self.lbSelection]:
			dlg = wx.MessageDialog(self, "Are you sure you want to delete this object?",
					'Delete', wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION)
			
			rc = dlg.ShowModal()
			dlg.Destroy()

			if rc != wx.ID_YES:
				return
		
		self.lb.Delete(self.lbSelection)
		del(self.lbMap[self.lbSelection])
		self.stlFrame.delStl()
		l = len(self.lbMap)
		if self.lbSelection >= l:
			self.lbSelection = l-1
		
		if self.lbSelection < 0:
			self.lbSelection = None
			self.setModified(False)
			self.enableButtons(False)
			self.lb.Clear()
			self.lbMap = []
			self.lbModified = []
		else:
			self.setModified()
			self.lb.SetSelection(self.lbSelection)
			self.stlFrame.setSelection(self.lbMap[self.lbSelection][1])

	def doDelAll(self, evt):
		dlg = wx.MessageDialog(self, "Are you sure you want to delete everything?",
					'Delete All', wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION)
			
		rc = dlg.ShowModal()
		dlg.Destroy()

		if rc != wx.ID_YES:
			return
		
		self.setModified(False)
		self.stlFrame.delAll()
		self.enableButtons(False)
		
		self.lb.Clear()
		self.lbSelection = None
		self.lbMap = []
		self.lbModified = []
		
	def doExport2Prep(self, evt):
		suffix = "%05d" % int(random.random() * 99999)
		fn = os.path.join(tempfile.gettempdir(), tempfile.gettempprefix+suffix)
		wx.LogMessage("Saving plate to temporary STL file: %s" % fn)
		self.exportToFile(fn, "OBJECT", clearModified = False)
		self.app.switchToFilePrep(fn)
		
	def doExport(self, evt):
			
		dlg = wx.FileDialog(
			self, message="Choose an STL file",
			defaultDir=self.settings.lastdirectory, 
			defaultFile="",
			wildcard=wildcard,
			style=wx.SAVE | wx.CHANGE_DIR | wx.FD_OVERWRITE_PROMPT
			)
		
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		
		else:
			paths = dlg.GetPaths()
			dlg.Destroy()
			if len(paths) < 1:
				return
			fn = paths[0]
			
		objname = os.path.splitext(os.path.basename(fn))[0]
		
		dlg = wx.TextEntryDialog(
				self, 'Enter object name',
				'Object name', objname)
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return
		
		objname = dlg.GetValue().strip()
		dlg.Destroy()

		self.exportToFile(fn, objname)

	def exportToFile(self, fn, objname, clearModified = True):
		self.stlFrame.applyDeltas()
		objs = self.stlFrame.getStls()
		facets = []
		for o in objs:
			facets.extend(o.facets)

		stltool.emitstl(fn, facets=facets, objname=objname, binary=False)
		if clearModified:
			self.setModified(False)
		
	def setModified(self, flag=True, itmId=None):
		self.modified = flag
		if not flag:
			for i in range(len(self.lbModified)):
				self.lbModified[i] = False
				
		elif itmId is not None:
			self.lbModified[itmId] = True
		
		
	def doArrange(self, evt):
		for i in range(len(self.lbModified)):
			self.lbModified[i] = True
		self.setModified()
			
		if self.stlFrame.arrange(): return
		
		dlg = wx.MessageDialog(self, 'Not enough room on plate for all objects!',
							   'Plate Full',
							   wx.OK | wx.ICON_INFORMATION
							   )
		dlg.ShowModal()
		dlg.Destroy()

