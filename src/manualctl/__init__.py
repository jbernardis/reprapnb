import wx
import wx.lib.newevent
import os.path
from imagemap import ImageMap
from extruder import Extruder
from hotbed import HotBed
from gcodeentry import GCodeEntry
from moveaxis import MoveAxis
from hotend import HotEnd
from images import Images
from macros import MacroDialog
from settings import BUTTONDIM, BUTTONDIMWIDE

snHotEnds = ("HE0", "HE1", "HE2")
snBed = "Bed"

(HttpEvent, EVT_HTTP_MANCTL) = wx.lib.newevent.NewEvent()
HTTPMC_SETHEATER = 0
HTTPMC_PENDANT = 1

pendantHomes = {
	'home': "G28",
	'homex': "G28 X0",
	'homey': "G28 Y0",
	'homez': "G28 Z0",
	}

pendantMoves = {
	'movex1': "X0.1",
	'movex2': "X1",
	'movex3': "X10",
	'movex4': "X100",
	'movex-1': "X-0.1",
	'movex-2': "X-1",
	'movex-3': "X-10",
	'movex-4': "X-100",
	'movey1': "Y0.1",
	'movey2': "Y1",
	'movey3': "Y10",
	'movey4': "Y100",
	'movey-1': "Y-0.1",
	'movey-2': "Y-1",
	'movey-3': "Y-10",
	'movey-4': "Y-100",
	'movez1': "Z0.1",
	'movez2': "Z1",
	'movez3': "Z10",
	'movez-1': "Z-0.1",
	'movez-2': "Z-1",
	'movez-3': "Z-10",
	}


class ManualControl(wx.Panel): 
	def __init__(self, parent, app, prtname, reprap):
		self.model = None
		self.parent = parent
		self.app = app
		self.logger = self.app.logger
		self.appsettings = app.settings
		self.settings = app.settings.manualctl
		self.prtName = prtname
		self.speedcommand = self.app.settings.printersettings[prtname].speedcommand
		self.reprap = reprap
		self.firmware = None
		self.firmwareName = self.app.settings.printersettings[prtname].firmware
		self.reprap.setFirmware(self.firmwareName)
		self.prtmon = None
		self.currentTool = 0
		self.macroActive = False
		self.nextr = self.app.settings.printersettings[prtname].nextr
		self.standardBedTemp = [ 0, self.settings.standardbedlo, self.settings.standardbedhi]
		self.standardHeTemp = [0, self.settings.standardhelo, self.settings.standardhehi]
		
		self.zEngaged = False
		
		if self.speedcommand is not None:
			self.reprap.addToAllowedCommands(self.speedcommand)


		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(100, 100))
		self.SetBackgroundColour("white")

		self.images = Images(os.path.join(self.settings.cmdfolder, "images"))

		self.slFeedTimer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.onFeedSpeedChanged, self.slFeedTimer)
		self.slFanTimer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.onFanSpeedChanged, self.slFanTimer)

		self.Bind(EVT_HTTP_MANCTL, self.httpRequest)

		self.moveAxis = MoveAxis(self, self.app, self.reprap)				
		self.sizerMove = wx.BoxSizer(wx.VERTICAL)
		self.sizerMove.AddSpacer((20,20))
		self.sizerMove.Add(self.moveAxis)
		
		self.sizerExtrude = self.addExtruder(self.nextr)
		self.sizerBed = self.addBed()
		self.sizerSpeed = self.addSpeedControls()
		self.sizerGCode = self.addGCEntry()
		
		self.sizerMain = wx.BoxSizer(wx.HORIZONTAL)
		sizerLeft = wx.BoxSizer(wx.VERTICAL)
		sizerRight = wx.BoxSizer(wx.VERTICAL)
		
		sizerLeft.AddSpacer((20,20))
		sizerLeft.Add(self.sizerMove)
		sizerLeft.Add(self.sizerGCode)
		
		sizerRight.AddSpacer((20, 20))
		sizerRight.Add(self.sizerExtrude)
		sizerBedSpd = wx.BoxSizer(wx.HORIZONTAL)
		sizerBedSpd.Add(self.sizerBed)
		sizerBedSpd.AddSpacer((10, 10))
		sizerBedSpd.Add(self.sizerSpeed)
		sizerRight.Add(sizerBedSpd)
		
		sizerBtn = wx.BoxSizer(wx.HORIZONTAL)
		self.bZEngage = wx.BitmapButton(self, wx.ID_ANY, self.images.pngEngagez, size=BUTTONDIM)
		self.zEngaged = False
		self.setZEngage()
		sizerBtn.Add(self.bZEngage)
		self.Bind(wx.EVT_BUTTON, self.onEngageZ, self.bZEngage)
		sizerBtn.AddSpacer((20, 20))
		
		if self.firmwareName in [ "MARLIN" ]:
			from firmwaremarlin import FirmwareMarlin 
			self.firmware = FirmwareMarlin(self.app, self.reprap)
			self.bFirmware = wx.BitmapButton(self, wx.ID_ANY, self.images.pngFirmware, size=BUTTONDIM)
			self.bFirmware.SetToolTipString("Manage Firmware settings")
			sizerBtn.Add(self.bFirmware)
			self.Bind(wx.EVT_BUTTON, self.doFirmware, self.bFirmware)
			sizerBtn.AddSpacer((20, 20))
			
		self.bRunMacro = wx.BitmapButton(self, wx.ID_ANY, self.images.pngRunmacro, size=BUTTONDIM)
		self.bRunMacro.SetToolTipString("Run a macro")
		sizerBtn.Add(self.bRunMacro)
		self.Bind(wx.EVT_BUTTON, self.doRunMacro, self.bRunMacro)
		sizerRight.Add(sizerBtn)
		
		self.sizerMain.AddSpacer((20, 20))
		self.sizerMain.Add(sizerLeft)
		self.sizerMain.AddSpacer((20, 20))
		self.sizerMain.Add(sizerRight)
		self.sizerMain.AddSpacer((20, 20))

		self.SetSizer(self.sizerMain)
		self.Layout()
		self.Fit()
		
	def setZEngage(self):
		if self.zEngaged:
			self.bZEngage.SetToolTipString("Disengage Z Axis")
			self.bZEngage.SetBitmapLabel(self.images.pngDisengagez)
		else:
			self.bZEngage.SetToolTipString("Engage Z Axis")
			self.bZEngage.SetBitmapLabel(self.images.pngEngagez)
		
	def onEngageZ(self, evt):
		if not self.zEngaged:
			if self.reprap.isPrinting():
				dlg = wx.MessageDialog(self, "Disallowed while printing",
					'Printer Busy', wx.OK | wx.ICON_INFORMATION)
				dlg.ShowModal()
				self.Destroy()
			else:
				self.zEngaged = True
				self.zdir = True
				self.ztimer = wx.Timer(self)
				self.Bind(wx.EVT_TIMER, self.onZTimer, self.ztimer)  
				self.ztimer.Start(10000)
		else:
			self.zEngaged = False
			self.ztimer.Stop()
		self.setZEngage()
		
	def leavePage(self):
		if self.zEngaged:
			self.logger.LogMessage("Disengaging Z axis")
			self.disengageZ()
		
	def disengageZ(self):
		if self.zEngaged:
			self.ztimer.Stop()
		self.zEngaged = False
		self.setZEngage()
			
	def onZTimer(self, evt):
		self.reprap.send_now("G91")
		if self.zdir:
			self.reprap.send_now("G1 Z0.1 F300")
		else:
			self.reprap.send_now("G1 Z-0.1 F300")
		self.reprap.send_now("G90")
		self.zdir = not self.zdir
		
	def setPrtMon(self, pm):
		self.prtmon = pm

	def doFirmware(self, evt):
		self.firmware.show()

	def doRunMacro(self, evt):
		self.bRunMacro.Enable(False)
		self.dlgMacro = MacroDialog(self, self.reprap) 
		self.dlgMacro.CenterOnScreen()
		self.dlgMacro.Show(True)
		self.macroActive = True
		
	def onMacroExit(self, respawn=False):
		self.bRunMacro.Enable(True)
		self.dlgMacro.Destroy()
		self.macroActive = False
		if respawn:
			self.doRunMacro(None)
		
	def closeMacro(self):
		if self.macroActive:
			self.dlgMacro.Destroy()
			self.macroActive = False
			
		self.bRunMacro.Enable(True)
		
	def setBedTarget(self, temp):
		self.bedWin.setHeatTarget(temp)
		
	def setHETarget(self, tool, temp):
		self.heWin.setHeatTarget(tool, temp)
		
	def setBedTemp(self, temp):
		self.bedWin.setHeatTemp(temp)
		
	def setHETemp(self, tool, temp):
		self.heWin.setHeatTemp(tool, temp)
		
	def getBedGCode(self):
		if self.prtmon is None:
			return None
		return self.prtmon.getBedGCode()
	
	def getHEGCode(self, tool):
		if self.prtmon is None:
			return None
		return self.prtmon.getHEGCode(tool)
		
	def setActiveTool(self, tool):
		self.heWin.setActiveTool(tool)
		
	def addExtruder(self, nExtr):
		sizerExtrude = wx.BoxSizer(wx.VERTICAL)
		sizerExtrude.AddSpacer((10,10))

		self.font12bold = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		self.font16 = wx.Font(16, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

		t = wx.StaticText(self, wx.ID_ANY, "Hot End(s)", style=wx.ALIGN_LEFT, size=(200, -1))
		t.SetFont(self.font12bold)
		sizerExtrude.Add(t, flag=wx.LEFT)
		sizerExtrude.AddSpacer((10,10))
		
		self.heWin = HotEnd(self, self.app, self.reprap, name=("Hot End 0", "Hot End 1", "Hot End 2"), shortname=snHotEnds, 
					target=(185, 185, 185), trange=((20, 250), (20, 250), (20, 250)), nextr=nExtr)
		sizerExtrude.Add(self.heWin, flag=wx.LEFT | wx.EXPAND)
		sizerExtrude.AddSpacer((10,10))

		t = wx.StaticText(self, wx.ID_ANY, "Extruder", style=wx.ALIGN_LEFT, size=(200, -1))
		t.SetFont(self.font12bold)
		sizerExtrude.Add(t, flag=wx.LEFT)
		sizerExtrude.AddSpacer((10,10))
		
		self.extWin = Extruder(self, self.app, self.reprap)
		sizerExtrude.Add(self.extWin, flag=wx.LEFT)
		sizerExtrude.AddSpacer((10,10))
			
		return sizerExtrude
			
	def addBed(self):
		sizerBed = wx.BoxSizer(wx.VERTICAL)
		sizerBed.AddSpacer((10,10))

		t = wx.StaticText(self, wx.ID_ANY, "Heated Print Bed", style=wx.ALIGN_LEFT, size=(200, -1))
		t.SetFont(self.font12bold)
		sizerBed.Add(t, flag=wx.LEFT)
		sizerBed.AddSpacer((10,10))
		
		self.bedWin = HotBed(self, self.app, self.reprap, name="Heated Print Bed", shortname=snBed, 
					target=60, trange=[20, 150])
		sizerBed.Add(self.bedWin)
		sizerBed.AddSpacer((10,10))

		return sizerBed
	
	def addSpeedControls(self):
		sizerSpeed = wx.BoxSizer(wx.VERTICAL)
		sizerSpeed.AddSpacer((10, 10))

		if self.firmwareName in [ "MARLIN" ]:
			t = wx.StaticText(self, wx.ID_ANY, "Feed Speed", style=wx.ALIGN_CENTER, size=(-1, -1))
			t.SetFont(self.font12bold)
			sizerSpeed.Add(t, flag=wx.ALL)
	
			self.slFeedSpeed = wx.Slider(
				self, wx.ID_ANY, 100, 50, 200, size=(320, -1), 
				style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS 
				)
			self.slFeedSpeed.SetTickFreq(5, 1)
			self.slFeedSpeed.SetPageSize(1)
			self.slFeedSpeed.Bind(wx.EVT_SCROLL_CHANGED, self.onFeedSpeedChanged)
			self.slFeedSpeed.Bind(wx.EVT_MOUSEWHEEL, self.onFeedSpeedWheel)
			sizerSpeed.Add(self.slFeedSpeed)
			sizerSpeed.AddSpacer((10, 10))

		t = wx.StaticText(self, wx.ID_ANY, "Fan Speed", style=wx.ALIGN_CENTER, size=(-1, -1))
		t.SetFont(self.font12bold)
		sizerSpeed.Add(t, flag=wx.ALL)
		
		self.slFanSpeed = wx.Slider(
			self, wx.ID_ANY, 0, 0, 255, size=(320, -1), 
			style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS 
			)
		self.slFanSpeed.SetTickFreq(5, 1)
		self.slFanSpeed.SetPageSize(1)
		self.slFanSpeed.Bind(wx.EVT_SCROLL_CHANGED, self.onFanSpeedChanged)
		self.slFanSpeed.Bind(wx.EVT_MOUSEWHEEL, self.onFanSpeedWheel)
		sizerSpeed.Add(self.slFanSpeed)
	
		if self.speedcommand is not None:			
			self.bSpeedQuery = wx.BitmapButton(self, wx.ID_ANY, self.images.pngSpeedquery, size=BUTTONDIMWIDE)
			self.bSpeedQuery.SetToolTipString("Retrieve current feed and fan speeds from printer")
			sizerSpeed.Add(self.bSpeedQuery, flag=wx.ALIGN_CENTER | wx.ALL, border=10)
			self.Bind(wx.EVT_BUTTON, self.doSpeedQuery, self.bSpeedQuery)
		
		return sizerSpeed
	
	def doSpeedQuery(self, evt):
		self.reprap.send_now(self.speedcommand)
		
	def updateSpeeds(self, fan, feed, flow):
		if feed is not None:
			self.slFeedSpeed.SetValue(feed)
		if fan is not None:
			self.slFanSpeed.SetValue(fan)
	
	def onFeedSpeedChanged(self, evt):
		self.setFeedSpeed(self.slFeedSpeed.GetValue())
	
	def onFeedSpeedWheel(self, evt):
		self.slFeedTimer.Start(500, True)
		l = self.slFeedSpeed.GetValue()
		if evt.GetWheelRotation() < 0:
			l -= 1
		else:
			l += 1
		if l >= 50 and l <= 200:
			self.slFeedSpeed.SetValue(l)
			
	def setFeedSpeed(self, spd):
		self.reprap.send_now("M220 S%d" % spd)
		
	def onFanSpeedChanged(self, evt):
		self.setFanSpeed(self.slFanSpeed.GetValue())
	
	def onFanSpeedWheel(self, evt):
		self.slFanTimer.Start(500, True)
		l = self.slFanSpeed.GetValue()
		if evt.GetWheelRotation() < 0:
			l -= 1
		else:
			l += 1
		if l >= 0 and l <= 255:
			self.slFanSpeed.SetValue(l)
		
	def setFanSpeed(self, spd):
		self.reprap.send_now("M106 S%d" % spd)

	def addGCEntry(self):
		sizerGCode = wx.BoxSizer(wx.VERTICAL)
		sizerGCode.AddSpacer((20,20))
		
		t = wx.StaticText(self, wx.ID_ANY, "G Code", style=wx.ALIGN_LEFT, size=(200, -1))
		t.SetFont(self.font12bold)
		self.GCELabel = t
		sizerGCode.Add(t, flag=wx.LEFT)
		
		sizerGCode.AddSpacer((10,10))

		self.GCEntry = GCodeEntry(self, self.app)	
		sizerGCode.Add(self.GCEntry)
		
		return sizerGCode

	def onClose(self, evt):
		return True
	
	def setHeaters(self, q):
		rv = {}
		errors = False
		count = 0
		for k in q.keys():
			if k.lower() == snBed.lower():
				try:
					t = int(q[k][0])
					evt = HttpEvent(cmd=HTTPMC_SETHEATER, heater=snBed, temp=t)
					wx.PostEvent(self, evt)
					rv[k] = str(t)
					count += 1
				except:
					rv[k] = "invalid temperature value"
					errors = True
			else:
				found = False
				for t in range(self.nextr):
					if k.lower() == snHotEnds[t].lower():
						found = True
						try:
							tmp = int(q[k][0])
							evt = HttpEvent(cmd=HTTPMC_SETHEATER, heater=snHotEnds[t], temp=tmp)
							wx.PostEvent(self, evt)
							rv[k] = str(tmp)
							count += 1
						except:
							rv[k] = "invalid temperature value"
							errors = True
						break
					
				if not found:
					rv[k] = ("Unknown heater: " + k)
					errors = True
							
		if count == 0 and not errors:
			evt = HttpEvent(cmd=HTTPMC_SETHEATER, heater=snBed, temp=0)
			wx.PostEvent(self, evt)

			rv[snBed] = 0
			for i in range(self.nextr):
				evt = HttpEvent(cmd=HTTPMC_SETHEATER, heater=snHotEnds[i], temp=0)
				wx.PostEvent(self, evt)
				rv[snHotEnds[i]] = 0
			rv['result'] = "Success - all heaters off posted"

		elif errors:
			rv['result'] = ("Failed - errors encountered, %d temp changes posted" % count)
		
		else:
			rv['result'] = ("Success - %d temp changes posted" % count)

		return errors, rv
	
	def httpRequest(self, evt):
		if evt.cmd == HTTPMC_SETHEATER:
			htr = evt.heater
			temp = evt.temp
			if htr == snBed:
				self.bedWin.heaterTemp(temp)
			else:
				for i in range(self.nextr):
					if htr == snHotEnds[i]:
						self.heWin.heaterTemp(i, temp)
		elif evt.cmd == HTTPMC_PENDANT:
			self.executePendantCommand(evt.button)

	def executePendantCommand(self, cmd):
		c = cmd.lower()
		if c in pendantMoves.keys():
			axis = pendantMoves[c]
			if axis.startswith("Z"):
				speed = "F%s" % str(self.settings.zspeed)
			else:
				speed = "F%s" % str(self.settings.xyspeed)
				
			self.reprap.send_now("G91")
			self.reprap.send_now("G1 %s %s" % (axis, speed))
			self.reprap.send_now("G90")
				
		elif c in pendantHomes.keys():
			self.reprap.send_now(pendantHomes[c])
			
		elif c == "extrude":
			self.extWin.doExtrude()
			
		elif c == "retract":
			self.extWin.doRetract()
			
		elif c.startswith("temp"):
			target = c[4:7]
			try:
				temp = int(c[7])
				if temp < 0 or temp > 2:
					temp = None
			except:
				temp = None

			if temp is not None:				
				if target == "bed":
					self.bedWin.heaterTemp(self.standardBedTemp[temp])
				elif target.startswith("he"):
					try:
						tool = int(target[2])
						if tool < 0 or tool >= self.nextr:
							tool = None
					except:
						tool = None
					if tool is not None:
						self.heWin.heaterTemp(tool, self.standardHeTemp[temp])
					else:
						self.logger.LogMessage("Pendant temp command had invalid tool number: " + cmd)
				else:
					self.logger.LogMessage("Pendant temp command had invalid target: " + cmd)
			else:
				self.logger.LogMessage("Pendant temp command had invalid temp index: " + cmd)
			
		else:
			self.logger.LogMessage("Unknown pendant command: %s" % cmd)

			
	def pendantCommand(self, cmd):
		evt = HttpEvent(cmd=HTTPMC_PENDANT, button=cmd)
		wx.PostEvent(self, evt)
		return {'result' : "Pendant command posted"}

				
