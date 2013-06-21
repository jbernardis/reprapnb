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

BUTTONDIM = (64, 64)

baudChoices = ["2400", "9600", "19200", "38400", "57600", "115200", "250000"]

		
class DataPage(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)	
		t = wx.StaticText(self, -1, "Temperature graphs, usage", (60,60))

class MainFrame(wx.Frame):
	def __init__(self):
		wx.Frame.__init__(self, None, title="Rep Rap Notebook", size=[1475, 950])
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.log_window = wx.LogWindow(self, 'Log Window', bShow=True)
		
		self.settings = Settings(self, cmd_folder)
		
		self.connected = False

		self.slicer = self.settings.getSlicerSettings(self.settings.slicer)
		if self.slicer is None:
			wx.LogError("Unable to get slicer settings")

		p = wx.Panel(self)

		f = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
		sizerBtns = wx.BoxSizer(wx.HORIZONTAL)
		sizerBtns.AddSpacer((20,20))
		
		path = os.path.join(self.settings.cmdfolder, "images/ports.png")	
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		self.bPort = wx.BitmapButton(p, wx.ID_ANY, png, size=BUTTONDIM)
		self.bPort.SetToolTipString("Refresh the list of available USB ports")
		sizerBtns.Add(self.bPort)
		ports = self.scanSerial()	
		self.Bind(wx.EVT_BUTTON, self.doPort, self.bPort)
		
		self.cbPort = wx.ComboBox(p, wx.ID_ANY, "", (-1, -1),  (-1, -1), ports, wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbPort.SetFont(f)
		self.cbPort.SetToolTipString("Choose the port to which to connect")
		sizerBtns.Add(self.cbPort)
		
		t = wx.StaticText(p, wx.ID_ANY, "@", style=wx.ALIGN_CENTER, size=(40, 35))
		t.SetFont(f)
		sizerBtns.Add(t)
		
		self.cbBaud = wx.ComboBox(p, wx.ID_ANY, "115200", (-1, -1), (-1, -1), baudChoices, wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbBaud.SetFont(f)
		self.cbBaud.SetToolTipString("Choose the baud rate")
		sizerBtns.Add(self.cbBaud, 1, wx.EXPAND)
		
		path = os.path.join(self.settings.cmdfolder, "images/connect.png")	
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		self.bConnect = wx.BitmapButton(p, wx.ID_ANY, png, size=BUTTONDIM)
		self.bConnect.SetToolTipString("Connect to the printer")
		sizerBtns.Add(self.bConnect)
		self.Bind(wx.EVT_BUTTON, self.doConnect, self.bConnect)
		if len(ports) < 1:
			self.bConnect.Enable(False)
			
		t = wx.StaticText(p, wx.ID_ANY, "Slicer:  ", style=wx.ALIGN_RIGHT)
		t.SetFont(f)
		sizerBtns.Add(t, 1, wx.EXPAND)
		
		self.cbSlicer = wx.ComboBox(p, wx.ID_ANY, self.settings.slicer, (-1, -1), (-1, -1), self.settings.slicers, wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbSlicer.SetFont(f)
		self.cbSlicer.SetToolTipString("Choose which slicer to use")
		sizerBtns.Add(self.cbSlicer)
		self.Bind(wx.EVT_COMBOBOX, self.doChooseSlicer, self.cbSlicer)
			
		t = wx.StaticText(p, wx.ID_ANY, "Profile:  ", style=wx.ALIGN_RIGHT)
		t.SetFont(f)
		sizerBtns.Add(t, 1, wx.EXPAND)
		
		self.cbProfile = wx.ComboBox(p, wx.ID_ANY, self.slicer.settings['profile'],
									(-1, -1), (-1, -1), self.slicer.type.getProfileOptions().keys(), wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbProfile.SetFont(f)
		self.cbSlicer.SetToolTipString("Choose which slicer profile to use")
		sizerBtns.Add(self.cbProfile)
		self.Bind(wx.EVT_COMBOBOX, self.doChooseProfile, self.cbProfile)

		sizerBtns.AddSpacer((60, 20))
				
		path = os.path.join(self.settings.cmdfolder, "images/log.png")	
		png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		mask = wx.Mask(png, wx.BLUE)
		png.SetMask(mask)
		self.bLog = wx.BitmapButton(p, wx.ID_ANY, png, size=BUTTONDIM)
		self.bLog.SetToolTipString("Hide/Show logging window")
		sizerBtns.Add(self.bLog)
		self.Bind(wx.EVT_BUTTON, self.doShowHideLog, self.bLog)
		self.logShowing = True
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.nb = wx.Notebook(p, style=wx.NB_TOP)

		self.pxPlater = 0
		self.pxFilePrep = 1
		self.pxManCtl = 2
		self.pxPrtMon = 3
		self.pxData = 4
		
		self.pgPlater = Plater(self.nb, self)
		self.pgFilePrep = FilePrepare(self.nb, self)
		self.pgManCtl = ManualControl(self.nb, self)
		self.pgPrtMon = PrintMonitor(self.nb, self)
		pgData = DataPage(self.nb)

		self.nb.AddPage(self.pgPlater, "Plating")
		self.nb.AddPage(self.pgFilePrep, "File Preparation")
		self.nb.AddPage(self.pgManCtl, "Manual Control")
		self.nb.AddPage(self.pgPrtMon, "Print/Monitor")
		self.nb.AddPage(pgData, "Data")
		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.checkPageChanged, self.nb)

		sizer.AddSpacer((20,20))
		sizer.Add(sizerBtns)
		sizer.AddSpacer((10,10))
		sizer.Add(self.nb)
		p.SetSizer(sizer)
	
	def doShowHideLog(self, evt):
		self.logShowing = not self.logShowing
		self.log_window.Show(self.logShowing)
		
	def checkPageChanged(self, evt):
		newPage = evt.GetSelection()
		currentPage = evt.GetOldSelection()
		if newPage in [self.pxManCtl, self.pxPrtMon] and not self.connected:
			wx.LogWarning("Tab is inaccessible unless printer is connected")
			self.nb.SetSelection(currentPage)
			evt.Veto()
		else:
			evt.Skip()
		
	def doChooseProfile(self, evt):
		newprof = self.cbProfile.GetValue()
		self.slicer.settings['profile'] = newprof
		self.slicer.setModified()
		
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
		self.cbPort.AppendItems(l)
		if len(l) == 0:
			self.bConnect.Enable(False)
		else:
			self.bConnect.Enable(True)
	
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
			# disconnect from the printer
			self.connected = False
			self.announcePrinter()
		else:
			# connect to the printer
			self.connected = True
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

		
	def onClose(self, evt):
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


