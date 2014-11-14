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
from modtemps import ModifyTempsDlg
from modspeed import ModifySpeedDlg
from editgcode import EditGCodeDlg
from stlmerge import StlMergeDlg
from images import Images
from tools import formatElapsed 
from stlview import StlViewer
from override import Override, ovUserKeyMap, ovKeyOrder
from slicequeue import SliceQueue
from gcodequeue import GCodeQueue
from toolbar import ToolBar

from reprap import MAX_EXTRUDERS

from settings import TEMPFILELABEL, BUTTONDIM, BUTTONDIMWIDE, FPSTATUS_IDLE, FPSTATUS_READY, FPSTATUS_READY_DIRTY, FPSTATUS_BUSY


wildcard = "G Code (*.gcode)|*.gcode"

GCODELINETEXT = "Current G Code Line: (%d)"

reX = re.compile("(.*[xX])([0-9\.]+)(.*)")
reY = re.compile("(.*[yY])([0-9\.]+)(.*)")
reS = re.compile("(.*[sS])([0-9\.]+)(.*)")
reF = re.compile("(.*[fF])([0-9\.]+)(.*)")
reE = re.compile("(.*[eE])([0-9\.]+)(.*)")

(SlicerEvent, EVT_SLICER_UPDATE) = wx.lib.newevent.NewEvent()
SLICER_RUNNING = 1
SLICER_RUNNINGCR = 2
SLICER_FINISHED = 3
SLICER_CANCELLED = 4

TEXT_PAD = 10
MAXCFGCHARS = 50

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

(BatchSlicerEvent, EVT_BATCHSLICER_UPDATE) = wx.lib.newevent.NewEvent()
BATCHSLICER_RUNNING = 1
BATCHSLICER_FINISHED = 3
BATCHSLICER_CANCELLED = 4
BATCHSLICER_STARTFILE = 5
BATCHSLICER_ENDFILE = 6

BATCHSTLPATTERN = "%BATCHSTL%"
BATCHGCPATTERN = "%BATCHGCODE%"


class BatchSlicerThread:
	def __init__(self, win, jobs):
		self.win = win
		self.jobs = jobs
		self.running = False
		self.cancelled = False
		self.hardcancel = False

	def Start(self):
		self.running = True
		self.cancelled = False
		thread.start_new_thread(self.Run, ())

	def Stop(self, hard=True):
		self.cancelled = True
		self.hardcancel = hard

	def IsRunning(self):
		return self.running

	def Run(self):
		for stlfn, gcfn, cmd in self.jobs:
			args = shlex.split(str(cmd))
			try:
				p = subprocess.Popen(args,stderr=subprocess.STDOUT,stdout=subprocess.PIPE)
			except:
				evt = BatchSlicerEvent(msg = "Exception occurred trying to spawn slicer", state = BATCHSLICER_CANCELLED)
				wx.PostEvent(self.win, evt)
				return
		
			obuf = ''
			evt = BatchSlicerEvent(stlfn = stlfn, state = BATCHSLICER_STARTFILE)
			wx.PostEvent(self.win, evt)
			while not self.hardcancel:
				o = p.stdout.read(1)
				if o == '': break
				if o == '\r' or o == '\n':
					evt = BatchSlicerEvent(msg = obuf, state = BATCHSLICER_RUNNING)
					wx.PostEvent(self.win, evt)
					obuf = ''
				elif ord(o) < 32:
					pass
				else:
					obuf += o
				
			if not self.hardcancel:
				evt = BatchSlicerEvent(stlfn = stlfn, gcfn = gcfn, state = BATCHSLICER_ENDFILE)
				wx.PostEvent(self.win, evt)

			if self.cancelled:
				evt = BatchSlicerEvent(msg = None, state = BATCHSLICER_CANCELLED)
				wx.PostEvent(self.win, evt)
				if self.hardcancel:
					p.kill()
				break
			
		if not self.cancelled:
			p.wait()
			evt = BatchSlicerEvent(state = BATCHSLICER_FINISHED)
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
	def __init__(self, win, gcode, layer, lh, fd, acceleration):
		self.win = win
		self.gcode = gcode
		self.layer = layer
		self.lh = lh
		self.fd = fd
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
		self.model = GCode(self.gcode, self.lh, self.fd, self.acceleration)
		evt = ModelerEvent(msg = None, state = MODELER_FINISHED)
		wx.PostEvent(self.win, evt)	
		self.running = False

class FilePrepare(wx.Panel):
	def __init__(self, parent, app):
		self.model = None
		self.app = app
		self.logger = self.app.logger
		self.settings = app.settings.fileprep
		self.modified = False
		self.temporaryFile = False	
		self.gcodeLoaded = False
		self.sliceActive = False
		self.exporting = False
		self.status = FPSTATUS_IDLE
		self.dlgEdit = None
		self.dlgMerge = None
		self.dlgView = None
		self.drawGCFirst = None;
		self.drawGCLast = None;
		self.overrideValues = {}
		
		self.lh = None
		self.fd = None
		
		self.allowPulls = False

		self.shiftX = 0
		self.shiftY = 0
		
		self.gcFile = None
		self.stlFile = None
		self.images = Images(os.path.join(self.settings.cmdfolder, "images"))
		self.tbimages = Images(os.path.join(self.settings.cmdfolder, "tbimages"))
		
		if len(self.app.settings.tools) > 0:
			self.toolBar = ToolBar(self.app, self.app.settings, self.tbimages)
		else:
			print "No toolbar generated"
			self.toolBar = None

		self.slicer = self.settings.getSlicerSettings(self.settings.slicer)
		if self.slicer is None:
			print "Unable to get slicer settings"
			
		self.settings.setLoggers(self.logger)
					
		self.buildarea = app.settings.buildarea
			
		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(900, 250))
		self.SetBackgroundColour("white")
		self.Bind(EVT_SLICER_UPDATE, self.slicerUpdate)
		self.Bind(EVT_BATCHSLICER_UPDATE, self.batchSlicerUpdate)
		self.Bind(EVT_READER_UPDATE, self.readerUpdate)
		self.Bind(EVT_MODELER_UPDATE, self.modelerUpdate)

		self.sizerMain = wx.BoxSizer(wx.HORIZONTAL)
		self.sizerMain.AddSpacer((20, 20))
		
		self.sizerLeft = wx.BoxSizer(wx.VERTICAL)
		self.sizerLeft.AddSpacer((20, 20))
		self.sizerRight = wx.BoxSizer(wx.VERTICAL)
		self.sizerRight.AddSpacer((20, 20))
		
		self.sizerSlice = wx.BoxSizer(wx.HORIZONTAL)

		self.bSlice = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSlice, size=BUTTONDIM)
		self.sizerSlice.Add(self.bSlice)
		self.Bind(wx.EVT_BUTTON, self.fileSlice, self.bSlice)
		self.setSliceMode(True)
		
		self.sizerSlice.AddSpacer((20, 20))

		self.bView = wx.BitmapButton(self, wx.ID_ANY, self.images.pngView, size=BUTTONDIM)
		self.bView.SetToolTipString("Launch the STL/AMF file viewer")
		self.sizerSlice.Add(self.bView)
		self.Bind(wx.EVT_BUTTON, self.stlView, self.bView)

		self.sizerSlice.AddSpacer((20, 20))
		
		f = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		dc = wx.WindowDC(self)
		dc.SetFont(f)
		
		text = " Slicer:"
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w, h))
		t.SetFont(f)
		self.sizerSlice.Add(t, flag=wx.EXPAND | wx.ALL, border=10)
	
		self.cbSlicer = wx.ComboBox(self, wx.ID_ANY, self.settings.slicer, (-1, -1), (120, -1), self.settings.slicers, wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbSlicer.SetFont(f)
		self.cbSlicer.SetToolTipString("Choose which slicer to use")
		self.sizerSlice.Add(self.cbSlicer, flag=wx.TOP, border=10)
		self.cbSlicer.SetStringSelection(self.settings.slicer)
		self.Bind(wx.EVT_COMBOBOX, self.doChooseSlicer, self.cbSlicer)

		self.bSliceCfg = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSlicecfg, size=BUTTONDIM)
		self.bSliceCfg.SetToolTipString("Configure Chosen Slicer")
		self.sizerSlice.Add(self.bSliceCfg)
		self.Bind(wx.EVT_BUTTON, self.doSliceConfig, self.bSliceCfg)
	
		text = self.slicer.type.getConfigString()
		self.lh, self.fd = self.slicer.type.getDimensionInfo()
		w, h = dc.GetTextExtent("X" * MAXCFGCHARS)
		w = int(0.75 * w)
		self.tSlicerCfg = wx.StaticText(self, wx.ID_ANY, " " * MAXCFGCHARS, style=wx.ALIGN_RIGHT, size=(w, h))
		self.tSlicerCfg.SetFont(f)
		self.updateSlicerConfigString(text)
		self.sizerSlice.Add(self.tSlicerCfg, flag=wx.EXPAND | wx.ALL, border=10)
		
		self.sizerLeft.Add(self.sizerSlice)
		self.sizerLeft.AddSpacer((10,10))
		
		self.sizerBtns = wx.BoxSizer(wx.HORIZONTAL)
		
		self.bMerge = wx.BitmapButton(self, wx.ID_ANY, self.images.pngMerge, size=BUTTONDIM)
		self.bMerge.SetToolTipString("Merge 2 or more STL files into an AMF file")
		self.sizerBtns.Add(self.bMerge)
		self.Bind(wx.EVT_BUTTON, self.fileMerge, self.bMerge)
		
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
		
		self.bTempProf = wx.BitmapButton(self, wx.ID_ANY, self.images.pngModtemp, size=BUTTONDIM)
		self.bTempProf.SetToolTipString("Modify Temperatures")
		self.sizerBtns.Add(self.bTempProf)
		self.Bind(wx.EVT_BUTTON, self.modifyTemps, self.bTempProf)
		self.bTempProf.Enable(False)
		
		self.bSpeedProf = wx.BitmapButton(self, wx.ID_ANY, self.images.pngModspeed, size=BUTTONDIM)
		self.bSpeedProf.SetToolTipString("Modify print speeds")
		self.sizerBtns.Add(self.bSpeedProf)
		self.Bind(wx.EVT_BUTTON, self.modifySpeeds, self.bSpeedProf)
		self.bSpeedProf.Enable(False)
		
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
	
		self.bToolbox = wx.BitmapButton(self, wx.ID_ANY, self.images.pngToolbox, size=BUTTONDIM)
		self.bToolbox.SetToolTipString("Open/Show the toolbox")
		self.sizerBtns.Add(self.bToolbox)
		self.Bind(wx.EVT_BUTTON, self.showToolBox, self.bToolbox)
		
		self.sizerLeft.Add(self.sizerBtns)
		self.sizerLeft.AddSpacer((20,20))
		
		self.sizerGraph = wx.BoxSizer(wx.HORIZONTAL)

		self.gcf = GcFrame(self, self.model, self.settings, self.buildarea)
		self.sizerGraph.Add(self.gcf)
		self.sizerGraph.AddSpacer((10,10))
		sz = self.buildarea[1] * self.settings.gcodescale

		self.slideLayer = wx.Slider(
			self, wx.ID_ANY, 1, 1, 9999, size=(50, sz),
			style = wx.SL_VERTICAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
		self.slideLayer.Bind(wx.EVT_SCROLL_CHANGED, self.onSpinLayer)
		self.slideLayer.Bind(wx.EVT_MOUSEWHEEL, self.onMouseLayer)
		self.slideLayer.SetRange(1, 10)
		self.slideLayer.SetValue(1)
		self.slideLayer.SetPageSize(1);
		self.slideLayer.Disable()
		self.sizerGraph.Add(self.slideLayer)

		self.slideGCFirst = wx.Slider(
			self, wx.ID_ANY, 1, 1, 99999, size=(60, sz),
			style = wx.SL_VERTICAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
		self.slideGCFirst.Bind(wx.EVT_SCROLL_CHANGED, self.onSpinGCFirst)
		self.slideGCFirst.Bind(wx.EVT_MOUSEWHEEL, self.onMouseGCFirst)
		self.slideGCFirst.SetRange(1, 10)
		self.slideGCFirst.SetValue(1)
		self.slideGCFirst.SetPageSize(1);
		self.slideGCFirst.Disable()
		self.sizerGraph.Add(self.slideGCFirst)

		self.slideGCLast = wx.Slider(
			self, wx.ID_ANY, 1, 1, 99999, size=(60, sz),
			style = wx.SL_VERTICAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
		self.slideGCLast.Bind(wx.EVT_SCROLL_CHANGED, self.onSpinGCLast)
		self.slideGCLast.Bind(wx.EVT_MOUSEWHEEL, self.onMouseGCLast)
		self.slideGCLast.SetRange(1, 10)
		self.slideGCLast.SetValue(10)
		self.slideGCLast.SetPageSize(1);
		self.slideGCLast.Disable()
		self.sizerGraph.Add(self.slideGCLast)
		
		self.sizerLeft.Add(self.sizerGraph)
		self.sizerLeft.AddSpacer((10, 10))

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

		self.cbToolOnly = wx.CheckBox(self, wx.ID_ANY, "Tool Path Only")
		self.cbToolOnly.SetToolTipString("Show narrow lines indicating tool path")
		self.Bind(wx.EVT_CHECKBOX, self.checkToolPathsOnly, self.cbToolOnly)
		self.cbToolOnly.SetValue(self.settings.toolpathsonly)
		self.sizerOpts.Add(self.cbToolOnly)
		
		self.sizerOpts.AddSpacer((20, 10))

		self.cbBuffDC = wx.CheckBox(self, wx.ID_ANY, "Use Buffered DC")
		self.Bind(wx.EVT_CHECKBOX, self.checkBuffDC, self.cbBuffDC)
		self.cbBuffDC.SetValue(self.settings.usebuffereddc)
		self.sizerOpts.Add(self.cbBuffDC)
		
		self.sizerLeft.Add(self.sizerOpts)
		self.sizerMain.Add(self.sizerLeft)
		
		self.sizerQueues = wx.BoxSizer(wx.HORIZONTAL)
		self.sizerQueues2 = wx.BoxSizer(wx.HORIZONTAL)
		
		self.sizerQueues.AddSpacer(BUTTONDIM)
		self.sizerQueues.AddSpacer((10, 10))
		
		self.bSliceQ = wx.BitmapButton(self, wx.ID_ANY, self.images.pngBatchslice, size=BUTTONDIMWIDE)
		self.bSliceQ.SetToolTipString("Manage batch slicing queue")
		self.Bind(wx.EVT_BUTTON, self.doBatchSlice, self.bSliceQ)
		self.sizerQueues.Add(self.bSliceQ)
		self.sizerQueues.AddSpacer((10, 10))
		
		stlqlen = len(self.settings.stlqueue)
		self.bSliceStart = wx.BitmapButton(self, wx.ID_ANY, self.images.pngStartbatch, size=BUTTONDIM)
		self.bSliceStart.SetToolTipString("Begin batch slicing")
		self.Bind(wx.EVT_BUTTON, self.doBeginSlice, self.bSliceStart)
		self.sizerQueues.Add(self.bSliceStart)
		self.sizerQueues.AddSpacer((10, 10))
		self.bSliceStart.Enable(stlqlen != 0)

		self.bSlicePause = wx.BitmapButton(self, wx.ID_ANY, self.images.pngPause, size=BUTTONDIM)
		self.bSlicePause.SetToolTipString("Pause batch slicing after the current file completes")
		self.Bind(wx.EVT_BUTTON, self.doPauseSlice, self.bSlicePause)
		self.sizerQueues.Add(self.bSlicePause)
		self.sizerQueues.AddSpacer((10, 10))
		self.bSlicePause.Enable(False)

		self.bSliceStop = wx.BitmapButton(self, wx.ID_ANY, self.images.pngStop, size=BUTTONDIM)
		self.bSliceStop.SetToolTipString("Stop batch slicing immediately")
		self.Bind(wx.EVT_BUTTON, self.doStopSlice, self.bSliceStop)
		self.sizerQueues.Add(self.bSliceStop)
		self.sizerQueues.AddSpacer((10, 10))
		self.bSliceStop.Enable(False)

		self.bSliceNext = wx.BitmapButton(self, wx.ID_ANY, self.images.pngNext, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.doNextSlice, self.bSliceNext)
		self.sizerQueues.Add(self.bSliceNext)
		self.sizerQueues.AddSpacer((10, 10))
		self.bSliceNext.Enable(stlqlen != 0)
			
		self.sizerQueues.AddSpacer((5,5))
		
		szt = wx.BoxSizer(wx.VERTICAL)			
		self.tSliceQLen = wx.StaticText(self, wx.ID_ANY, "")
		szt.Add(self.tSliceQLen)
		self.setSliceQLen(stlqlen)
		
		self.cbAddBatch = wx.CheckBox(self, wx.ID_ANY, "Add to G Code Queue")
		self.cbAddBatch.SetToolTipString("Add the files created by batch slicing to the G Code Queue")
		self.Bind(wx.EVT_CHECKBOX, self.checkAddBatch, self.cbAddBatch)
		self.cbAddBatch.SetValue(self.settings.batchaddgcode)
		szt.Add(self.cbAddBatch)
		
		self.sizerQueues.Add(szt)
		
		self.bAddGCodeQ = wx.BitmapButton(self, wx.ID_ANY, self.images.pngAdd, size=BUTTONDIM)
		self.bAddGCodeQ.SetToolTipString("Add the current file to the G Code queue")
		self.Bind(wx.EVT_BUTTON, self.doAddGCodeQueue, self.bAddGCodeQ)
		self.sizerQueues2.Add(self.bAddGCodeQ)
		self.sizerQueues2.AddSpacer((10, 10))
		self.bAddGCodeQ.Enable(False)
		
		self.bGCodeQ = wx.BitmapButton(self, wx.ID_ANY, self.images.pngGcodequeue, size=BUTTONDIMWIDE)
		self.bGCodeQ.SetToolTipString("Manage G Code queue")
		self.Bind(wx.EVT_BUTTON, self.doGCodeQueue, self.bGCodeQ)
		self.sizerQueues2.Add(self.bGCodeQ)
		self.sizerQueues2.AddSpacer((10, 10))

		gcqlen = len(self.settings.gcodequeue)
		self.bGCodeNext = wx.BitmapButton(self, wx.ID_ANY, self.images.pngNext, size=BUTTONDIM)
		self.Bind(wx.EVT_BUTTON, self.doNextGCode, self.bGCodeNext)
		self.sizerQueues2.Add(self.bGCodeNext)
		self.sizerQueues2.AddSpacer((10, 10))
		self.bGCodeNext.Enable(gcqlen != 0)
		
		szt = wx.BoxSizer(wx.VERTICAL)			
		self.tGCodeQLen = wx.StaticText(self, wx.ID_ANY, "")
		szt.Add(self.tGCodeQLen)
		self.setGCodeQLen(gcqlen)
		
		self.sizerQueues2.Add(szt)

		
		self.sizerRight.Add(self.sizerQueues, 0, wx.LEFT, 1)
		self.sizerRight.AddSpacer((5, 5))
		self.sizerRight.Add(self.sizerQueues2, 0, wx.LEFT, 1)
		self.sizerRight.AddSpacer((20, 20))
		
		self.infoPane = wx.GridBagSizer()
		t = wx.StaticText(self, wx.ID_ANY, "G Code Preparation")
		f = wx.Font(18,  wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		t.SetFont(f)
		self.infoPane.AddSpacer((100, 10), pos=(0,0))
		self.infoPane.Add(t, pos=(1,0), span=(1,2), flag=wx.ALIGN_CENTER)
		
		self.infoPane.AddSpacer((20, 10), pos=(2,0))
		
		ipfont = wx.Font(12,  wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		
		dc = wx.WindowDC(self)
		dc.SetFont(ipfont)

		self.ipFileName = wx.StaticText(self, wx.ID_ANY, "")
		self.ipFileName.SetFont(ipfont)
		self.infoPane.Add(self.ipFileName, pos=(3,0), span=(1,2), flag=wx.ALIGN_LEFT)
		
		self.infoPane.AddSpacer((40, 10), pos=(4,0))
		
		text = "Layer Number: "
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, size=(w, h+TEXT_PAD))
		t.SetFont(ipfont)
		self.infoPane.Add(t, pos=(5,0), flag=wx.ALIGN_RIGHT)
		
		self.ipLayerNum = wx.StaticText(self, wx.ID_ANY, "")
		self.ipLayerNum.SetFont(ipfont)
		self.infoPane.Add(self.ipLayerNum, pos=(5,1), flag=wx.ALIGN_LEFT)
		
		text = "Height (mm): " 
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, size=(w, h+TEXT_PAD))
		t.SetFont(ipfont)
		self.infoPane.Add(t, pos=(6,0), flag=wx.ALIGN_RIGHT)
		
		self.ipLayerHeight = wx.StaticText(self, wx.ID_ANY, "")
		self.ipLayerHeight.SetFont(ipfont)
		self.infoPane.Add(self.ipLayerHeight, pos=(6,1), flag=wx.ALIGN_LEFT)

		text = "Min/Max X (mm): "
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, size=(w, h+TEXT_PAD))
		t.SetFont(ipfont)
		self.infoPane.Add(t, pos=(7,0), flag=wx.ALIGN_RIGHT)
		
		self.ipMinMaxX = wx.StaticText(self, wx.ID_ANY, "")
		self.ipMinMaxX.SetFont(ipfont)
		self.infoPane.Add(self.ipMinMaxX, pos=(7,1), flag=wx.ALIGN_LEFT)
		
		text = "Min/Max Y (mm): "
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, size=(w, h+TEXT_PAD))
		t.SetFont(ipfont)
		self.infoPane.Add(t, pos=(8,0), flag=wx.ALIGN_RIGHT)
		
		self.ipMinMaxY = wx.StaticText(self, wx.ID_ANY, "")
		self.ipMinMaxY.SetFont(ipfont)
		self.infoPane.Add(self.ipMinMaxY, pos=(8,1), flag=wx.ALIGN_LEFT)
		
		text = "Filament (mm): "
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, size=(w, h+TEXT_PAD))
		t.SetFont(ipfont)
		self.infoPane.Add(t, pos=(9,0), flag=wx.ALIGN_RIGHT)
		
		self.ipFilament = []
		ln = 9
		for i in range(MAX_EXTRUDERS):
			w = wx.StaticText(self, wx.ID_ANY, "", size=(-1, h+TEXT_PAD))
			w.SetFont(ipfont)
			self.infoPane.Add(w, pos=(ln, 1), flag=wx.ALIGN_LEFT)
			ln += 1
			self.ipFilament.append(w)
		
		text = "Temp Profile: "
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, size=(w, h+TEXT_PAD))
		t.SetFont(ipfont)
		self.infoPane.Add(t, pos=(ln,0), flag=wx.ALIGN_RIGHT)
		
		self.ipTempProf = wx.StaticText(self, wx.ID_ANY, "")
		self.ipTempProf.SetFont(ipfont)
		self.infoPane.Add(self.ipTempProf, pos=(ln,1), flag=wx.ALIGN_LEFT)
		
		ln += 1
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
		
		ln += 2
		ipHeight = dc.GetTextExtent("20")[1] + TEXT_PAD
		self.ipGCodeLine = wx.StaticText(self, wx.ID_ANY, "", size=(-1, ipHeight))
		self.ipGCodeLine.SetFont(ipfont)
		self.infoPane.Add(self.ipGCodeLine, pos=(ln,0), flag=wx.ALIGN_LEFT)
		
		self.ipGCodeSource = wx.StaticText(self, wx.ID_ANY, "")
		self.ipGCodeSource.SetFont(ipfont)
		self.infoPane.Add(self.ipGCodeSource, pos=(ln+1, 0), span=(1, 2), flag=wx.ALIGN_LEFT)

		self.sizerRight.Add(self.infoPane)
		self.sizerRight.AddSpacer((5,5))

		ovsizer = wx.BoxSizer(wx.HORIZONTAL);
		ovsizer.AddSpacer((20, 20))
		
		self.bOverride = wx.BitmapButton(self, wx.ID_ANY, self.images.pngOverride, size=BUTTONDIM)
		self.bOverride.SetToolTipString("Override slicer settings")
		ovsizer.Add(self.bOverride, 0, wx.TOP, 40)
		self.Bind(wx.EVT_BUTTON, self.doOverride, self.bOverride)
		ovsizer.AddSpacer((20, 20))
		
		ovlistsizer = wx.BoxSizer(wx.VERTICAL)
		ovlistsizer.AddSpacer((10, 10))

		t = wx.StaticText(self, wx.ID_ANY, "Overrides Selected:")
		ovlistsizer.Add(t, 0, wx.ALL, 5)

		self.teOverride = wx.TextCtrl(self, -1, "", size=(300, 180), style=wx.TE_MULTILINE|wx.TE_READONLY)
		ovlistsizer.Add(self.teOverride, 0, wx.ALL, 5)
		
		ovsizer.Add(ovlistsizer)
		self.sizerRight.AddSpacer((10, 10))
		self.sizerRight.Add(ovsizer)
		self.displayOverrides(self.getOverrideSummary(self.overrideValues))
	
		self.sizerMain.Add(self.sizerRight)
		
		self.SetSizer(self.sizerMain)
		self.Layout()
		self.Fit()
		
	def doBatchSlice(self, evt):
		stllist = self.settings.stlqueue[:]
		dlg = SliceQueue(self, stllist, self.settings, self.images)
		if dlg.ShowModal() == wx.ID_OK:
			self.settings.stlqueue = dlg.getSliceQueue()
			self.settings.setModified()
			n = len(self.settings.stlqueue)
			self.setSliceQLen(n)
			self.bSliceStart.Enable(n != 0)
			self.bSliceNext.Enable(n != 0)
				
		dlg.Destroy();
		
	def setSliceQLen(self, qlen):
		self.tSliceQLen.SetLabel("%d files in queue" % qlen)
		s = "Remove the first file and slice it"
		if qlen != 0:
			s += ": (" + os.path.basename(self.settings.stlqueue[0]) + ")"
		self.bSliceNext.SetToolTipString(s)
				
	def checkAddBatch(self, evt):
		self.settings.batchaddgcode = evt.IsChecked()
		self.settings.setModified()
		
	def doBeginSlice(self, evt):
		if self.settings.batchaddgcode:
			s = ""
		else:
			s = "NOT "
		self.logger.LogMessage("Beginning batch slice.  Resultant G Code files will " + s + "be saved in the G Code queue")
		self.logOverrides(self.overrideValues)
		self.slicer.setOverrides(self.overrideValues)
		
		saveStlFile = self.stlFile
		saveGcFile = self.gcFile
		self.stlFile = BATCHSTLPATTERN
		self.gcFile = BATCHGCPATTERN
		self.lh, self.fd = self.slicer.type.getDimensionInfo()
		cmd = self.slicer.buildSliceCommand()

		self.stlFile = saveStlFile
		self.gcFile = saveGcFile
		
		joblist = []
		
		for fn in self.settings.stlqueue:
			gcfn = self.slicer.buildSliceOutputFile(fn)
			c = cmd.replace(BATCHSTLPATTERN, fn).replace(BATCHGCPATTERN, gcfn)
			joblist.append([fn, gcfn, c])
			
		self.batchSliceThread = BatchSlicerThread(self, joblist)
			
		self.bSliceStart.Enable(False)
		self.bSlice.Enable(False)
		self.bSliceQ.Enable(False)
		self.bSliceNext.Enable(False)
		self.bSlicePause.Enable(True)
		self.bSliceStop.Enable(True)
		self.batchSliceThread.Start()
		
	def doPauseSlice(self, evt):
		self.bSliceStop.Enable(False)
		self.bSlicePause.Enable(False)
		self.batchSliceThread.Stop(False)
	
	def doStopSlice(self, evt):
		self.bSliceStop.Enable(False)
		self.bSlicePause.Enable(False)
		self.batchSliceThread.Stop()
	
	def doNextSlice(self, evt):
		fn = self.settings.stlqueue[0]
		self.settings.stlqueue = self.settings.stlqueue[1:]
		self.setSliceQLen(len(self.settings.stlqueue))
		self.nextSliceProhibit()
		self.sliceFile(fn)

	def nextSliceAllow(self):
		if len(self.settings.stlqueue) != 0:
			self.bSliceStart.Enable(True)
			self.bSliceNext.Enable(True)
		if len(self.settings.gcodequeue) != 0:
			self.bGCodeNext.Enable(True)
	
	def nextSliceProhibit(self):
		self.bSliceStart.Enable(False)
		self.bSliceNext.Enable(False)
		self.bGCodeNext.Enable(False)
	
	def doGCodeQueue(self, evt):
		gclist = self.settings.gcodequeue[:]
		dlg = GCodeQueue(self, gclist, self.settings, self.images)
		if dlg.ShowModal() == wx.ID_OK:
			self.settings.gcodequeue = dlg.getGCodeQueue()
			self.settings.setModified()
			n = len(self.settings.gcodequeue)
			self.setGCodeQLen(n)
			self.bGCodeNext.Enable(n != 0)
				
		dlg.Destroy();
		
	def doAddGCodeQueue(self, evt):
		if not self.gcFile in self.settings.gcodequeue:
			self.settings.gcodequeue.append(self.gcFile)
			self.addGCodeQEnable(False)
			n = len(self.settings.gcodequeue)
			self.setGCodeQLen(n)
			self.bGCodeNext.Enable(n != 0)
	
	def addGCodeQueueEnable(self, enable):
		if enable and self.gcFile in self.settings.gcodequeue:
			enable = False   # duplicate - no need to add
			
		self.bAddGCodeQ.Enable(enable)
			
	def setGCodeQLen(self, qlen):
		self.tGCodeQLen.SetLabel("%d files in queue" % qlen)
		s = "Remove the first file and load it"
		if qlen != 0:
			s += ": (" + os.path.basename(self.settings.gcodequeue[0]) + ")"
		self.bGCodeNext.SetToolTipString(s)
	
	def doNextGCode(self, evt):
		fn = self.settings.gcodequeue[0]
		self.settings.gcodequeue = self.settings.gcodequeue[1:]
		self.setGCodeQLen(len(self.settings.gcodequeue))
		self.nextSliceProhibit()
		self.loadFile(fn)
		
	def batchSlicerUpdate(self, evt):
			
		if evt.state == BATCHSLICER_RUNNING:
			if evt.msg is not None:
				self.logger.LogMessage("(s) - " + evt.msg)
				
		elif evt.state == BATCHSLICER_CANCELLED:
			if len(self.settings.stlqueue) != 0:
				self.bSliceStart.Enable(True)
				self.bSliceNext.Enable(True)
			self.bSliceQ.Enable(True)
			self.bSlice.Enable(True)
			self.bSliceStop.Enable(False)
			self.bSlicePause.Enable(False)
			self.logger.LogMessage("Batch Slicer: Cancelled")
			
		elif evt.state == BATCHSLICER_FINISHED:
			self.logger.LogMessage("Batch Slicer: finished all files")
			self.settings.stlqueue = []
			self.setSliceQLen(0)
			self.bSliceQ.Enable(True)
			self.bSliceStart.Enable(False)
			self.bSlice.Enable(True)
			self.bSliceNext.Enable(False)
			self.bSliceStop.Enable(False)
			self.bSlicePause.Enable(False)
		
		elif evt.state == BATCHSLICER_STARTFILE:
			self.logger.LogMessage("Batch Slicer: starting file: " + evt.stlfn)
		
		elif evt.state == BATCHSLICER_ENDFILE:
			self.logger.LogMessage("Batch Slicer: finished file: " + evt.stlfn)
			if self.settings.batchaddgcode:
				if evt.gcfn in self.settings.gcodequeue:
					self.logger.LogMessage("G Code file %s is already in queue" % evt.gcfn)
				else:
					self.logger.LogMessage("Adding %s to G Code queue" % evt.gcfn)
					self.settings.gcodequeue.append(evt.gcfn)
					self.setGCodeQLen(len(self.settings.gcodequeue))
					self.settings.setModified()
			try:
				self.settings.stlqueue.remove(evt.stlfn)
			except:
				pass
			
			self.setSliceQLen(len(self.settings.stlqueue))
			
		else:
			self.logger.LogError("unknown slicer thread state: %s" % evt.state)

		
	def doOverride(self, evt):
		dlg = Override(self, self.overrideValues, self.slicer.type.getOverrideHelpText())
		dlg.CenterOnScreen()
		if dlg.ShowModal() == wx.ID_OK:
			self.overrideValues = dlg.getOverrides()
			self.displayOverrides(self.getOverrideSummary(self.overrideValues))
			
		dlg.Destroy()

	def getOverrideSummary(self, ovVals):
		result = []
		for k in ovKeyOrder:
			if k in ovVals.keys():
				result.append("%s = %s" % (ovUserKeyMap[k], ovVals[k]))
				
		return result
	
	def displayOverrides(self, ovSummary):
		self.teOverride.Clear()
		if len(ovSummary) == 0:
			self.teOverride.AppendText("None")
			return
		
		c = ""
		for l in ovSummary:
			self.teOverride.AppendText(c+l)
			c = '\n'
	
	def logOverrides(self, ovVals):
		for k in ovKeyOrder:
			if k in ovVals.keys():
				self.logger.LogMessage("Overriding %s = %s" % (ovUserKeyMap[k], self.overrideValues[k]))
		
	def getSlicerConfigString(self):
		return self.slicer.getSlicerName() + ": " + self.slicer.getConfigString()
		
	def updateSlicerConfigString(self, text):
		if len(text) > MAXCFGCHARS:
			text = text[:MAXCFGCHARS]
		self.tSlicerCfg.SetLabel(text)

	def doChooseSlicer(self, evt):
		self.settings.slicer = self.cbSlicer.GetValue()
		self.settings.setModified()
		self.slicer = self.settings.getSlicerSettings(self.settings.slicer)
		if self.slicer is None:
			self.logger.LogError("Unable to get slicer settings") 
		self.updateSlicerConfigString(self.slicer.type.getConfigString())	
		self.lh, self.fd = self.slicer.type.getDimensionInfo()
		
	def doSliceConfig(self, evt):
		if self.slicer.configSlicer():
			self.updateSlicerConfigString(self.slicer.type.getConfigString())	
			self.lh, self.fd = self.slicer.type.getDimensionInfo()
		
	def stlView(self, evt):
		self.dlgView = StlViewer(self)
		self.dlgView.CenterOnScreen()
		self.dlgView.Show()
		
	def stlViewExit(self):
		self.dlgView = None

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

		if self.toolBar:
			self.toolBar.Destroy()
		if self.dlgView:
			self.dlgView.Destroy()
		if self.dlgMerge:
			self.dlgMerge.Destroy()	
		if self.dlgEdit:
			self.dlgEdit.Destroy()	
		return True
	
	def setAllowPulls(self, flag):
		self.allowPulls = flag
		self.app.assertAllowPulls(flag)
	
	def pullGCode(self, printmon):
		if not self.allowPulls:
			return
		self.disableButtons()
		self.setAllowPulls(False)
		self.exporting = True
		self.exportTo = printmon
		self.logger.LogMessage("Beginning forwarding to print monitor")
		self.status = FPSTATUS_BUSY
		self.app.updateFilePrepStatus(self.status)
		self.modelerThread = ModelerThread(self, self.gcode, 0, self.lh, self.fd, self.settings.acceleration)
		self.modelerThread.Start()
		
	def fileSlice(self, event):
		if self.sliceActive:
			self.sliceThread.Stop()
			self.bSlice.Enable(False)
			self.setAllowPulls(False)
			self.bOpen.Enable(False)
			self.bMerge.Enable(False)
			return
		
		if self.checkModified(message='Close file without saving changes?'):
			return
		
		dlg = wx.FileDialog(
			self, message="Choose an STL file",
			defaultDir=self.settings.laststldirectory, 
			defaultFile="",
			wildcard=self.slicer.fileTypes(),
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
		self.gcFile = self.slicer.buildSliceOutputFile(fn)
		self.logOverrides(self.overrideValues)
		self.slicer.setOverrides(self.overrideValues)
		self.lh, self.fd = self.slicer.type.getDimensionInfo()
		cmd = self.slicer.buildSliceCommand()
		self.sliceThread = SlicerThread(self, cmd)
		self.gcodeLoaded = False
		self.nextSliceProhibit()
		self.bOpen.Enable(False)
		self.bMerge.Enable(False)
		self.disableEditButtons()
		self.setAllowPulls(False)
		self.setSliceMode(False)
		self.sliceActive = True
		self.status = FPSTATUS_BUSY
		self.app.updateFilePrepStatus(self.status)
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
			self.slicer.sliceComplete()
			self.sliceActive = False
			self.status = FPSTATUS_IDLE
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
			self.slicer.sliceComplete()
			if os.path.exists(self.gcFile):
				self.loadFile(self.gcFile)
			else:
				self.logger.LogMessage("Slicer failed to produce expected G Code file: %s" % self.gcFile)
				self.gcFile = None
				self.bOpen.Enable(True)
				self.nextSliceAllow()
				self.bMerge.Enable(True)
				self.status = FPSTATUS_IDLE
				self.app.updateFilePrepStatus(self.status)
			
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
		
	def fileMerge(self, event):
		self.disableButtons()
		if self.dlgMerge is None:
			self.dlgMerge = StlMergeDlg(self)
			self.dlgMerge.CenterOnScreen()
			self.dlgMerge.Show()
		
	def dlgMergeClosed(self):
		self.dlgMerge = None
		self.enableButtons()

	def loadFile(self, fn):
		self.status = FPSTATUS_BUSY
		self.app.updateFilePrepStatus(self.status)
		self.bOpen.Enable(False)
		self.bMerge.Enable(False)
		self.bSlice.Enable(False)
		self.disableEditButtons()
		self.setAllowPulls(False)
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
			self.setModified(False)		
			self.buildModel()
		
			if self.temporaryFile:
				self.addGCodeQueueEnable(False)
				try:
					self.logger.LogMessage("Removing temporary G Code file: %s" % self.gcFile)
					os.unlink(self.gcFile)
				except:
					pass
			else:
				self.addGCodeQueueEnable(True)

			
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
			self.app.updateFilePrepStatus(FPSTATUS_IDLE)
			self.status = FPSTATUS_IDLE
		
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
		self.modelerThread = ModelerThread(self, self.gcode, layer, self.lh, self.fd, self.settings.acceleration)
		self.modelerThread.Start()
		
	def getModelData(self, layer=0):
		self.layerCount = self.model.countLayers()
		
		self.layerInfo = self.model.getLayerInfo(layer)
		if self.layerInfo is None:
			return
		
		self.showLayerInfo(layer)

		self.currentGCLine = self.layerInfo[4][0]
		self.firstGLine = self.layerInfo[4][0]
		self.lastGLine = self.layerInfo[4][-1]
		
		self.slideLayer.SetRange(1, self.layerCount)
		self.slideLayer.SetValue(layer+1)
		n = int(self.layerCount/20)
		if n<1: n=1
		self.slideLayer.SetTickFreq(n, 1)
		self.slideLayer.SetPageSize(1)
		self.slideLayer.Enable()
		self.slideLayer.Refresh()
		
		self.slideGCFirst.SetRange(self.firstGLine+1, self.lastGLine+1)
		self.slideGCFirst.SetValue(self.firstGLine+1)
		self.drawGCFirst = self.firstGLine
		self.slideGCLast.SetRange(self.firstGLine+1, self.lastGLine+1)
		self.slideGCLast.SetValue(self.lastGLine+1)
		self.drawGCLast = self.lastGLine
		
		n = int((self.lastGLine-self.firstGLine)/20)
		if n<1: n=1
		self.slideGCFirst.SetTickFreq(n, 1)
		self.slideGCFirst.SetPageSize(1)
		self.slideGCFirst.Enable()
		self.slideGCFirst.Refresh()
		self.slideGCLast.SetTickFreq(n, 1)
		self.slideGCLast.SetPageSize(1)
		self.slideGCLast.Enable()
		self.slideGCLast.Refresh()
		
		self.ipGCodeSource.SetLabel(self.model.lines[self.currentGCLine].orig)
		self.ipGCodeLine.SetLabel(GCODELINETEXT % (self.currentGCLine+1))
		
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
			self.nextSliceAllow()
			if self.exporting:
				if self.temporaryFile:
					name = TEMPFILELABEL
				else:
					name = self.gcFile
					
				self.logger.LogMessage("Modeling complete - forwarding %s to printer %s" % (name, self.exportTo.prtname))
				self.exportTo.forwardModel(model, name=name)
				self.exportTo = None
				self.logger.LogMessage("Forwarding complete")
				self.enableButtons()

			else:
				self.model = model
				self.getModelData(self.modelerThread.getLayer())			
				self.logger.LogMessage("Min/Max X: %.2f/%.2f" % (self.model.xmin, self.model.xmax))
				self.logger.LogMessage("Min/Max Y: %.2f/%.2f" % (self.model.ymin, self.model.ymax))
				self.logger.LogMessage("Max Z: %.2f" % self.model.zmax)
				self.logger.LogMessage("Total Filament Length: %s" % str(self.model.total_e))
				self.logger.LogMessage("Estimated duration: %s" % formatElapsed(self.model.duration))
				self.enableButtons();
				
			if self.modified:
				self.status = FPSTATUS_READY_DIRTY
			else:
				self.status = FPSTATUS_READY
			self.app.updateFilePrepStatus(self.status)

			
		elif evt.state == MODELER_CANCELLED:
			if evt.msg is not None:
				self.logger.LogMessage(evt.msg)
				
			self.enableButtons()
			self.nextSliceAllow()
			self.model = None
				
			self.status = FPSTATUS_IDLE
			self.app.updateFilePrepStatus(self.status)
				
		else:
			self.logger.LogError("unknown modeler thread state: %s" % evt.state)
		
	def enableButtons(self):
		self.bOpen.Enable(True)
		self.bMerge.Enable(True)
		self.bSlice.Enable(True)
		self.bSave.Enable(self.gcodeLoaded)
		self.bSaveLayer.Enable(self.gcodeLoaded)
		self.bFilamentChange.Enable(self.gcodeLoaded)
		self.bShift.Enable(self.gcodeLoaded)
		self.bTempProf.Enable(self.gcodeLoaded)
		self.bSpeedProf.Enable(self.gcodeLoaded)
		self.bEdit.Enable(self.gcodeLoaded)
		self.setAllowPulls(self.gcodeLoaded)
		
	def disableButtons(self):
		self.bOpen.Enable(False)
		self.bMerge.Enable(False)
		self.bSlice.Enable(False)
		self.bSave.Enable(False)
		self.bSaveLayer.Enable(False)
		self.bFilamentChange.Enable(False)
		self.bShift.Enable(False)
		self.bTempProf.Enable(False)
		self.bSpeedProf.Enable(False)
		self.bEdit.Enable(False)
		self.setAllowPulls(False)
		
	def disableEditButtons(self):
		self.bSave.Enable(False)
		self.bSaveLayer.Enable(False)
		self.bFilamentChange.Enable(False)
		self.bShift.Enable(False)
		self.bTempProf.Enable(False)
		self.bSpeedProf.Enable(False)
		self.bEdit.Enable(False)

	def editGCode(self, event):
		self.disableButtons()
		if self.dlgEdit is None:
			self.dlgEdit = EditGCodeDlg(self)
			self.dlgEdit.CenterOnScreen()
			self.dlgEdit.Show()
		
	def dlgClosed(self, rc, data):
		self.dlgEdit = None
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
		self.status = FPSTATUS_BUSY
		self.app.updateFilePrepStatus(self.status)
		self.logger.LogMessage("Applying axis shift in G Code")
		for i in range(len(self.gcode)):
			l = self.gcode[i]
			l = self.applyAxisShift(l, 'x', self.shiftX)
			l = self.applyAxisShift(l, 'y', self.shiftY)
			self.gcode[i] = l

		self.shiftX = 0
		self.shiftY = 0
		self.setModified(True)
		l = self.gcf.getCurrentLayer()
		self.buildModel(layer=l)

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
	
	def modifyTemps(self, event):
		dlg = ModifyTempsDlg(self)
		dlg.CenterOnScreen()
		val = dlg.ShowModal()

		if val == wx.ID_OK:
			modTemps = dlg.getResult()
			self.applyTempChange(modTemps)

		dlg.Destroy()

	def applyTempChange(self, temps):
		self.status = FPSTATUS_BUSY
		self.app.updateFilePrepStatus(self.status)
		self.logger.LogMessage("Modifying temperature in G Code")
		self.currentTool = 0
		for i in range(len(self.gcode)):
			l = self.applySingleTempChange(self.gcode[i], temps)
			self.gcode[i] = l

		self.setModified(True)
		l = self.gcf.getCurrentLayer()
		self.buildModel(layer=l)

	def applySingleTempChange(self, s, temps):
		if "m104" in s.lower() or "m109" in s.lower():
			m = reS.match(s)
			difference = temps[1][self.currentTool]
		elif "m140" in s.lower() or "m190" in s.lower():
			m = reS.match(s)
			difference = temps[0]
		elif s.startswith("T"):
			try:
				t = int(s[1:])
			except:
				t = None

			if t is not None:
				self.currentTool = t
			return s
		else:
			return s

		if m is None or m.lastindex != 3:
			return s

		value = float(m.group(2))
		if value == 0.0:
			return s

		value += float(difference)
		return "%s%s%s" % (m.group(1), str(value), m.group(3))

	def modifySpeeds(self, event):
		dlg = ModifySpeedDlg(self)
		dlg.CenterOnScreen()
		val = dlg.ShowModal()

		if val == wx.ID_OK:
			modSpeeds = dlg.getResult()
			self.applySpeedChange(modSpeeds)

		dlg.Destroy()

	def applySpeedChange(self, speeds):
		self.status = FPSTATUS_BUSY
		self.app.updateFilePrepStatus(self.status)
		self.logger.LogMessage("Modifying speeds in G Code")
		self.currentTool = 0
		for i in range(len(self.gcode)):
			l = self.applySingleSpeedChange(self.gcode[i], speeds)
			self.gcode[i] = l

		self.setModified(True)
		l = self.gcf.getCurrentLayer()
		self.buildModel(layer=l)

	def applySingleSpeed(self, s, speeds):
		if "m117" in s or "M117" in s:
			return s

		m = reF.match(s)
		if m is None or m.lastindex != 3:
			return s

		e = reE.match(s)
		if e is None: #no extrusion - must  be a move
			factor = speeds[1]
		else:
			factor = speeds[0]

		value = float(m.group(2)) * float(factor)
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
		self.gcFile = path
		self.addGCodeQueueEnable(True)

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
		
		info = self.model.getLayerInfo(v[0])
		sx = info[4][0]
		sTool = self.model.findToolByLine(sx)
		info = self.model.getLayerInfo(v[1])
		ex = info[4][1]
		eTool = self.model.findToolByLine(ex)
		z = info[0]
		
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
		
		for ln in self.gcode[sx:ex+1]:
			fp.write(ln + "\n")
		
		if v[7]:
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
		self.gcode[self.currentGCLine:self.currentGCLine] = gc
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
		
	def checkToolPathsOnly(self, evt):
		self.settings.toolpathsonly = evt.IsChecked()
		self.settings.setModified()
		self.gcf.setToolPathsOnly(self.settings.toolpathsonly)
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
		
	def showToolBox(self, evt):	
		if self.toolBar.IsShown():
			self.toolBar.Raise()
		else:
			self.toolBar.Show()
		
	def onMouseGCFirst(self, evt):
		l = self.slideGCFirst.GetValue()-1
		if evt.GetWheelRotation() < 0:
			l += 1
		else:
			l -= 1
		if l >= self.firstGLine and l < self.lastGLine:
			self.setGCode(l, None)

		self.gcf.setGCode(self.drawGCFirst, self.drawGCLast)
		
	def onMouseGCLast(self, evt):
		l = self.slideGCLast.GetValue()-1
		if evt.GetWheelRotation() < 0:
			l += 1
		else:
			l -= 1
		if l > self.firstGLine and l <= self.lastGLine:
			self.setGCode(None, l)

		self.gcf.setGCode(self.drawGCFirst, self.drawGCLast)

	def onSpinGCFirst(self, evt):
		l = evt.EventObject.GetValue()-1
		if l < self.firstGLine:
			l = self.firstGLine
		elif l >= self.lastGLine:
			l = self.lastGLine - 1

		self.setGCode(l, None)

		self.gcf.setGCode(self.drawGCFirst, self.drawGCLast)

	def onSpinGCLast(self, evt):
		l = evt.EventObject.GetValue()-1
		if l <= self.firstGLine:
			l = self.firstGLine + 1
		elif l > self.lastGLine:
			l = self.lastGLine

		self.setGCode(None, l)

		self.gcf.setGCode(self.drawGCFirst, self.drawGCLast)
		
	def setGCode(self, newFirst, newLast):
		if not newFirst is None:
			if newFirst >= self.firstGLine and newFirst < self.lastGLine:
				self.currentGCLine = newFirst
				self.drawGCFirst = newFirst
				self.ipGCodeSource.SetLabel(self.model.lines[newFirst].orig)
				self.ipGCodeLine.SetLabel(GCODELINETEXT % (newFirst+1))
				self.slideGCFirst.SetValue(newFirst+1)
				if newFirst >= self.drawGCLast:
					self.drawGCLast = newFirst + 1
					self.slideGCLast.SetValue(self.drawGCLast + 1)

		if not newLast is None:
			if newLast > self.firstGLine and newLast <= self.lastGLine:
				self.slideGCLast.SetValue(newLast+1)
				self.drawGCLast = newLast
				if newLast <= self.drawGCFirst:
					self.drawGCFirst = newLast - 1
					self.slideGCFirst.SetValue(self.drawGCFirst + 1)
		
		if newFirst is None and newLast is None:
			self.ipGCodeSource.SetLabel("")
			self.ipGCodeLine.SetLabel("")
		
	def onMouseLayer(self, evt):
		l = self.slideLayer.GetValue()-1
		if evt.GetWheelRotation() < 0:
			l += 1
		else:
			l -= 1
		if l >= 0 and l < self.layerCount:
			self.setLayer(l)
			self.gcf.setLayer(l)

	def onSpinLayer(self, evt):
		l = evt.EventObject.GetValue()-1
		self.setLayer(l)
		self.gcf.setLayer(l)
		
	def setLayer(self, l):
		if l >=0 and l < self.layerCount:
			self.slideLayer.SetValue(l+1)
			
			self.layerInfo = self.model.getLayerInfo(l)
			if self.layerInfo is None:
				return
	
			self.currentGCLine = self.layerInfo[4][0]
			self.firstGLine = self.layerInfo[4][0]
			self.lastGLine = self.layerInfo[4][-1]
			self.drawGCFirst = self.layerInfo[4][0]
			self.drawGCLast = self.layerInfo[4][-1]
		
			if self.firstGLine >= self.lastGLine:
				self.slideGCFirst.SetRange(self.firstGLine+1, self.firstGLine+2)
				self.slideGCFirst.SetValue(self.firstGLine+1)
				self.slideGCFirst.Enable(False)
				self.slideGCLast.SetRange(self.firstGLine+1, self.firstGLine+2)
				self.slideGCLast.SetValue(self.firstGLine+1)
				self.slideGCLast.Enable(False)
			else:
				self.slideGCFirst.SetRange(self.firstGLine+1, self.lastGLine+1)
				self.slideGCFirst.SetValue(self.firstGLine+1)
				n = int((self.lastGLine-self.firstGLine)/20)
				if n<1: n=1
				self.slideGCFirst.SetTickFreq(n, 1)
				self.slideGCFirst.SetPageSize(1);
				self.slideGCFirst.Refresh()
				self.slideGCFirst.Enable(True)
				self.slideGCLast.SetRange(self.firstGLine+1, self.lastGLine+1)
				self.slideGCLast.SetValue(self.lastGLine+1)
				self.slideGCLast.SetTickFreq(n, 1)
				self.slideGCLast.SetPageSize(1);
				self.slideGCLast.Refresh()
				self.slideGCLast.Enable(True)
			
			self.showLayerInfo(l)
			
			if self.model.checkPendingPause(l+1):
				# TODO Pending Pause at start of this layer
				pass
			plines = self.model.checkImmediatePause(l+1)
			if len(plines) > 0:
				# TODO ct Immediate Pauses on this layer
				pass

			
			self.ipGCodeSource.SetLabel(self.model.lines[self.currentGCLine].orig)
			self.ipGCodeLine.SetLabel(GCODELINETEXT % (self.currentGCLine+1))
			
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
		
		(bed, hes) = self.model.getTemps()
		if bed is None:
			tp = "B:??"
		else:
			tp = "B:%.1f" % bed
		for i in range(MAX_EXTRUDERS):
			if hes[i] is None:
				tp += " / T%d:??" % i
			else:
				tp += " / T%d:%.1f" % (i, hes[i])
				
		self.ipTempProf.SetLabel(tp)
		
	def setModified(self, flag=True):
		self.modified = flag
		newstat = False
		
		if self.modified:
			if self.status in [ FPSTATUS_READY  ]:
				self.status = FPSTATUS_READY_DIRTY
				newstat = True
		else:
			if self.status == FPSTATUS_READY_DIRTY:
				self.status = FPSTATUS_READY
				newstat = True
				
		if newstat:
			self.app.updateFilePrepStatus(self.status)
			
		if self.temporaryFile:
			fn = TEMPFILELABEL
		else:
			if len(self.gcFile) > 60:
				fn = os.path.basename(self.gcFile)
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
		

