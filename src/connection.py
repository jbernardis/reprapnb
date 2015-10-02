import wx
import wx.lib.newevent
import glob
import time 
import pygame.camera

from settings import BUTTONDIM, BUTTONDIMLG, RECEIVED_MSG
from pendant import Pendant

baudChoices = ["2400", "9600", "19200", "38400", "57600", "115200", "250000"]

from reprap import RepRap, RepRapParser

(PendantEvent, EVT_PENDANT) = wx.lib.newevent.NewEvent()
PENDANT_CONNECT = 0
PENDANT_DISCONNECT = 1
PENDANT_COMMAND = 3

TRACE = False


class Connection:
	def __init__(self, app, printer, port, baud):
		self.app = app
		self.logger = self.app.logger
		self.printer = printer
		self.port = port
		self.parser = RepRapParser(self.app)
		self.reprap = RepRap(self.app)
		self.reprap.connect(port, baud)
		self.prtmon = None
		self.manctl = None

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
			
		return pl
					
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

	def connect(self, printer, port, baud):
		cx = Connection(self.app, printer, port, baud)
		self.connections.append(cx)
		if len(self.connections) == 1:
			self.pendantConnection = cx
			self.pendantIndex = 0
			
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
		
		if self.pendantIndex == idx:
			self.pendantIndex = None
			self.pendantConnection = None
		
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
		
		if self.pendantIndex == idx:
			self.pendantIndex = None
			self.pendantConnection = None
		
		self.printerList.append(printer)
		self.printerList.sort()
		self.portList.append(port)
		self.portList.sort()
		self.app.delPages(printer)

		con.close()
		return True
	
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
	def __init__(self, parent, data):
		self.failed = False
		wx.Frame.__init__(self, parent, wx.ID_ANY, "Snapshot", (-1, -1), (-1, -1), wx.DEFAULT_FRAME_STYLE)
		self.Bind(wx.EVT_CLOSE, self.onClose)
		
		s = pygame.image.tostring(data, 'RGB')  # Convert the surface to an RGB string
		img = wx.ImageFromData(data.get_width(), data.get_height(), s)  # Load this string into a wx image
		bmp = wx.BitmapFromImage(img)  # Get the image in bitmap form
		
		wx.StaticBitmap(self, wx.ID_ANY, bmp, (-1, -1), (bmp.GetWidth(), bmp.GetHeight()))
		self.Fit()
			
	def onClose(self, evt):
		self.Destroy()

class ConnectionManagerPanel(wx.Panel):
	def __init__(self, parent, app):
		self.parent = parent
		self.app = app
		self.settings = self.app.settings
		self.logger = self.app.logger
		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(400, 250))

		self.cm = ConnectionManager(self.app)
		self.Bind(EVT_PENDANT, self.pendantCommand)
		self.pendant = Pendant(self.pendantEvent, self.settings.pendantPort, self.settings.pendantBaud)
		
		pygame.init()
		pygame.camera.init()
		
		self.camActive = False
		self.Camera = None
		self.CameraPort = None
		
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

		self.lbConnections = wx.ListBox(self, wx.ID_ANY, (-1, -1), (400, 120), [], wx.LB_SINGLE)
		self.lbConnections.SetFont(f)
		self.lbConnections.SetToolTipString("Choose the connection")
		self.loadConnections(connections)
		szDisconnect.Add(self.lbConnections, flag=wx.ALL, border=10)
		
		szBtns = wx.BoxSizer(wx.VERTICAL)
		
		szBtns.AddSpacer((20, 20))

		self.bReset = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngReset, size=BUTTONDIM)
		self.bReset.SetToolTipString("Reset the printer")
		szBtns.Add(self.bReset, flag=wx.ALL, border=10)
		self.Bind(wx.EVT_BUTTON, self.doReset, self.bReset)
		self.bReset.Enable(False)
		
		szDisconnect.AddSpacer((10, 10))
		szDisconnect.Add(szBtns)

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
		self.bPort = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngPorts, size=BUTTONDIMLG)
		self.bPort.SetToolTipString("Refresh list of available ports")
		szButtons.Add(self.bPort, flag=wx.ALL, border=10)
		self.Bind(wx.EVT_BUTTON, self.doPort, self.bPort)

		szsbConnect.Add(szConnect)
		szsbDisconnect.Add(szDisconnect)

		sboxCamera = wx.StaticBox(self, -1, "Camera:")
		szsbCamera = wx.StaticBoxSizer(sboxCamera, wx.VERTICAL)
		szCamera = wx.BoxSizer(wx.HORIZONTAL)
		szCamera.AddSpacer((20, 20))

		self.cbCamActive = wx.CheckBox(self, wx.ID_ANY, "Activate Camera")
		self.cbCamActive.SetToolTipString("Activate/Deactivate the camera")
		self.Bind(wx.EVT_CHECKBOX, self.checkCamActive, self.cbCamActive)
		szCamera.AddSpacer((10, 10))
		szCamera.Add(self.cbCamActive)
		self.cbCamActive.SetValue(False)
		self.camActive = False
		
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
		szCamera.AddSpacer((10, 10))
		szCamera.Add(self.bSnapShot)
		self.Bind(wx.EVT_BUTTON, self.doSnapShot, self.bSnapShot)
		self.bSnapShot.Enable(False)
		
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
		
		self.sizer.AddSpacer((50, 50))
		self.sizer.Add(sz)

		self.sizer.AddSpacer((20, 20))
		self.SetSizer(self.sizer)
		self.lbCamPort.SetSelection(0)
		
	def loadConnections(self, cxlist):
		self.lbConnections.Clear()
		for cx in cxlist:
			self.lbConnections.Append("%s on %s" % (cx.printer, cx.port), cx)
		if len(cxlist) > 0:
			self.lbConnections.SetSelection(0)
			
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
				else:
					self.lbCamPort.SetSelection(0)
					self.cbCamActive.SetValue(False)
					self.camActive = False
					self.bSnapShot.Enable(False)
					self.Camera = None
					self.CameraPort = None
			else:
				self.cbCamActive.SetValue(False)
				self.camActive = False
				self.bSnapShot.Enable(False)
				self.lbCamPort.SetSelection(0)
		else:
			self.lbCamPort.Enable(False)
			self.cbCamActive.Enable(False)
			self.bSnapShot.Enable(False)
			self.camActive = False
			self.Camera = None
			self.CameraPort = None
	
	def getCamPorts(self):
		pl = glob.glob('/dev/video*')
		return pl
	
	def checkCamActive(self, evt):
		self.camActive = evt.IsChecked()
		if self.camActive:
			port = 	self.lbCamPort.GetString(self.lbCamPort.GetSelection())
			try:
				self.Camera = pygame.camera.Camera(port, (640,480))
				self.CameraPort = port[:]
				self.bSnapShot.Enable(True)
				self.lbCamPort.Enable(False)
			except:
				dlg = wx.MessageDialog(self, "Error Initializing Camera",
									'Camera Error', wx.OK | wx.ICON_ERROR)
	
				dlg.ShowModal()
				dlg.Destroy()

				self.Camera = None
				self.CameraPort = None
				self.cbCamActive.SetValue(False)
				self.camActive = False
				self.bSnapShot.Enable(False)
				self.lbCamPort.Enable(True)
		else:
			self.bSnapShot.Enable(False)
			self.lbCamPort.Enable(True)
			self.Camera = None
			self.CameraPort = None
			
	def doSnapShot(self, evt):
		pic = self.snapShot()
		if pic is None:
			dlg = wx.MessageDialog(self, "Error Taking Picture\nCamera Disconnected",
					'Camera Error', wx.OK | wx.ICON_ERROR)
	
			dlg.ShowModal()
			dlg.Destroy()
			return
		
		s = SnapFrame(self, pic)
		s.Show()
			
	def snapShot(self):
		if not self.camActive:
			return None
		
		try:
			self.Camera.start()
			image = self.Camera.get_image()
			self.Camera.stop()
		except:
			wx.CallAfter(self.disconnectCamera)
			return None

		return image
	
	def disconnectCamera(self):
		self.logger.LogMessage("Disconnecting camera due to error")
		self.camActive = False
		self.Camera = None
		self.CameraPort = None
		self.cbCamActive.SetValue(False)
		self.refreshCamPorts()
	
	def tick(self):
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
		wx.PostEvent(self, evt)
		
	def pendantCommand(self, evt):
		if evt.eid == PENDANT_CONNECT:
			self.logger.LogMessage("Pendant connected")
		elif evt.eid == PENDANT_DISCONNECT:
			self.logger.LogMessage("Pendant disconnected")
		else:
			if TRACE:
				self.logger.LogMessage(evt.cmdString)
			self.cm.pendantCommand(evt.cmdString)
	
	def doDisconnect(self, evt):
		cxtext = self.lbConnections.GetString(self.lbConnections.GetSelection())
		try:
			prtr = cxtext.split()[0]
		except:
			prtr = None
		if prtr is not None:
			cx = self.cm.connectionByPrinter(prtr)
			if cx is not None:
				if cx.isPrinting():
					if self.pgConnMgr.isAnyPrinting():
						dlg = wx.MessageDialog(self, "Are you sure you want to disconnect while printing is active",
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
			self.loadConnections(connections)
			if len(connections) == 0:
				self.bDisconnect.Enable(False)
				self.bReset.Enable(False)

	def doConnect(self, evt):
		port = 	self.lbPort.GetString(self.lbPort.GetSelection())
		baud = 	self.lbBaud.GetString(self.lbBaud.GetSelection())
		printer = 	self.lbPrinter.GetString(self.lbPrinter.GetSelection())
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
		
	def onClose(self):
		self.cm.disconnectAll()
		self.bDisconnect.Enable(False)

	def doReset(self, evt):
		cx = self.lbConnections.GetClientData(self.lbConnections.GetSelection())
		if cx.reprap is not None:
			dlg = wx.MessageDialog(self, "Are you sure you want to reset the printer",
								'Printer Reset', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_INFORMATION)
		
			rc = dlg.ShowModal()
			dlg.Destroy()

			if rc == wx.ID_YES:
				cx.reprap.reset()
				if cx.prtmon is not None:
					cx.prtmon.printerReset()


