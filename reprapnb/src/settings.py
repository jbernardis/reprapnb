'''
Created on Aug 21, 2012

@author: jbernard
'''
import ConfigParser
import os
import wx

from slicer import createSlicerObject
from printer import createPrinterObject

INIFILE = "rrh.ini"


def parseBoolean(val, defaultVal):
	lval = val.lower();
	
	if lval == 'true' or lval == 't' or lval == 'yes' or lval == 'y':
		return True
	
	if lval == 'false' or lval == 'f' or lval == 'no' or lval == 'n':
		return False
	
	return defaultVal

class PrinterSettings:
	def __init__(self, app, name):
		self.app = app
		self.name = name
		self.settings = {}
		self.modified = False
		self.type = None
		
	def setPrinterType(self):
		self.type = createPrinterObject(self.name, self.app, self)
		
	def setModified(self, flag=True):
		self.modified = flag
		
	def checkModified(self):
		return self.modified

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

class Settings:
	def __init__(self, app, folder):
		self.app = app
		self.logger = self.app.logger
		self.cmdfolder = folder
		self.inifile = os.path.join(folder, INIFILE)
		self.slicer = "slic3r"
		self.slicers = ["slic3r"]
		self.printer=""
		self.printers=[]
		
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
				if opt == 'slicer':
					self.slicer = value
				elif opt == 'slicers':
					s = value.split(',')
					self.slicers = [x.strip() for x in s]
				elif opt == 'printer':
					self.printer = value
				elif opt == 'printers':
					s = value.split(',')
					self.printers = [x.strip() for x in s]
				else:
					self.logger.LogWarning("Unknown %s option: %s - ignoring" % (self.section, opt))
		else:
			self.logger.LogWarning("Missing %s section - assuming defaults" % self.section)

		self.printersettings = []
		for printer in self.printers:
			st = PrinterSettings(self.app, printer)
			self.printersettings.append(st)
			sc = "printer." + printer
			distNames = ["Edistance"]
			speedNames = ["ESpeed"]
			if self.cfg.has_section(sc):
				for opt, value in self.cfg.items(sc):
					if opt == 'buildarea':
						try:
							exec("s=%s" % value)
						except:
							s = (200, 200)
							self.logger.LogWarning("invalid buildarea for printer %s" % printer)
						st.settings[opt] = s
						
					elif opt == 'axisletters':
						try:
							exec("s=%s" % value)
						except:
							s = ['E']
							self.logger.LogWarning("invalid axis letter spec for printer %s" % printer)
						st.settings[opt] = s
						distNames = []
						speedNames = []
						for n in s:
							distNames.append(n+"distance")
							speedNames.append(n+"speed")
							
					elif opt in distNames or opt in speedNames or opt in ["xyspeed", "zspeed"]:
						try:
							v = float(value)
						except:
							self.logger.LogError("Invalid value for %s for printer %s" % (opt, printer))
							v = 0
						st.settings[opt] = v

					elif opt == 'extruders':
						try:
							st.settings[opt] = int(value)
						except:
							self.logger.LogWarning("Invalid extruders value for printer %s" % printer)
							st.settings[opt] = 1
					else:
						self.logger.LogWarning("Unknown %s option: %s - ignoring" % (sc, opt))
			else:
				self.logger.LogError("No settings for printer %s" % printer)

			if 'buildarea' not in st.settings.keys():
				self.logger.LogWarning("Settings for printer %s missing buildarea" % printer)
				st.settings['buildarea'] = (200,200)
				st.setModified(True)
			if 'extruders' not in st.settings.keys():
				self.logger.LogWarning("Settings for printer %s missing extruders" % printer)
				st.settings['extruders'] = 1
				st.setModified(True)
			if 'axisletters' not in st.settings.keys():
				self.logger.LogWarning("Settings for printer %s missing axis letters" % printer)
				st.settings['axisletters'] = ['E']
				st.setModified(True)
			if len(st.settings['axisletters']) != st.settings['extruders']:
				self.logger.LogError("Printer %s does not have enough axis letters defined" % printer)
			for n in distNames:
				if n not in st.settings.keys():
					self.logger.LogWarning("%s not specified for printer %s" % (n, printer))
					st.settings[n] = 5
					st.setModified(True)
			for n in speedNames:
				if n not in st.settings.keys():
					self.logger.LogWarning("%s not specified for printer %s" % (n, printer))
					st.settings[n] = 1800
					st.setModified(True)
			if "xyspeed" not in st.settings.keys():
				self.logger.LogWarning("xyspeed not specified for printer %s" % (n, printer))
				st.settings["xyspeed"] = 1800
				st.setModified(True)
			if "zspeed" not in st.settings.keys():
				self.logger.LogWarning("xyspeed not specified for printer %s" % (n, printer))
				st.settings["zspeed"] = 300
				st.setModified(True)
			
		self.slicersettings = []
		for slicer in self.slicers:
			st = SlicerSettings(self.app, slicer)
			sc = "slicer." + slicer
			self.slicersettings.append(st)
			if self.cfg.has_section(sc):
				for opt, value in self.cfg.items(sc):
					if opt in ['profile', 'profiledir', 'command', 'config']:
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
		
	def getPrinterSettings(self, printer):
		for i in range(len(self.printers)):
			if self.printers[i] == printer:
				return self.printersettings[i]
		return None
		
	def setModified(self):
		self.modified = True
		
	def checkModified(self):
		if self.modified: return True
		for p in self.printersettings:
			if p.checkModified(): return True
			
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
			
			self.cfg.set(self.section, "slicer", str(self.slicer))
			self.cfg.set(self.section, "slicers", ",".join(self.slicers))
			self.cfg.set(self.section, "printer", str(self.printer))
			self.cfg.set(self.section, "printers", ",".join(self.printers))
			
			for i in range(len(self.printers)):
				p = self.printers[i]
				sc = "printer." + p
				try:
					self.cfg.add_section(sc)
				except ConfigParser.DuplicateSectionError:
					pass

				pt = self.printersettings[i]	
				if pt.checkModified():
					spds = []
					dsts = []
					for n in pt.settings['axisletters']:
						spds.append(n+"speed")
						dsts.append(n+"distance")			
					for k in pt.settings.keys():
						if k in ['buildarea', 'extruders', 'axisletters', 'xyspeed', 'zspeed'] or k in dsts or k in spds:
							self.cfg.set(sc, k, pt.settings[k])
						
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
						if k in ['profile', 'profiledir', 'command', 'config']:
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

		if cfg is None:
			self.modified = True
			return
		
		self.cfg = cfg
		self.modified = False
		self.section = section	
		if cfg.has_section(section):
			for opt, value in cfg.items(section):
				if opt == 'xxxxxxxxxx':
					pass
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
	
