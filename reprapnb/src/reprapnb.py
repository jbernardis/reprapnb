import os.path
import sys, inspect
import wx
import glob
import time

if os.name=="nt":
	try:
		import _winreg
	except:
		pass

cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
if cmd_folder not in sys.path:
	sys.path.insert(0, cmd_folder)
	
from fileprep import FilePrepare
from printmon import PrintMonitor
from manualctl import ManualControl
from plater import Plater
from settings import Settings
from logger import Logger
from images import Images
from parser import RepRapParser
from reprap import RepRap, RECEIVED_MSG

TB_TOOL_PORTS = 10
TB_TOOL_CONNECT = 11
TB_TOOL_LOG = 19

TEMPINTERVAL = 3
POSITIONINTERVAL = 1

BUTTONDIM = (64, 64)

baudChoices = ["2400", "9600", "19200", "38400", "57600", "115200", "250000"]

secpday = 60 * 60 * 24
secphour = 60 * 60

def formatElapsed(secs):
	ndays = int(secs/secpday)
	secday = secs % secpday
	
	nhour = int(secday/secphour)
	sechour = secday % secphour
	
	nmin = int(sechour/60)
	nsec = sechour % 60

	if ndays == 0:
		if nhour == 0:
			return "%d:%02d" % (nmin, nsec)
		else:
			return "%d:%02d:%02d" % (nhour, nmin, nsec)
	else:
		return "%d-%d:%02d:%02d" % (ndays, nhour, nmin, nsec)	

class MainFrame(wx.Frame):
	def __init__(self):
		self.ctr = 0
		self.cycle = 0
		self.timer = None
		self.discPending = False
		self.M105pending = False
		self.printPosition = None
		wx.Frame.__init__(self, None, title="Rep Rap Notebook", size=[1475, 950])
		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.logger = Logger(self, wx.ID_ANY, "logger")
		self.logger.Show()
		
		self.logger.LogMessage("Hello there")
		
		self.settings = Settings(self, cmd_folder)
		
		self.reprap = RepRap(self, self.evtRepRap)
		self.parser = RepRapParser(self)
		self.connected = False

		self.slicer = self.settings.getSlicerSettings(self.settings.slicer)
		if self.slicer is None:
			self.logger.LogError("Unable to get slicer settings")
			
		self.buildarea = self.slicer.type.getSlicerSettings()[0]
			
		self.images = Images(os.path.join(self.settings.cmdfolder, "images"))

		p = wx.Panel(self)

		self.tb = wx.ToolBar(p, style=wx.TB_HORIZONTAL) # | wx.TB_FLAT)
		f = wx.Font(12, wx.SWISS, wx.BOLD, wx.NORMAL)
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
			
		self.tb.AddSeparator()
			
		text = " Printer:"
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self.tb, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w,h))
		t.SetFont(f)
		self.tb.AddControl(t)
		
		self.cbPrinter = wx.ComboBox(self.tb, wx.ID_ANY, self.slicer.settings['printer'], (-1, -1), (100, -1), self.slicer.type.getPrinterOptions().keys(), wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbPrinter.SetFont(f)
		self.cbPrinter.SetToolTipString("Choose which printer profile to use")
		self.tb.AddControl(self.cbPrinter)
		self.cbPrinter.SetStringSelection(self.slicer.settings['printer'])
		self.Bind(wx.EVT_COMBOBOX, self.doChoosePrinter, self.cbPrinter)
		
		text = " Profile:"
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self.tb, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w,h))
		t.SetFont(f)
		self.tb.AddControl(t)
	
		self.cbProfile = wx.ComboBox(self.tb, wx.ID_ANY, self.slicer.settings['profile'],
									(-1, -1), (120, -1), self.slicer.type.getProfileOptions().keys(), wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbProfile.SetFont(f)
		self.cbProfile.SetToolTipString("Choose which print profile to use")
		self.tb.AddControl(self.cbProfile)
		self.cbProfile.SetStringSelection(self.slicer.settings['profile'])
		self.Bind(wx.EVT_COMBOBOX, self.doChooseProfile, self.cbProfile)
		
		text = " Filament:"
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self.tb, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w,h))
		t.SetFont(f)
		self.tb.AddControl(t)
	
		self.cbFilament = wx.ComboBox(self.tb, wx.ID_ANY, self.slicer.settings['filament'],
									(-1, -1), (120, -1), self.slicer.type.getFilamentOptions().keys(), wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbFilament.SetFont(f)
		self.cbFilament.SetToolTipString("Choose which filament profile to use")
		self.tb.AddControl(self.cbFilament)
		self.cbFilament.SetStringSelection(self.slicer.settings['filament'])
		self.Bind(wx.EVT_COMBOBOX, self.doChooseFilament, self.cbFilament)

		self.tb.AddSeparator()
				
		self.tb.AddSimpleTool(TB_TOOL_LOG, self.images.pngLog, "Hide/Show log window", "")
		self.Bind(wx.EVT_TOOL, self.doShowHideLog, id=TB_TOOL_LOG)
		self.logShowing = True

		self.tb.Realize()
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.nb = wx.Notebook(p, style=wx.NB_TOP)

		self.pxPlater = 0
		self.pxFilePrep = 1
		self.pxManCtl = 2
		self.pxPrtMon = 3

		self.pgPlater = Plater(self.nb, self)
		self.pgFilePrep = FilePrepare(self.nb, self)
		self.pgManCtl = ManualControl(self.nb, self)
		self.pgPrtMon = PrintMonitor(self.nb, self, self.reprap)

		self.nb.AddPage(self.pgPlater, "Plating")
		self.nb.AddPage(self.pgFilePrep, "File Preparation")
		self.nb.AddPage(self.pgManCtl, "Manual Control")
		self.nb.AddPage(self.pgPrtMon, "Print/Monitor")
		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.checkPageChanged, self.nb)

		sizer.AddSpacer((20,20))
		sizer.Add(sizerBtns)
		sizer.AddSpacer((10,10))
		sizer.Add(self.nb)
		p.SetSizer(sizer)
		
		self.doChoosePrinter(None)
		self.setPrinterBusy(True)  # disconnected printer is for all intents busy
		
		if self.settings.startpane == self.pxPlater:
			self.nb.SetSelection(self.pxPlater)
		elif self.settings.startpane == self.pxFilePrep:
			self.nb.SetSelection(self.pxFilePrep)

	def evtRepRap(self, evt):
		if evt.event == RECEIVED_MSG:
			if not self.parser.parseMsg(evt.msg):
				self.logger.LogMessage(evt.msg)
		else:
			self.pgPrtMon.reprapEvent(evt)
	
	def doShowHideLog(self, evt):
		self.logShowing = not self.logShowing
		if self.logShowing:
			self.logger.Show()
		else:
			self.logger.Hide()
		
	def checkPageChanged(self, evt):
		newPage = evt.GetSelection()
		currentPage = evt.GetOldSelection()
		if newPage in [self.pxManCtl, self.pxPrtMon] and not self.connected:
			self.logger.LogMessage("Tab is inaccessible unless printer is connected")
			self.nb.SetSelection(currentPage)
			evt.Veto()
		else:
			evt.Skip()
		
	def doChoosePrinter(self, evt):
		newprinter = self.cbPrinter.GetValue()
		self.slicer.type.setPrinter(newprinter)
		self.updateWithNewSlicerInfo()
		
	def doChooseProfile(self, evt):
		newprof = self.cbProfile.GetValue()
		self.slicer.type.setProfile(newprof)
		self.updateWithNewSlicerInfo()
		
	def doChooseFilament(self, evt):
		newfilament = self.cbFilament.GetValue()
		self.slicer.type.setFilament(newfilament)
		self.updateWithNewSlicerInfo()

	def updateWithNewSlicerInfo(self):		
		extruders = []
		heaters = []
		(buildarea, nextr, axes, hetemps, bedtemp) = self.slicer.type.getSlicerSettings()
		if len(hetemps) < 1:
			self.logger.LogError("No hot end temperatures configured in slicer")
			return
	
		if len(hetemps) != nextr:
			self.logger.LogWarning("Slicer does not have the correct number of extruders configured")
			if len(hetemps) < nextr:
				t = hetemps[0]
				r = range(nextr - len(hetemps))
				for i in r:
					hetemps.append(t)

		if len(axes) != nextr:
			self.logger.LogWarning("Slicer does not have the correct number of axis letters configured")
			if len(axes) < nextr:
				t = axes[0]
				r = range(nextr - len(axes))
				for i in r:
					axes.append(t)
				
		if nextr == 1:
			extruders.append(["Ext", "Extruder", axes[0]])
			heaters.append(["HE", "Hot End", hetemps[0], (20, 250), "M104"])
		else:
			for i in range(nextr):
				extruders.append(["Ext%d" % i, "Extruder %d" % i, axes[i]])
				heaters.append(["HE%d" % i, "Hot End %d" % i, hetemps[i], (20, 250), "M104"])
			
		heaters.append(["HBP", "Build Platform", bedtemp, (20, 150), "M140"])

		self.pgManCtl.changePrinter(heaters, extruders)
		self.pgPrtMon.changePrinter(heaters, extruders)
		self.parser.setPrinter(heaters, extruders)
		
	def doChooseSlicer(self, evt):
		self.settings.slicer = self.cbSlicer.GetValue()
		self.settings.setModified()
		self.slicer = self.settings.getSlicerSettings(self.settings.slicer)
		if self.slicer is None:
			self.logger.LogError("Unable to get slicer settings") 
			
		self.cbProfile.Clear()
		self.cbProfile.AppendItems(self.slicer.type.getProfileOptions().keys())
		self.cbProfile.SetStringSelection(self.slicer.settings['profile'])
		
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
		if os.name=="nt":
			try:
				key=_winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,"HARDWARE\\DEVICEMAP\\SERIALCOMM")
				i=0
				while(1):
					baselist+=[_winreg.EnumValue(key,i)[1]]
					i+=1
			except:
				pass
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
		self.connected = False 
		self.discPending = False
		self.tb.SetToolShortHelp(TB_TOOL_CONNECT, "Connect to the Printer")
		self.tb.SetToolNormalBitmap(TB_TOOL_CONNECT, self.images.pngConnect)
		self.timer.Stop()
		self.timer = None
		if self.nb.GetSelection() not in [ self.pxPlater, self.pxFilePrep ]:
			self.nb.SetSelection(self.pxFilePrep)

	def replace(self, s):
		d = {}
		
		st, et = self.pgPrtMon.getPrintTimes()
		if st is not None:				
			d['%starttime%'] = time.strftime('%H:%M:%S', time.localtime(st))
		if et is not None:
			d['%endtime%'] = time.strftime('%H:%M:%S', time.localtime(et))
		if st is not None and et is not None:
			d['%elapsed%'] = formatElapsed(et - st)
			
		d['%profile%'] = self.slicer.settings['profilefile']
		d['%printer%'] = self.slicer.settings['printerfile']
		d['%filament%'] = self.slicer.settings['filamentfile']
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
		self.pgFilePrep.setPrinterBusy(flag)
	
	def switchToFilePrep(self, fn):
		self.nb.SetSelection(self.pxFilePrep)
		self.pgFilePrep.loadTempSTL(fn)

	def forwardToPrintMon(self, model, name=""):
		self.nb.SetSelection(self.pxPrtMon)
		self.pgPrtMon.forwardModel(model, name=name)
		
	def setHeatTarget(self, name, temp):
		self.pgManCtl.setHeatTarget(name, temp)
		self.pgPrtMon.setHeatTarget(name, temp)
		
	def setHeatTemp(self, name, temp):
		self.pgManCtl.setHeatTemp(name, temp)
		self.pgPrtMon.setHeatTemp(name, temp)
		
	def onTimer(self, evt):
		self.cycle += 1
		
		if self.discPending:
			self.finishDisconnection()
		
		if self.cycle % TEMPINTERVAL == 0:
			if not self.M105pending:
				self.M105pending = True
				self.reprap.send_now("M105")
			
		if self.cycle % POSITIONINTERVAL == 0:
			n = self.reprap.getPrintPosition()
			if n is not None and n != self.printPosition:
				self.printPosition = n
				self.pgPrtMon.updatePrintPosition(n)
		
	def onClose(self, evt):
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
	
		self.settings.cleanUp()	
		self.Destroy()

class App(wx.App):
	def OnInit(self):
		self.frame = MainFrame()
		self.frame.Show()
		self.SetTopWindow(self.frame)
		return True

app = App(False)
app.MainLoop()


