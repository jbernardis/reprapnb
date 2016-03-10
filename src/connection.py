import os
import wx.lib.newevent
import glob
import time 
import thread
from sys import platform as _platform
if _platform == "linux" or _platform == "linux2":
	import termios #@UnresolvedImport

from settings import BUTTONDIM, BUTTONDIMLG, RECEIVED_MSG
from pendant import Pendant
from webcamclient import Webcam
from XMLDoc import XMLDoc

baudChoices = ["2400", "9600", "19200", "38400", "57600", "115200", "250000"]

from reprap import RepRap, RepRapParser

(PendantEvent, EVT_PENDANT) = wx.lib.newevent.NewEvent()
PENDANT_CONNECT = 0
PENDANT_DISCONNECT = 1
PENDANT_COMMAND = 3

TRACE = False

VISIBLELISTSIZE =  5

TLTICKRATE = 10
MAXDIRCHARS = 50
MAXSTATCHARS = 50


class Connection:
	def __init__(self, app, printer, port, baud):
		self.app = app
		self.logger = self.app.logger
		self.printer = printer
		self.port = port
		self.parser = RepRapParser(self.app)
		self.reprap = RepRap(self.app, printer)
		self.reprap.connect(port, baud)
		self.prtmon = None
		self.manctl = None
		self.pendantConnected = False

	def hasPendant(self):
		return self.pendantConnected

	def setPendant(self, flag=True):
		self.pendantConnected = flag

	def tick(self):
		if self.prtmon is not None:
			self.prtmon.tick()
		
	def assertAllowPulls(self, flag):
		if self.prtmon is not None:
			self.prtmon.assertAllowPulls(flag)
			
	def isPrinting(self):
		if self.prtmon is not None:
			return self.prtmon.isPrinting()
		return False
		
	def close(self):
		self.reprap.disconnect()
		while not self.reprap.checkDisconnection():
			time.sleep(0.1)
		self.reprap = None
		
		self.parser = None
		
		if self.prtmon:
			self.prtmon.onClose(None)
			self.prtmon = None
			
		if self.manctl:
			self.manctl = None

	def setNBPages(self, pm, mc):
		self.prtmon = pm
		self.manctl = mc
		self.parser.config(pm, mc)
		self.reprap.bind(pm, self.evtRepRap)
		
	def evtRepRap(self, evt):
		if evt.event == RECEIVED_MSG:
			if self.parser is not None:
				if not self.parser.parseMsg(evt.msg):
					self.logger.LogMessage("(r) - " + evt.msg)
		elif self.prtmon is not None:
			self.prtmon.reprapEvent(evt)

class ConnectionManager:
	def __init__(self, app):
		self.app = app
		self.settings = self.app.settings
		self.logger = self.app.logger
		self.connections = []
	
		self.portList = self.getPortList()	
					
		self.printerList = self.settings.printers[:]
		self.activePorts = []
		self.activePrinters = []
		self.pendantConnection = None
		self.pendantIndex = None
		self.manageDlg = None
		
	def manageDlgClose(self):
		self.manageDlg = None
		
	def getPortList(self):
		"""scan for available ports. return a list of device names."""
		pl = []
		for pt in self.settings.portprefixes:
			pl += glob.glob(pt)
			
		return sorted(pl)

	def connectionCount(self):
		return len(self.connections)
					
	def getLists(self, refreshPorts=False):
		if refreshPorts:
			pl = self.getPortList()
			self.portList = []
			for p in pl:
				if p not in self.activePorts:
					self.portList.append(p)

		return (self.printerList, self.portList, self.connections)
		
	def getStatus(self):
		stat = {}
		stat['nconnections'] = len(self.connections)

		cx = 1			
		for p in self.connections:
			pst = {}
			pst['printer'] = p.printer
			pst['port'] = p.port
			if p.isPrinting():
				pst['status'] = "printing"
				pst['printstat'] = p.prtmon.getStatus()
			else:
				pst['status'] = "idle"

			cid = "connection.%d" % cx				
			stat[cid] = pst
			cx += 1
				
		return stat
	
	def getTemps(self):
		result = {}
		result['nconnections'] = len(self.connections)

		cx = 1			
		for p in self.connections:
			pt = {}
			pt['printer'] = p.printer
			pt['temps'] = p.prtmon.getTemps()

			cid = "connection.%d" % cx				
			result[cid] = pt
			cx += 1
			
		return result
	
	def pendantCommand(self, cmd):
		if self.pendantConnection:
			if not self.pendantConnection.manctl.pendantCommand(cmd):
				if not self.pendantConnection.prtmon.pendantCommand(cmd):
					self.logger.LogMessage("Unknown pendant command: %s" % cmd)

		else:
			self.logger.LogMessage("Pendant command ignored - no printer connected")

	def activatePendant(self, flag):
		self.pendantConnection = None
		self.pendantIndex = None
		for cx in self.connections:
			cx.setPendant(False)

		if flag:
			if len(self.connections) > 0:
				self.pendantConnection = self.connections[0]
				self.pendantConnection.setPendant(True)
				self.pendantIndex = 0

	def connectPendant(self, cx):
		if cx == self.pendantIndex:
			return

		if cx < 0 or cx >= len(self.connections):
			self.pendantIndex = None
			self.pendantConnection = None
			for c in self.connections:
				c.setPendant(False)
		else:
			self.pendantIndex = cx
			if not self.pendantConnection is None:
				self.pendantConnection.setPendant(False)
			self.pendantConnection = self.connections[cx]
			self.pendantConnection.setPendant(True)
	
	def connect(self, printer, port, baud):
		cx = Connection(self.app, printer, port, baud)
		self.connections.append(cx)
		if len(self.connections) == 1:
			self.pendantConnection = cx
			self.pendantIndex = 0
			cx.setPendant(True)
		else:
			cx.setPendant(False)
			
		self.activePorts.append(port)
		self.activePrinters.append(printer)
		self.portList.remove(port)
		self.printerList.remove(printer)
		(pm, mc) = self.app.addPages(printer, cx.reprap)
		cx.setNBPages(pm, mc)
		
	def connectionByPrinter(self, printer):
		try:
			idx = self.activePrinters.index(printer)
		except:
			self.logger.LogMessage("Unable to find connection with printer %s" % printer)
			return None
		
		return self.connections[idx]
	
	def getConnection(self, cx):
		if cx < 0 or cx >= len(self.connections):
			return None
		else:
			return self.connections[cx]
		
	def disconnectByPrinter(self, printer):
		try:
			idx = self.activePrinters.index(printer)
		except:
			self.logger.LogMessage("Unable to find connection with printer %s" % printer)
			return False
		
		del self.activePrinters[idx]
		port = self.activePorts[idx]
		del self.activePorts[idx]
		con = self.connections[idx]
		del self.connections[idx]
		
		self.fixPendantLinkage(self.pendantIndex == idx)
		
		self.printerList.append(printer)
		self.printerList.sort()
		self.portList.append(port)
		self.portList.sort()
		self.app.delPages(printer)

		con.close()
		return True
		
	def disconnectByPort(self, port):
		try:
			idx = self.activePorts.index(port)
		except:
			self.logger.LogMessage("Unable to find connection with port %s" % port)
			return False
		
		del self.activePorts[idx]
		printer = self.activePrinters[idx]
		del self.activePrinters[idx]
		con = self.connections[idx]
		del self.connections[idx]
		
		self.fixPendantLinkage(self.pendantIndex == idx)
		
		self.printerList.append(printer)
		self.printerList.sort()
		self.portList.append(port)
		self.portList.sort()
		self.app.delPages(printer)

		con.close()
		return True


	def fixPendantLinkage(self, delPendant):
		if delPendant:
			if len(self.connections) == 0:
				self.pendantIndex = None
				self.pendantConnection = None
			else:
				self.pendantIndex = 0
				self.pendantConnection = self.connections[0]
				self.pendantConnection.setPendant(True)
		else:
			self.pendantIndex = None
			for ix in range(len(self.connections)):
				if self.connections[ix].hasPendant():
					self.pendantIndex = ix
					break
			if self.pendantIndex is None:
				self.pendantConnection = None
	
	def disconnectAll(self):
		for p in self.activePrinters:
			self.app.delPages(p)
		self.printerList.extend(self.activePrinters)
		self.activePrinters = []
		self.portList.extend(self.activePorts)
		self.activePorts = []
		for c in self.connections:
			c.close()
		self.connections = []
		self.pendantIndex = None
		self.pendantConnection = None
	
	def disconnectByRepRap(self, reprap):
		port = reprap.getPort()
		return self.disconnectByPort(port)
	
class SnapFrame(wx.Frame):
	def __init__(self, parent, picfn):
		self.fn = picfn
		wx.Frame.__init__(self, parent, wx.ID_ANY, "Snapshot", (-1, -1), (-1, -1), wx.DEFAULT_FRAME_STYLE)
		self.Bind(wx.EVT_CLOSE, self.onClose)
		
		png = wx.Image(picfn, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		
		sz = wx.BoxSizer(wx.VERTICAL)
		
		sz.Add(wx.StaticBitmap(self, wx.ID_ANY, png, (-1, -1), (png.GetWidth(), png.GetHeight())))
		sz.AddSpacer((10,10))
		
		self.cbRetain = wx.CheckBox(self, wx.ID_ANY, "Retain file %s" % picfn)
		sz.Add(self.cbRetain, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
		sz.AddSpacer((10,10))
		
		self.SetSizer(sz)
		self.Fit()
			
	def onClose(self, evt):
		if not self.cbRetain.IsChecked():
			try:
				os.unlink(self.fn)
			except:
				pass
		self.Destroy()

class ConnectionManagerPanel(wx.Panel):
	def __init__(self, parent, app):
		self.parent = parent
		self.app = app
		self.settings = self.app.settings
		self.logger = self.app.logger
		self.CameraPort = None
		self.timeLapsePaused = False
		self.timeLapseRunning = False
		self.tlTick = 0
		
		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(400, 250))
		
		self.CamLock = thread.allocate_lock()

		self.cm = ConnectionManager(self.app)
		self.Bind(EVT_PENDANT, self.pendantCommand)
		self.pendant = Pendant(self.pendantEvent, self.settings.pendantPort, self.settings.pendantBaud)
		self.pendantActive = False
		
		self.webcam = Webcam(self.settings.cameraport, self.settings.cmdfolder)
		
		self.camActive = False
		self.resolution = self.settings.resolution #TODO: work this back in
		
		self.SetBackgroundColour("white")

		f = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		dc = wx.WindowDC(self)
		dc.SetFont(f)

		self.sizer = wx.BoxSizer(wx.VERTICAL)

		sboxConnect = wx.StaticBox(self, -1, "Available ports/printers:")
		szsbConnect = wx.StaticBoxSizer(sboxConnect, wx.VERTICAL)
		
		szConnect = wx.BoxSizer(wx.VERTICAL)
		szConnect.AddSpacer((20, 20))
		
		szRow = wx.BoxSizer(wx.HORIZONTAL)
		szRow.AddSpacer((20, 20))
		sz = wx.BoxSizer(wx.VERTICAL)
		text = "Port:"
		w, h = dc.GetTextExtent(text)
			
		t = wx.StaticText(self, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w, h))
		t.SetFont(f)
		sz.Add(t)
		
		(printers, ports, connections) = self.cm.getLists()
		
		self.lbPort = wx.ListBox(self, wx.ID_ANY, (-1, -1),  (270, 120), ports, wx.LB_SINGLE)
		self.lbPort.SetFont(f)
		self.lbPort.SetToolTipString("Choose the port to which to connect")
		self.lbPort.SetSelection(0)
		sz.Add(self.lbPort)
		szRow.Add(sz)
		szRow.AddSpacer((10, 10))
		
		sz = wx.BoxSizer(wx.VERTICAL)
		
		text = "Baud:"
		w, h = dc.GetTextExtent(text)
		
		t = wx.StaticText(self, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w, h))
		t.SetFont(f)
		sz.Add(t)
		
		self.lbBaud = wx.ListBox(self, wx.ID_ANY, (-1, -1), (100, 150), baudChoices, wx.LB_SINGLE)
		self.lbBaud.SetFont(f)
		self.lbBaud.SetToolTipString("Choose the baud rate")
		self.lbBaud.SetSelection(5)
		sz.Add(self.lbBaud)
		szRow.Add(sz)
		szRow.AddSpacer((10, 10))
		
		sz = wx.BoxSizer(wx.VERTICAL)
			
		text = "Printer:"
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w, h))
		t.SetFont(f)
		sz.Add(t)
		
		self.lbPrinter = wx.ListBox(self, wx.ID_ANY, (-1, -1), (100, 120), printers, wx.LB_SINGLE)
		self.lbPrinter.SetFont(f)
		self.lbPrinter.SetToolTipString("Choose the printer")
		self.lbPrinter.SetSelection(0)
		sz.Add(self.lbPrinter)
		szRow.Add(sz)
		szRow.AddSpacer((20, 20))
		szConnect.Add(szRow)
		szConnect.AddSpacer((20, 20))
		
		sboxDisconnect = wx.StaticBox(self, -1, "Active Connections:")
		szsbDisconnect = wx.StaticBoxSizer(sboxDisconnect, wx.VERTICAL)
		szDisconnect = wx.BoxSizer(wx.HORIZONTAL)
		szDisconnect.AddSpacer((20, 20))

		self.lbConnections = ActiveConnectionCtrl(self, self.app.images)
		self.lbConnections.SetToolTipString("Choose the connection")
		self.loadConnections(connections)
		szDisconnect.Add(self.lbConnections, flag=wx.ALL, border=10)
		
		szButtons = wx.BoxSizer(wx.VERTICAL)
			
		szButtons.AddSpacer((10, 10))
		
		self.bConnect = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngConnect, size=BUTTONDIMLG)
		self.bConnect.SetToolTipString("Connect to the printer")
		self.Bind(wx.EVT_BUTTON, self.doConnect, self.bConnect)
		szButtons.Add(self.bConnect, flag=wx.ALL, border=10)
		self.bConnect.Enable(len(ports) >= 1)
		szButtons.AddSpacer((10, 10))

		self.bDisconnect = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngDisconnect, size=BUTTONDIMLG)
		self.bDisconnect.SetToolTipString("Disconnect the printer")
		szButtons.Add(self.bDisconnect, flag=wx.ALL, border=10)
		self.bDisconnect.Enable(False)
		self.Bind(wx.EVT_BUTTON, self.doDisconnect, self.bDisconnect)
		szButtons.AddSpacer((20, 20))

		self.bReset = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngReset, size=BUTTONDIMLG)
		self.bReset.SetToolTipString("Reset the printer")
		szButtons.Add(self.bReset, flag=wx.ALL, border=10)
		self.Bind(wx.EVT_BUTTON, self.doReset, self.bReset)
		self.bReset.Enable(False)
		szButtons.AddSpacer((20, 20))
		
		self.bPort = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngPorts, size=BUTTONDIMLG)
		self.bPort.SetToolTipString("Refresh list of available ports")
		szButtons.Add(self.bPort, flag=wx.ALL, border=10)
		self.Bind(wx.EVT_BUTTON, self.doPort, self.bPort)

		szsbConnect.Add(szConnect)
		szsbDisconnect.Add(szDisconnect)

		sboxCamera = wx.StaticBox(self, -1, "Camera")
		szsbCamera = wx.StaticBoxSizer(sboxCamera, wx.VERTICAL)
		szCamera = wx.BoxSizer(wx.HORIZONTAL)

		sboxCamCtrl = wx.StaticBox(self, -1, "Camera Control")
		hszCamCtrl = wx.StaticBoxSizer(sboxCamCtrl, wx.HORIZONTAL)
		szCamCtrl = wx.BoxSizer(wx.VERTICAL)
		szCamCtrl.AddSpacer((10, 10))

		self.cbCamActive = wx.CheckBox(self, wx.ID_ANY, "Activate Camera")
		self.cbCamActive.SetToolTipString("Activate/Deactivate the camera")
		self.Bind(wx.EVT_CHECKBOX, self.checkCamActive, self.cbCamActive)
		szCamCtrl.Add(self.cbCamActive)
		self.cbCamActive.SetValue(False)
		self.camActive = False
		
		szCamCtrl.AddSpacer((10, 10))
		
		ports = self.getCamPorts()
		self.lbCamPort = wx.ListBox(self, wx.ID_ANY, (-1, -1),  (270, 120), ports, wx.LB_SINGLE)
		self.lbCamPort.SetFont(f)
		self.lbCamPort.SetToolTipString("Choose the port to which to connect")
		self.lbCamPort.SetSelection(0)
		szCamera.AddSpacer((10, 10))
		szCamera.Add(self.lbCamPort)
		
		if len(ports) <= 0:
			self.cbCamActive.Enable(False)
			self.camActive = False
		else:
			self.cbCamActive.Enable(True)

		self.bSnapShot = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngSnapshot, size=BUTTONDIM)
		self.bSnapShot.SetToolTipString("Take a picture")
		szCamCtrl.AddSpacer((10, 10))
		szCamCtrl.Add(self.bSnapShot, 1, wx.ALIGN_CENTER_HORIZONTAL, 0)
		self.Bind(wx.EVT_BUTTON, self.doSnapShot, self.bSnapShot)
		self.bSnapShot.Enable(False)
		
		hb = wx.BoxSizer(wx.HORIZONTAL)
		
		hb.Add(wx.StaticText(self, wx.ID_ANY, "Brightness: ", size=(100, -1)), 1, wx.TOP, 20)
		self.slBrightness = wx.Slider(
			self, wx.ID_ANY, 50, 0, 100, size=(320, -1), 
			style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS 
			)
		self.slBrightness.SetTickFreq(10, 1)
		self.slBrightness.SetPageSize(1)
		hb.Add(self.slBrightness)
		szCamCtrl.AddSpacer((10, 10))
		szCamCtrl.Add(hb)
		
		hb = wx.BoxSizer(wx.HORIZONTAL)
		
		hb.Add(wx.StaticText(self, wx.ID_ANY, "Contrast: ", size=(100, -1)), 1, wx.TOP, 20)
		self.slContrast = wx.Slider(
			self, wx.ID_ANY, 50, 0, 100, size=(320, -1), 
			style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS 
			)
		self.slContrast.SetTickFreq(10, 1)
		self.slContrast.SetPageSize(1)
		hb.Add(self.slContrast)
		szCamCtrl.AddSpacer((10, 10))
		szCamCtrl.Add(hb)
		
		hb = wx.BoxSizer(wx.HORIZONTAL)
		
		hb.Add(wx.StaticText(self, wx.ID_ANY, "Saturation: ", size=(100, -1)), 1, wx.TOP, 20)
		self.slSaturation = wx.Slider(
			self, wx.ID_ANY, 50, 0, 100, size=(320, -1), 
			style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS 
			)
		self.slSaturation.SetTickFreq(10, 1)
		self.slSaturation.SetPageSize(1)
		hb.Add(self.slSaturation)
		szCamCtrl.AddSpacer((10, 10))
		szCamCtrl.Add(hb)

		szCamCtrl.AddSpacer((10, 10))
		hszCamCtrl.AddSpacer((10, 10))
		hszCamCtrl.Add(szCamCtrl)
		hszCamCtrl.AddSpacer((10, 10))

		sboxTl = wx.StaticBox(self, wx.ID_ANY, "Time Lapse Control")
		hszTlCtrl = wx.StaticBoxSizer(sboxTl, wx.HORIZONTAL)
		szTlCtrl = wx.BoxSizer(wx.VERTICAL)
		szTlCtrl.AddSpacer((10, 10))
		
		hb = wx.BoxSizer(wx.HORIZONTAL)
		self.bTimeStart = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngTimestart, size=BUTTONDIM)
		self.bTimeStart.SetToolTipString("Start time lapse photography")
		hb.AddSpacer((10, 10))
		hb.Add(self.bTimeStart)
		self.Bind(wx.EVT_BUTTON, self.doTimeLapseStart, self.bTimeStart)
		self.bTimeStart.Enable(False)
		
		self.bTimePause = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngTimepause, size=BUTTONDIM)
		self.bTimePause.SetToolTipString("Pause/resume time lapse photography")
		hb.AddSpacer((10, 10))
		hb.Add(self.bTimePause)
		self.Bind(wx.EVT_BUTTON, self.doTimeLapsePause, self.bTimePause)
		self.bTimePause.Enable(False)
		
		self.bTimeStop = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngTimestop, size=BUTTONDIM)
		self.bTimeStop.SetToolTipString("Stop time lapse photography")
		hb.AddSpacer((10, 10))
		hb.Add(self.bTimeStop)
		self.Bind(wx.EVT_BUTTON, self.doTimeLapseStop, self.bTimeStop)
		self.bTimeStop.Enable(False)
		
		szTlCtrl.AddSpacer((10, 10))
		szTlCtrl.Add(hb)
		
		szTlCtrl.AddSpacer((10, 10))
		hb = wx.BoxSizer(wx.HORIZONTAL)
		
		hb.Add(wx.StaticText(self, wx.ID_ANY, "Interval(sec): "), 1, wx.TOP, 20)
		hb.AddSpacer((20, 20))
		self.slInterval = wx.Slider(
			self, wx.ID_ANY, 10, 5, 300, size=(320, -1), 
			style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS 
			)
		self.slInterval.SetTickFreq(10, 1)
		self.slInterval.SetPageSize(1)
		hb.Add(self.slInterval)
		
		szTlCtrl.AddSpacer((10, 10))
		szTlCtrl.Add(hb)
		
		hb = wx.BoxSizer(wx.HORIZONTAL)
		
		self.rbDuration = wx.RadioBox(
				self, wx.ID_ANY, "Duration", wx.DefaultPosition, wx.DefaultSize,
				["Count", "Seconds"], 1, wx.RA_SPECIFY_COLS)
		
		hb.Add(self.rbDuration)
		hb.AddSpacer((20, 20))
		
		self.tcDuration = wx.TextCtrl(self, -1, "10", size=(80, -1))
		hb.Add(self.tcDuration, 0, wx.TOP, 20)
		
		szTlCtrl.AddSpacer((10, 10))
		szTlCtrl.Add(hb)
		
		hb = wx.BoxSizer(wx.HORIZONTAL)
		
		self.bDir = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngDirectory, size=BUTTONDIM)
		hb.Add(self.bDir)
		self.Bind(wx.EVT_BUTTON, self.setTlDirectory, self.bDir)
		hb.AddSpacer((20, 20))

		ipfont = wx.Font(14,  wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		dc = wx.WindowDC(self)
		dc.SetFont(ipfont)
		self.tlDir = os.path.join(self.settings.cmdfolder, "tlpics")
		w, h = dc.GetTextExtent("X" * MAXDIRCHARS)
		w = int(0.75 * w)
		padding = " " * MAXDIRCHARS
		self.txtDir = wx.StaticText(self, wx.ID_ANY, self.tlDir + padding, style=wx.ALIGN_LEFT, size=(w, h))
		self.txtDir.SetFont(ipfont)
		hb.Add(self.txtDir, 1, wx.TOP, 12)
				
		szTlCtrl.AddSpacer((10, 10))
		szTlCtrl.Add(hb)
		
		szTlCtrl.AddSpacer((10, 10))
		hb = wx.BoxSizer(wx.HORIZONTAL)

		self.tlDir = "."
		w, h = dc.GetTextExtent("X" * MAXSTATCHARS)
		w = int(0.75 * w)
		padding = " " * MAXSTATCHARS
		self.txtTlStatus = wx.StaticText(self, wx.ID_ANY, padding, style=wx.ALIGN_LEFT, size=(w, h))
		self.txtTlStatus.SetFont(ipfont)
		hb.Add(self.txtTlStatus)
		
		szTlCtrl.Add(hb)
		szTlCtrl.AddSpacer((10, 10))
		
		hszTlCtrl.AddSpacer((20, 20))
		hszTlCtrl.Add(szTlCtrl)
		hszTlCtrl.AddSpacer((10, 10))
		
		szCamera.AddSpacer((10, 10))
		szsbCamera.AddSpacer((10, 10))
		szsbCamera.Add(szCamera)
		szsbCamera.AddSpacer((10, 10))

		sz = wx.BoxSizer(wx.HORIZONTAL)
		sz.AddSpacer((20, 20))
		sz.Add(szsbConnect)
		sz.AddSpacer((20, 20))
		sz.Add(szButtons)
		sz.AddSpacer((20, 20))
		sz.Add(szsbDisconnect)
		sz.AddSpacer((20, 20))
		
		self.sizer.AddSpacer((20, 20))
		self.sizer.Add(sz)

		sz = wx.BoxSizer(wx.HORIZONTAL)
		sz.AddSpacer((20, 20))
		sz.Add(szsbCamera)
		sz.AddSpacer((20, 20))
		sz.Add(hszCamCtrl)
		sz.AddSpacer((20, 20))
		sz.Add(hszTlCtrl)
		
		self.sizer.AddSpacer((50, 50))
		self.sizer.Add(sz)

		self.sizer.AddSpacer((20, 20))
		self.SetSizer(self.sizer)
		self.lbCamPort.SetSelection(0)
		
	def setTlDirectory(self, evt):
		dlg = wx.DirDialog(self, "Choose a directory for timelapse pictures:")
		if dlg.ShowModal() == wx.ID_OK:
			self.tlDir = dlg.GetPath()
			self.txtDir.SetLabel(self.tlDir)

		dlg.Destroy()
		
	def doTimeLapseStart(self, evt):
		interval = self.slInterval.GetValue()
		
		dType = self.rbDuration.GetSelection()
		try:
			print "duration=(%s)" % self.tcDuration.GetValue()
			dVal = int(self.tcDuration.GetValue())
		except:
			dlg = wx.MessageDialog(self, "Invalid duration Value",
					'Invalid Value', wx.OK | wx.ICON_ERROR)
	
			dlg.ShowModal()
			dlg.Destroy()
			return
			
		if dType == 0:
			count = dVal
			seconds = None
		else:
			count = None
			seconds = dVal
			
		self.webcam.timelapseStart(interval, count=count, duration=seconds, directory=self.tlDir)
		self.timeLapsePaused = False
		self.timeLapseRunning = True
		self.tlTick = TLTICKRATE
		
		#self.bSnapShot.Enable(False)
		self.bTimeStart.Enable(False)
		self.lbCamPort.Enable(False)
		self.cbCamActive.Enable(False)

		self.bTimePause.Enable(True)
		self.bTimeStop.Enable(True)
		
	def timeLapseEnded(self):
		self.timeLapsePaused = False
		self.timeLapseRunning = False
		
		self.updateTimeLapseStatus("")
		self.bTimeStart.Enable(True)
		self.lbCamPort.Enable(True)
		self.cbCamActive.Enable(True)

		self.bTimePause.Enable(False)
		self.bTimeStop.Enable(False)
		
	def updateTimeLapseStatus(self, text):
		self.txtTlStatus.SetLabel(text)
		
	def doTimeLapsePause(self, evt):
		self.timeLapsePaused = not self.timeLapsePaused
		if self.timeLapsePaused:
			self.webcam.pause()
		else:
			self.webcam.resume()
			
	def doTimeLapseStop(self, evt):
		self.webcam.stop()
		
		self.bSnapShot.Enable(True)
		self.bTimeStart.Enable(True)
		self.lbCamPort.Enable(True)
		self.cbCamActive.Enable(True)

		self.bTimePause.Enable(False)
		self.bTimeStop.Enable(False)

	def loadConnections(self, cxlist):
		self.lbConnections.loadConnections(cxlist)
			
	def isPendantActive(self):
		return self.pendantActive

	def doCamPort(self, evt):
		self.refreshCamPorts()
			
	def refreshCamPorts(self):
		ports = self.getCamPorts()
		self.lbCamPort.Enable(True)
		self.lbCamPort.SetItems(ports)

		if len(ports) >= 1:
			self.cbCamActive.Enable(True)
			if self.CameraPort is not None:
				if self.CameraPort in ports:
					self.lbCamPort.SetSelection(ports.index(self.CameraPort))
					self.cbCamActive.SetValue(True)
					self.camActive = True
					self.bSnapShot.Enable(True)
					self.bTimeStart.Enable(not self.timeLapseRunning)
				else:
					self.lbCamPort.SetSelection(0)
					self.cbCamActive.SetValue(False)
					self.camActive = False
					self.bSnapShot.Enable(False)
					self.bTimeStart.Enable(False)
			else:
				self.cbCamActive.SetValue(False)
				self.camActive = False
				self.bSnapShot.Enable(False)
				self.bTimeStart.Enable(False)
				self.lbCamPort.SetSelection(0)
		else:
			self.lbCamPort.Enable(False)
			self.cbCamActive.Enable(False)
			self.bSnapShot.Enable(False)
			self.bTimeStart.Enable(False)
			self.camActive = False
	
	def getCamPorts(self):
		pl = glob.glob('/dev/video*')
		return sorted(pl)

	def checkCamActive(self, evt):
		self.camActive = evt.IsChecked()
		if self.camActive:
			port = 	self.lbCamPort.GetString(self.lbCamPort.GetSelection())
			self.bSnapShot.Enable(True)
			self.bTimeStart.Enable(not self.timeLapseRunning)
			self.lbCamPort.Enable(False)
			self.webcam.connect(port)
			self.CameraPort = port[:]
		else:
			self.bSnapShot.Enable(False)
			self.bTimeStart.Enable(False)
			self.lbCamPort.Enable(True)
			self.webcam.disconnect()
			self.CameraPort = None

	def doSnapShot(self, evt):
		picfn = self.snapShot()
		if picfn is None:
			dlg = wx.MessageDialog(self, "Error Taking Picture",
					'Camera Error', wx.OK | wx.ICON_ERROR)
	
			dlg.ShowModal()
			dlg.Destroy()
		else:
			s = SnapFrame(self, picfn)
			s.Show()
			
	def snapShot(self, block=True):
		if not self.camActive:
			return None
		
		rc, xml = self.webcam.picture(directory="pics") # TODO - settings
		if not rc:
			return None
			
		xd = XMLDoc(xml).getRoot()
		return str(xd.filename)
	
	def tick(self):
		if self.timeLapseRunning and not self.timeLapsePaused:
			self.tlTick -= 1
			if self.tlTick <= 0:
				self.tlTick = TLTICKRATE
				rc, xml = self.webcam.timelapseStatus()
				if not rc:
					self.timeLapseEnded()
				else:
					xd = XMLDoc(xml).getRoot()
					try:
						st = str(xd.result)
					except AttributeError:
						self.timeLapseEnded()
					else:
						if st == "idle":
							self.timeLapseEnded()
						else:
							iteration = int(str(xd.iterations))
							maxIteration = int(str(xd.maxiterations))
							statLine = st + " - %d out of %d completed" % (iteration, maxIteration)
							self.updateTimeLapseStatus(statLine)
							
		cxlist = self.cm.getLists()[2]
		for cx in cxlist:
			cx.tick()
	
	def assertAllowPulls(self, flag):
		cxlist = self.cm.getLists()[2]
		for cx in cxlist:
			cx.assertAllowPulls(flag)
		
	def isAnyPrinting(self):
		cxlist = self.cm.getLists()[2]
		for cx in cxlist:
			if cx.isPrinting():
				return True
		return False

	def doPort(self, evt):
		self.refreshPorts()
		
	def refreshPorts(self):
		ports = self.cm.getLists(True)[1]
		self.lbPort.SetItems(ports)
		if len(ports) >= 1:
			self.bConnect.Enable(True)
			self.lbPort.SetSelection(0)
		else:
			self.bConnect.Enable(False)
			
		self.refreshCamPorts()
			
	def getStatus(self):
		return self.cm.getStatus()
			
	def getTemps(self):
		return self.cm.getTemps()
	
	def pendantEvent(self, cmd):
		if cmd == "pendant connected":
				evt = PendantEvent(eid = PENDANT_CONNECT)
		elif cmd == "pendant disconnected":
				evt = PendantEvent(eid = PENDANT_DISCONNECT)
		else:
				evt = PendantEvent(eid = PENDANT_COMMAND, cmdString=cmd)
		try:
			wx.PostEvent(self, evt)
		except:
			pass
		
	def pendantCommand(self, evt):
		if evt.eid == PENDANT_CONNECT:
			self.logger.LogMessage("Pendant connected")
			self.pendantActive = True
			self.cm.activatePendant(True)
			connections = self.cm.getLists()[2]
			self.loadConnections(connections)

		elif evt.eid == PENDANT_DISCONNECT:
			self.logger.LogMessage("Pendant disconnected")
			self.pendantActive = False
			connections = self.cm.getLists()[2]
			self.loadConnections(connections)
		else:
			if TRACE:
				self.logger.LogMessage(evt.cmdString)
			self.cm.pendantCommand(evt.cmdString)
	
	def doSetPendant(self, evt):
		if not self.pendantActive:
			return

		cx = self.lbConnections.GetFirstSelected()
		
		self.cm.connectPendant(cx)
		connections = self.cm.getLists()[2]
		self.loadConnections(connections)

	def setPendant(self, cx):
		if not self.pendantActive:
			return
		
		self.cm.connectPendant(cx)
		connections = self.cm.getLists()[2]
		self.loadConnections(connections)

	def doDisconnect(self, evt):
		item = self.lbConnections.GetFirstSelected()
		if item == -1:
			if self.cm.connectionCount() == 1:
				item = 0
			else:
				dlg = wx.MessageDialog(self, "Please choose a connection to disconnect",
					'No Connection Selected', wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()
				return
		
		cxtext = self.lbConnections.GetItemText(item)
		try:
			prtr = cxtext.split()[0]
			if prtr == "*":
				try:
					prtr = cxtext.split()[1]
				except:
					prtr = None
		except:
			prtr = None

		if prtr is not None:
			cx = self.cm.connectionByPrinter(prtr)
			if cx is not None:
				if cx.isPrinting():
					if self.pgConnMgr.isAnyPrinting():
						dlg = wx.MessageDialog(self, "Are you sure you want to disconnect printer %s while it is active" % prtr,
											'Printing Active', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_INFORMATION)
			
						rc = dlg.ShowModal()
						dlg.Destroy()
		
						if rc != wx.ID_YES:
							return
				self.disconnectByPrinter(prtr)

	def disconnectByPrinter(self, prtr):			
		if self.cm.disconnectByPrinter(prtr):
			(printers, ports, connections) = self.cm.getLists()
			self.lbPort.SetItems(ports)
			self.lbPort.SetSelection(0)
			self.lbPrinter.SetItems(printers)
			self.lbPrinter.SetSelection(0)
			if len(ports) > 0 and len(printers) > 0:
				self.bConnect.Enable(True)
			if len(connections) == 0:
				self.bDisconnect.Enable(False)
				self.bReset.Enable(False)
			self.loadConnections(connections)
				

	def doConnect(self, evt):
		port = 	self.lbPort.GetString(self.lbPort.GetSelection())
		baud = 	self.lbBaud.GetString(self.lbBaud.GetSelection())
		printer = 	self.lbPrinter.GetString(self.lbPrinter.GetSelection())
		
		if self.settings.resetonconnect:
			self.resetPort(port)
			
		self.cm.connect(printer, port, baud)
		(printers, ports, connections) = self.cm.getLists()
		self.lbPort.SetItems(ports)
		if len(ports) == 0:
			self.bConnect.Enable(False)
		else:
			self.lbPort.SetSelection(0)
		self.lbPrinter.SetItems(printers)
		if len(printers) == 0:
			self.bConnect.Enable(False)
		else:
			self.lbPrinter.SetSelection(0)
		self.loadConnections(connections)
		self.bDisconnect.Enable(True)
		self.bReset.Enable(True)
		
	def resetPort(self, port):
		if _platform == "linux" or _platform == "linux2":
			fp = open(port, "r")
			new = termios.tcgetattr(fp)
			new[2] = new[2] | ~termios.CREAD
			termios.tcsetattr(fp, termios.TCSANOW, new)
			fp.close()
		
	def onClose(self):
		self.webcam.exit()
		self.cm.disconnectAll()
		self.bDisconnect.Enable(False)

	def doReset(self, evt):
		item = self.lbConnections.GetFirstSelected()
		if item == -1:
			if self.cm.connectionCount() == 1:
				item = 0
			else:
				dlg = wx.MessageDialog(self, "Please choose a connection to reset",
					'No Connection Selected', wx.OK | wx.ICON_ERROR)
				dlg.ShowModal()
				dlg.Destroy()
				return
			
		connections = self.cm.getLists()[2]
		cx = connections[item]

		cxtext = self.lbConnections.GetItemText(item)
		try:
			prtr = cxtext.split()[0]
			if prtr == "*":
				try:
					prtr = cxtext.split()[1]
				except:
					prtr = ""
		except:
			prtr = ""


		if cx.reprap is not None:
			dlg = wx.MessageDialog(self, "Are you sure you want to reset printer %s" % prtr,
								'Printer Reset', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_INFORMATION)
		
			rc = dlg.ShowModal()
			dlg.Destroy()

			if rc == wx.ID_YES:
				cx.reprap.reset()
				if cx.prtmon is not None:
					cx.prtmon.printerReset()

class ActiveConnectionCtrl(wx.ListCtrl):	
	def __init__(self, parent, images):
		
		f = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		dc = wx.ScreenDC()
		dc.SetFont(f)
		fontHeight = dc.GetTextExtent("Xy")[1]
		
		colWidths = [150, 200]
		colTitles = ["Printer", "Port"]
		
		totwidth = 20;
		for w in colWidths:
			totwidth += w
		
		wx.ListCtrl.__init__(self, parent, wx.ID_ANY, size=(totwidth, fontHeight*(VISIBLELISTSIZE+1)),
			style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES|wx.LC_SINGLE_SEL
			)

		self.parent = parent		
		self.il = wx.ImageList(16, 16)
		self.il.Add(images.pngNopendant)
		self.il.Add(images.pngPendant)
		self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

		self.cxList = []
		
		self.SetFont(f)
		for i in range(len(colWidths)):
			self.InsertColumn(i, colTitles[i])
			self.SetColumnWidth(i, colWidths[i])
		
		self.SetItemCount(0)
		
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.doSetPendant)
		
	def doSetPendant(self, evt):
		sx = self.GetFirstSelected()
		if sx == -1:
			return
		self.parent.setPendant(sx)
	
	def loadConnections(self, cxList):
		self.cxList = cxList
		self.SetItemCount(len(cxList))
		self.Refresh()
	
	def OnGetItemText(self, item, col):
		if col == 0:
			return self.cxList[item].printer
		elif col == 1:
			return self.cxList[item].port
		else:
			return ""

	def OnGetItemImage(self, item):
		if self.parent.isPendantActive() and self.cxList[item].hasPendant():
			return 1
		else:
			return 0
	
	def OnGetItemAttr(self, item):
		return None
