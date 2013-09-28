'''
Created on Aug 21, 2012

@author: jbernard
'''
import ConfigParser
import os

from slic3r import Slic3r
from skeinforge import Skeinforge

INIFILE = "rrh.ini"

TEMPFILELABEL = "<temporary>"


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
	
	def buildSliceCommand(self):
		if self.type is None:
			return None
		
		return self.type.buildSliceCommand()
	
	def sliceComplete(self):
		if self.type is not None:
			self.type.sliceComplete()
			
	def configSlicer(self):
		if self.type is None:
			return False
		else:
			return self.type.configSlicer()
		
	def getSlicerParameters(self):
		if self.type is None:
			return []
		
		return self.type.getSlicerParameters()

	
	def getConfigString(self):
		if self.type is None:
			return None
		
		return self.type.getConfigString()

class Settings:
	def __init__(self, app, folder):
		self.app = app
		self.cmdfolder = folder
		self.inifile = os.path.join(folder, INIFILE)
		self.slicer = "slic3r"
		self.slicers = ["slic3r"]
		self.slicersettings = []
		self.startpane=0
		self.lastlogdirectory = "."
		self.speedcommand = None
		self.port = 8989
		
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
				if opt == 'startpane':
					try:
						self.startpane = int(value)
					except:
						self.showWarning("Invalid value for startpane")
						self.startpane = 0
						self.modified = True
					if self.startpane not in [0, 1, 2]:
						self.showWarning("Startpane may only be 0, 1, or 2")
						self.startpane = 0
						self.modified = True
						
				elif opt == 'slicer':
					self.slicer = value
				elif opt == 'slicers':
					s = value.split(',')
					self.slicers = [x.strip() for x in s]
				elif opt == 'lastlogdirectory':
					self.lastlogdirectory = value
				elif opt == 'speedcommand':
					if value.lower() == "none":
						self.speedcommand = None
					else:
						self.speedcommand = value
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
			
		self.fileprep = SettingsFilePrep(self, self.app, self.cfg, folder, "fileprep")
		self.plater = SettingsPlater(self, self.app, self.cfg, folder, "plater")
		self.manualctl = SettingsManualCtl(self, self.app, self.cfg, folder, "manualctl")
		self.printmon = SettingsPrintMon(self, self.app, self.cfg, folder, "printmon")

	def showWarning(self, msg):
		print "Settings WARNING: " + msg
		
	def showError(self, msg):
		print "Settings ERROR: " + msg
				
	def getSlicerSettings(self, slicer):
		for i in range(len(self.slicers)):
			if self.slicers[i] == slicer:
				if i >= len(self.slicersettings):
					return None
				return self.slicersettings[i]
		return None
	
	def setModified(self):
		self.modified = True
		
	def checkModified(self):
		if self.modified: return True
			
		for s in self.slicersettings:
			if s.checkModified(): return True
			
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
			
			self.cfg.set(self.section, "startpane", str(self.startpane))
			self.cfg.set(self.section, "speedcommand", str(self.speedcommand))
			self.cfg.set(self.section, "slicer", str(self.slicer))
			self.cfg.set(self.section, "slicers", ",".join(self.slicers))
			self.cfg.set(self.section, "lastlogdirectory", str(self.lastlogdirectory))
			self.cfg.set(self.section, "port", str(self.port))
			
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

		self.gcodescale = 3
		self.laststldirectory="."
		self.lastgcdirectory="."
		self.showprevious = True
		self.showmoves = True
		self.usebuffereddc = True
		
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
			
				elif opt == 'laststldirectory':
					self.laststldirectory = value
						
				elif opt == 'lastgcdirectory':
					self.lastgcdirectory = value
						
				elif opt == 'showprevious':
					self.showprevious = parseBoolean(value, True)
						
				elif opt == 'showmoves':
					self.showmoves = parseBoolean(value, True)
						
				elif opt == 'usebuffereddc':
					self.usebuffereddc = parseBoolean(value, False)
				else:
					self.parent.showWarning("Unknown %s option: %s - ignoring" % (section, opt))
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
			self.cfg.set(self.section, "laststldirectory", str(self.laststldirectory))
			self.cfg.set(self.section, "lastgcdirectory", str(self.lastgcdirectory))
			self.cfg.set(self.section, "showprevious", str(self.showprevious))
			self.cfg.set(self.section, "showmoves", str(self.showmoves))
			self.cfg.set(self.section, "usebuffereddc", str(self.usebuffereddc))
						
	
class SettingsPlater:
	def __init__(self, parent, app, cfg, folder, section):
		self.parent = parent
		self.app = app
		self.cmdfolder = os.path.join(folder, section)

		self.stlscale = 2
		self.lastdirectory="."
		self.autoarrange = False
		
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
			
				elif opt == 'lastdirectory':
					self.lastdirectory = value
						
				elif opt == 'autoarrange':
					self.autoarrange = parseBoolean(value, False)
					
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
			self.cfg.set(self.section, "lastdirectory", str(self.lastdirectory))
			self.cfg.set(self.section, "autoarrange", str(self.autoarrange))
	
	
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
	
