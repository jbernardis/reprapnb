import os.path
import sys, inspect
import wx
import glob
import time

cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
if cmd_folder not in sys.path:
	sys.path.insert(0, cmd_folder)
	
from fileprep import FilePrepare, FPSTATUS_EQUAL, FPSTATUS_EQUAL_DIRTY, FPSTATUS_UNEQUAL, FPSTATUS_UNEQUAL_DIRTY

from printmon import PrintMonitor
from manualctl import ManualControl
from plater import Plater
from settings import Settings
from logger import Logger
from images import Images
from reprap import RepRap, RepRapParser, RECEIVED_MSG
from reprapserver import RepRapServer
from tools import formatElapsed

TB_TOOL_PORTS = 10
TB_TOOL_CONNECT = 11
TB_TOOL_SLICECFG = 12
TB_TOOL_LOG = 19

TEMPINTERVAL = 3
POSITIONINTERVAL = 1

LOGGER_TAB_TEXT = "Log"
PLATER_TAB_TEXT = "Plater"
FILEPREP_TAB_TEXT = "File Preparation"
MANCTL_TAB_TEXT = "Manual Control"
PRTMON_TAB_TEXT = "Print Monitor"

MAXCFGCHARS = 80

BUTTONDIM = (64, 64)

baudChoices = ["2400", "9600", "19200", "38400", "57600", "115200", "250000"]

class MainFrame(wx.Frame):
	def __init__(self):
		self.ctr = 0
		self.cycle = 0
		self.timer = None
		self.discPending = False
		self.M105pending = False
		self.printPosition = None
		self.logger = None
		wx.Frame.__init__(self, None, title="Rep Rap Notebook", size=[1300, 930])
		self.Bind(wx.EVT_CLOSE, self.onClose)
		
		self.settings = Settings(self, cmd_folder)
		
		self.reprap = RepRap(self, self.evtRepRap)
		if self.settings.speedcommand is not None:
			self.reprap.addToAllowedCommands(self.settings.speedcommand)
			
		self.parser = RepRapParser(self)
		self.connected = False
		self.printing = False
		self.httpServer = None

		self.slicer = self.settings.getSlicerSettings(self.settings.slicer)
		if self.slicer is None:
			print "Unable to get slicer settings"
			
		(self.buildarea, nExtr, heTemps, bedTemps) = self.slicer.getSlicerParameters()
			
		self.images = Images(os.path.join(self.settings.cmdfolder, "images"))
		self.nbil = wx.ImageList(16, 16)
		self.nbilAttentionIdx = self.nbil.Add(self.images.pngAttention)
		self.nbilPrinterBusyIdx = self.nbil.Add(self.images.pngPrinterbusy)
		self.nbilPrinterReadyIdx = self.nbil.Add(self.images.pngPrinterready)
		self.nbilEqualIdx = self.nbil.Add(self.images.pngEqual)
		self.nbilEqualDirtyIdx = self.nbil.Add(self.images.pngEqualdirty)
		self.nbilUnequalIdx = self.nbil.Add(self.images.pngUnequal)
		self.nbilUnequalDirtyIdx = self.nbil.Add(self.images.pngUnequaldirty)

		p = wx.Panel(self)

		self.tb = wx.ToolBar(p, style=wx.TB_HORIZONTAL) # | wx.TB_FLAT)
		f = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		sizerBtns = wx.BoxSizer(wx.HORIZONTAL)
		sizerBtns.AddSpacer((10,10))
		sizerBtns.Add(self.tb)

		dc = wx.WindowDC(self)
		dc.SetFont(f)
		text = "Port:"
		w, h = dc.GetTextExtent(text)
			
		t = wx.StaticText(self.tb, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w, h))
		t.SetFont(f)
		self.tb.AddControl(t)

		self.tb.AddSimpleTool(TB_TOOL_PORTS, self.images.pngPorts, "Refresh list of available ports", "")
		self.Bind(wx.EVT_TOOL, self.doPort, id=TB_TOOL_PORTS)

		ports = self.scanSerial()	
		choice = ""
		if len(ports) > 0:
			choice = ports[0]
		
		self.cbPort = wx.ComboBox(self.tb, wx.ID_ANY, choice, (-1, -1),  (140, -1), ports, wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbPort.SetFont(f)
		self.cbPort.SetToolTipString("Choose the port to which to connect")
		self.cbPort.SetStringSelection(choice)
		self.tb.AddControl(self.cbPort)
		text = "@"
		w, h = dc.GetTextExtent(text)
		
		t = wx.StaticText(self.tb, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w, h))
		t.SetFont(f)
		self.tb.AddControl(t)
		
		self.cbBaud = wx.ComboBox(self.tb, wx.ID_ANY, "115200", (-1, -1), (100, -1), baudChoices, wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbBaud.SetFont(f)
		self.cbBaud.SetToolTipString("Choose the baud rate")
		self.cbBaud.SetStringSelection("115200")
		self.tb.AddControl(self.cbBaud)
		
		self.tb.AddSimpleTool(TB_TOOL_CONNECT, self.images.pngConnect, "Connect to the Printer", "")
		self.Bind(wx.EVT_TOOL, self.doConnect, id=TB_TOOL_CONNECT)
		
		self.tb.AddSeparator()

		if len(ports) < 1:
			self.tb.EnableTool(TB_TOOL_CONNECT, False)
			
		text = " Slicer:"
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self.tb, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w, h))
		t.SetFont(f)
		self.tb.AddControl(t)
		
		self.cbSlicer = wx.ComboBox(self.tb, wx.ID_ANY, self.settings.slicer, (-1, -1), (120, -1), self.settings.slicers, wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbSlicer.SetFont(f)
		self.cbSlicer.SetToolTipString("Choose which slicer to use")
		self.tb.AddControl(self.cbSlicer)
		self.cbSlicer.SetStringSelection(self.settings.slicer)
		self.Bind(wx.EVT_COMBOBOX, self.doChooseSlicer, self.cbSlicer)
		
		self.tb.AddSimpleTool(TB_TOOL_SLICECFG, self.images.pngSlicecfg, "Choose slicer options", "")
		self.Bind(wx.EVT_TOOL, self.doSliceConfig, id=TB_TOOL_SLICECFG)
		
		text = self.slicer.type.getConfigString()
		w, h = dc.GetTextExtent("X" * MAXCFGCHARS)
		self.tSlicerCfg = wx.StaticText(self.tb, wx.ID_ANY, "", style=wx.ALIGN_RIGHT, size=(w, h))
		self.tSlicerCfg.SetFont(f)
		self.updateSlicerConfigString(text)
		self.tb.AddControl(self.tSlicerCfg)
			
		self.tb.AddSeparator()

		self.tb.Realize()
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.nb = wx.Notebook(p, style=wx.NB_TOP)
		self.nb.AssignImageList(self.nbil)

		self.logger = Logger(self.nb, self)
		
		self.pxLogger = 0
		self.pxPlater = 1
		self.pxFilePrep = 2
		self.pxManCtl = 3
		self.pxPrtMon = 4

		self.pgPlater = Plater(self.nb, self)
		self.pgFilePrep = FilePrepare(self.nb, self)
		self.pgManCtl = ManualControl(self.nb, self, nExtr, heTemps[0], bedTemps[0])
		self.pgPrtMon = PrintMonitor(self.nb, self, self.reprap)

		self.nb.AddPage(self.logger, LOGGER_TAB_TEXT, imageId=-1)
		self.nb.AddPage(self.pgPlater, PLATER_TAB_TEXT, imageId=-1)
		self.nb.AddPage(self.pgFilePrep, FILEPREP_TAB_TEXT, imageId=-1)
		self.nb.AddPage(self.pgManCtl, MANCTL_TAB_TEXT)
		self.nb.AddPage(self.pgPrtMon, PRTMON_TAB_TEXT, imageId=-1)
		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.checkPageChanged, self.nb)

		sizer.AddSpacer((20,20))
		sizer.Add(sizerBtns)
		sizer.AddSpacer((10,10))
		sizer.Add(self.nb)
		p.SetSizer(sizer)
		
		self.setPrinterBusy(True)  # disconnected printer is for all intents busy
		self.updateWithSlicerInfo()  # initially populate with current slicer info
		
		if self.settings.startpane == self.pxLogger:
			self.nb.SetSelection(self.pxLogger)
		elif self.settings.startpane == self.pxPlater:
			self.nb.SetSelection(self.pxPlater)
		elif self.settings.startpane == self.pxFilePrep:
			self.nb.SetSelection(self.pxFilePrep)
			
		self.httpServer = RepRapServer(self, self.settings, self.logger)
		self.logger.LogMessage("Reprap host ready!")

	def evtRepRap(self, evt):
		if evt.event == RECEIVED_MSG:
			if not self.parser.parseMsg(evt.msg):
				self.logger.LogMessage(evt.msg)
		else:
			self.pgPrtMon.reprapEvent(evt)
		
	def checkPageChanged(self, evt):
		newPage = evt.GetSelection()
		currentPage = evt.GetOldSelection()
		if newPage in [self.pxManCtl, self.pxPrtMon] and not self.connected:
			self.logger.LogMessage("Tab is inaccessible unless printer is connected")
			self.nb.SetSelection(currentPage)
			evt.Veto()
		else:
			evt.Skip()
			
	def hiLiteLogTab(self, flag):
		if flag:
			self.nb.SetPageImage(self.pxLogger, self.nbilAttentionIdx)
		else:
			self.nb.SetPageImage(self.pxLogger, -1)
						
	def updateSlicerConfigString(self, text):
		if len(text) > MAXCFGCHARS:
			text = text[:MAXCFGCHARS]
		self.tSlicerCfg.SetLabel(text)

	def updateWithSlicerInfo(self):	
		self.updateSlicerConfigString(self.slicer.type.getConfigString())	
		(hetemps, bedtemps) = self.slicer.getSlicerParameters()[2:4]
		
		if len(hetemps) < 1:
			self.logger.LogError("No hot end temperatures configured in slicer")
			return
	
		if len(bedtemps) < 1:
			self.logger.LogError("No bed temperatures configured in slicer")
			return

		self.pgManCtl.changePrinter(hetemps, bedtemps)
		self.pgPrtMon.changePrinter(hetemps, bedtemps)
		
	def doChooseSlicer(self, evt):
		self.settings.slicer = self.cbSlicer.GetValue()
		self.settings.setModified()
		self.slicer = self.settings.getSlicerSettings(self.settings.slicer)
		if self.slicer is None:
			self.logger.LogError("Unable to get slicer settings") 
		self.updateWithSlicerInfo()
		
	def doSliceConfig(self, evt):
		if self.slicer.configSlicer():
			self.updateWithSlicerInfo()
		
	def doPort(self, evt):
		l = self.scanSerial()
		self.cbPort.Clear()
		if len(l) > 0:
			self.cbPort.AppendItems(l)
			self.cbPort.SetStringSelection(l[0])
			self.tb.EnableTool(TB_TOOL_CONNECT, True)
		else:
			self.cbPort.SetStringSelection("")
			self.tb.EnableTool(TB_TOOL_CONNECT, False)
	
	def scanSerial(self):
		"""scan for available ports. return a list of device names."""
		baselist=[]
		return baselist+glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*') +glob.glob("/dev/tty.*")+glob.glob("/dev/cu.*")+glob.glob("/dev/rfcomm*")

	def doConnect(self, evt):
		if self.connected:
			self.reprap.disconnect()
			self.discPending = True
			self.setPrinterBusy(True)
			self.tb.EnableTool(TB_TOOL_CONNECT, False)

		else:
			port = 	self.cbPort.GetStringSelection()
			baud = 	self.cbBaud.GetStringSelection()

			self.reprap.connect(port, baud)
			self.connected = True
			
			self.timer = wx.Timer(self)
			self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)        
			self.timer.Start(1000)

			self.tb.SetToolNormalBitmap(TB_TOOL_CONNECT, self.images.pngDisconnect)
			self.tb.SetToolShortHelp(TB_TOOL_CONNECT, "Disconnect from the Printer")
			self.setPrinterBusy(False)

	def finishDisconnection(self):
		if not self.reprap.checkDisconnection():
			return
					
		self.tb.EnableTool(TB_TOOL_CONNECT, True)
		self.pgPrtMon.disconnect()
		self.connected = False 
		self.discPending = False
		self.tb.SetToolShortHelp(TB_TOOL_CONNECT, "Connect to the Printer")
		self.tb.SetToolNormalBitmap(TB_TOOL_CONNECT, self.images.pngConnect)
		self.timer.Stop()
		self.timer = None
		if self.nb.GetSelection() not in [ self.pxPlater, self.pxFilePrep ]:
			self.nb.SetSelection(self.pxFilePrep)
			
	def onLoggerPage(self):
		return self.nb.GetSelection() == self.pxLogger

	def replace(self, s):
		d = {}
		
		st, et = self.pgPrtMon.getPrintTimes()
		if st is not None:				
			d['%starttime%'] = time.strftime('%H:%M:%S', time.localtime(st))
		if et is not None:
			d['%endtime%'] = time.strftime('%H:%M:%S', time.localtime(et))
		if st is not None and et is not None:
			d['%elapsed%'] = formatElapsed(et - st)
			
		if 'configfile' in self.slicer.settings.keys():
			d['%config%'] = self.slicer.settings['configfile']
		else:
			d['%config%'] = ""
		d['%slicer%'] = self.settings.slicer
		
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
			
		if self.pgPrtMon.gcFile is not None:
			d['%gcodebase%'] = os.path.basename(self.pgPrtMon.gcFile)
			d['%gcode%'] = self.pgPrtMon.gcFile
		else:
			d['%gcodebase%'] = ""
			d['%gcode%'] = ""
			
		for t in d.keys():
			if d[t] is not None:
				s = s.replace(t, d[t])
			
		s = s.replace('""', '')
		return s
	
	def setPrinterBusy(self, flag=True):
		if flag:
			self.printPosition = None
		self.printing = flag
		
		if flag:
			self.nb.SetPageImage(self.pxPrtMon, self.nbilPrinterBusyIdx)
		elif self.pgPrtMon.hasFileLoaded():
			self.nb.SetPageImage(self.pxPrtMon, self.nbilPrinterReadyIdx)
		else:
			self.nb.SetPageImage(self.pxPrtMon, -1)
			
		self.pgFilePrep.setPrinterBusy(flag)
		
	def updateFilePrepStatus(self, status):
		if status == FPSTATUS_EQUAL:
			self.nb.SetPageImage(self.pxFilePrep, self.nbilEqualIdx)
		elif status == FPSTATUS_EQUAL_DIRTY:
			self.nb.SetPageImage(self.pxFilePrep, self.nbilEqualDirtyIdx)
		elif status == FPSTATUS_UNEQUAL:
			self.nb.SetPageImage(self.pxFilePrep, self.nbilUnequalIdx)
		elif status == FPSTATUS_UNEQUAL_DIRTY:
			self.nb.SetPageImage(self.pxFilePrep, self.nbilUnequalDirtyIdx)
		else:
			self.nb.SetPageImage(self.pxFilePrep, -1)
		
	def getStatus(self):
		stat = {}
		if self.connected:
			stat['connection'] = "on line"
		else:
			stat['connection'] = "off line"
			if self.printing:
				stat['status'] = "printing"
				stat['printstat'] = self.pgPrtMon.getStatus()
			else:
				stat['status'] = "idle"
				
		return stat
	
	def switchToFilePrep(self, fn):
		self.nb.SetSelection(self.pxFilePrep)
		self.pgFilePrep.loadTempSTL(fn)

	def forwardToPrintMon(self, model, name=""):
		self.pgPrtMon.forwardModel(model, name=name)
		pg = self.nb.GetSelection()
		if pg != self.pxPrtMon:
			askok = wx.MessageDialog(self, "Do you want to switch to the Print Monitor Tab",
					'Model Transfer Complete', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_INFORMATION)
			
			rc = askok.ShowModal()
			askok.Destroy()

			if rc == wx.ID_YES:
				self.nb.SetSelection(self.pxPrtMon)
		
	def setHETarget(self, temp):
		self.pgManCtl.setHETarget(temp)
		self.pgPrtMon.setHETarget(temp)
		
	def setHETemp(self, temp):
		self.pgManCtl.setHETemp(temp)
		self.pgPrtMon.setHETemp(temp)
		
	def setBedTarget(self, temp):
		self.pgManCtl.setBedTarget(temp)
		self.pgPrtMon.setBedTarget(temp)
		
	def setBedTemp(self, temp):
		self.pgManCtl.setBedTemp(temp)
		self.pgPrtMon.setBedTemp(temp)
		
	def updateSpeeds(self, fan, feed, flow):
		self.pgManCtl.updateSpeeds(fan, feed, flow)
		
	def onTimer(self, evt):
		self.cycle += 1
		
		if self.discPending:
			self.finishDisconnection()
		
		if self.connected and (self.cycle % TEMPINTERVAL == 0):
			if not self.M105pending:
				self.M105pending = True
				self.reprap.send_now("M105")
			
		if self.connected and (self.cycle % POSITIONINTERVAL == 0):
			n = self.reprap.getPrintPosition()
			if n is not None and n != self.printPosition:
				self.printPosition = n
				self.pgPrtMon.updatePrintPosition(n)
		
	def onClose(self, evt):
		if self.checkPrinting():
			return
		
		if self.connected:
			self.reprap.disconnect()
			
		if not self.pgPlater.onClose(evt):
			self.nb.SetSelection(self.pxPlater)
			return
		
		if not self.pgFilePrep.onClose(evt):
			self.nb.SetSelection(self.pxFilePrep)
			return
		
		if not self.pgPrtMon.onClose(evt):
			self.nb.SetSelection(self.pxPrtMon)
			return
		
		if not self.pgManCtl.onClose(evt):
			self.nb.SetSelection(self.pxManCtl)
			return

		if self.httpServer is not None:
			self.httpServer.close()
				
		self.settings.cleanUp()	
		self.Destroy()
		
	def checkPrinting(self):
		if self.printing and self.connected:
			dlg = wx.MessageDialog(self, "Are you sure you want to exit while printing is active",
					'Printing Active', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_INFORMATION)
			
			rc = dlg.ShowModal()
			dlg.Destroy()

			if rc != wx.ID_YES:
				return True

		return False


class App(wx.App):
	def OnInit(self):
		self.frame = MainFrame()
		self.frame.Show()
		self.SetTopWindow(self.frame)
		return True

app = App(False)
app.MainLoop()


