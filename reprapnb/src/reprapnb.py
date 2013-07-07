import os.path
import sys, inspect
import wx
import glob

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
from reprap import RepRap
from logger import Logger

TB_TOOL_PORTS = 10
TB_TOOL_CONNECT = 11
TB_TOOL_LOG = 19

BUTTONDIM = (64, 64)

baudChoices = ["2400", "9600", "19200", "38400", "57600", "115200", "250000"]

class Images:
	def __init__(self, settings):
		self.pngPorts = self.loadImg(os.path.join(settings.cmdfolder, "images/ports.png"))
		self.pngConnect = self.loadImg(os.path.join(settings.cmdfolder, "images/connect.png"))
		self.pngDisconnect = self.loadImg(os.path.join(settings.cmdfolder, "images/disconnect.png"))
		self.pngLog = self.loadImg(os.path.join(settings.cmdfolder, "images/log.png"))
		
	def loadImg(self, path):
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		return png

class MainFrame(wx.Frame):
	def __init__(self):
		self.ctr = 0
		wx.Frame.__init__(self, None, title="Rep Rap Notebook", size=[1475, 950])
		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.logger = Logger(self, wx.ID_ANY, "logger")
		self.logger.Show()
		
		self.logger.LogMessage("Hello there")
		
		self.settings = Settings(self, cmd_folder)
		
		self.reprap = RepRap(self, self.evtRepRap)
		self.connected = False

		self.slicer = self.settings.getSlicerSettings(self.settings.slicer)
		if self.slicer is None:
			self.logger.LogError("Unable to get slicer settings")

		self.printersettings = self.settings.getPrinterSettings(self.settings.printer)
		if self.printersettings is None:
			self.logger.LogError("Unable to get printer settings")
			
		self.images = Images(self.settings)

		p = wx.Panel(self)

		self.tb = wx.ToolBar(p, style=wx.TB_HORIZONTAL | wx.TB_FLAT)
		f = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
		sizerBtns = wx.BoxSizer(wx.HORIZONTAL)
		sizerBtns.AddSpacer((10,10))
		sizerBtns.Add(self.tb)
			
		t = wx.StaticText(self.tb, wx.ID_ANY, "  Printer:  ", style=wx.ALIGN_RIGHT)
		t.SetFont(f)
		self.tb.AddControl(t)
		
		self.cbPrinter = wx.ComboBox(self.tb, wx.ID_ANY, self.settings.printer, (-1, -1), (100, -1), self.settings.printers, wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbPrinter.SetFont(f)
		self.cbPrinter.SetToolTipString("Choose which printer to use")
		self.tb.AddControl(self.cbPrinter)
		self.cbPrinter.SetStringSelection(self.settings.printer)
		self.Bind(wx.EVT_COMBOBOX, self.doChoosePrinter, self.cbPrinter)
		
		self.tb.AddSeparator()
			
		t = wx.StaticText(self.tb, wx.ID_ANY, " Port:  ", style=wx.ALIGN_RIGHT)
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
		
		t = wx.StaticText(self.tb, wx.ID_ANY, " @ ", style=wx.ALIGN_CENTER, size=(40, 35))
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
			
		t = wx.StaticText(self.tb, wx.ID_ANY, " Slicer:  ", style=wx.ALIGN_RIGHT)
		t.SetFont(f)
		self.tb.AddControl(t)
		
		self.cbSlicer = wx.ComboBox(self.tb, wx.ID_ANY, self.settings.slicer, (-1, -1), (120, -1), self.settings.slicers, wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbSlicer.SetFont(f)
		self.cbSlicer.SetToolTipString("Choose which slicer to use")
		self.tb.AddControl(self.cbSlicer)
		self.cbSlicer.SetStringSelection(self.settings.slicer)
		self.Bind(wx.EVT_COMBOBOX, self.doChooseSlicer, self.cbSlicer)
			
		t = wx.StaticText(self.tb, wx.ID_ANY, " Profile:  ", style=wx.ALIGN_RIGHT)
		t.SetFont(f)
		self.tb.AddControl(t)
	
		self.cbProfile = wx.ComboBox(self.tb, wx.ID_ANY, self.slicer.settings['profile'],
									(-1, -1), (120, -1), self.slicer.type.getProfileOptions().keys(), wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbProfile.SetFont(f)
		self.cbProfile.SetToolTipString("Choose which slicer profile to use")
		self.tb.AddControl(self.cbProfile)
		self.cbProfile.SetStringSelection(self.slicer.settings['profile'])
		self.Bind(wx.EVT_COMBOBOX, self.doChooseProfile, self.cbProfile)

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
		self.pgPrtMon = PrintMonitor(self.nb, self)

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
		
		if self.settings.startpane == self.pxPlater:
			self.nb.SetSelection(self.pxPlater)
		elif self.settings.startpane == self.pxFilePrep:
			self.nb.SetSelection(self.pxFilePrep)


	def evtRepRap(self, evt):
		print "Reprap evnt received, event = ", evt.event
	
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
#FIXIT
# 			self.logger.LogMessage("Tab is inaccessible unless printer is connected")
# 			self.nb.SetSelection(currentPage)
			evt.Veto()
		else:
			evt.Skip()
		
	def doChoosePrinter(self, evt):
		self.settings.printer = self.cbPrinter.GetValue()
		self.settings.setModified()
		self.printersettings = self.settings.getPrinterSettings(self.settings.printer)
		if self.printersettings is None:
			self.logger.LogError("Unable to get printer settings")
			return
		
		extruders = []
		heaters = []
		temps = self.slicer.type.getProfileTemps()
		maxExt = self.printersettings.settings['extruders']
		axes = self.printersettings.settings['axisletters']
		if len(temps) < 2:
			self.logger.LogError("No hot end temperatures configured in profile")
			return
		hbpTemp = temps[0]
		temps = temps[1:]
		if len(temps) != maxExt:
			self.logger.LogWarning("Profile does not have the correct number of extruders configured")
			t = temps[0]
			for i in range(maxExt - len(temps)):
				temps.append(t)
				
		if maxExt == 1:
			extruders.append(["Ext", "Extruder", axes[0]])
			heaters.append(["HE", "Hot End", temps[0], (20, 250), "G104"])
		else:
			for i in range(maxExt):
				extruders.append(["Ext%d" % i, "Extruder %d" % i, axes[i]])
				heaters.append(["HE%d" % i, "Hot End %d" % i, temps[i], (20, 250), "G104"])
			
		heaters.append(["HBP", "Build Platform", hbpTemp, (20, 150), "G140"])

		self.pgManCtl.changePrinter(heaters, extruders)
		self.pgPrtMon.changePrinter(heaters, extruders)
		
	def doChooseProfile(self, evt):
		newprof = self.cbProfile.GetValue()
		self.slicer.type.setProfile(newprof)
		#FIXIT - notify MANCTL and prtmin
		
	def doChooseSlicer(self, evt):
		self.settings.slicer = self.cbSlicer.GetValue()
		self.settings.setModified()
		self.slicer = self.settings.getSlicerSettings(self.settings.slicer)
		if self.slicer is None:
			self.logger.LogError("Unable to get slicer settings") 
			
		self.cbProfile.Clear()
		self.cbProfile.AppendItems(self.slicer.type.getProfileOptions().keys())
		self.cbProfile.SetStringSelection(self.slicer.settings['profile'])
		#FIXIT - notify MANCTL and prtmin
		
	def doPort(self, evt):
		if self.ctr == 0:
			self.setHeatTarget("HBP", 60)
		elif self.ctr == 1:
			self.setHeatTarget("HE0", 185)
		elif self.ctr == 2:
			self.setHeatTarget("HE1", 155)
		elif self.ctr == 3:
			self.setHeatTemp("HBP", 40)
		elif self.ctr == 4:
			self.setHeatTemp("HBP", 50)
		elif self.ctr == 5:
			self.setHeatTemp("HBP", None)
		
		self.ctr += 1
		if self.ctr == 9:
			self.ctr = 0
			
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
			self.connected = False 
			self.announcePrinter()
			self.tb.SetToolNormalBitmap(TB_TOOL_CONNECT, self.images.pngConnect)
			if self.nb.GetSelection() not in [ self.pxPlater, self.pxFilePrep ]:
				self.nb.SetSelection(self.pxFilePrep)
		else:
			port = 	self.cbPort.GetStringSelection()
			baud = 	self.cbBaud.GetStringSelection()

			self.reprap.connect(port, baud)
			self.connected = True
			self.tb.SetToolNormalBitmap(TB_TOOL_CONNECT, self.images.pngDisconnect)
			self.announcePrinter()

	def announcePrinter(self):
		#FIXIT
		pass
	
	def replace(self, s):
		d = {}
# FIXIT					
# 		d['%starttime%'] = time.strftime('%H:%M:%S', time.localtime(self.startTime))
# 		d['%endtime%'] = time.strftime('%H:%M:%S', time.localtime(self.endTime))
# 		d['%elapsed%'] = formatElapsed(self.elapsedTime)
			
		d['%profile%'] = self.slicer.settings['profilefile']
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
#----------------------------------------------------------------------------

app = App(False)
app.MainLoop()


