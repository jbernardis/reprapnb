'''
Created on Aug 21, 2012

@author: jbernard
'''
import ConfigParser
import os
import wx

from slicer import createSlicerObject

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
		
	def setSlicerType(self):
		self.type = createSlicerObject(self.name, self.app, self)
		
	def setModified(self, flag=True):
		self.modified = flag
		
	def checkModified(self):
		return self.modified

class PrinterSettings:
	def __init__(self, app, name):
		self.app = app
		self.name = name
		self.settings = {}
		self.modified = False
		self.type = None
		
	def setModified(self, flag=True):
		self.modified = flag
		
	def checkModified(self):
		return self.modified

class Settings:
	def __init__(self, app, folder):
		self.app = app
		self.logger = self.app.logger
		self.cmdfolder = folder
		self.inifile = os.path.join(folder, INIFILE)
		self.slicer = "slic3r"
		self.slicers = ["slic3r"]
		self.startpane=0
		
		self.cfg = ConfigParser.ConfigParser()
		self.cfg.optionxform = str
		if not self.cfg.read(self.inifile):
			self.logger.LogWarning("Settings file %s does not exist.  Using default values" % INIFILE)
			self.modified = True
			
			self.fileprep = SettingsFilePrep(self.app, None, folder, "fileprep")
			self.plater = SettingsPlater(self.app, None, folder, "plater")
			self.manualctl = SettingsManualCtl(self.app, None, folder, "manualctl")
			return

		self.section = "global"	
		self.modified = False	
		if self.cfg.has_section(self.section):
			for opt, value in self.cfg.items(self.section):
				if opt == 'startpane':
					try:
						self.startpane = int(value)
					except:
						self.logger.LogWarning("Invalid value for startpane")
						self.startpane = 0
						self.modified = True
					if self.startpane not in [0, 1]:
						self.logger.LogWarning("Startpane may only be 0, or 1")
						self.startpane = 0
						self.modified = True
						
				elif opt == 'slicer':
					self.slicer = value
				elif opt == 'slicers':
					s = value.split(',')
					self.slicers = [x.strip() for x in s]
				else:
					self.logger.LogWarning("Unknown %s option: %s - ignoring" % (self.section, opt))
		else:
			self.logger.LogWarning("Missing %s section - assuming defaults" % self.section)
			
		self.slicersettings = []
		for slicer in self.slicers:
			st = SlicerSettings(self.app, slicer)
			sc = "slicer." + slicer
			self.slicersettings.append(st)
			if self.cfg.has_section(sc):
				for opt, value in self.cfg.items(sc):
					if opt in ['profile', 'profiledir', 'filament', 'printer', 'command', 'config']:
						st.settings[opt] = value
					else:
						self.logger.LogWarning("Unknown %s option: %s - ignoring" % (sc, opt))
					st.settings[opt] = value
			else:
				self.logger.LogError("No settings for slicer %s" % slicer)

			err = False					
			if 'profile' not in st.settings.keys():
				err = True
				self.logger.LogError("Settings for slicer %s missing profile" % slicer)
			if 'printer' not in st.settings.keys():
				err = True
				self.logger.LogError("Settings for slicer %s missing printer" % slicer)
			if 'filament' not in st.settings.keys():
				err = True
				self.logger.LogError("Settings for slicer %s missing filament" % slicer)
			if 'profiledir' not in st.settings.keys():
				err = True
				self.logger.LogError("Settings for slicer %s missing profiledir" % slicer)
			if 'command' not in st.settings.keys():
				err = True
				self.logger.LogError("Settings for slicer %s missing command" % slicer)
			if 'config' not in st.settings.keys():
				err = True
				self.logger.LogError("Settings for slicer %s missing config" % slicer)
				
			if not err:
				st.setSlicerType()
			
		self.fileprep = SettingsFilePrep(self.app, self.cfg, folder, "fileprep")
		self.plater = SettingsPlater(self.app, self.cfg, folder, "plater")
		self.manualctl = SettingsManualCtl(self.app, self.cfg, folder, "manualctl")
		self.printmon = SettingsPrintMon(self.app, self.cfg, folder, "printmon")
		
	def getSlicerSettings(self, slicer):
		for i in range(len(self.slicers)):
			if self.slicers[i] == slicer:
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
			self.cfg.set(self.section, "slicer", str(self.slicer))
			self.cfg.set(self.section, "slicers", ",".join(self.slicers))
			
			for i in range(len(self.slicers)):
				s = self.slicers[i]
				sc = "slicer." + s
				try:
					self.cfg.add_section(sc)
				except ConfigParser.DuplicateSectionError:
					pass

				sl = self.slicersettings[i]	
				if sl.checkModified():			
					for k in sl.settings.keys():
						if k in ['profile', 'printer', 'filament', 'profiledir', 'command', 'config']:
							self.cfg.set(sc, k, sl.settings[k])
			
			self.fileprep.cleanUp()
			self.plater.cleanUp()
			self.manualctl.cleanUp()
			self.printmon.cleanUp()
		
			cfp = open(self.inifile, 'wb')
			self.cfg.write(cfp)
			cfp.close()


class SettingsFilePrep:
	def __init__(self, app, cfg, folder, section):
		self.app = app
		self.logger = self.app.logger
		self.cmdfolder = os.path.join(folder, section)

		self.gcodescale = 3
		self.lastdirectory="."
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
						self.logger.LogWarning("Non-integer value in ini file for gcodescale")
						self.gcodescale = 3
			
				elif opt == 'lastdirectory':
					self.lastdirectory = value
						
				elif opt == 'showprevious':
					self.showprevious = parseBoolean(value, True)
						
				elif opt == 'showmoves':
					self.showmoves = parseBoolean(value, True)
						
				elif opt == 'usebuffereddc':
					self.usebuffereddc = parseBoolean(value, False)
				else:
					self.logger.LogWarning("Unknown %s option: %s - ignoring" % (section, opt))
		else:
			self.logger.LogWarning("Missing %s section - assuming defaults" % section)
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
			self.cfg.set(self.section, "lastdirectory", str(self.lastdirectory))
			self.cfg.set(self.section, "showprevious", str(self.showprevious))
			self.cfg.set(self.section, "showmoves", str(self.showmoves))
			self.cfg.set(self.section, "usebuffereddc", str(self.usebuffereddc))
						
	
class SettingsPlater:
	def __init__(self, app, cfg, folder, section):
		self.app = app
		self.logger = self.app.logger
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
						self.logger.LogWarning("Non-integer value in ini file for stlscale")
						self.stlscale = 2
			
				elif opt == 'lastdirectory':
					self.lastdirectory = value
						
				elif opt == 'autoarrange':
					self.autoarrange = parseBoolean(value, False)
					
				else:
					self.logger.LogWarning("Unknown %s option: %s - ignoring" % (section,  opt))
		else:
			self.logger.LogWarning("Missing %s section - assuming defaults" % section)
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
	def __init__(self, app, cfg, folder, section):
		self.app = app
		self.logger = self.app.logger
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
						print "Non-integer value in ini file for xyspeed"
						self.xyspeed = 2000
				elif opt == 'zspeed':
					try:
						self.zspeed = int(value)
					except:
						print "Non-integer value in ini file for zspeed"
						self.zspeed = 300
				elif opt == 'espeed':
					try:
						self.espeed = int(value)
					except:
						print "Non-integer value in ini file for espeed"
						self.zspeed = 300
				elif opt == 'edistance':
					try:
						self.edistance = int(value)
					except:
						print "Non-integer value in ini file for edistance"
						self.edistance = 5
				else:
					self.logger.LogWarning("Unknown %s option: %s - ignoring" % (section,  opt))
		else:
			self.logger.LogWarning("Missing %s section - assuming defaults" % section)
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
	def __init__(self, app, cfg, folder, section):
		self.app = app
		self.logger = self.app.logger
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
						self.logger.LogWarning("Non-integer value in ini file for gcodescale")
						self.gcodescale = 3
				elif opt == 'showprevious':
					self.showprevious = parseBoolean(value, True)
						
				elif opt == 'showmoves':
					self.showmoves = parseBoolean(value, True)
						
				elif opt == 'usebuffereddc':
					self.usebuffereddc = parseBoolean(value, False)
				else:
					self.logger.LogWarning("Unknown %s option: %s - ignoring" % (section,  opt))
		else:
			self.logger.LogWarning("Missing %s section - assuming defaults" % section)
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
	
