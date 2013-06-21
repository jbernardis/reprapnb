'''
Created on Aug 21, 2012

@author: jbernard
'''
import ConfigParser
import os
import wx

from slicer import createSlicerObject

INIFILE = "rrh.ini"


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
		self.type = createSlicerObject(self.name, self.app, self.settings)
		
	def setModified(self, flag=True):
		self.modified = flag
		
	def checkModified(self):
		return self.modified

class Settings:
	def __init__(self, app, folder):
		self.app = app
		self.cmdfolder = folder
		self.buildarea = (200, 200)
		self.inifile = os.path.join(folder, INIFILE)
		self.slicer = "slic3r"
		self.slicers = ["slic3r"]
		
		self.cfg = ConfigParser.ConfigParser()
		if not self.cfg.read(self.inifile):
			wx.LogWarning("Settings file %s does not exist.  Using default values" % INIFILE)
			return

		self.section = "global"	
		self.modified = False	
		if self.cfg.has_section(self.section):
			for opt, value in self.cfg.items(self.section):
				if opt == 'buildarea':
					try:
						s = (200, 200)
						exec("s=%s" % value)
						self.buildarea = s
					except:
						wx.LogWarning("invalid value in ini file for buildarea")
				elif opt == 'slicer':
					self.slicer = value
				elif opt == 'slicers':
					s = value.split(',')
					self.slicers = [x.strip() for x in s]
				else:
					wx.LogWarning("Unknown %s option: %s - ignoring" % (self.section, opt))
		else:
			wx.LogWarning("Missing %s section - assuming defaults" % self.section)

		self.slicersettings = []
		for slicer in self.slicers:
			st = SlicerSettings(self.app, slicer)
			self.slicersettings.append(st)
			if self.cfg.has_section(slicer):
				for opt, value in self.cfg.items(slicer):
					st.settings[opt] = value
			else:
				wx.LogError("No settings for slicer %s" % slicer)

			err = False					
			if 'profile' not in st.settings.keys():
				err = True
				wx.LogError("Settings for slicer %s missing profile" % slicer)
			if 'profiledir' not in st.settings.keys():
				err = True
				wx.LogError("Settings for slicer %s missing profiledir" % slicer)
			if 'command' not in st.settings.keys():
				err = True
				wx.LogError("Settings for slicer %s missing command" % slicer)
			if 'config' not in st.settings.keys():
				err = True
				wx.LogError("Settings for slicer %s missing config" % slicer)
				
			if not err:
				st.setSlicerType()
			
		self.fileprep = SettingsFilePrep(self.app, self.cfg, folder, "fileprep")
		self.plater = SettingsPlater(self.app, self.cfg, folder, "plater")
		
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
		
		return False
		
	def cleanUp(self):
		if self.checkModified():
			try:
				self.cfg.add_section(self.section)
			except ConfigParser.DuplicateSectionError:
				pass
			
			self.cfg.set(self.section, "buildarea", str(self.buildarea))
			self.cfg.set(self.section, "slicer", str(self.slicer))
			self.cfg.set(self.section, "slicers", ",".join(self.slicers))
			
			for i in range(len(self.slicers)):
				s = self.slicers[i]
				try:
					self.cfg.add_section(s)
				except ConfigParser.DuplicateSectionError:
					pass

				sl = self.slicersettings[i]	
				if sl.checkModified():			
					for k in sl.settings.keys():
						self.cfg.set(s, k, sl.settings[k])
			
			self.fileprep.cleanUp()
			self.plater.cleanUp()
		
			cfp = open(self.inifile, 'wb')
			self.cfg.write(cfp)
			cfp.close()


class SettingsFilePrep:
	def __init__(self, app, cfg, folder, section):
		self.app = app
		self.cmdfolder = os.path.join(folder, section)

		self.gcodescale = 3
		self.lastdirectory="."
		self.showprevious = True
		self.showmoves = True
		self.usebuffereddc = True

		self.cfg = cfg		
		self.section = section
		self.modified = False	
		if cfg.has_section(section):
			for opt, value in cfg.items(section):
				if opt == 'gcodescale':
					try:
						self.gcodescale = int(value)
					except:
						wx.LogWarning("Non-integer value in ini file for gcodescale")
						self.gcodescale = 4
			
				elif opt == 'lastdirectory':
					self.lastdirectory = value
						
				elif opt == 'showprevious':
					self.showprevious = parseBoolean(value, True)
						
				elif opt == 'showmoves':
					self.showmoves = parseBoolean(value, True)
						
				elif opt == 'usebuffereddc':
					self.usebuffereddc = parseBoolean(value, False)
				else:
					wx.LogWarning("Unknown %s option: %s - ignoring" % (section, opt))
		else:
			wx.LogWarning("Missing %s section - assuming defaults" % section)
		
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
		self.cmdfolder = os.path.join(folder, section)

		self.stlscale = 2
		self.lastdirectory="."
		self.autoarrange = False

		self.cfg = cfg
		self.modified = False
		self.section = section	
		if cfg.has_section(section):
			for opt, value in cfg.items(section):
				if opt == 'stlscale':
					try:
						self.stlscale = int(value)
					except:
						wx.LogWarning("Non-integer value in ini file for stlscale")
						self.stlscale = 2
			
				elif opt == 'lastdirectory':
					self.lastdirectory = value
						
				elif opt == 'autoarrange':
					self.autoarrange = parseBoolean(value, False)
					
				else:
					wx.LogWarning("Unknown %s option: %s - ignoring" % (section,  opt))
		else:
			wx.LogWarning("Missing %s section - assuming defaults" % section)


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
	
