'''
Created on Jun 20, 2013

@author: ejefber
'''
import os
import wx

def createSlicerObject(name, app, parent):
	if name == 'slic3r':
		return Slic3r(app, parent)
	
	return None

#FIXIT - work with slic3r ini files - 3 files	
	
class Slic3r:
	def __init__(self, app, parent):
		self.app = app
		self.logger = self.app.logger
		self.parent = parent
		self.settings = parent.settings
		self.getProfileOptions()
		p = self.settings['profile']
		if p in self.profmap.keys():
			self.settings['profilefile'] = self.profmap[p]
		else:
			self.settings['profilefile'] = None

		self.getFilamentOptions()		
		p = self.settings['filament']
		if p in self.filmap.keys():
			self.settings['filamentfile'] = self.filmap[p]
		else:
			self.settings['filamentfile'] = None

		self.getPrinterOptions()		
		p = self.settings['printer']
		if p in self.printermap.keys():
			self.settings['printerfile'] = self.printermap[p]
		else:
			self.settings['printerfile'] = None
		
	def getProfile(self):
		return self.settings['profile']
		
	def getFilament(self):
		return self.settings['filament']
		
	def getPrinter(self):
		return self.settings['printer']
	
	def getSlicerSettings(self):
		#FIXIT
		#       buildarea  next axes  hotendtemp  bedtemp
		return [[200, 200], 1, ['E'], [185], 60]
	
	def setProfile(self, nprof):
		self.getProfileOptions()
		self.settings['profile'] = nprof
		if nprof in self.profmap.keys():
			self.settings['profilefile'] = self.profmap[nprof]
		else:
			self.settings['profilefile'] = None
		self.parent.setModified()
	
	def setPrinter(self, nprinter):
		self.getPrinterOptions()
		self.settings['printer'] = nprinter
		if nprinter in self.printermap.keys():
			self.settings['printerfile'] = self.printermap[nprinter]
		else:
			self.settings['printerfile'] = None
		self.parent.setModified()
	
	def setFilament(self, nfil):
		self.getFilamentOptions()
		self.settings['filament'] = nfil
		if nfil in self.filmap.keys():
			self.settings['filamentfile'] = self.profmap[nfil]
		else:
			self.settings['filamentfile'] = None
		self.parent.setModified()
		
	def buildSliceOutputFile(self, fn):
		return fn.replace(".stl", ".gcode")
		
	def buildSliceCommand(self):
		s = self.settings['command']
		return os.path.expandvars(os.path.expanduser(self.app.replace(s)))
		
	def getProfileOptions(self):
		self.profmap = {}
		try:
			pdir = os.path.expandvars(os.path.expanduser(self.settings['profiledir'] + os.path.sep + "print"))
			l = os.listdir(pdir)
		except:
			self.logger.LogError("Unable to get print profiles from slic3r profile directory: " + self.settings['profiledir'])
			return {}
		r = {}
		for f in sorted(l):
			if not os.path.isdir(f) and f.lower().endswith(".ini"):
				r[os.path.splitext(os.path.basename(f))[0]] = os.path.join(pdir, f)
		self.profmap = r
		return r
			
	def getFilamentOptions(self):
		self.filmap = {}
		try:
			pdir = os.path.expandvars(os.path.expanduser(self.settings['profiledir'] + os.path.sep + "filament"))
			l = os.listdir(pdir)
		except:
			self.logger.LogError("Unable to get filament profiles from slic3r profile directory: " + self.settings['profiledir'])
			return {}
		r = {}
		for f in sorted(l):
			if not os.path.isdir(f) and f.lower().endswith(".ini"):
				r[os.path.splitext(os.path.basename(f))[0]] = os.path.join(pdir, f)
		self.filmap = r
		return r
			
	def getPrinterOptions(self):
		self.printermap = {}
		try:
			pdir = os.path.expandvars(os.path.expanduser(self.settings['profiledir'] + os.path.sep + "printer"))
			l = os.listdir(pdir)
		except:
			self.logger.LogError("Unable to get printer profiles from slic3r profile directory: " + self.settings['profiledir'])
			return {}
		r = {}
		for f in sorted(l):
			if not os.path.isdir(f) and f.lower().endswith(".ini"):
				r[os.path.splitext(os.path.basename(f))[0]] = os.path.join(pdir, f)
		self.printermap = r
		return r