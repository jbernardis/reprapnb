import os
import wx
import shlex, subprocess

from settings import BUTTONDIM

CBSIZE = 200


proFiles = ["carve.csv", "skirt.csv", "chamber.csv", "temperature.csv", "speed.csv"]

def intersection(a, b):
	return len([val for val in a if val in b]) != 0

def modifyCSV(fn, ovr, logger):
	try:
		os.unlink(fn + ".save")
	except:
		pass
	
	bfn = os.path.basename(fn)
	
	if bfn == "carve.csv" and 'layerheight' in ovr.keys():
		try:
			os.rename(fn, fn + ".save")
			fpCsv = list(open(fn + ".save"))
			fpNew = open(fn, "w")
			for s in fpCsv:
				if s.startswith("Layer Height (mm):"):
					ns = "Layer Height (mm):\t"+str(ovr['layerheight'])
				else:
					ns = s.rstrip()
				fpNew.write(ns + "\n")
			
			fpNew.close()
		except:
			restoreCSV(fn)
			logger("Unable to modify carve.csv")
			
	elif bfn == "chamber.csv" and intersection(['layer1bedtemperature', 'bedtemperature'], ovr.keys()):
		try:
			os.rename(fn, fn + ".save")
			fpCsv = list(open(fn + ".save"))
			fpNew = open(fn, "w")
			for s in fpCsv:
				if s.startswith("Bed Temperature (Celcius):") and 'layer1bedtemperature' in ovr.keys():
					ns = "Bed Temperature (Celcius):\t"+str(ovr['layer1bedtemperature'])
					
				elif s.startswith("Bed Temperature End (Celcius):") and 'bedtemperature' in ovr.keys():
					ns = "Bed Temperature End (Celcius):\t"+str(ovr['bedtemperature'])
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
					
				elif s.startswith("Object First Layer Infill Temperature (Celcius):") and 'layer1temperature' in ovr.keys():
					ns = "Object First Layer Infill Temperature (Celcius):\t"+str(ovr['layer1temperature']).split(',')[0]
				elif s.startswith("Object First Layer Perimeter Temperature (Celcius):") and 'layer1temperature' in ovr.keys():
					ns = "Object First Layer Perimeter Temperature (Celcius):\t"+str(ovr['layer1temperature']).split(',')[0]
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
					try:
						spd = float(ovr['printspeed'])
					except:
						logger("Unable to parse first layer speed value: %s" % ovr['printspeed'])
						spd = 60.0
						
				elif s.startswith("Flow Rate Setting (float):") and 'printspeed' in ovr.keys():
					ns = "Flow Rate Setting (float):\t"+str(ovr['printspeed'])
					
				elif s.startswith("Travel Feed Rate (mm/s):") and 'travelspeed' in ovr.keys():
					ns = "Travel Feed Rate (mm/s):\t"+str(ovr['travelspeed'])
					
					
				elif s.startswith("Object First Layer") and 'print1speed' in ovr.keys():
					if p1 > 2.0:
						np1 = p1 / spd
						logger("Recalculating First Layer speed value of %0.2f to be ratio of %0.2f times speed %0.2f mm/s" % (p1, np1, spd))
						p1 = np1

					sp1 = str(p1)
						
					if s.startswith("Object First Layer Feed Rate Infill Multiplier (ratio):"):
						ns = "Object First Layer Feed Rate Infill Multiplier (ratio):\t"+sp1
					elif s.startswith("Object First Layer Feed Rate Perimeter Multiplier (ratio):"):
						ns = "Object First Layer Feed Rate Perimeter Multiplier (ratio):\t"+sp1
					elif s.startswith("Object First Layer Flow Rate Infill Multiplier (ratio):"):
						ns = "Object First Layer Flow Rate Infill Multiplier (ratio):\t"+sp1
					elif s.startswith("Object First Layer Flow Rate Perimeter Multiplier (ratio):"):
						ns = "Object First Layer Flow Rate Perimeter Multiplier (ratio):\t"+sp1
				else:
					ns = s.rstrip()
				fpNew.write(ns + "\n")
			
			fpNew.close()
		except:
			restoreCSV(fn)
			logger("Unable to modify speed.csv")
			
	elif bfn == "skirt.csv" and 'skirt' in ovr.keys():	
		try:	
			os.rename(fn, fn + ".save")
			fpCsv = list(open(fn + ".save"))
			fpNew = open(fn, "w")
			for s in fpCsv:
				if s.startswith("Activate Skirt") and 'skirt' in ovr.keys():
					ns = "Activate Skirt\t"+str(ovr['skirt'])
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
			p = subprocess.Popen(args,stderr=subprocess.STDOUT,stdout=subprocess.PIPE)
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
		try:
			l = list(open(os.path.join(dr, "carve.csv")))
			for s in l:
				if s.startswith("Layer Height (mm):"):
					lh = float(s[18:].strip())
					break
			l = list(open(os.path.join(dr, "dimension.csv")))
			for s in l:
				if s.startswith("Filament Diameter (mm):"):
					fd = float(s[23:].strip())
					break
				
			return lh, [fd]
				
		except:
			self.log("Unable to open skeinforge profile file for reading: " + dr)
			return None, None
	
	def buildSliceOutputFile(self, fn):
		return fn.split('.')[0] + "_export.gcode"

	def setOverrides(self, ovr):
		self.overrides = ovr.copy()
		
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
