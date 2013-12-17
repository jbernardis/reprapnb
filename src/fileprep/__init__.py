import wx
import wx.lib.newevent
import re, time, shlex, subprocess
import os.path
import thread

from gcread import GCode
from gcframe import GcFrame
from savelayer import SaveLayerDlg
from filamentchange import FilamentChangeDlg
from shiftmodel import ShiftModelDlg
from editgcode import EditGCodeDlg
from images import Images
from tools import formatElapsed 

from reprap import MAX_EXTRUDERS

from settings import TEMPFILELABEL

wildcard = "G Code (*.gcode)|*.gcode"
STLwildcard = "STL (*.stl)|*.stl"

GCODELINETEXT = "Current G Code Line: (%d)"

TITLETEXT = "G Code Viewer"
BUTTONDIM = (48, 48)
BUTTONDIMWIDE = (144, 80)

reX = re.compile("(.*[xX])([0-9\.]+)(.*)")
reY = re.compile("(.*[yY])([0-9\.]+)(.*)")

(SlicerEvent, EVT_SLICER_UPDATE) = wx.lib.newevent.NewEvent()
SLICER_RUNNING = 1
SLICER_RUNNINGCR = 2
SLICER_FINISHED = 3
SLICER_CANCELLED = 4

FPSTATUS_IDLE = 0
FPSTATUS_EQUAL = 1
FPSTATUS_EQUAL_DIRTY = 2
FPSTATUS_UNEQUAL = 3
FPSTATUS_UNEQUAL_DIRTY = 4
FPSTATUS_BUSY = 5

TEXT_PAD = 10

class SlicerThread:
	def __init__(self, win, cmd):
		self.win = win
		self.cmd = cmd
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

	def Run(self):
		args = shlex.split(str(self.cmd))
		try:
			p = subprocess.Popen(args,stderr=subprocess.STDOUT,stdout=subprocess.PIPE)
		except:
			evt = SlicerEvent(msg = "Exception occurred trying to spawn slicer", state = SLICER_CANCELLED)
			wx.PostEvent(self.win, evt)
			return
		
		obuf = ''
		while not self.cancelled:
			o = p.stdout.read(1)
			if o == '': break
			if o == '\r' or o == '\n':
				state = SLICER_RUNNING
				if o == '\r':
					state = SLICER_RUNNINGCR
				evt = SlicerEvent(msg = obuf, state = state)
				wx.PostEvent(self.win, evt)
				obuf = ''
			elif ord(o) < 32:
				pass
			else:
				obuf += o
				
		if self.cancelled:
			evt = SlicerEvent(msg = None, state = SLICER_CANCELLED)
			p.kill()
		else:
			evt = SlicerEvent(msg = None, state = SLICER_FINISHED)
			
		p.wait()
		wx.PostEvent(self.win, evt)

		self.running = False


(ReaderEvent, EVT_READER_UPDATE) = wx.lib.newevent.NewEvent()
READER_RUNNING = 1
READER_FINISHED = 2
READER_CANCELLED = 3

class ReaderThread:
	def __init__(self, win, fn):
		self.win = win
		self.fn = fn
		self.running = False
		self.cancelled = False
		self.gcode = []

	def Start(self):
		self.running = True
		self.cancelled = False
		thread.start_new_thread(self.Run, ())

	def Stop(self):
		self.cancelled = True

	def IsRunning(self):
		return self.running
	
	def getGCode(self):
		return self.gcode

	def Run(self):
		evt = ReaderEvent(msg = "Reading G Code...", state = READER_RUNNING)
		wx.PostEvent(self.win, evt)
		self.gcode = []
		try:
			l = list(open(self.fn))
		except:
			evt = ReaderEvent(msg = "Error opening file %s" % self.fn, state = READER_CANCELLED)
			wx.PostEvent(self.win, evt)	
			self.running = False
			return
			
		for s in l:
			self.gcode.append(s.rstrip())
		
		ct = len(self.gcode)
		if self.cancelled or ct == 0:
			evt = ReaderEvent(msg = None, state = READER_CANCELLED)
		else:
			evt = ReaderEvent(msg = "%d lines read." % ct, state = READER_FINISHED)

		wx.PostEvent(self.win, evt)	
		self.running = False


(ModelerEvent, EVT_MODELER_UPDATE) = wx.lib.newevent.NewEvent()
MODELER_RUNNING = 1
MODELER_FINISHED = 2
MODELER_CANCELLED = 3

class ModelerThread:
	def __init__(self, win, gcode, layer, acceleration):
		self.win = win
		self.gcode = gcode
		self.layer = layer
		self.acceleration = acceleration
		self.running = False
		self.cancelled = False
		self.model = None

	def Start(self):
		self.running = True
		self.cancelled = False
		thread.start_new_thread(self.Run, ())

	def Stop(self):
		self.cancelled = True

	def IsRunning(self):
		return self.running
	
	def getModel(self):
		return self.model
	
	def getLayer(self):
		return self.layer

	def Run(self):
		evt = ModelerEvent(msg = "Processing...", state = MODELER_RUNNING)
		wx.PostEvent(self.win, evt)
		self.model = GCode(self.gcode, self.acceleration)
		evt = ModelerEvent(msg = None, state = MODELER_FINISHED)
		wx.PostEvent(self.win, evt)	
		self.running = False

class FilePrepare(wx.Panel):
	def __init__(self, parent, app):
		self.model = None
		self.app = app
		self.buildarea = self.app.buildarea
		self.logger = self.app.logger
		self.settings = app.settings.fileprep
		self.modified = False
		self.temporaryFile = False	
		self.printerBusy = True	
		self.gcodeLoaded = False
		self.sliceActive = False
		self.exporting = False
		self.status = FPSTATUS_IDLE
		self.dlg = None

		self.shiftX = 0
		self.shiftY = 0
		
		self.gcFile = None
		self.stlFile = None

		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(400, 250))
		self.SetBackgroundColour("white")
		self.Bind(EVT_SLICER_UPDATE, self.slicerUpdate)
		self.Bind(EVT_READER_UPDATE, self.readerUpdate)
		self.Bind(EVT_MODELER_UPDATE, self.modelerUpdate)

		self.sizerMain = wx.GridBagSizer()
		self.sizerMain.AddSpacer((20, 20), pos=(0,0))
		
		self.sizerBtns = wx.BoxSizer(wx.HORIZONTAL)
		self.sizerBtns.AddSpacer((20, 20))
		
		self.images = Images(os.path.join(self.settings.cmdfolder, "images"))
		
		self.bSlice = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSlice, size=BUTTONDIM)
		self.sizerBtns.Add(self.bSlice)
		self.Bind(wx.EVT_BUTTON, self.fileSlice, self.bSlice)
		self.setSliceMode(True)
		
		self.sizerBtns.AddSpacer((20, 20))
		
		self.bOpen = wx.BitmapButton(self, wx.ID_ANY, self.images.pngFileopen, size=BUTTONDIM)
		self.bOpen.SetToolTipString("Open a G Code file directly")
		self.sizerBtns.Add(self.bOpen)
		self.Bind(wx.EVT_BUTTON, self.fileOpen, self.bOpen)
		
		self.bSave = wx.BitmapButton(self, wx.ID_ANY, self.images.pngFilesave, size=BUTTONDIM)
		self.bSave.SetToolTipString("Save the modified G Code file")
		self.sizerBtns.Add(self.bSave)
		self.Bind(wx.EVT_BUTTON, self.fileSave, self.bSave)
		self.bSave.Enable(False)
		
		self.sizerBtns.AddSpacer((20, 20))
		
		self.bSaveLayer = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSavelayers, size=BUTTONDIM)
		self.bSaveLayer.SetToolTipString("Save specific layers out of this G Code")
		self.sizerBtns.Add(self.bSaveLayer)
		self.Bind(wx.EVT_BUTTON, self.editSaveLayer, self.bSaveLayer)
		self.bSaveLayer.Enable(False)
		
		self.bFilamentChange = wx.BitmapButton(self, wx.ID_ANY, self.images.pngFilchange, size=BUTTONDIM)
		self.bFilamentChange.SetToolTipString("Insert G Code at the current location to change filament")
		self.sizerBtns.Add(self.bFilamentChange)
		self.Bind(wx.EVT_BUTTON, self.editFilamentChange, self.bFilamentChange)
		self.bFilamentChange.Enable(False)
		
		self.bShift = wx.BitmapButton(self, wx.ID_ANY, self.images.pngShift, size=BUTTONDIM)
		self.bShift.SetToolTipString("Shift object(s) in X and/or Y directions")
		self.sizerBtns.Add(self.bShift)
		self.Bind(wx.EVT_BUTTON, self.shiftModel, self.bShift)
		self.bShift.Enable(False)
		
		self.bEdit = wx.BitmapButton(self, wx.ID_ANY, self.images.pngEdit, size=BUTTONDIM)
		self.bEdit.SetToolTipString("Edit the G Code")
		self.sizerBtns.Add(self.bEdit)
		self.Bind(wx.EVT_BUTTON, self.editGCode, self.bEdit)
		self.bEdit.Enable(False)
		
		self.sizerBtns.AddSpacer((20, 20))
	
		self.bZoomIn = wx.BitmapButton(self, wx.ID_ANY, self.images.pngZoomin, size=BUTTONDIM)
		self.bZoomIn.SetToolTipString("Zoom the view in")
		self.sizerBtns.Add(self.bZoomIn)
		self.Bind(wx.EVT_BUTTON, self.viewZoomIn, self.bZoomIn)
		
		self.bZoomOut = wx.BitmapButton(self, wx.ID_ANY, self.images.pngZoomout, size=BUTTONDIM)
		self.bZoomOut.SetToolTipString("Zoom the view out")
		self.sizerBtns.Add(self.bZoomOut)
		self.Bind(wx.EVT_BUTTON, self.viewZoomOut, self.bZoomOut)
		
		self.sizerBtns.AddSpacer((20, 20))
	
		self.bToPrinter = wx.BitmapButton(self, wx.ID_ANY, self.images.pngToprinter, size=BUTTONDIMWIDE)
		self.bToPrinter.SetToolTipString("Send this GCode file to the printer")
		self.sizerBtns.Add(self.bToPrinter)
		self.Bind(wx.EVT_BUTTON, self.toPrinter, self.bToPrinter)
		self.bToPrinter.Enable(False)
		
		self.sizerMain.Add(self.sizerBtns, pos=(1,1), span=(1,4))
		self.sizerMain.AddSpacer((20,20), pos=(2,0))

		self.gcf = GcFrame(self, self.model, self.settings, self.buildarea)
		self.sizerMain.Add(self.gcf, pos=(3,1))
		self.sizerMain.AddSpacer((20,20), pos=(4,0))
		sz = self.buildarea[1] * self.settings.gcodescale
		
		self.sizerMain.AddSpacer((20, 20), pos=(3,2))

		self.slideLayer = wx.Slider(
			self, wx.ID_ANY, 1, 1, 9999, size=(80, sz),
			style = wx.SL_VERTICAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
		self.slideLayer.Bind(wx.EVT_SCROLL_CHANGED, self.onSpinLayer)
		self.slideLayer.Bind(wx.EVT_MOUSEWHEEL, self.onMouseLayer)
		self.slideLayer.SetRange(1, 10)
		self.slideLayer.SetValue(1)
		self.slideLayer.SetPageSize(1);
		self.slideLayer.Disable()
		self.sizerMain.Add(self.slideLayer, pos=(3,3), flag=wx.ALIGN_RIGHT)

		self.slideGCode = wx.Slider(
			self, wx.ID_ANY, 1, 1, 99999, size=(80, sz),
			style = wx.SL_VERTICAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
		self.slideGCode.Bind(wx.EVT_SCROLL_CHANGED, self.onSpinGCode)
		self.slideGCode.Bind(wx.EVT_MOUSEWHEEL, self.onMouseGCode)
		self.slideGCode.SetRange(1, 10)
		self.slideGCode.SetValue(1)
		self.slideGCode.SetPageSize(1);
		self.slideGCode.Disable()
		self.sizerMain.Add(self.slideGCode, pos=(3,4))

		self.sizerOpts = wx.BoxSizer(wx.HORIZONTAL)
				
		self.cbPrevious = wx.CheckBox(self, wx.ID_ANY, "Show Previous Layer")
		self.cbPrevious.SetToolTipString("Turn on/off drawing of the previous layer in the background")
		self.Bind(wx.EVT_CHECKBOX, self.checkPrevious, self.cbPrevious)
		self.cbPrevious.SetValue(self.settings.showprevious)
		self.sizerOpts.Add(self.cbPrevious)
		
		self.sizerOpts.AddSpacer((20, 10))

		self.cbMoves = wx.CheckBox(self, wx.ID_ANY, "Show Moves")
		self.cbMoves.SetToolTipString("Turn on/off the drawing of non-extrusion moves")
		self.Bind(wx.EVT_CHECKBOX, self.checkMoves, self.cbMoves)
		self.cbMoves.SetValue(self.settings.showmoves)
		self.sizerOpts.Add(self.cbMoves)
		
		self.sizerOpts.AddSpacer((20, 10))

		self.cbBuffDC = wx.CheckBox(self, wx.ID_ANY, "Use Buffered DC")
		self.Bind(wx.EVT_CHECKBOX, self.checkBuffDC, self.cbBuffDC)
		self.cbBuffDC.SetValue(self.settings.usebuffereddc)
		self.sizerOpts.Add(self.cbBuffDC)
		
		self.sizerMain.Add(self.sizerOpts, pos=(5, 1))
		self.sizerMain.AddSpacer((20, 20), pos=(6,0))
		
		self.infoPane = wx.GridBagSizer()
		t = wx.StaticText(self, wx.ID_ANY, "G Code Preparation")
		f = wx.Font(18,  wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		t.SetFont(f)
		self.infoPane.AddSpacer((100, 1), pos=(0,0))
		self.infoPane.Add(t, pos=(1,0), span=(1,2), flag=wx.ALIGN_CENTER)
		
		self.infoPane.AddSpacer((20, 20), pos=(2,0))
		
		ipfont = wx.Font(12,  wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		
		dc = wx.WindowDC(self)
		dc.SetFont(ipfont)

		self.ipSlicerCfg = wx.StaticText(self, wx.ID_ANY, "")
		self.ipSlicerCfg.SetFont(ipfont)
		self.infoPane.Add(self.ipSlicerCfg, pos=(3,0), span=(1,2), flag=wx.ALIGN_CENTER)
		
		self.infoPane.AddSpacer((20, 20), pos=(4,0))

		self.ipFileName = wx.StaticText(self, wx.ID_ANY, "")
		self.ipFileName.SetFont(ipfont)
		self.infoPane.Add(self.ipFileName, pos=(5,0), span=(1,2), flag=wx.ALIGN_LEFT)
		
		self.infoPane.AddSpacer((40, 40), pos=(6,0))
		
		text = "Layer Number: "
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, size=(w, h+TEXT_PAD))
		t.SetFont(ipfont)
		self.infoPane.Add(t, pos=(7,0), flag=wx.ALIGN_RIGHT)
		
		self.ipLayerNum = wx.StaticText(self, wx.ID_ANY, "")
		self.ipLayerNum.SetFont(ipfont)
		self.infoPane.Add(self.ipLayerNum, pos=(7,1), flag=wx.ALIGN_LEFT)
		
		text = "Height (mm): " 
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, size=(w, h+TEXT_PAD))
		t.SetFont(ipfont)
		self.infoPane.Add(t, pos=(8,0), flag=wx.ALIGN_RIGHT)
		
		self.ipLayerHeight = wx.StaticText(self, wx.ID_ANY, "")
		self.ipLayerHeight.SetFont(ipfont)
		self.infoPane.Add(self.ipLayerHeight, pos=(8,1), flag=wx.ALIGN_LEFT)

		text = "Min/Max X (mm): "
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, size=(w, h+TEXT_PAD))
		t.SetFont(ipfont)
		self.infoPane.Add(t, pos=(9,0), flag=wx.ALIGN_RIGHT)
		
		self.ipMinMaxX = wx.StaticText(self, wx.ID_ANY, "")
		self.ipMinMaxX.SetFont(ipfont)
		self.infoPane.Add(self.ipMinMaxX, pos=(9,1), flag=wx.ALIGN_LEFT)
		
		text = "Min/Max Y (mm): "
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, size=(w, h+TEXT_PAD))
		t.SetFont(ipfont)
		self.infoPane.Add(t, pos=(10,0), flag=wx.ALIGN_RIGHT)
		
		self.ipMinMaxY = wx.StaticText(self, wx.ID_ANY, "")
		self.ipMinMaxY.SetFont(ipfont)
		self.infoPane.Add(self.ipMinMaxY, pos=(10,1), flag=wx.ALIGN_LEFT)
		
		text = "Filament (mm): "
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, size=(w, h+TEXT_PAD))
		t.SetFont(ipfont)
		self.infoPane.Add(t, pos=(11,0), flag=wx.ALIGN_RIGHT)
		
		self.ipFilament = []
		ln = 11
		for i in range(MAX_EXTRUDERS):
			w = wx.StaticText(self, wx.ID_ANY, "", size=(-1, h+TEXT_PAD))
			w.SetFont(ipfont)
			self.infoPane.Add(w, pos=(ln, 1), flag=wx.ALIGN_LEFT)
			ln += 1
			self.ipFilament.append(w)
		
		text = "G Code Line from/to: "
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, size=(w, h+TEXT_PAD))
		t.SetFont(ipfont)
		self.infoPane.Add(t, pos=(ln,0), flag=wx.ALIGN_RIGHT)
		
		self.ipGCLines = wx.StaticText(self, wx.ID_ANY, "")
		self.ipGCLines.SetFont(ipfont)
		self.infoPane.Add(self.ipGCLines, pos=(ln,1), flag=wx.ALIGN_LEFT)
		
		ln += 1
		text = "Print Time: "
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, size=(w, h+TEXT_PAD))
		t.SetFont(ipfont)
		self.infoPane.Add(t, pos=(ln,0), flag=wx.ALIGN_RIGHT)
		
		self.ipPrintTime = wx.StaticText(self, wx.ID_ANY, "")
		self.ipPrintTime.SetFont(ipfont)
		self.infoPane.Add(self.ipPrintTime, pos=(ln,1), flag=wx.ALIGN_LEFT)
		
		ln += 1
		text = "Extrusion Speeds: "
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, size=(w, h+TEXT_PAD))
		t.SetFont(ipfont)
		self.infoPane.Add(t, pos=(ln,0), flag=wx.ALIGN_RIGHT)
		
		ipHeight = dc.GetTextExtent("20")[1] + TEXT_PAD
		t = wx.TextCtrl(self, wx.ID_ANY, "< 20 mm/s", size=(150, ipHeight),
						style=wx.TE_RICH2|wx.TE_READONLY)
		t.SetBackgroundColour(wx.Colour(237, 139, 33))
		t.SetFont(ipfont)
		self.infoPane.Add(t, pos=(ln,1), flag=wx.ALIGN_LEFT)
		
		self.infoPane.AddSpacer((10, 10), pos=(ln+1, 1))
		
		t = wx.TextCtrl(self, wx.ID_ANY, "< 50 mm/s", size=(150, ipHeight),
						style=wx.TE_RICH2|wx.TE_READONLY)
		t.SetBackgroundColour(wx.Colour(240, 0, 0))
		t.SetFont(ipfont)
		self.infoPane.Add(t, pos=(ln+2,1), flag=wx.ALIGN_LEFT)
		
		self.infoPane.AddSpacer((10, 10), pos=(ln+3, 1))
		
		t = wx.TextCtrl(self, wx.ID_ANY, "< 60 mm/s", size=(150, ipHeight),
						style=wx.TE_RICH2|wx.TE_READONLY)
		t.SetBackgroundColour("blue")
		t.SetFont(ipfont)
		self.infoPane.Add(t, pos=(ln+4,1), flag=wx.ALIGN_LEFT)
		
		self.infoPane.AddSpacer((10, 10), pos=(ln+5, 1))
		
		t = wx.TextCtrl(self, wx.ID_ANY, "< 120 mm/s", size=(150, ipHeight),
						style=wx.TE_RICH2|wx.TE_READONLY)
		t.SetBackgroundColour("purple")
		t.SetFont(ipfont)
		self.infoPane.Add(t, pos=(ln+6,1), flag=wx.ALIGN_LEFT)
		
		self.infoPane.AddSpacer((10, 10), pos=(ln+7, 1))
		
		t = wx.TextCtrl(self, wx.ID_ANY, ">= 120 mm/s", size=(150, ipHeight),
						style=wx.TE_RICH2|wx.TE_READONLY)
		t.SetBackgroundColour("green")
		t.SetFont(ipfont)
		self.infoPane.Add(t, pos=(ln+8,1), flag=wx.ALIGN_LEFT)
		
		self.infoPane.AddSpacer((40, 40), pos=(ln+9, 0))
		
		ln += 10
		self.ipGCodeLine = wx.StaticText(self, wx.ID_ANY, "", size=(-1, ipHeight))
		self.ipGCodeLine.SetFont(ipfont)
		self.infoPane.Add(self.ipGCodeLine, pos=(ln,0), flag=wx.ALIGN_LEFT)
		
		self.ipGCodeSource = wx.StaticText(self, wx.ID_ANY, "")
		self.ipGCodeSource.SetFont(ipfont)
		self.infoPane.Add(self.ipGCodeSource, pos=(ln+1, 0), span=(1, 2), flag=wx.ALIGN_LEFT)

		self.sizerMain.Add(self.infoPane, pos=(2,5), span=(4,1))
		self.sizerMain.AddSpacer((40, 20), pos=(0,6))
		
		self.SetSizer(self.sizerMain)
		self.Layout()
		self.Fit()

	def setSliceMode(self, flag=True):
		if flag:
			self.bSlice.SetBitmapLabel(self.images.pngSlice)
			self.bSlice.SetToolTipString("Slice a file using the currently configured slicer")
		else:
			self.bSlice.SetBitmapLabel(self.images.pngCancelslice)
			self.bSlice.SetToolTipString("Cancel slicer")
		
	def onClose(self, evt):
		if self.checkModified():
			return False
	
		return True
	
	def toPrinter(self, evt):
		#name = self.ipFileName.GetLabel()
		self.disableButtons()
		self.bToPrinter.Enable(False)
		self.exporting = True
		self.logger.LogMessage("Beginning forwarding to print monitor")
		self.app.updateFilePrepStatus(FPSTATUS_BUSY)
		self.modelerThread = ModelerThread(self, self.gcode, 0, self.settings.acceleration)
		self.modelerThread.Start()
		
	def fileSlice(self, event):
		if self.sliceActive:
			self.sliceThread.Stop()
			self.bSlice.Enable(False)
			self.bToPrinter.Enable(False)
			self.bOpen.Enable(False)
			return
		
		if self.checkModified(message='Close file without saving changes?'):
			return
		
		dlg = wx.FileDialog(
			self, message="Choose an STL file",
			defaultDir=self.settings.laststldirectory, 
			defaultFile="",
			wildcard=STLwildcard,
			style=wx.OPEN | wx.CHANGE_DIR
			)
		
		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()
			self.settings.laststldirectory = os.path.dirname(path)
			self.settings.setModified()
			self.sliceFile(path)

		dlg.Destroy()
		
	def loadTempSTL(self, fn):
		self.sliceFile(fn, tempFile=True)
		
	def sliceFile(self, fn, tempFile = False):
		self.stlFile = fn
		self.temporaryFile = tempFile
		self.gcFile = self.app.slicer.buildSliceOutputFile(fn)
		cmd = self.app.slicer.buildSliceCommand()
		self.sliceThread = SlicerThread(self, cmd)
		self.gcodeLoaded = False
		self.bOpen.Enable(False)
		self.disableEditButtons()
		#self.bSlice.Enable(False)
		self.bToPrinter.Enable(False)
		self.setSliceMode(False)
		self.sliceActive = True
		self.app.updateFilePrepStatus(FPSTATUS_BUSY)
		self.sliceThread.Start()
		
	def slicerUpdate(self, evt):
		if evt.msg is not None:
			self.logger.LogMessage("(s) - " + evt.msg)
			
		if evt.state == SLICER_RUNNING:
			pass
				
		elif evt.state == SLICER_RUNNINGCR:
			pass
				
		elif evt.state == SLICER_CANCELLED:
			self.gcFile = None
			self.setSliceMode()
			self.enableButtons()
			self.app.slicer.sliceComplete()
			self.sliceActive = False
			self.app.updateFilePrepStatus(self.status)
			
		elif evt.state == SLICER_FINISHED:
			if self.temporaryFile:
				try:
					self.logger.LogMessage("Removing temporary STL file: %s" % self.stlFile)
					os.unlink(self.stlFile)
				except:
					pass
				self.stlFile = None
			self.setSliceMode()
			self.sliceActive = False
			self.enableButtons()
			self.app.slicer.sliceComplete()
			if os.path.exists(self.gcFile):
				self.loadFile(self.gcFile)
			else:
				self.logger.LogMessage("Slicer failed to produce expected G Code file: %s" % self.gcFile)
				self.gcFile = None
				self.bOpen.Enable(True)
			
		else:
			self.logger.LogError("unknown slicer thread state: %s" % evt.state)

	def fileOpen(self, event):
		if self.checkModified(message='Close file without saving changes?'):
			return

		self.temporaryFile = False		
		dlg = wx.FileDialog(
			self, message="Choose a G Code file",
			defaultDir=self.settings.lastgcdirectory, 
			defaultFile="",
			wildcard=wildcard,
			style=wx.OPEN | wx.CHANGE_DIR
			)
		
		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()
			self.stlFile = None
			self.loadFile(path)

		dlg.Destroy()

	def loadFile(self, fn):
		self.bOpen.Enable(False)
		self.bSlice.Enable(False)
		self.disableEditButtons()
		self.bToPrinter.Enable(False)
		self.filename = fn
		self.gcFile = fn
		self.readerThread = ReaderThread(self, fn)
		if self.temporaryFile:
			self.logger.LogMessage("Temporary G Code file")
		else:
			self.logger.LogMessage("G Code file %s" % fn)
		self.readerThread.Start()
			
	def readerUpdate(self, evt):
		if evt.state == READER_RUNNING:
			if evt.msg is not None:
				self.logger.LogMessage(evt.msg)
				
		elif evt.state == READER_FINISHED:
			if evt.msg is not None:
				self.logger.LogMessage(evt.msg)
			
			if self.temporaryFile:
				lfn = TEMPFILELABEL
			else:
				self.settings.lastgcdirectory = os.path.dirname(self.gcFile)
				self.settings.setModified()
				if len(self.gcFile) > 60:
					lfn = os.path.basename(self.gcFile)
				else:
					lfn = self.gcFile
			self.ipFileName.SetLabel(lfn)

			self.gcode = self.readerThread.getGCode()
			self.gcodeLoaded = True
			self.logger.LogMessage("G Code reading complete - building model")
			self.app.updateFilePrepStatus(FPSTATUS_UNEQUAL)
			self.status = FPSTATUS_UNEQUAL
			self.setModified(False)		
			self.buildModel()
		
			if self.temporaryFile:
				try:
					self.logger.LogMessage("Removing temporary G Code file: %s" % self.gcFile)
					os.unlink(self.gcFile)
				except:
					pass
			
		elif evt.state == READER_CANCELLED:
			if evt.msg is not None:
				self.logger.LogMessage(evt.msg)
			self.gcode = []
			self.filename = None
			self.ipFileName.SetLabel("")
			self.gcFile = None
			self.gcodeLoaded = False
			self.model = None
			self.enableButtons()
		
			if self.temporaryFile:
				try:
					self.logger.LogMessage("Removing temporary G Code file: %s" % self.gcFile)
					os.unlink(self.gcFile)
				except:
					pass
				
		else:
			self.logger.LogError("unknown reader thread state: %s" % evt.state)


	def buildModel(self, layer=0):
		self.exporting = False
		self.modelerThread = ModelerThread(self, self.gcode, layer, self.settings.acceleration)
		self.modelerThread.Start()
		
	def getModelData(self, layer=0):
		self.layerCount = self.model.countLayers()
		
		self.layerInfo = self.model.getLayerInfo(layer)
		if self.layerInfo is None:
			return
		
		self.showLayerInfo(layer)

		self.hilite = self.layerInfo[4][0]
		self.firstGLine = self.layerInfo[4][0]
		self.lastGLine = self.layerInfo[4][-1]
		
		self.slideLayer.SetRange(1, self.layerCount)
		self.slideLayer.SetValue(layer+1)
		n = int(self.layerCount/20)
		if n<1: n=1
		self.slideLayer.SetTickFreq(n, 1)
		self.slideLayer.SetPageSize(1);
		self.slideLayer.Enable()
		self.slideLayer.Refresh()
		
		self.slideGCode.SetRange(self.firstGLine+1, self.lastGLine+1)
		self.slideGCode.SetValue(self.firstGLine+1)
		n = int((self.lastGLine-self.firstGLine)/20)
		if n<1: n=1
		self.slideGCode.SetTickFreq(n, 1)
		self.slideGCode.SetPageSize(1);
		self.slideGCode.Enable()
		self.slideGCode.Refresh()
		
		self.ipGCodeSource.SetLabel(self.model.lines[self.hilite].orig)
		self.ipGCodeLine.SetLabel(GCODELINETEXT % (self.hilite+1))
		
		self.Fit()
		
		self.gcf.loadModel(self.model, layer=layer)
			
	def modelerUpdate(self, evt):
		if evt.state == MODELER_RUNNING:
			if evt.msg is not None:
				self.logger.LogMessage(evt.msg)
				
		elif evt.state == MODELER_FINISHED:
			if evt.msg is not None:
				self.logger.LogMessage(evt.msg)

			model = self.modelerThread.getModel()				
			if self.exporting:
				if self.temporaryFile:
					name = TEMPFILELABEL
				else:
					name = self.gcFile
					
				self.logger.LogMessage("Modeling complete - forwarding %s to print monitor" % name)
				self.app.forwardToPrintMon(model, name=name)
				self.logger.LogMessage("Forwarding complete")
				self.enableButtons()
				
				newstat = False
				if self.status == FPSTATUS_UNEQUAL:
					self.status = FPSTATUS_EQUAL
					newstat = True
				elif self.status == FPSTATUS_UNEQUAL_DIRTY:
					self.status = FPSTATUS_EQUAL_DIRTY
					newstat = True
				if newstat:
					self.app.updateFilePrepStatus(self.status)

			else:
				self.model = model
				self.getModelData(self.modelerThread.getLayer())			
				self.logger.LogMessage("Min/Max X: %.2f/%.2f" % (self.model.xmin, self.model.xmax))
				self.logger.LogMessage("Min/Max Y: %.2f/%.2f" % (self.model.ymin, self.model.ymax))
				self.logger.LogMessage("Max Z: %.2f" % self.model.zmax)
				self.logger.LogMessage("Total Filament Length: %s" % str(self.model.total_e))
				self.logger.LogMessage("Estimated duration: %s" % formatElapsed(self.model.duration))
				self.enableButtons();
			
		elif evt.state == MODELER_CANCELLED:
			if evt.msg is not None:
				self.logger.LogMessage(evt.msg)
				
			self.enableButtons()
			self.model = None
				
		else:
			self.logger.LogError("unknown modeler thread state: %s" % evt.state)
		
	def setPrinterBusy(self, flag=True):
		self.printerBusy = flag
		self.enableButtons()
		
	def enableButtons(self):
		self.bOpen.Enable(True)
		self.bSlice.Enable(True)
		self.bSave.Enable(self.gcodeLoaded)
		self.bSaveLayer.Enable(self.gcodeLoaded)
		self.bFilamentChange.Enable(self.gcodeLoaded)
		self.bShift.Enable(self.gcodeLoaded)
		self.bEdit.Enable(self.gcodeLoaded)
		self.bToPrinter.Enable(self.gcodeLoaded and not self.printerBusy)
		
	def disableButtons(self):
		self.bOpen.Enable(False)
		self.bSlice.Enable(False)
		self.bSave.Enable(False)
		self.bSaveLayer.Enable(False)
		self.bFilamentChange.Enable(False)
		self.bShift.Enable(False)
		self.bEdit.Enable(False)
		self.bToPrinter.Enable(False)
		
	def disableEditButtons(self):
		self.bSave.Enable(False)
		self.bSaveLayer.Enable(False)
		self.bFilamentChange.Enable(False)
		self.bShift.Enable(False)
		self.bEdit.Enable(False)

	def editGCode(self, event):
		self.disableButtons()
		if self.dlg is None:
			self.dlg = EditGCodeDlg(self)
			self.dlg.CenterOnScreen()
			self.dlg.Show()
		
	def dlgClosed(self, rc, data):
		self.dlg = None
		if not rc:
			self.enableButtons()
			return

		self.gcode = data[:]
		self.buildModel()
		
		self.layerCount = self.model.countLayers()
		self.slideLayer.SetRange(1, self.layerCount)
		l = self.slideLayer.GetValue()-1
		self.setLayer(l)
		self.gcf.setLayer(l)
		self.setModified(True)
		self.enableButtons()

	def shiftModel(self, event):
		dlg = ShiftModelDlg(self)
		dlg.CenterOnScreen()
		val = dlg.ShowModal()
		dlg.Destroy()
	
		if val == wx.ID_OK:
			self.applyShift()
		else:
			self.shiftX = 0
			self.shiftY = 0
			self.gcf.setShift(0, 0)

	def setShift(self, sx, sy):
		self.shiftX = sx
		self.shiftY = sy
		self.gcf.setShift(sx, sy)

	def applyShift(self):
		for i in range(len(self.gcode)):
			l = self.gcode[i]
			l = self.applyAxisShift(l, 'x', self.shiftX)
			l = self.applyAxisShift(l, 'y', self.shiftY)
			self.gcode[i] = l

		self.shiftX = 0
		self.shiftY = 0
		l = self.gcf.getCurrentLayer()
		self.buildModel(layer=l)
		self.setModified(True)

	def applyAxisShift(self, s, axis, shift):
		if "m117" in s or "M117" in s:
			return s

		if axis == 'x':
			m = reX.match(s)
			shift = self.shiftX
		elif axis == 'y':
			m = reY.match(s)
			shift = self.shiftY
		else:
			return s
		
		if m is None or m.lastindex != 3:
			return s
		
		value = float(m.group(2)) + float(shift)
		return "%s%s%s" % (m.group(1), str(value), m.group(3))


	def fileSave(self, event):
		dlg = wx.FileDialog(
			self, message="Save as ...", defaultDir=self.settings.lastgcdirectory, 
			defaultFile="", wildcard=wildcard, style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
		
		val = dlg.ShowModal()

		if val != wx.ID_OK:
			dlg.Destroy()
			return
		
		path = dlg.GetPath()
		dlg.Destroy()

		ext = os.path.splitext(os.path.basename(path))[1]
		if ext == "":
			path += ".gcode"
			
		fp = file(path, 'w')
		
		for ln in self.gcode:
			fp.write("%s\n" % ln)
			
		self.setModified(False)
			
		fp.close()

	def editSaveLayer(self, event):
		dlg = SaveLayerDlg(self)
		dlg.CenterOnScreen()
		val = dlg.ShowModal()
	
		if val != wx.ID_OK:
			dlg.Destroy()
			return
		
		v = dlg.getValues()
		dlg.Destroy()
		
		dlg = wx.FileDialog(
			self, message="Save layer(s) as ...", defaultDir=self.settings.lastgcdirectory, 
			defaultFile="", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
			)
		
		val = dlg.ShowModal()

		if val != wx.ID_OK:
			dlg.Destroy()
			return
		
		path = dlg.GetPath()
		dlg.Destroy()

		ext = os.path.splitext(os.path.basename(path))[1]
		if ext == "":
			path += ".gcode"

		fp = file(path, 'w')
		
		if v[3] or v[4] or v[5]:
			s = "G28"
			if v[3]:
				s += " X0"
			if v[4]:
				s += " Y0"
			if v[5]:
				s += " Z0"
			fp.write(s+"\n")
				
		if v[2]:
			fp.write("G92 E%.3f\n" % self.model.layer_e_start[v[0]])
		
		info = self.model.getLayerInfo(v[0])
		sx = info[4][0]
		info = self.model.getLayerInfo(v[1])
		ex = info[4][1]
		z = info[0]
		for ln in self.gcode[sx:ex+1]:
			fp.write(ln + "\n")
		
		if v[7]:
			# TODO: need to revisit this later - for now, assume tool 0
			fp.write("G92 E%.3f\n" % (self.model.layer_e_end[v[1]][0]+2))
			fp.write("G1 E%.3f\n" % self.model.layer_e_end[v[1][0]])
		
		if v[6]:
			fp.write("G1 Z%.3f" % (z+10))
			
		fp.close()
		
	def editFilamentChange(self, evt):
		dlg = FilamentChangeDlg(self)
		dlg.CenterOnScreen()
		val = dlg.ShowModal()
	
		if val != wx.ID_OK:
			dlg.Destroy()
			return
		
		gc = dlg.getValues()
		self.gcode[self.hilite:self.hilite] = gc
		self.buildModel()
		
		self.layerCount = self.model.countLayers()
		self.slideLayer.SetRange(1, self.layerCount)
		l = self.slideLayer.GetValue()-1
		self.setLayer(l)
		self.gcf.setLayer(l)
		self.setModified(True)

		dlg.Destroy()
		self.Fit()
		self.Layout()
		
	def checkBuffDC(self, evt):
		self.settings.usebuffereddc = evt.IsChecked()
		self.settings.setModified()
		self.gcf.redrawCurrentLayer()
		
	def checkPrevious(self, evt):
		self.settings.showprevious = evt.IsChecked()
		self.settings.setModified()
		self.gcf.redrawCurrentLayer()
		
	def checkMoves(self, evt):
		self.settings.showmoves = evt.IsChecked()
		self.settings.setModified()
		self.gcf.redrawCurrentLayer()
		
	def viewZoomIn(self, evt):
		self.gcf.zoomIn()
		
	def viewZoomOut(self, evt):
		self.gcf.zoomOut()
		
	def onMouseGCode(self, evt):
		l = self.slideGCode.GetValue()-1
		if evt.GetWheelRotation() < 0:
			l += 1
		else:
			l -= 1
		if l >= self.firstGLine and l <= self.lastGLine:
			self.gcf.setGCode(l)
			self.setGCode(l)

	def onSpinGCode(self, evt):
		l = evt.EventObject.GetValue()-1
		if l >= self.firstGLine and l <= self.lastGLine:
			self.gcf.setGCode(l)
			self.setGCode(l)
		
	def setGCode(self, l):
		if l >= self.firstGLine and l <= self.lastGLine:
			self.hilite = l
			self.ipGCodeSource.SetLabel(self.model.lines[l].orig)
			self.ipGCodeLine.SetLabel(GCODELINETEXT % (l+1))
			self.slideGCode.SetValue(l+1)
		else:
			self.ipGCodeSource.SetLabel("")
			self.ipGCodeLine.SetLabel("")
		
	def onMouseLayer(self, evt):
		l = self.slideLayer.GetValue()-1
		if evt.GetWheelRotation() < 0:
			l += 1
		else:
			l -= 1
		if l >= 0 and l < self.layerCount:
			self.gcf.setLayer(l)
			self.setLayer(l)

	def onSpinLayer(self, evt):
		l = evt.EventObject.GetValue()-1
		self.gcf.setLayer(l)
		self.setLayer(l)
		
	def setLayer(self, l):
		if l >=0 and l < self.layerCount:
			self.slideLayer.SetValue(l+1)
			
			self.layerInfo = self.model.getLayerInfo(l)
			if self.layerInfo is None:
				return
	
			self.hilite = self.layerInfo[4][0]
			self.firstGLine = self.layerInfo[4][0]
			self.lastGLine = self.layerInfo[4][-1]
		
			if self.firstGLine >= self.lastGLine:
				self.slideGCode.SetRange(self.firstGLine+1, self.firstGLine+2)
				self.slideGCode.SetValue(self.firstGLine+1)
				self.slideGCode.Enable(False)
			else:
				self.slideGCode.SetRange(self.firstGLine+1, self.lastGLine+1)
				self.slideGCode.SetValue(self.firstGLine+1)
				n = int((self.lastGLine-self.firstGLine)/20)
				if n<1: n=1
				self.slideGCode.SetTickFreq(n, 1)
				self.slideGCode.SetPageSize(1);
				self.slideGCode.Refresh()
				self.slideGCode.Enable(True)
			
			self.showLayerInfo(l)
			
			self.ipGCodeSource.SetLabel(self.model.lines[self.hilite].orig)
			self.ipGCodeLine.SetLabel(GCODELINETEXT % (self.hilite+1))
			
			self.Layout()
			self.Fit()
			
	def showLayerInfo(self, ln):
		self.ipLayerNum.SetLabel("%d/%d" % (ln+1, self.layerCount))
		self.ipLayerHeight.SetLabel("%9.3f" % self.layerInfo[0])
		if self.layerInfo[1][0] > self.layerInfo[2][0]:
			s = "N/A"
		else:
			s = "%9.3f/%9.3f" % (self.layerInfo[1][0], self.layerInfo[2][0])
		self.ipMinMaxX.SetLabel(s)
		
		if self.layerInfo[1][1] > self.layerInfo[2][1]:
			s = "N/A"
		else:
			s = "%9.3f/%9.3f" % (self.layerInfo[1][1], self.layerInfo[2][1])
		self.ipMinMaxY.SetLabel(s)

		
		for i in range(MAX_EXTRUDERS):
			s = "T%d: %.3f/%.3f" % (i, self.layerInfo[3][i], self.model.total_e[i])
			self.ipFilament[i].SetLabel(s)
			
		self.ipGCLines.SetLabel("%4d/%4d" % (self.layerInfo[4][0]+1, self.layerInfo[4][1]+1))
		
		lt = time.strftime('%H:%M:%S', time.gmtime(self.layerInfo[5]))
		tt = time.strftime('%H:%M:%S', time.gmtime(self.model.duration))
		self.ipPrintTime.SetLabel("%s/%s" % (lt, tt))
		
	def setModified(self, flag=True):
		self.modified = flag
		newstat = False
		
		if self.modified:
			if self.status in [ FPSTATUS_UNEQUAL, FPSTATUS_EQUAL_DIRTY, FPSTATUS_EQUAL ]:
				self.status = FPSTATUS_UNEQUAL_DIRTY
				newstat = True
		else:
			if self.status == FPSTATUS_UNEQUAL_DIRTY:
				self.status = FPSTATUS_UNEQUAL
				newstat = True
			elif self.status == FPSTATUS_EQUAL_DIRTY:
				self.status = FPSTATUS_EQUAL
				newstat = True
				
		if newstat:
			self.app.updateFilePrepStatus(self.status)
			
		if self.temporaryFile:
			fn = TEMPFILELABEL
		else:
			fn = self.gcFile
			
		if flag:
			self.ipFileName.SetLabel("* " + fn)
		else:
			self.ipFileName.SetLabel(fn)
			
	def checkModified(self, message='Exit without saving changes?'):
		if self.modified:
			dlg = wx.MessageDialog(self, message,
					'File Preparation', wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION)
			
			rc = dlg.ShowModal()
			dlg.Destroy()

			if rc != wx.ID_YES:
				return True

		return False
		

