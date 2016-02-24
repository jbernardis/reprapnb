import os
import wx
import shlex, subprocess

from settings import BUTTONDIM, MAX_EXTRUDERS

CBSIZE = 200


proFiles = ["carve.csv", "dimension.csv", "inset.csv", "fill.csv", "skirt.csv", "chamber.csv", "temperature.csv", "raft.csv", "speed.csv"]

def intersection(a, b):
	return len([val for val in a if val in b]) != 0

def modifyCSV(fn, ovr, logger):
	try:
		os.unlink(fn + ".save")
	except:
		pass
	
	bfn = os.path.basename(fn)
	
	if bfn == "carve.csv" and intersection(['layerheight', 'extrusionwidth'],  ovr.keys()):
		try:
			os.rename(fn, fn + ".save")
			fpCsv = list(open(fn + ".save"))
			fpNew = open(fn, "w")
			for s in fpCsv:
				if s.startswith("Layer Height (mm):") and 'layerheight' in ovr.keys():
					ns = "Layer Height (mm):\t"+str(ovr['layerheight'])
					logger("Override: " + ns + " (carve)")
				elif s.startswith("Edge Width over Height (ratio):") and 'extrusionwidth' in ovr.keys():
					ns = "Edge Width over Height (ratio):\t"+str(ovr['extrusionwidth'])
					logger("Override: " + ns + " (carve)")
				else:
					ns = s.rstrip()
				fpNew.write(ns + "\n")
			
			fpNew.close()
		except:
			restoreCSV(fn)
			logger("Unable to modify carve.csv")
	
	elif bfn == "dimension.csv" and intersection(['filamentdiam', 'extrusionmult'],  ovr.keys()):
		try:
			os.rename(fn, fn + ".save")
			fpCsv = list(open(fn + ".save"))
			fpNew = open(fn, "w")
			for s in fpCsv:
				if s.startswith("Filament Diameter (mm):") and 'filamentdiam' in ovr.keys():
					ns = "Filament Diameter (mm):\t"+str(ovr['filamentdiam'])
					logger("Override: " + ns + " (dimension)")
				elif s.startswith("Filament Packing Density (ratio):") and 'extrusionmult' in ovr.keys():
					ns = "Filament Packing Density (ratio):\t"+str(ovr['extrusionmult'])
					logger("Override: " + ns + " (dimension)")
				else:
					ns = s.rstrip()
				fpNew.write(ns + "\n")
			
			fpNew.close()
		except:
			restoreCSV(fn)
			logger("Unable to modify dimension.csv")
	
	elif bfn == "inset.csv" and intersection(['extrusionwidth'],  ovr.keys()):
		try:
			os.rename(fn, fn + ".save")
			fpCsv = list(open(fn + ".save"))
			fpNew = open(fn, "w")
			for s in fpCsv:
				if s.startswith("Infill Width over Thickness (ratio):"):
					ns = "Infill Width over Thickness (ratio):\t"+str(ovr['extrusionwidth'])
					logger("Override: " + ns + " (inset)")
				else:
					ns = s.rstrip()
				fpNew.write(ns + "\n")
			
			fpNew.close()
		except:
			restoreCSV(fn)
			logger("Unable to modify inset.csv")
	
	elif bfn == "fill.csv" and intersection(['infilldensity'],  ovr.keys()):
		try:
			os.rename(fn, fn + ".save")
			fpCsv = list(open(fn + ".save"))
			fpNew = open(fn, "w")
			for s in fpCsv:
				if s.startswith("Infill Solidity (ratio):"):
					ns = "Infill Solidity (ratio):\t"+str(ovr['infilldensity'])
					logger("Override: " + ns + " (fill)")
				else:
					ns = s.rstrip()
				fpNew.write(ns + "\n")
			
			fpNew.close()
		except:
			restoreCSV(fn)
			logger("Unable to modify fill.csv")
			
	elif bfn == "chamber.csv" and intersection(['layer1bedtemperature', 'bedtemperature'], ovr.keys()):
		try:
			os.rename(fn, fn + ".save")
			fpCsv = list(open(fn + ".save"))
			fpNew = open(fn, "w")
			for s in fpCsv:
				if s.startswith("Bed Temperature (Celcius):") and 'layer1bedtemperature' in ovr.keys():
					ns = "Bed Temperature (Celcius):\t"+str(ovr['layer1bedtemperature'])
					logger("Override: " + ns + " (chamber)")					
				elif s.startswith("Bed Temperature End (Celcius):") and 'bedtemperature' in ovr.keys():
					ns = "Bed Temperature End (Celcius):\t"+str(ovr['bedtemperature'])
					logger("Override: " + ns + " (chamber)")
				else:
					ns = s.rstrip()
				fpNew.write(ns + "\n")
			
			fpNew.close()
		except:
			restoreCSV(fn)
			logger("Unable to modify chamber.csv")

	elif bfn == "temperature.csv" and intersection(['layer1temperature', 'temperature'], ovr.keys()):	
		try:		
			os.rename(fn, fn + ".save")
			fpCsv = list(open(fn + ".save"))
			fpNew = open(fn, "w")
			for s in fpCsv:
				if s.startswith("Object Next Layers Temperature (Celcius):") and 'temperature' in ovr.keys():
					ns = "Object Next Layers Temperature (Celcius):\t"+str(ovr['temperature']).split(',')[0]
					logger("Override: " + ns + " (temperature)")
				elif s.startswith("Object First Layer Infill Temperature (Celcius):") and 'layer1temperature' in ovr.keys():
					ns = "Object First Layer Infill Temperature (Celcius):\t"+str(ovr['layer1temperature']).split(',')[0]
					logger("Override: " + ns + " (temperature)")
				elif s.startswith("Object First Layer Perimeter Temperature (Celcius):") and 'layer1temperature' in ovr.keys():
					ns = "Object First Layer Perimeter Temperature (Celcius):\t"+str(ovr['layer1temperature']).split(',')[0]
					logger("Override: " + ns + " (temperature)")
				else:
					ns = s.rstrip()
				fpNew.write(ns + "\n")
			
			fpNew.close()
		except:
			restoreCSV(fn)
			logger("Unable to modify temperature.csv")
	
	elif bfn == "speed.csv" and intersection(['printspeed', 'travelspeed', 'print1speed'], ovr.keys()):	
		try:	
			os.rename(fn, fn + ".save")
			fpCsv = list(open(fn + ".save"))
			if 'print1speed' in ovr.keys():
				spd = 60.0
				for s in fpCsv:
					if s.startswith("Feed Rate (mm/s):"):
						try:
							spd = float(s.split('\t')[1])
						except:
							spd = 60.0
							
				p1 = ovr['print1speed'].strip()
				if p1.endswith('%'):
					try:
						p1 = float(p1[:-1])/100.0
					except:
						p1 = 1.0
				else:
					p1 = float(p1)
					
					
			fpNew = open(fn, "w")
			for s in fpCsv:
				if s.startswith("Feed Rate (mm/s):") and 'printspeed' in ovr.keys():
					ns = "Feed Rate (mm/s):\t"+str(ovr['printspeed'])
					logger("Override: " + ns + " (speed)")
					try:
						spd = float(ovr['printspeed'])
					except:
						logger("Unable to parse first layer speed value: %s" % ovr['printspeed'])
						spd = 60.0
						
				elif s.startswith("Flow Rate Setting (float):") and 'printspeed' in ovr.keys():
					ns = "Flow Rate Setting (float):\t"+str(ovr['printspeed'])
					logger("Override: " + ns + " (speed)")
					
				elif s.startswith("Travel Feed Rate (mm/s):") and 'travelspeed' in ovr.keys():
					ns = "Travel Feed Rate (mm/s):\t"+str(ovr['travelspeed'])
					logger("Override: " + ns + " (speed)")
					
				elif s.startswith("Object First Layer") and 'print1speed' in ovr.keys():
					if p1 > 2.0:
						np1 = p1 / spd
						logger("Recalculating First Layer speed value of %0.2f to be ratio of %0.2f times speed %0.2f mm/s" % (p1, np1, spd))
						p1 = np1

					sp1 = str(p1)
						
					if s.startswith("Object First Layer Feed Rate Infill Multiplier (ratio):"):
						ns = "Object First Layer Feed Rate Infill Multiplier (ratio):\t"+sp1
						logger("Override: " + ns + " (speed)")
					elif s.startswith("Object First Layer Feed Rate Perimeter Multiplier (ratio):"):
						ns = "Object First Layer Feed Rate Perimeter Multiplier (ratio):\t"+sp1
						logger("Override: " + ns + " (speed)")
					elif s.startswith("Object First Layer Flow Rate Infill Multiplier (ratio):"):
						ns = "Object First Layer Flow Rate Infill Multiplier (ratio):\t"+sp1
						logger("Override: " + ns + " (speed)")
					elif s.startswith("Object First Layer Flow Rate Perimeter Multiplier (ratio):"):
						ns = "Object First Layer Flow Rate Perimeter Multiplier (ratio):\t"+sp1
						logger("Override: " + ns + " (speed)")
					else:
						ns = s.rstrip()			
				else:
					ns = s.rstrip()
				fpNew.write(ns + "\n")
			
			fpNew.close()
		except:
			restoreCSV(fn)
			logger("Unable to modify speed.csv")
			
	elif bfn == "raft.csv" and intersection(['adhesion', 'support'], ovr.keys()):	
		try:	
			os.rename(fn, fn + ".save")
			fpCsv = list(open(fn + ".save"))
			fpNew = open(fn, "w")
			for s in fpCsv:
				if s.startswith("None\t") and 'support' in ovr.keys():
					if ovr['support'] == "True":
						ns = "None\tFalse"
					else:
						ns = "None\tTrue"
					logger("Override: " + ns + " (raft)")
						
				elif s.startswith("Everywhere\t") and 'support' in ovr.keys():
					if ovr['support'] == "True":
						ns = "Everywhere\tTrue"
					else:
						ns = "Everywhere\tFalse"
					logger("Override: " + ns + " (raft)")
						
				elif s.startswith("Base Layers (integer):") and 'adhesion' in ovr.keys():
					if ovr['adhesion'] == "Raft":
						ns = "Base Layers (integer):\t1"
					else:
						ns = "Base Layers (integer):\t0"
					logger("Override: " + ns + " (raft)")
						
				elif s.startswith("Interface Layers (integer):") and 'adhesion' in ovr.keys():
					if ovr['adhesion'] == "Raft":
						ns = "Interface Layers (integer):\t2"
					else:
						ns = "Interface Layers (integer):\t0"
					logger("Override: " + ns + " (raft)")
						
				else:
					ns = s.rstrip()
				
				fpNew.write(ns + "\n")
			
			fpNew.close()
		except:
			restoreCSV(fn)
			logger("Unable to modify raft.csv")
			
	elif bfn == "skirt.csv" and intersection(['skirt', 'adhesion'], ovr.keys()):	
		try:	
			os.rename(fn, fn + ".save")
			fpCsv = list(open(fn + ".save"))
			fpNew = open(fn, "w")
			for s in fpCsv:
				if s.startswith("Activate Skirt"):
					if 'adhesion' in ovr.keys():
						if ovr['adhesion'] == "Brim":
							ns = "Activate Skirt\tTrue"
							logger("Override: " + ns + " (skirt)")
						elif 'skirt' in ovr.keys():
							ns = "Activate Skirt\t"+str(ovr['skirt'])
							logger("Override: " + ns + " (skirt)")
						else:
							ns = s.rstrip()
					else:
						ns = "Activate Skirt\t"+str(ovr['skirt'])
						logger("Override: " + ns + " (skirt)")
				
				elif s.startswith("Brim Width:") and 'adhesion' in ovr.keys():	
					if ovr['adhesion'] == "Brim":
						ns = "Brim Width:\t6"
					else:
						ns = "Brim Width:\t0"
					logger("Override: " + ns + " (skirt)")
				
				else:
					ns = s.rstrip()
				
				fpNew.write(ns + "\n")
			
			fpNew.close()
		except:
			restoreCSV(fn)
			logger("Unable to modify skirt.csv")
	
def restoreCSV(fn):
	if os.path.exists(fn + ".save"):
		try:
			os.unlink(fn)
		except:
			pass
		
		os.rename(fn + ".save", fn)

class SkeinforgeCfgDialog(wx.Dialog):
	def __init__(self, slicer):
		self.slicer = slicer
		self.app = slicer.app
		self.settings = slicer.parent.settings
		self.vprofile = self.settings['profile']
		self.profilemap = slicer.profilemap
		self.refreshed = False
		
		pre = wx.PreDialog()
		pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
		pos = wx.DefaultPosition
		sz = wx.DefaultSize
		style = wx.DEFAULT_DIALOG_STYLE
		pre.Create(self.app, wx.ID_ANY, "Skeinforge Profiles", pos, sz, style)
		self.PostCreate(pre)
		
		sizer = wx.BoxSizer(wx.VERTICAL)
				
		f = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		dc = wx.WindowDC(self)
		dc.SetFont(f)
		prf = wx.BoxSizer(wx.HORIZONTAL)
		
		text = " Profile:"
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w,h))
		t.SetFont(f)
		prf.Add(t, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.TOP, 10)
	
		self.cbProfile = wx.ComboBox(self, wx.ID_ANY, self.vprofile,
 			(-1, -1), (CBSIZE, -1), self.profilemap.keys(), wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbProfile.SetFont(f)
		self.cbProfile.SetToolTipString("Choose which skeinforge profile to use")
		prf.Add(self.cbProfile, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		self.cbProfile.SetStringSelection(self.vprofile)
		self.Bind(wx.EVT_COMBOBOX, self.doChooseProfile, self.cbProfile)

		sizer.Add(prf, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		
		btnsizer = wx.StdDialogButtonSizer()
		
		btn = wx.Button(self, wx.ID_OK)
		btn.SetDefault()
		btnsizer.AddButton(btn)
		
		btn = wx.Button(self, wx.ID_CANCEL)
		btnsizer.AddButton(btn)

		btnsizer.Realize()
	
		btnsizer2 = wx.BoxSizer()
		
		btn = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngSlicecfg, size=BUTTONDIM)
		btn.SetToolTipString("Configure Slicer")
		self.Bind(wx.EVT_BUTTON, self.cfgSlicer, btn)
		
		btnsizer2.Add(btn, flag=wx.ALL, border=5)
		
		btn = wx.BitmapButton(self, wx.ID_ANY, self.app.images.pngRefresh, size=BUTTONDIM)
		btn.SetToolTipString("Refresh Slicer Profiles")
		self.Bind(wx.EVT_BUTTON, self.refreshSlicer, btn)
		
		btnsizer2.Add(btn, flag=wx.ALL, border=5)

		row = wx.BoxSizer(wx.HORIZONTAL)
		row.Add(btnsizer, flag=wx.TOP, border=10)
		row.AddSpacer((100, 10))
		row.Add(btnsizer2)
		
		sizer.Add(row, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

		self.SetSizer(sizer)
		sizer.Fit(self)

	def cfgSlicer(self, evt):
		s = self.settings['config']
		cmd = os.path.expandvars(os.path.expanduser(self.app.replace(s)))

		args = shlex.split(str(cmd))
		try:
			subprocess.Popen(args,stderr=subprocess.STDOUT,stdout=subprocess.PIPE)
		except:
			print "Exception occurred trying to spawn slicer"
			return

	def refreshSlicer(self, evt):
		self.refreshed = True
		self.slicer.initialize()
		
		self.profilemap = self.slicer.profilemap
		if self.vprofile not in self.profilemap.keys():
			self.vprofile = self.profilemap.keys()[0]
			
		self.cbProfile.SetItems(self.profilemap.keys())
		self.cbProfile.SetStringSelection(self.vprofile)
		
	def getValues(self):
		return [self.vprofile, self.refreshed]
		
	def doChooseProfile(self, evt):
		self.vprofile = self.cbProfile.GetValue()
		
class Skeinforge:
	def __init__(self, app, parent):
		self.app = app
		self.parent = parent
		self.logger = None
		self.overrides = {}

	def setLogger(self, logger):
		self.logger = logger
		
	def log(self, msg):
		if self.logger:
			self.logger.LogMessage(msg)
		else:
			print msg
		
	def fileTypes(self):
		return "STL (*.stl)|*.stl;*.STL"
		
	def getSettingsKeys(self):
		return ['profilefile', 'profiledir', 'profile', 'command', 'config'], []
		
	def initialize(self, flag=False):
		if flag:
			np = self.loadProfile()
			if np is not None:
				self.parent.settings['profile'] = np
			self.vprofile = self.parent.settings['profile']
			
		self.getProfileOptions()

	def configSlicer(self):
		self.getProfileOptions()
		
		dlg = SkeinforgeCfgDialog(self) 
		dlg.CenterOnScreen()
		val = dlg.ShowModal()
	
		if val != wx.ID_OK:
			dlg.Destroy()
			return False
		
		self.vprofile, refreshFlag = dlg.getValues()
		dlg.Destroy()
		return self.updateSlicerCfg(refreshFlag)
		
	def configSlicerDirect(self, cfgopts):
		self.getProfileOptions()
		if len(cfgopts) != 1:
			return False, "incorrect number of parameters for configuring skeinforge - 1 expected"
		if cfgopts[0] not in self.profilemap.keys():
			return False, "invalid profile : %s" % cfgopts[0]
		
		self.vprofile = cfgopts[0]
		self.updateSlicerCfg(False)
		return True, "success"

	def updateSlicerCfg(self, refreshFlag):
		chg = refreshFlag
		if self.parent.settings['profile'] != self.vprofile:
			self.writeProfile(self.parent.settings['profile'], self.vprofile)
			self.parent.settings['profile'] = self.vprofile
			chg = True
			
		if chg:
			self.parent.setModified()
			
		return chg
		
	def getConfigString(self):
		return "(" + str(self.vprofile) + ")"
	
	def getDimensionInfo(self):
		dr = os.path.join(os.path.expandvars(os.path.expanduser(self.parent.settings['profiledir'])), str(self.vprofile))
		lh = 0.0
		fd = 0.0
		try:
			if "layerheight" in self.overrides.keys():
				lh = float(self.overrides["layerheight"])
			else:
				l = list(open(os.path.join(dr, "carve.csv")))
				for s in l:
					if s.startswith("Layer Height (mm):"):
						lh = float(s[18:].strip())
						break
			if "filamentdiam" in self.overrides.keys():
				try:
					fd = float(self.overrides("filamentdiam"))
				except:
					fd = 0.0
			else:
				l = list(open(os.path.join(dr, "dimension.csv")))
				for s in l:
					if s.startswith("Filament Diameter (mm):"):
						fd = float(s[23:].strip())
						break
				
			return lh, [fd]
				
		except:
			self.log("Unable to open skeinforge profile file for reading: " + dr)
			return None, None
	
	def getTempProfile(self):
		dr = os.path.join(os.path.expandvars(os.path.expanduser(self.parent.settings['profiledir'])), str(self.vprofile))
		bt = None
		bt1 = None
		tp = None
		tp1 = None
		try:
			if "bedtemperature" in self.overrides.keys():
				bt = self.overrides["bedtemperature"]
			else:
				l = list(open(os.path.join(dr, "chamber.csv")))
				for s in l:
					if s.startswith("Bed Temperature End (Celcius):"):
						bt = float(s[30:].strip())
						break
			if "layer1bedtemperature" in self.overrides.keys():
				bt1 = self.overrides["layer1bedtemperature"]
			else:
				l = list(open(os.path.join(dr, "chamber.csv")))
				for s in l:
					if s.startswith("Bed Temperature (Celcius):"):
						bt1 = float(s[26:].strip())
						break
			if "temperature" in self.overrides.keys():
				tp = self.overrides("temperature")
			else:
				l = list(open(os.path.join(dr, "temperature.csv")))
				for s in l:
					if s.startswith("Object Next Layers Temperature (Celcius):"):
						tp = float(s[41:].strip())
						break
			if "layer1temperature" in self.overrides.keys():
				tp1 = self.overrides("layer1temperature")
			else:
				l = list(open(os.path.join(dr, "temperature.csv")))
				for s in l:
					if s.startswith("Object First Layer Infill Temperature (Celcius):"):
						tp1 = float(s[48:].strip())
						break
				
			if not bt is None:
				if bt1 is None:
					bt = [bt, bt]
				else:
					bt = [bt1, bt]
					
			if not tp is None:
				if tp1 is None:
					tp = [tp, tp]
				else:
					tp = [tp1, tp]
					
			return bt, [tp] * MAX_EXTRUDERS
				
		except:
			self.log("Unable to open skeinforge profile file for reading: " + dr)
			return None, [None] * MAX_EXTRUDERS
	
	def buildSliceOutputFile(self, fn):
		return fn.split('.')[0] + "_export.gcode"

	def setOverrides(self, ovr):
		self.overrides = ovr.copy()
		
	def getOverrideHelpText(self):
		ht = {}
		ht["filamentdiam"] = "Filament diameter (dimension)"
		ht["extrusionmult"] = "Filament Packing Density (dimension)"
		ht["layerheight"] = "Used directly as Layer Height (carve)"
		ht["extrusionwidth"] = "Used directly as Edge Width over Height (carve) and Infill Width over Thickness (inset)"
		ht["infilldensity"] = "Used directly as Infill Solidity (fill)"
		ht["temperature"] = "Used directly as Object Next Layers Temperature (temperature)"
		ht["bedtemperature"] = "Used directly as Bed Temperature End (chamber) - assumes change height settings"
		ht["layer1temperature"] = "Used directly as Object First Layer Infill and Object First Layer Perimeter Temperatures (temperature)"
		ht["layer1bedtemperature"] = "Used directly as Bed Temperature (chamber) - assumes change height settings"
		ht["printspeed"] = "Used directly as boht Feed Rate and Flow Rate (speed)"
		ht["print1speed"] = "Used for ALL Object First Layer Feed and Flow rates (speed).  Values > 2 are assumed to be explicit values and are recalculated as rations"
		ht["travelspeed"] = "Used directly as Travel Feed Rate (speed)"
		ht["skirt"] = "Used directly as Activate Skirt (skirt)"
		ht["support"] = "Maps to Support (raft).  Enabled => Everywhere = True, Disabled => None = True"
		ht["adhesion"] = "Maps to Brim Width (skirt) and Base Layers and Interface Layers (raft) to set either none, brim, or raft adhesion"
		
		return ht
		
	def buildSliceCommand(self):
		s = self.parent.settings['command']
		self.doOverride = False
		if len(self.overrides.keys()) > 0:
			self.doOverride = True
			dr = os.path.join(os.path.expandvars(os.path.expanduser(self.parent.settings['profiledir'])), str(self.vprofile))
			for f in proFiles:
				modifyCSV(os.path.join(dr, f), self.overrides, self.log)
			
		return os.path.expandvars(os.path.expanduser(self.app.replace(s)))
	
	def sliceComplete(self):
		if self.doOverride:
			dr = os.path.join(os.path.expandvars(os.path.expanduser(self.parent.settings['profiledir'])), str(self.vprofile))
			for f in proFiles:
				restoreCSV(os.path.join(dr, f))
	
	def loadProfile(self):
		profile = None
		try:
			self.profContents = []
			l = list(open(os.path.expandvars(os.path.expanduser(self.parent.settings['profilefile']))))
			for s in l:
				if s.startswith("Profile Selection:"):
					profile = s[18:].strip()
				self.profContents.append(s)
				
		except:
			self.log("Unable to open skeinforge profile file for reading: " + self.parent.settings['profilefile'])
			self.profContents = []
			return None
		
		return profile
	
	def writeProfile(self, oprof, nprof):
		try:
			fp = open(os.path.expandvars(os.path.expanduser(self.parent.settings['profilefile'])), "w")
			for i in self.profContents:
				if i.startswith("Profile Selection:"):
					fp.write(i.replace(oprof, nprof))
				else:
					fp.write(i)
			fp.close()
			self.loadProfile()
			
		except:
			self.log("Unable to open skeinforge profile file for writing: " + self.parent.settings['profilefile'])
			
	def getProfileOptions(self):
		self.profilemap = {}
		try:
			d = os.path.expandvars(os.path.expanduser(self.parent.settings['profiledir']))
			l = os.listdir(d)
		except:
			self.log("Unable to get listing from skeinforge profile directory: " + self.parent.settings['profiledir'])
			return {}
		r = {}
		for f in sorted(l):
			p = os.path.join(d, f)
			if os.path.isdir(p):
				r[f] = p
				
		self.profilemap = r
		return r
