import ConfigParser
import os

INIFILE = "reprap.ini"

SAVE_SETTINGS_FILE = False

BUTTONDIM = (48, 48)
BUTTONDIMLG = (128, 64)
BUTTONDIMWIDE = (96, 48)

MAX_EXTRUDERS = 2
MAINTIMER = 1000

FPSTATUS_IDLE = 0
FPSTATUS_READY = 1
FPSTATUS_READY_DIRTY = 2
FPSTATUS_BUSY = 3

BATCHSL_RUNNING = 1
BATCHSL_IDLE = 0

PLSTATUS_EMPTY = 0
PLSTATUS_LOADED_CLEAN = 1
PLSTATUS_LOADED_DIRTY = 2

PMSTATUS_NOT_READY = 0
PMSTATUS_READY = 1
PMSTATUS_PRINTING = 2
PMSTATUS_PAUSED = 3

SD_CARD_OK = 0
SD_CARD_FAIL = 1
SD_CARD_LIST = 2

SDSTATUS_IDLE = 0
SDSTATUS_CHECKING = 1
SDSTATUS_LISTING = 2

SD_PRINT_COMPLETE = 1
SD_PRINT_POSITION = 2
PRINT_COMPLETE = 10
PRINT_STOPPED = 11
PRINT_AUTOSTOPPED = 12
PRINT_STARTED = 13
PRINT_RESUMED = 14
PRINT_MESSAGE = 15
QUEUE_DRAINED = 16
RECEIVED_MSG = 17
PRINT_ERROR = 99

CMD_GCODE = 1
CMD_STARTPRINT = 2
CMD_STOPPRINT = 3
CMD_DRAINQUEUE = 4
CMD_ENDOFPRINT = 5
CMD_RESUMEPRINT = 6

TEMPFILELABEL = "<temporary>"

from slic3r import Slic3r
from skeinforge import Skeinforge
from cura import Cura

def parseBoolean(val, defaultVal):
	lval = val.lower();
	
	if lval == 'true' or lval == 't' or lval == 'yes' or lval == 'y':
		return True
	
	if lval == 'false' or lval == 'f' or lval == 'no' or lval == 'n':
		return False
	
	return defaultVal

class SlicerSettings:
	def __init__(self, app, name):
		self.app = app
		self.name = name
		self.settings = {}
		self.modified = False
		self.type = None
		if self.name == 'slic3r':
			self.type = Slic3r(self.app, self)
		elif self.name == 'skeinforge':
			self.type = Skeinforge(self.app, self)
		elif self.name == 'cura':
			self.type = Cura(self.app, self)
		else:
			self.type = None
			print "Unknown slicer type: %s" % self.name
	
	def setModified(self, flag=True):
		self.modified = flag
		
	def checkModified(self):
		return self.modified
	
	def initialize(self):
		if self.type is not None:
			self.type.initialize(True)
			
	def getSettingsKeys(self):
		if self.type is None:
			return [], []
		
		return self.type.getSettingsKeys()
	
	def buildSliceOutputFile(self, fn):
		if self.type is None:
			return None
		
		return self.type.buildSliceOutputFile(fn)
	
	def setLogger(self, logger):
		if self.type is None:
			return None
		
		return self.type.setLogger(logger)
	
	def setOverrides(self, overrides):
		if self.type is None:
			return None
		
		return self.type.setOverrides(overrides)
	
	def buildSliceCommand(self):
		if self.type is None:
			return None
		
		return self.type.buildSliceCommand()
	
	def sliceComplete(self):
		if self.type is not None:
			self.type.sliceComplete()
			
	def fileTypes(self):
		if self.type is None:
			return ""

		return self.type.fileTypes()
			
	def configSlicer(self):
		if self.type is None:
			return False

		return self.type.configSlicer()
		
	def getConfigString(self):
		if self.type is None:
			return None
		
		return self.type.getConfigString()
	
	def getSlicerName(self):
		return self.name
		
	def getDimensionInfo(self):
		if self.type is None:
			return None
		
		return self.type.getDimensionInfo()
	
	def getOverrideHelpText(self):
		if self.type is None:
			return None
		
		return self.type.getOverrideHelpText()
	
class PrinterSettings:
	def __init__(self, name):
		self.name = name
		self.nextr = 1
		self.buildarea = [200, 200]
		self.speedcommand = None
		self.firmware = "MARLIN"

class Settings:
	def __init__(self, app, folder):
		self.app = app
		self.cmdfolder = folder
		self.inifile = os.path.join(folder, INIFILE)
		self.printers=[]
		self.lastlogdirectory = folder
		self.usepopup = True
		self.port = 8989
		self.maxloglines = 5000
		self.buildarea = [200, 200]
		self.macroList = {}
		self.macroOrder = []
		self.tools = {}
		self.toolOrder = []
		self.historysize = 100
		self.slicehistoryfile = os.path.join(folder, "slice.history")
		self.printhistoryfile = os.path.join(folder, "print.history")
		self.webbase = "/var/www/html/images"
		self.lastmacrodirectory = os.path.join(folder, "macros")
		self.shares = {}
		
		self.cfg = ConfigParser.ConfigParser()
		self.cfg.optionxform = str
		if not self.cfg.read(self.inifile):
			self.showWarning("Settings file %s does not exist.  Using default values" % INIFILE)
			
			self.modified = True
			
			self.fileprep = SettingsFilePrep(self, self.app, None, folder, "fileprep")
			self.plater = SettingsPlater(self, self.app, None, folder, "plater")
			self.manualctl = SettingsManualCtl(self, self.app, None, folder, "manualctl")
			self.printmon = SettingsPrintMon(self, self.app, None, folder, "printmon")
			return

		self.section = "global"	
		self.modified = False	
		if self.cfg.has_section(self.section):
			for opt, value in self.cfg.items(self.section):
				if opt == 'printers':
					s = value.split(',')
					self.printers = [x.strip() for x in s]
				elif opt == 'lastlogdirectory':
					self.lastlogdirectory = value
				elif opt == 'lastmacrodirectory':
					self.lastmacrodirectory = value
				elif opt == 'slicehistoryfile':
					self.slicehistoryfile = value
				elif opt == 'printhistoryfile':
					self.printhistoryfile = value
				elif opt == 'webbase':
					self.webbase = value
				elif opt == 'usepopuplog':
					self.usepopup = parseBoolean(value, True)
				elif opt == 'buildarea':
					try:
						exec("s=%s" % value)
						self.buildarea = s
					except:
						print "invalid value in ini file for buildarea"
						self.buildarea = (200, 200)
				elif opt == 'maxloglines':
					if value.lower() == "none":
						self.maxloglines = None
					else:
						try:
							self.maxloglines = int(value)
						except:
							self.showWarning("Invalid value for maxloglines")
							self.maxloglines = 5000
							self.modified = True
				elif opt == 'historysize':
					try:
						self.historysize = int(value)
					except:
						self.showWarning("Invalid value for history size")
						self.historysize = 100
						self.modified = True
						
				elif opt == 'port':
					try:
						self.port = int(value)
					except:
						self.port = 8989
						self.showWarning("Invalid value (%s) for port - using %d" % (value, self.port))
				else:
					self.showWarning("Unknown %s option: %s - ignoring" % (self.section, opt))
		else:
			self.showWarning("Missing %s section - assuming defaults" % self.section)
				
		self.printersettings = {}
		for printer in self.printers:
			pt = PrinterSettings(printer)
			sc = "printer." + printer
			self.printersettings[printer] = pt
			if self.cfg.has_section(sc):
				for opt, value in self.cfg.items(sc):
					if opt == "nextruders":
						try:
							pt.nextr = int(value)
						except:
							self.showWarning("Illegal number of extruders for %s - using 1" % sc)
							pt.nextr = 1
							
					elif opt == 'firmware':
						pt.firmware = value
							
					elif opt == 'speedcommand':
						if value.lower() == "none":
							pt.speedcommand = None
						else:
							pt.speedcommand = value

					elif opt == 'buildarea':
						try:
							exec("s=%s" % value)
							pt.buildarea = s
						except:
							print "invalid value in ini file for buildarea"
							pt.buildarea = (200, 200)

					else:
						self.showWarning("Unknown %s option: %s - ignoring" % (sc, opt))
			else:
				self.showError("No settings for printer %s" % printer)
			
		section = "macros"	
		if self.cfg.has_section(section):
			i = 0
			while True:
				i += 1
				key = "macro." + str(i)
				if not self.cfg.has_option(section, key): break
				
				try:
					mkey, mfile = self.cfg.get(section, key).split(',', 1)
				except:
					self.showError("Unable to parse config for %s" % key)
					break
				
				mkey = mkey.strip()
				self.macroOrder.append(mkey)
				self.macroList[mkey] = mfile.strip()
				
		section = "tools"	
		group = ""
		if self.cfg.has_section(section):
			for opt, value in self.cfg.items(section):
				p = value.split(",")
				if len(p) == 3:
					group = p[0]
					self.tools[opt] = p
					self.toolOrder.append(opt)
				elif len(p) == 2:
					self.tools[opt] = [group] + p
					self.toolOrder.append(opt)
				else:
					self.showError("Invalid number of parameters for tool %s - skipping" % opt)
					
		section = "shares"
		self.shares = {}
		if self.cfg.has_section(section):
			for opt, value in self.cfg.items(section):
				self.shares[opt] = value

		self.fileprep = SettingsFilePrep(self, self.app, self.cfg, folder, "fileprep")
		self.plater = SettingsPlater(self, self.app, self.cfg, folder, "plater")
		self.manualctl = SettingsManualCtl(self, self.app, self.cfg, folder, "manualctl")
		self.printmon = SettingsPrintMon(self, self.app, self.cfg, folder, "printmon")

	def showWarning(self, msg):
		print "Settings WARNING: " + msg
		
	def showError(self, msg):
		print "Settings ERROR: " + msg
	
	def setModified(self):
		self.modified = True
		
	def checkModified(self):
		if self.modified: return True
			
		if self.fileprep.checkModified(): return True
		if self.plater.checkModified(): return True
		if self.manualctl.checkModified(): return True
		if self.printmon.checkModified(): return True
		
		return False
		
	def cleanUp(self):
		if self.checkModified():
			try:
				self.cfg.add_section(self.section)
			except ConfigParser.DuplicateSectionError:
				pass
			
			self.cfg.set(self.section, "printers", ",".join(self.printers))
			self.cfg.set(self.section, "lastlogdirectory", str(self.lastlogdirectory))
			self.cfg.set(self.section, "lastmacrodirectory", str(self.lastmacrodirectory))
			self.cfg.set(self.section, "slicehistoryfile", str(self.slicehistoryfile))
			self.cfg.set(self.section, "printhistoryfile", str(self.printhistoryfile))
			self.cfg.set(self.section, "webbase", str(self.webbase))
			self.cfg.set(self.section, "port", str(self.port))
			self.cfg.set(self.section, "maxloglines", str(self.maxloglines))
			self.cfg.set(self.section, "historysize", str(self.historysize))
			self.cfg.set(self.section, "usepopuplog", str(self.usepopup))
			self.cfg.set(self.section, "buildarea", str(self.buildarea))
							
			for p in self.printersettings.keys():
				sc = "printer." + p
				pt = self.printersettings[p]
				try:
					self.cfg.add_section(sc)
				except ConfigParser.DuplicateSectionError:
					pass
				self.cfg.set(sc, "nextruders", str(pt.nextr))
				self.cfg.set(sc, "speedcommand", str(pt.speedcommand))
				self.cfg.set(sc, "buildarea", str(pt.buildarea))
				self.cfg.set(sc, "firmware", str(pt.firmware))

			section = "macros"
			try:
				self.cfg.add_section(section)
			except ConfigParser.DuplicateSectionError:
				pass
				
			for m in range(len(self.macroOrder)):
				opt = "macro.%d" % (m+1)
				val = self.macroOrder[m] + "," + self.macroList[self.macroOrder[m]]
				self.cfg.set(section, opt, val)
				
			section = "shares"
			try:
				self.cfg.add_section(section)
			except ConfigParser.DuplicateSectionError:
				pass
				
			for m in self.shares.keys():
				self.cfg.set(section, m, self.shares[m])
			
			self.fileprep.cleanUp()
			self.plater.cleanUp()
			self.manualctl.cleanUp()
			self.printmon.cleanUp()

			try:		
				cfp = open(self.inifile, 'wb')
			except:
				print "Unable to open settings file %s for writing" % self.inifile
				return
			self.cfg.write(cfp)
			cfp.close()

class SettingsFilePrep:
	def __init__(self, parent, app, cfg, folder, section):
		self.parent = parent
		self.app = app
		self.cmdfolder = os.path.join(folder, section)

		self.slicer = "slic3r"
		self.slicers = ["slic3r"]
		self.slicersettings = []
		self.gcodescale = 3
		self.laststldirectory="."
		self.lastgcdirectory="."
		self.showprevious = True
		self.showmoves = True
		self.usebuffereddc = True
		self.acceleration = 1500
		self.drawstlgrid = True
		self.toolpathsonly = False
		self.showhistbasename = True
		self.batchaddgcode = True
		self.stlqueue = []
		self.gcodequeue = []
		self.showgcbasename = False
		self.showstlbasename = False
		
		if cfg is None:
			self.modified = True
			return

		self.cfg = cfg		
		self.section = section
		self.modified = False	
		if cfg.has_section(section):
			for opt, value in cfg.items(section):
				if opt == 'gcodescale':
					try:
						self.gcodescale = int(value)
					except:
						self.parent.showWarning("Non-integer value in ini file for gcodescale")
						self.gcodescale = 3
						
				elif opt == 'slicer':
					self.slicer = value

				elif opt == 'slicers':
					s = value.split(',')
					self.slicers = [x.strip() for x in s]

				elif opt == 'showhistbasename':
					self.showhistbasename = parseBoolean(value, True)

				elif opt == 'acceleration':
					try:
						self.acceleration = float(value)
					except:
						self.parent.showWarning("Non-valid value in ini file for acceleration")
						self.acceleration = 1500
			
				elif opt == 'laststldirectory':
					self.laststldirectory = value
						
				elif opt == 'lastgcdirectory':
					self.lastgcdirectory = value
						
				elif opt == 'toolpathsonly':
					self.toolpathsonly = parseBoolean(value, False)
						
				elif opt == 'showprevious':
					self.showprevious = parseBoolean(value, True)
						
				elif opt == 'drawstlgrid':
					self.drawstlgrid = parseBoolean(value, True)
						
				elif opt == 'showmoves':
					self.showmoves = parseBoolean(value, True)
						
				elif opt == 'usebuffereddc':
					self.usebuffereddc = parseBoolean(value, False)
						
				elif opt == 'batchaddgcode':
					self.batchaddgcode = parseBoolean(value, False)
						
				elif opt == 'showstlbasename':
					self.showstlbasename = parseBoolean(value, False)
						
				elif opt == 'showgcbasename':
					self.showgcbasename = parseBoolean(value, False)
						
				elif opt == 'stlqueue':
					if value == '':
						self.stlqueue = []
					else:
						s = value.split(',')
						self.stlqueue = [x.strip() for x in s]
						
				elif opt == 'gcodequeue':
					if value == '':
						self.gcodequeue = []
					else:
						s = value.split(',')
						self.gcodequeue = [x.strip() for x in s]

				else:
					self.parent.showWarning("Unknown %s option: %s - ignoring" % (section, opt))
		else:
			self.parent.showWarning("Missing %s section - assuming defaults" % section)
			self.modified = True
		
		self.slicersettings = []
		for slicer in self.slicers:
			err = False	
			st = SlicerSettings(self.app, slicer)
			slicerKeys, slicerArrayKeys = st.getSettingsKeys()
			sc = "slicer." + slicer
			self.slicersettings.append(st)
			if self.cfg.has_section(sc):
				for opt, value in self.cfg.items(sc):
					if opt in slicerArrayKeys:
						st.settings[opt] = value.split(',')
					elif opt in slicerKeys:
						st.settings[opt] = value
					else:
						self.showWarning("Unknown %s option: %s - ignoring" % (sc, opt))
			else:
				self.showError("No settings for slicer %s" % slicer)
				err = True

			for k in slicerKeys:				
				if k not in st.settings.keys():
					err = True
					self.showError("Settings for slicer %s missing %s" % (slicer, k))
				
			if not err:
				st.initialize()

	def getSlicerSettings(self, slicer):
		for i in range(len(self.slicers)):
			if self.slicers[i] == slicer:
				if i >= len(self.slicersettings):
					return None
				return self.slicersettings[i]
		return None

	def setModified(self):
		self.modified = True
		
	def setLoggers(self, logger):
		for s in self.slicersettings:
			s.setLogger(logger)
		
	def checkModified(self):
		for s in self.slicersettings:
			if s.checkModified(): return True
			
		return self.modified
		
	def cleanUp(self):
		if self.modified:
			try:
				self.cfg.add_section(self.section)
			except ConfigParser.DuplicateSectionError:
				pass
			
			self.cfg.set(self.section, "slicer", str(self.slicer))
			self.cfg.set(self.section, "slicers", ",".join(self.slicers))
			self.cfg.set(self.section, "gcodescale", str(self.gcodescale))
			self.cfg.set(self.section, "laststldirectory", str(self.laststldirectory))
			self.cfg.set(self.section, "lastgcdirectory", str(self.lastgcdirectory))
			self.cfg.set(self.section, "showprevious", str(self.showprevious))
			self.cfg.set(self.section, "drawstlgrid", str(self.drawstlgrid))
			self.cfg.set(self.section, "showmoves", str(self.showmoves))
			self.cfg.set(self.section, "usebuffereddc", str(self.usebuffereddc))
			self.cfg.set(self.section, "acceleration", str(self.acceleration))
			self.cfg.set(self.section, "toolpathsonly", str(self.toolpathsonly))
			self.cfg.set(self.section, "batchaddgcode", str(self.batchaddgcode))
			self.cfg.set(self.section, "showhistbasename", str(self.showhistbasename))
			self.cfg.set(self.section, "stlqueue", ",".join(self.stlqueue))
			self.cfg.set(self.section, "gcodequeue", ",".join(self.gcodequeue))
			self.cfg.set(self.section, "showstlbasename", str(self.showstlbasename))
			self.cfg.set(self.section, "showgcbasename", str(self.showgcbasename))
			
			for i in range(len(self.slicers)):
				s = self.slicers[i]
				sc = "slicer." + s
				try:
					self.cfg.add_section(sc)
				except ConfigParser.DuplicateSectionError:
					pass

				sl = self.slicersettings[i]	
				if sl.checkModified():			
					slicerKeys, slicerArrayKeys = sl.getSettingsKeys()
					for k in sl.settings.keys():
						if k in slicerArrayKeys:
							self.cfg.set(sc, k, ",".join(sl.settings[k]))
						elif k in slicerKeys:
							self.cfg.set(sc, k, sl.settings[k])
	
class SettingsPlater:
	def __init__(self, parent, app, cfg, folder, section):
		self.parent = parent
		self.app = app
		self.cmdfolder = os.path.join(folder, section)

		self.stlscale = 2
		self.laststldirectory="."
		self.autoarrange = False
		self.drawstlgrid = True
		
		if cfg is None:
			self.modified = True
			return

		self.cfg = cfg
		self.modified = False
		self.section = section	
		if cfg.has_section(section):
			for opt, value in cfg.items(section):
				if opt == 'stlscale':
					try:
						self.stlscale = int(value)
					except:
						self.parent.showWarning("Non-integer value in ini file for stlscale")
						self.stlscale = 2
			
				elif opt == 'laststldirectory':
					self.laststldirectory = value
						
				elif opt == 'autoarrange':
					self.autoarrange = parseBoolean(value, False)
						
				elif opt == 'drawstlgrid':
					self.drawstlgrid = parseBoolean(value, True)
					
				else:
					self.parent.showWarning("Unknown %s option: %s - ignoring" % (section,  opt))
		else:
			self.parent.showWarning("Missing %s section - assuming defaults" % section)
			self.modified = True

	def setModified(self):
		self.modified = True

	def checkModified(self):
		return self.modified
			
	def cleanUp(self):
		if self.modified:
			try:
				self.cfg.add_section(self.section)
			except ConfigParser.DuplicateSectionError:
				pass
			
			self.cfg.set(self.section, "stlscale", str(self.stlscale))
			self.cfg.set(self.section, "laststldirectory", str(self.laststldirectory))
			self.cfg.set(self.section, "autoarrange", str(self.autoarrange))
			self.cfg.set(self.section, "drawstlgrid", str(self.drawstlgrid))
	
class SettingsManualCtl:
	def __init__(self, parent, app, cfg, folder, section):
		self.parent = parent
		self.app = app
		self.cmdfolder = os.path.join(folder, section)
		
		self.xyspeed = 2000
		self.zspeed = 300
		self.espeed = 300
		self.edistance = 5

		if cfg is None:
			self.modified = True
			return
		
		self.cfg = cfg
		self.modified = False
		self.section = section	
		if cfg.has_section(section):
			for opt, value in cfg.items(section):
			
				if opt == 'xyspeed':
					try:
						self.xyspeed = int(value)
					except:
						self.parent.showWarning("Non-integer value in ini file for xyspeed")
						self.xyspeed = 2000
				elif opt == 'zspeed':
					try:
						self.zspeed = int(value)
					except:
						self.parent.showWarning("Non-integer value in ini file for zspeed")
						self.zspeed = 300
				elif opt == 'espeed':
					try:
						self.espeed = int(value)
					except:
						self.parent.showWarning("Non-integer value in ini file for espeed")
						self.zspeed = 300
				elif opt == 'edistance':
					try:
						self.edistance = int(value)
					except:
						self.parent.showWarning("Non-integer value in ini file for edistance")
						self.edistance = 5
				else:
					self.parent.showWarning("Unknown %s option: %s - ignoring" % (section,  opt))
		else:
			self.parent.showWarning("Missing %s section - assuming defaults" % section)
			self.modified = True

	def setModified(self):
		self.modified = True

	def checkModified(self):
		return self.modified
			
	def cleanUp(self):
		if self.modified:
			try:
				self.cfg.add_section(self.section)
			except ConfigParser.DuplicateSectionError:
				pass
			
			self.cfg.set(self.section, "xyspeed", str(self.xyspeed))
			self.cfg.set(self.section, "zspeed", str(self.zspeed))
			self.cfg.set(self.section, "espeed", str(self.espeed))
			self.cfg.set(self.section, "edistance", str(self.edistance))
	
class SettingsPrintMon:
	def __init__(self, parent, app, cfg, folder, section):
		self.parent = parent
		self.app = app
		self.cmdfolder = os.path.join(folder, section)
		
		self.gcodescale = 3
		self.showprevious = True
		self.showmoves = True
		self.usebuffereddc = True
		self.toolpathsonly = False
		
		if cfg is None:
			self.modified = True
			return
		
		self.cfg = cfg
		self.modified = False
		self.section = section	
		if cfg.has_section(section):
			for opt, value in cfg.items(section):
				if opt == 'gcodescale':
					try:
						self.gcodescale = int(value)
					except:
						self.parent.showWarning("Non-integer value in ini file for gcodescale")
						self.gcodescale = 3
				elif opt == 'showprevious':
					self.showprevious = parseBoolean(value, True)
						
				elif opt == 'showmoves':
					self.showmoves = parseBoolean(value, True)
						
				elif opt == 'usebuffereddc':
					self.usebuffereddc = parseBoolean(value, False)
						
				elif opt == 'toolpathsonly':
					self.toolpathsonly = parseBoolean(value, False)
					
				else:
					self.parent.showWarning("Unknown %s option: %s - ignoring" % (section,  opt))
		else:
			self.parent.showWarning("Missing %s section - assuming defaults" % section)
			self.modified = True

	def setModified(self):
		self.modified = True

	def checkModified(self):
		return self.modified
			
	def cleanUp(self):
		if self.modified:
			try:
				self.cfg.add_section(self.section)
			except ConfigParser.DuplicateSectionError:
				pass
			
			self.cfg.set(self.section, "gcodescale", str(self.gcodescale))
			self.cfg.set(self.section, "showprevious", str(self.showprevious))
			self.cfg.set(self.section, "showmoves", str(self.showmoves))
			self.cfg.set(self.section, "usebuffereddc", str(self.usebuffereddc))
			self.cfg.set(self.section, "toolpathsonly", str(self.toolpathsonly))
