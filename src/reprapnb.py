import os.path
import sys, inspect
import wx
import time

cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
if cmd_folder not in sys.path:
	sys.path.insert(0, cmd_folder)
	
from settings import (Settings, MAINTIMER, FPSTATUS_READY, FPSTATUS_READY_DIRTY, FPSTATUS_BUSY, FPSTATUS_IDLE,
					PMSTATUS_NOT_READY, PMSTATUS_READY, PMSTATUS_PRINTING, PMSTATUS_PAUSED,
					BATCHSL_IDLE, BATCHSL_RUNNING)
from fileprep import FilePrepare
from printmon import PrintMonitor
from manualctl import ManualControl
from logger import Logger
from images import Images
from reprapserver import RepRapServer
from tools import formatElapsed
from gcref import GCRef
from connection import ConnectionManagerPanel
from history import History

LOGGER_TAB_TEXT = "Log"
GCREF_TAB_TEXT = "G Code Reference"
PLATER_TAB_TEXT = "Plater"
FILEPREP_TAB_TEXT = "File Preparation"
CONNMGR_TAB_TEXT = "Connection Manager"
MANCTL_TAB_TEXT = "Manual Control: %s"
PRTMON_TAB_TEXT = "Print Monitor: %s"

NBWIDTH = 1500
NBHEIGHT = 930
bkgd = wx.Colour(229, 214, 169)

class MainFrame(wx.Frame):
	def __init__(self):
		self.timer = None
		self.logger = None
		
		self.allowPulls = False
		self.shuttingDown = False
		self.fpstatus = FPSTATUS_READY
		self.batchslstatus = BATCHSL_IDLE
		
		self.pgPrinters = {}
		self.pgManCtl = {}
		self.pxManCtl = {}
		self.pgPrtMon = {}
		self.connected = {}
		self.printing = {}
		
		wx.Frame.__init__(self, None, title="Rep Rap Notebook", size=[NBWIDTH, NBHEIGHT])
		
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)        

		self.Bind(wx.EVT_CLOSE, self.onClose)
		
		self.settings = Settings(self, cmd_folder)
		self.history = History(self.settings)
		
		ico = wx.Icon(os.path.join(self.settings.cmdfolder, "images", "rrh.ico"), wx.BITMAP_TYPE_ICO)
		self.SetIcon(ico)

		self.httpServer = None

		self.images = Images(os.path.join(self.settings.cmdfolder, "images"))
		self.nbil = wx.ImageList(16, 16)
		self.nbilAttentionIdx = self.nbil.Add(self.images.pngAttention)
		self.nbilLoadedCleanIdx = self.nbil.Add(self.images.pngLoadedclean)
		self.nbilLoadedDirtyIdx = self.nbil.Add(self.images.pngLoadeddirty)
		self.nbilNotReadyIdx = self.nbil.Add(self.images.pngNotready)
		self.nbilReadyIdx = self.nbil.Add(self.images.pngReady)
		self.nbilReadyDirtyIdx = self.nbil.Add(self.images.pngReadydirty)
		self.nbilPrintingIdx = self.nbil.Add(self.images.pngPrinting)
		self.nbilPausedIdx = self.nbil.Add(self.images.pngPaused)
		self.nbilIdleIdx = self.nbil.Add(self.images.pngIdle)
		self.nbilNotReadyBSIdx = self.nbil.Add(self.images.pngNotreadybs)
		self.nbilReadyBSIdx = self.nbil.Add(self.images.pngReadybs)
		self.nbilReadyDirtyBSIdx = self.nbil.Add(self.images.pngReadydirtybs)
		self.nbilIdleBSIdx = self.nbil.Add(self.images.pngIdlebs)

		p = wx.Panel(self)
		sizer = wx.BoxSizer(wx.VERTICAL)

		sizerBtns = wx.BoxSizer(wx.HORIZONTAL)
		
		self.nb = wx.Notebook(p, size=(NBWIDTH, NBHEIGHT), style=wx.NB_TOP)
		self.nb.SetBackgroundColour(bkgd)
		self.nb.AssignImageList(self.nbil)
		self.Show()

		self.logger = Logger(self.nb, self)
		self.logger.SetBackgroundColour(bkgd)
		self.pgGCodeRef = GCRef(self.nb, self, cmd_folder)
		self.pgGCodeRef.SetBackgroundColour(bkgd)
		self.pgConnMgr = ConnectionManagerPanel(self.nb, self)
		self.pgConnMgr.SetBackgroundColour(bkgd)
	
		self.pxLogger = 0
		self.pxGCodeRef = 1
		self.pxFilePrep = 2
		self.pxConnMgr = 3

		self.pgFilePrep = FilePrepare(self.nb, self, self.history)
		self.pgFilePrep.SetBackgroundColour(bkgd)

		self.nb.AddPage(self.logger, LOGGER_TAB_TEXT, imageId=-1)
		self.nb.AddPage(self.pgGCodeRef, GCREF_TAB_TEXT, imageId=-1)
		self.nb.AddPage(self.pgFilePrep, FILEPREP_TAB_TEXT, imageId=self.nbilIdleIdx)
		self.nb.AddPage(self.pgConnMgr, CONNMGR_TAB_TEXT, imageId=-1)

		sizer.AddSpacer((20,20))
		sizer.Add(sizerBtns)
		sizer.AddSpacer((10,10))
		sizer.Add(self.nb)
		p.SetSizer(sizer)
		
		self.nb.SetSelection(self.pxFilePrep)

		self.httpServer = RepRapServer(self, self.settings, self.logger)
		self.logger.LogMessage("Reprap host ready!")
		self.nb.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.changePages)
		self.history.SetLogger(self.logger)
		self.timer.Start(MAINTIMER)
		
	def changePages(self, evt):
		if self.shuttingDown:
			return
		
		sel = evt.GetSelection()
		oldSel = evt.GetOldSelection()
		for p in self.pxManCtl.keys():
			if oldSel == self.pxManCtl[p]:
				self.pgManCtl[p].leavePage()
				
		if sel != self.pxLogger:
			self.logger.checkShowToaster()
			
		if sel == self.pxConnMgr:
			self.pgConnMgr.refreshPorts()
		elif sel == self.pxLogger:
			self.logger.hideToaster()
		
	def addPages(self, printer, reprap):
		mc = self.pgManCtl[printer] = ManualControl(self.nb, self, printer, reprap)
		mc.SetBackgroundColour(bkgd)
		pm = self.pgPrtMon[printer] = PrintMonitor(self.nb, self, printer, reprap, self.history)
		pm.SetBackgroundColour(bkgd)
		self.connected[printer] = True
		self.printing[printer] = False
		pm.setManCtl(mc)
		mc.setPrtMon(pm)
		mcText = MANCTL_TAB_TEXT % printer
		pmText = PRTMON_TAB_TEXT % printer
		self.pxManCtl[printer] = self.nb.GetPageCount()
		self.nb.AddPage(mc, mcText)
		self.nb.AddPage(pm, pmText, imageId=self.nbilNotReadyIdx)
		self.pgPrinters[printer] = (mcText, pmText)
		return (pm, mc)
		
	def delPages(self, printer):
		if printer not in self.pgPrinters.keys():
			return
		
		del self.connected[printer]
		del self.printing[printer]
		self.pgManCtl[printer].leavePage()
		mcText, pmText = self.pgPrinters[printer]
		self.deletePageByTabText(mcText)
		self.deletePageByTabText(pmText)
		del self.pgPrinters[printer]
		del self.pgManCtl[printer]
		del self.pxManCtl[printer]
		del self.pgPrtMon[printer]
		
	def deletePageByTabText(self, text):
		pc = self.nb.GetPageCount()
		for i in range(pc):
			if text == self.nb.GetPageText(i):
				self.nb.RemovePage(i)
				return
		
	def findPMPageByPrinter(self, prtname):
		if prtname not in self.pgPrinters.keys():
			return None
		text = self.pgPrinters[prtname][1]
		pc = self.nb.GetPageCount()
		for i in range(pc):
			if text == self.nb.GetPageText(i):
				return i
		return None
	
	def setPendantConnection(self, printer):
		if printer is None:
			print "clear pendant connection information"
		else:
			print "set pendant connection to printer (%s)" % printer
		
	def hiLiteLogTab(self, flag):
		if flag:
			self.nb.SetPageImage(self.pxLogger, self.nbilAttentionIdx)
		else:
			self.nb.SetPageImage(self.pxLogger, -1)

	def doPrinterError(self, printer):
		if self.nb.GetSelection() not in [ self.pxLogger, self.pxFilePrep ]:
			self.nb.SetSelection(self.pxFilePrep)
		self.pgConnMgr.disconnectByPrinter(printer)
		self.pgConnMgr.refreshPorts()
			
	def onLoggerPage(self):
		return self.nb.GetSelection() == self.pxLogger

	def replace(self, s, pm=None):
		d = {}

		d['%gcodebase%'] = ""
		d['%gcode%'] = ""
		
		if pm is not None:		
			st, et = self.pm.getPrintTimes()
			if st is not None:				
				d['%starttime%'] = time.strftime('%H:%M:%S', time.localtime(st))
			if et is not None:
				d['%endtime%'] = time.strftime('%H:%M:%S', time.localtime(et))
			if st is not None and et is not None:
				d['%elapsed%'] = formatElapsed(et - st)
				
			if self.pm.gcFile is not None:
				d['%gcodebase%'] = os.path.basename(self.pm.gcFile)
				d['%gcode%'] = self.pm.gcFile
						
		if 'configfile' in self.pgFilePrep.slicer.settings.keys():
			d['%config%'] = self.pgFilePrep.slicer.settings['configfile']
		else:
			d['%config%'] = ""
		d['%slicer%'] = self.pgFilePrep.settings.slicer
		
		if self.pgFilePrep.stlFile is not None:
			d['%stlbase%'] =  os.path.basename(self.pgFilePrep.stlFile)
			d['%stl%'] = self.pgFilePrep.stlFile
		else:
			d['%stlbase%'] = ""
			d['%stl%'] = ""

		if self.pgFilePrep.gcFile is not None:
			d['%slicegcodebase%'] = os.path.basename(self.pgFilePrep.gcFile)
			d['%slicegcode%'] = self.pgFilePrep.gcFile
		else:
			d['%slicegcodebase%'] = ""
			d['%slicegcode%'] = ""
			
		for t in d.keys():
			if d[t] is not None:
				s = s.replace(t, d[t])
			
		s = s.replace('""', '')
		return s
		
	def updatePrintMonStatus(self, pname, status):	
		pn =  self.findPMPageByPrinter(pname)
		if pn is not None:
			if status == PMSTATUS_NOT_READY:
				self.nb.SetPageImage(pn, self.nbilNotReadyIdx)
				self.printing[pname] = False
			elif status == PMSTATUS_READY:
				self.nb.SetPageImage(pn, self.nbilReadyIdx)
				self.printing[pname] = False
			elif status == PMSTATUS_PRINTING:
				self.nb.SetPageImage(pn, self.nbilPrintingIdx)
				self.printing[pname] = True
			elif status == PMSTATUS_PAUSED:
				self.nb.SetPageImage(pn, self.nbilPausedIdx)
				self.printing[pname] = False
			else:
				self.nb.SetPageImage(pn, -1)
				self.printing[pname] = False
		
	def updateFilePrepStatus(self, status, batchstat):
		self.fpstatus = status
		self.batchslstatus = batchstat
		if status == FPSTATUS_READY:
			if batchstat == BATCHSL_IDLE:
				self.nb.SetPageImage(self.pxFilePrep, self.nbilReadyIdx)
			else:
				self.nb.SetPageImage(self.pxFilePrep, self.nbilReadyBSIdx)
				
		elif status == FPSTATUS_READY_DIRTY:
			if batchstat == BATCHSL_IDLE:
				self.nb.SetPageImage(self.pxFilePrep, self.nbilReadyDirtyIdx)
			else:
				self.nb.SetPageImage(self.pxFilePrep, self.nbilReadyDirtyBSIdx)
				
		elif status == FPSTATUS_BUSY:
			if batchstat == BATCHSL_IDLE:
				self.nb.SetPageImage(self.pxFilePrep, self.nbilNotReadyIdx)
			else:
				self.nb.SetPageImage(self.pxFilePrep, self.nbilNotReadyBSIdx)
				
		elif status == FPSTATUS_IDLE:
			if batchstat == BATCHSL_IDLE:
				self.nb.SetPageImage(self.pxFilePrep, self.nbilIdleIdx)
			else:
				self.nb.SetPageImage(self.pxFilePrep, self.nbilIdleBSIdx)

		else:
			self.nb.SetPageImage(self.pxFilePrep, -1)
			
	def isFilePrepModified(self, message):
		return self.pgFilePrep.checkModified(message=message)
		
	def getStatus(self):
		r = self.pgConnMgr.getStatus()
		r['fileprep'] = self.pgFilePrep.getStatus()
		return r
	
	def stopPrint(self, pname):
		if pname is None:
			if len(self.connected) >= 1:
				pname = self.connected.keys()[0]
			else:
				self.logger.LogMessage("No printer connected to stop")
				return
		else:
			if pname not in self.settings.printers and pname != 'all':
				self.logger.LogMessage("Unknown printer in stop print request")
				return
		
		if pname == 'all':
			for p in self.settings.printers:
				if p in self.connected.keys() and self.printing[p]:
					#pst = self.pgPrtMon[p].stopPrint()
					self.logger.LogMessage("We would have stopped printer %s here" %  p)
				
		else:
			if pname in self.connected.keys() and self.printing[pname]:
				#return self.pgPrtMon[p].stopPrint()
				self.logger.LogMessage("We would have stopped printer %s here" %  pname)
			else:
				self.logger.LogMessage("Printer %s not printing - skipping stop request" % pname)
	
	def setHeaters(self, pname, heaters):
		if pname is None:
			if len(self.connected) >= 1:
				pname = self.connected.keys()[0]
			else:
				self.logger.LogMessage("No printer connected to set heaters")
				return
		else:
			if pname not in self.settings.printers and pname != 'all':
				self.logger.LogMessage("Unknown printer in set heater request")
				return
		
		if pname == 'all':
			for p in self.settings.printers:
				if p in self.connected.keys():
					self.pgManCtl[p].setHeaters(heaters)
				
		else:
			if pname in self.connected.keys():
				self.pgManCtl[pname].setHeaters(heaters)
			else:
				self.logger.LogMessage("Printer %s not connected - skipping set heater request" % pname)
	
	def setSlicer(self, slicername, config):
		self.pgFilePrep.httpSetSlicer(slicername)
		
		if config is not None:				
			self.pgFilePrep.httpCfgSlicer(config)
	
	def sliceFile(self, fn):
		self.pgFilePrep.httpSliceFile(fn)

	def getSlicer(self):
		return {'result': self.pgFilePrep.getSlicerConfigString()}
		
	def getTemps(self):
		return self.pgConnMgr.getTemps()
	
	def sendToFilePrep(self, fn):
		self.pgFilePrep.loadTempSTL(fn)
		
	def pullGCode(self, printmon, acceleration, retractiontime):
		self.pgFilePrep.pullGCode(printmon, acceleration, retractiontime)
		
	def currentPullStatus(self):
		return self.allowPulls
		
	def assertAllowPulls(self, flag):
		self.allowPulls = flag
		self.pgConnMgr.assertAllowPulls(flag)

	def onTimer(self, evt):
		self.pgConnMgr.tick()
		
	def onClose(self, evt):
		if self.checkPrinting():
			return
		
		if not self.pgFilePrep.onClose(evt):
			self.nb.SetSelection(self.pxFilePrep)
			return

		for p in self.pgPrtMon.keys():		
			self.pgPrtMon[p].onClose(evt)
			
		for p in self.pgManCtl.keys():		
			self.pgManCtl[p].onClose(evt)

		self.pgConnMgr.onClose()

		if self.httpServer is not None:
			self.httpServer.close()
			
		if self.logger is not None:
			self.logger.close()
				
		self.shuttingDown = True
		self.settings.cleanUp()	
		self.Destroy()
		
	def checkPrinting(self):
		if self.pgConnMgr.isAnyPrinting():
			dlg = wx.MessageDialog(self, "Are you sure you want to exit while printing is active",
				'Printing Active', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_INFORMATION)
	
			rc = dlg.ShowModal()
			dlg.Destroy()

			if rc != wx.ID_YES:
				return True

		return False
	
	def snapShot(self):
		return self.pgConnMgr.snapShot(block=False)

class App(wx.App):
	def OnInit(self):
		self.frame = MainFrame()
		self.frame.Show()
		self.SetTopWindow(self.frame)
		return True

app = App(False)
app.MainLoop()


