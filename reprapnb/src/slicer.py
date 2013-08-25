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
		p = parent.settings['profile']
		if p in self.profmap.keys():
			self.settings['profilefile'] = self.profmap[p]
		else:
			self.settings['profilefile'] = None
		
	def getProfile(self):
		return self.settings['profile']
	
	def getProfileTemps(self):
		#FIXIT
		return [60, 185]
	
	def setProfile(self, nprof):
		self.getProfileOptions()
		self.settings['profile'] = nprof
		if nprof in self.profmap.keys():
			self.settings['profilefile'] = self.profmap[nprof]
		else:
			self.settings['profilefile'] = None
		self.parent.setModified()
		
	def buildSliceOutputFile(self, fn):
		return fn.replace(".stl", ".gcode")
		
	def buildSliceCommand(self):
		s = self.settings['command']
		return os.path.expandvars(os.path.expanduser(self.app.replace(s)))
		
	def getProfileOptions(self):
		self.profmap = {}
		try:
			pdir = os.path.expandvars(os.path.expanduser(self.settings['profiledir']))
			l = os.listdir(pdir)
		except:
			self.logger.LogError("Unable to get listing from slic3r profile directory: " + self.settings['profiledir'])
			return {}
		r = {}
		for f in sorted(l):
			if not os.path.isdir(f) and f.lower().endswith(".ini"):
				r[os.path.splitext(os.path.basename(f))[0]] = os.path.join(pdir, f)
		self.profmap = r
		return r