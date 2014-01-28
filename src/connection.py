import wx
import glob

from settings import BUTTONDIM, RECEIVED_MSG 

baudChoices = ["2400", "9600", "19200", "38400", "57600", "115200", "250000"]

from reprap import RepRap, RepRapParser

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
		self.reprap = None

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
		
		"""scan for available ports. return a list of device names."""
		self.portList = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*') + \
					glob.glob("/dev/tty.*")+glob.glob("/dev/cu.*")+glob.glob("/dev/rfcomm*")
					
		self.printerList = self.settings.printers[:]
		self.activePorts = []
		self.activePrinters = []
		self.manageDlg = None
		
	def manageDlgClose(self):
		self.manageDlg = None
		
	def getLists(self, refreshPorts=False):
		if refreshPorts:
			pl = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*') + \
					glob.glob("/dev/tty.*")+glob.glob("/dev/cu.*")+glob.glob("/dev/rfcomm*")
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

	def connect(self, printer, port, baud):
		cx = Connection(self.app, printer, port, baud)
		self.connections.append(cx)
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
		
		con.close()
		self.printerList.append(printer)
		self.printerList.sort()
		self.portList.append(port)
		self.portList.sort()
		self.app.delPages(printer)
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
		
		con.close()
		self.printerList.append(printer)
		self.printerList.sort()
		self.portList.append(port)
		self.portList.sort()
		self.app.delPages(printer)
		return True
	
	def disconnectAll(self):
		for c in self.connections:
			c.close()
		self.connections = []
		for p in self.activePrinters:
			self.app.delPages(p)
		self.printerList.extend(self.activePrinters)
		self.activePrinters = []
		self.portList.extend(self.activePorts)
		self.activePorts = []
	
	def disconnectByRepRap(self, reprap):
		port = reprap.getPort()
		return self.disconnectByPort(port)

BSIZE = (140, 40)	
class ConnectionManagerPanel(wx.Panel):
	def __init__(self, parent, app):
		self.parent = parent
		self.app = app
		self.settings = self.app.settings
		self.logger = self.app.logger
		self.cm = ConnectionManager(self.app)
		
		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(400, 250))
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
		
		szRow = wx.BoxSizer(wx.HORIZONTAL)
		szRow.AddSpacer((20, 20))

		self.bPort = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngPorts, size=BUTTONDIM)
		self.bPort.SetToolTipString("Refresh list of available ports")
		szRow.Add(self.bPort)
		self.Bind(wx.EVT_BUTTON, self.doPort, self.bPort)
		
		sz.AddSpacer((20, 20))

		self.bConnect = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngConnect, size=BUTTONDIM)
		self.bConnect.SetToolTipString("Connect to the printer")
		self.Bind(wx.EVT_BUTTON, self.doConnect, self.bConnect)
		szRow.Add(self.bConnect)
		self.bConnect.Enable(len(ports) >= 1)

		szRow.AddSpacer((20, 20))
		szConnect.Add(szRow)

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
		szBtns.AddSpacer((10, 10))

		self.bDisconnect = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngDisconnect, size=BUTTONDIM)
		self.bDisconnect.SetToolTipString("Disconnect the printer")
		szBtns.Add(self.bDisconnect, flag=wx.ALL, border=10)
		self.bDisconnect.Enable(False)
		self.Bind(wx.EVT_BUTTON, self.doDisconnect, self.bDisconnect)
		
		szBtns.AddSpacer((20, 20))

		self.bReset = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngReset, size=BUTTONDIM)
		self.bReset.SetToolTipString("Reset the printer")
		szBtns.Add(self.bReset, flag=wx.ALL, border=10)
		self.Bind(wx.EVT_BUTTON, self.doReset, self.bReset)
		self.bReset.Enable(False)
		
		szDisconnect.AddSpacer((10, 10))
		szDisconnect.Add(szBtns)

		if len(ports) < 1:
			self.bConnect.Enable(False)
			
		szsbConnect.Add(szConnect)
		szsbDisconnect.Add(szDisconnect)
		self.sizer.AddSpacer((20, 20))

		sz = wx.BoxSizer(wx.HORIZONTAL)
		sz.AddSpacer((20, 20))
		sz.Add(szsbConnect)
		sz.AddSpacer((20, 20))
		self.sizer.Add(sz)
		self.sizer.AddSpacer((20, 20))
		sz = wx.BoxSizer(wx.HORIZONTAL)
		sz.AddSpacer((20, 20))
		sz.Add(szsbDisconnect)
		sz.AddSpacer((20, 20))
		self.sizer.Add(sz)
		self.sizer.AddSpacer((20, 20))
		self.SetSizer(self.sizer)
		
	def loadConnections(self, cxlist):
		self.lbConnections.Clear()
		for cx in cxlist:
			self.lbConnections.Append("%s on %s" % (cx.printer, cx.port), cx)
		if len(cxlist) > 0:
			self.lbConnections.SetSelection(0)
	
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
		ports = self.cm.getLists(True)[1]
		self.lbPort.SetItems(ports)
		if len(ports) >= 1:
			self.bConnect.Enable(True)
			self.lbPort.SetSelection(0)
		else:
			self.bConnect.Enable(False)
			
	def getStatus(self):
		return self.cm.getStatus()
			
	def getTemps(self):
		return self.cm.getTemps()
	
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


