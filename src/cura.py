import os
import wx
import tempfile
import shlex, subprocess
import ConfigParser

from settings import BUTTONDIM, SAVE_SETTINGS_FILE
from cProfile import Profile

CBSIZE = 200
PREFSECTION = 'preference'

class CuraCfgDialog(wx.Dialog):
	def __init__(self, slicer):
		self.slicer = slicer
		self.app = slicer.app
		self.settings = slicer.parent.settings
		self.vprofile = self.settings['profile']
		self.vprinter = self.settings['printer']
		self.profilemap = slicer.profilemap
		self.printermap = slicer.printermap
		self.refreshed = False
		
		pre = wx.PreDialog()
		pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
		pos = wx.DefaultPosition
		sz = wx.DefaultSize
		style = wx.DEFAULT_DIALOG_STYLE
		pre.Create(self.app, wx.ID_ANY, "Cura Profiles", pos, sz, style)
		self.PostCreate(pre)
		
		sizer = wx.BoxSizer(wx.VERTICAL)
				
		f = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		dc = wx.WindowDC(self)
		dc.SetFont(f)
		cbsz = wx.BoxSizer(wx.HORIZONTAL)
		
		text = " Profile:"
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w,h))
		t.SetFont(f)
		cbsz.Add(t, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.TOP, 10)
	
		self.cbProfile = wx.ComboBox(self, wx.ID_ANY, self.vprofile,
 			(-1, -1), (CBSIZE, -1), self.profilemap.keys(), wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbProfile.SetFont(f)
		self.cbProfile.SetToolTipString("Choose which cura profile to use")
		cbsz.Add(self.cbProfile, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		self.cbProfile.SetStringSelection(self.vprofile)
		self.Bind(wx.EVT_COMBOBOX, self.doChooseProfile, self.cbProfile)

		text = " Printer:"
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w,h))
		t.SetFont(f)
		cbsz.Add(t, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.TOP, 10)
	
		self.cbPrinter = wx.ComboBox(self, wx.ID_ANY, self.vprofile,
 			(-1, -1), (CBSIZE, -1), self.printermap.keys(), wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbPrinter.SetFont(f)
		self.cbPrinter.SetToolTipString("Choose which cura printer to use")
		cbsz.Add(self.cbPrinter, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		self.cbPrinter.SetStringSelection(self.vprinter)
		self.Bind(wx.EVT_COMBOBOX, self.doChoosePrinter, self.cbPrinter)

		sizer.Add(cbsz, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		
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
		
		self.printermap = self.slicer.printermap
		if self.vprinter not in self.printermap.keys():
			self.vprinter = self.printermap.keys()[0]
			
		self.cbPrinter.SetItems(self.printermap.keys())
		self.cbPrinter.SetStringSelection(self.vprinter)
		
	def getValues(self):
		return [self.vprofile, self.vprinter, self.refreshed]
		
	def doChooseProfile(self, evt):
		self.vprofile = self.cbProfile.GetValue()
		
	def doChoosePrinter(self, evt):
		self.vprinter = self.cbPrinter.GetValue()
		
class Cura:
	def __init__(self, app, parent):
		self.app = app
		self.parent = parent
		self.overrides = {}
		self.tempFile = None
		self.logger = None

	def setLogger(self, logger):
		self.logger = logger
		
	def log(self, msg):
		if self.logger:
			self.logger.LogMessage(msg)
		else:
			print msg
		
	def fileTypes(self):
		return "STL (*.stl)|*.stl;*.STL|" \
			"AMF (*.amf)|*.amf;*.AMF|" \
			"STL or AMF (*.stl, *amf)|*.stl;*.STL;*.amf;*.AMF"
		
	def getSettingsKeys(self):
		return ['curapreferences', 'profiledir', 'profile', 'printer', 'command', 'config'], []
	
	def loadPrefs(self):
		self.prefs = ConfigParser.ConfigParser()
		self.prefs.optionxform = str
		self.prefFile = self.parent.settings['curapreferences']
		if not self.prefs.read(self.prefFile):
			self.log("Cura preferences file %s does not exist.  Using default values" % self.prefFile)
		
	def initialize(self, flag=False):
		if flag:
			self.vprinter = self.parent.settings['printer']
			self.vprofile = self.parent.settings['profile']
			
		self.loadPrefs()

		self.getProfileOptions()
		p = self.vprofile
		if p in self.profilemap.keys():
			self.parent.settings['profile'] = p
		else:
			self.parent.settings['profile'] = None

		self.getPrinterOptions()
		p = self.vprinter
		if p in self.printermap.keys():
			self.parent.settings['printer'] = p
		else:
			self.parent.settings['printer'] = None

	def configSlicer(self):
		self.getProfileOptions()
		
		dlg = CuraCfgDialog(self) 
		dlg.CenterOnScreen()
		val = dlg.ShowModal()
	
		if val != wx.ID_OK:
			dlg.Destroy()
			return False
		
		self.vprofile, self.vprinter, refreshFlag = dlg.getValues()
		dlg.Destroy()
		return self.updateSlicerCfg(refreshFlag)
		
	def configSlicerDirect(self, cfgopts):
		self.getProfileOptions()
		if len(cfgopts) != 2:
			return False, "incorrect number of parameters for configuring cura - 2 expected"

		err = False
		msg = ""
		if cfgopts[0] not in self.profilemap.keys():
			err = True
			msg += "invalid profile: %s " % cfgopts[0]
		if cfgopts[1] not in self.printermap.keys():
			err = True
			msg += "invalid printer: %s " % cfgopts[1]
			
		if err:
			return False, msg
		
		self.vprofile = cfgopts[0]
		self.vprinter = cfgopts[1]
		self.updateSlicerCfg(False)
		return True, "success"
		
	def updateSlicerCfg(self, refreshFlag):
		chg = refreshFlag
		if self.parent.settings['profile'] != self.vprofile:
			self.parent.settings['profile'] = self.vprofile
			chg = True
			
		if self.parent.settings['printer'] != self.vprinter:
			self.parent.settings['printer'] = self.vprinter
			chg = True
			
		if chg:
			self.parent.setModified()
			
		self.updatePrinterPreference()
			
		return chg
	
	def updatePrinterPreference(self):
		if self.vprinter not in self.printermap.keys():
			return
		
		n = self.printermap[self.vprinter][0]
		self.prefs.set(PREFSECTION, "active_machine", n)
		
		try:		
			cfp = open(self.prefFile, 'wb')
		except:
			self.log("Unable to open Cura preferences file %s for writing" % self.prefFile)
			return
		self.prefs.write(cfp)
		cfp.close()
		
	def getConfigString(self):
		return "(" + str(self.vprinter) + "/" + str(self.vprofile) + ")"
	
	def getDimensionInfo(self):
		try:
			d = os.path.expandvars(os.path.expanduser(self.parent.settings['profiledir']))
			fn = os.path.join(d, str(self.vprofile) + ".ini")
			l = list(open(fn))
			d0 = None
			d1 = None
			d2 = None
			d3 = None
			for s in l:
				if s.startswith("layer_height ="):
					lh = float(s[14:].strip())
				elif s.startswith("filament_diameter ="):
					dx = float(s[19:].strip())
					if dx != 0:
						d0 = dx
				elif s.startswith("filament_diameter2 ="):
					dx = float(s[20:].strip())
					if dx != 0:
						d1 = dx
				elif s.startswith("filament_diameter3 ="):
					dx = float(s[20:].strip())
					if dx != 0:
						d2 = dx
				elif s.startswith("filament_diameter4 ="):
					dx = float(s[20:].strip())
					if dx != 0:
						d3 = dx
						
			fd = []
			if d0:
				fd.append(d0)
				if d1:
					fd.append(d1)
					if d2:
						fd.append(d2)
						if d3:
							fd.append(d3)
	
			return lh, fd
		
		except:
			self.log("Unable to open/parse cura profile file ", fn)
			return None, None
	
	def buildSliceOutputFile(self, fn):
		return fn.split('.')[0] + ".gcode"
	
	def setOverrides(self, ovr):
		self.overrides = ovr.copy()
		
	def getOverrideHelpText(self):
		ht = {}
		ht["layerheight"] = "Used directly as cura's layer_height setting"
		ht["extrusionwidth"] = "Used directly as cura's wall_thickness setting"
		ht["infilldensity"] = "Used for cura's fill_density setting.  Values less than 1 are assumed as ratios and are scaled to a percentage"
		ht["temperature"] = "Maps to cura's print_temperature fields.  This may be a comma separated list of values each corresponding to the appropriate setting"
		ht["bedtemperature"] = "Used directly for cura's print_bed_temperature setting"
		ht["layer1temperature"] = " Unused in cura"
		ht["layer1bedtemperature"] = "Unused in cura"
		ht["printspeed"] = "Used directly as cura's print_speed setting"
		ht["print1speed"] = "Used directly as cura's bottom_layer_speed setting"
		ht["travelspeed"] = "Used directly as cura's travel_speed setting"
		ht["skirt"] = "Maps to cura's skirt_line_count setting.  Enable => 2, Disable => 0"
		ht["support"] = "Maps to cura's support setting.  Enable => Everywhere, Disable => None"
		ht["adhesion"] = "Used directly for cura's platform_adhesion setting.  None, Brim, or Raft"
		
		return ht
		
	def buildSliceCommand(self):
		s = self.parent.settings['command']
		
		if len(self.overrides.keys()) > 0:
			tfn = tempfile.NamedTemporaryFile(delete=False, suffix=".ini")
			fn = self.profilemap[self.parent.settings['profile']]
			ll = list(open(fn))
	
			tempOver = False		
			if 'temperature' in self.overrides.keys():
				tempOver = True
				temps = self.overrides['temperature'].split(',')
				
			for l in ll:
				if l.startswith("layer_height = "):
					if 'layerheight' in self.overrides.keys():
						nl = "layer_height = " + str(self.overrides['layerheight']) + "\n"
					else:
						nl = l.rstrip() + "\n"
						
				elif l.startswith("wall_thickness = "):
					if 'extrusionwidth' in self.overrides.keys():
						self.log("Using override value of %s for extrusion width as wall_thickness value" % self.overrides['extrusionwidth'])
						nl = "wall_thickness = " + str(self.overrides['extrusionwidth']) + "\n"
					else:
						nl = l.rstrip() + "\n"
						
				elif l.startswith("fill_density = "):
					if 'infilldensity' in self.overrides.keys():
						v = self.overrides['infilldensity']
						if v.endswith("%"):
							v = v[:-1]
						else:
							try:
								fv = float(v)
								if fv < 1.0:
									v = "%f" % (fv*100.0)
							except:
								self.log("Unable to parse infill density override value %s as a float - ignoring" % v)
								v = None
								
						if v is None:
							nl = l.rstrip() + "\n"
						else:
							nl = "fill_density = " + v + "\n"
					else:
						nl = l.rstrip() + "\n"
						
				elif l.startswith("print_bed_temperature = "):
					if 'bedtemperature' in self.overrides.keys():
						nl = "print_bed_temperature = " + str(self.overrides['bedtemperature']) + "\n"
					else:
						nl = l.rstrip() + "\n"
						
				elif l.startswith("print_temperature"):
					if tempOver:
						try:
							ix = int(l[17]) - 1
							prefix = l[:21]
						except:
							ix = 0
							prefix = l[:20]
						if ix < len(temps):
							nl = prefix + temps[ix] + "\n"
						else:
							nl = l.rstrip() + "\n"
					else:
						nl = l.rstrip() + "\n"
						
				elif l.startswith("skirt_line_count = "):
					if 'skirt' in self.overrides.keys():
						skv = 0
						if self.overrides['skirt'] == 'True':
							skv = 1
						nl = "skirt_line_count = %d\n" % skv
					else:
						nl = l.rstrip() + "\n"
						
				elif l.startswith("support = "):
					if 'support' in self.overrides.keys():
						res = "None"
						if self.overrides['support'] == 'True':
							res = "Everywhere"
						nl = "support = %s\n" % res
					else:
						nl = l.rstrip() + "\n"
						
				elif l.startswith("print_speed = "):
					if 'printspeed' in self.overrides.keys():
						nl = "print_speed = " + str(self.overrides['printspeed']) + "\n"
					else:
						nl = l.rstrip() + "\n"
						
				elif l.startswith("travel_speed = "):
					if 'travelspeed' in self.overrides.keys():
						nl = "travel_speed = " + str(self.overrides['travelspeed']) + "\n"
					else:
						nl = l.rstrip() + "\n"
						
				elif l.startswith("bottom_layer_speed = "):
					if 'print1speed' in self.overrides.keys():
						nl = "bottom_layer_speed = " + str(self.overrides['print1speed']) + "\n"
					else:
						nl = l.rstrip() + "\n"
						
				elif l.startswith("platform_adhesion = "):
					if 'adhesion' in self.overrides.keys():
						nl = "platform_adhesion = " + str(self.overrides['adhesion']) + "\n"
					else:
						nl = l.rstrip() + "\n"
						
				else:
					nl = l

				tfn.write(nl)
			
			tfn.close()
			self.tempFile = tfn.name
			self.parent.settings['configfile'] = tfn.name
		else:
			self.parent.settings['configfile'] = self.profilemap[self.parent.settings['profile']]

		return os.path.expandvars(os.path.expanduser(self.app.replace(s)))
	
	def sliceComplete(self):
		if self.tempFile is not None and not SAVE_SETTINGS_FILE:
			os.unlink(self.tempFile)
		self.tempFile = None
		del self.parent.settings['configfile']
			
	def getProfileOptions(self):
		self.profilemap = {}
		try:
			d = os.path.expandvars(os.path.expanduser(self.parent.settings['profiledir']))
			l = os.listdir(d)
		except:
			self.log("Unable to get listing from cura profile directory: " + self.parent.settings['profiledir'])
			return {}
		r = {}
		for f in sorted(l):
			bn, ext = os.path.splitext(f)
			if ext in [".ini", ".INI"]:
				p = os.path.join(d, f)
				r[bn] = p
				
		self.profilemap = r
		return r
			
	def getPrinterOptions(self):
		self.printermap = {}
		r = {}
		self.vxprinter = 0
		if self.prefs.has_option(PREFSECTION, 'active_machine'):
			self.vxprinter = self.prefs.getint(PREFSECTION, 'active_machine')
		for ix in range(5):
			section = "machine_%d" % ix
			if self.prefs.has_section(section):
				if self.prefs.has_option(section, 'machine_name'):
					name = self.prefs.get(section, 'machine_name')
				else:
					name = section
					
				if self.prefs.has_option(section, 'machine_width'):
					width = self.prefs.getint(section, 'machine_width')
				else:
					width = 200
					
				if self.prefs.has_option(section, 'machine_depth'):
					depth = self.prefs.getint(section, 'machine_depth')
				else:
					depth = 200
					
				r[name] = (ix, width, depth)
				
		self.printermap = r
		return r
