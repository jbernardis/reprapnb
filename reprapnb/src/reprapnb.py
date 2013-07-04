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

TB_TOOL_PORTS = 10
TB_TOOL_CONNECT = 11
TB_TOOL_LOG = 19

BUTTONDIM = (64, 64)

baudChoices = ["2400", "9600", "19200", "38400", "57600", "115200", "250000"]

class MainFrame(wx.Frame):
	def __init__(self):
		wx.Frame.__init__(self, None, title="Rep Rap Notebook", size=[1475, 950])
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.log_window = wx.LogWindow(self, 'Log Window', bShow=True)
		
		self.settings = Settings(self, cmd_folder)
		
		self.reprap = RepRap(self, self.evtRepRap)
		self.connected = False

		self.slicer = self.settings.getSlicerSettings(self.settings.slicer)
		if self.slicer is None:
			wx.LogError("Unable to get slicer settings")

		self.printersettings = self.settings.getPrinterSettings(self.settings.printer)
		if self.printersettings is None:
			wx.LogError("Unable to get printer settings")

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

		path = os.path.join(self.settings.cmdfolder, "images/ports.png")	
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		self.tb.AddSimpleTool(TB_TOOL_PORTS, png, "Refresh list of available ports", "")
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
		
		path = os.path.join(self.settings.cmdfolder, "images/connect.png")	
		self.connectPng = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(self.connectPng, wx.BLUE)
		self.connectPng.SetMask(mask)
		self.tb.AddSimpleTool(TB_TOOL_CONNECT, self.connectPng, "Connect to the Printer", "")
		self.Bind(wx.EVT_TOOL, self.doConnect, id=TB_TOOL_CONNECT)
		
		self.tb.AddSeparator()

		if len(ports) < 1:
			self.tb.EnableTool(TB_TOOL_CONNECT, False)
		path = os.path.join(self.settings.cmdfolder, "images/disconnect.png")	
		self.disconnectPng = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(self.disconnectPng, wx.BLUE)
		self.disconnectPng.SetMask(mask)
			
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
				
		path = os.path.join(self.settings.cmdfolder, "images/log.png")	
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		self.tb.AddSimpleTool(TB_TOOL_LOG, png, "Hide/Show log window", "")
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

	def evtRepRap(self, evt):
		print "Reprap evnt received, event = ", evt.event
	
	def doShowHideLog(self, evt):
		self.logShowing = not self.logShowing
		self.log_window.Show(self.logShowing)
		
	def checkPageChanged(self, evt):
		newPage = evt.GetSelection()
		currentPage = evt.GetOldSelection()
		if newPage in [self.pxManCtl, self.pxPrtMon] and not self.connected:
# 			wx.LogWarning("Tab is inaccessible unless printer is connected")
# 			self.nb.SetSelection(currentPage)
			evt.Veto()
		else:
			evt.Skip()
		
	def doChoosePrinter(self, evt):
		self.settings.printer = self.cbPrinter.GetValue()
		self.settings.setModified()
		self.printer = self.settings.getPrinterSettings(self.settings.printer)
		if self.printer is None:
			wx.LogError("Unable to get printer settings")
		
	def doChooseProfile(self, evt):
		newprof = self.cbProfile.GetValue()
		self.slicer.type.setProfile(newprof)
		
	def doChooseSlicer(self, evt):
		self.settings.slicer = self.cbSlicer.GetValue()
		self.settings.setModified()
		self.slicer = self.settings.getSlicerSettings(self.settings.slicer)
		if self.slicer is None:
			wx.LogError("Unable to get slicer settings") 
			
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
			self.connected = False 
			self.announcePrinter()
			self.tb.SetToolNormalBitmap(TB_TOOL_CONNECT, self.connectPng)
			if self.nb.GetSelection() not in [ self.pxPlater, self.pxFilePrep ]:
				self.nb.SetSelection(self.pxFilePrep)
		else:
			port = 	self.cbPort.GetStringSelection()
			baud = 	self.cbBaud.GetStringSelection()

			self.reprap.connect(port, baud)
			self.connected = True
			self.tb.SetToolNormalBitmap(TB_TOOL_CONNECT, self.disconnectPng)
			self.announcePrinter()

	def announcePrinter(self):
		pass
	
	def replace(self, s):
		d = {}
					
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
		self.filePrep.setPrinterBusy(flag)
	
	def switchToFilePrep(self, fn):
		self.nb.SetSelection(self.pxFilePrep)
		self.pgFilePrep.loadTempSTL(fn)

	def forwardToPrintMon(self, model):
		self.nb.SetSelection(self.pxPrtMon)
		self.pgPrtMon.forwardModel(model)

		
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
		self.log_window.this.disown()
		wx.Log.SetActiveTarget(None)
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


