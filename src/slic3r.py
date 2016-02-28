import os, time, tempfile
import wx
import shlex, subprocess

from settings import BUTTONDIM, MAX_EXTRUDERS, SAVE_SETTINGS_FILE

BASE_ID = 500

def loadProfiles(fnames, mergeKeys):
	kdict = {}
	
	for fn in fnames:
		try:
			l = list(open(fn))
		except:
			print "Unable to open Slic3r settings file: %s" % fn
			return kdict
		
		for ln in l:
			if ln.startswith('#'):
				continue
			
			lw = ln.split('=')
			if len(lw) != 2:
				continue
			
			dkey = lw[0].strip()
			dval = lw[1].strip()
			if dkey in kdict.keys():
				if dkey in mergeKeys:
					kdict[dkey] += ',' + dval
			else:
				kdict[dkey] = dval
				
	return kdict

def checkTagInt(s, tag):
	if not s.startswith(tag):
		return None
	
	try:
		r = int(s[len(tag):].strip())
		return r
	except:
		return None

def checkTagList(s, tag):
	if not s.startswith(tag):
		return None
		
	r = s[len(tag):].strip().split(',')
	for i in range(len(r)):
		try:
			r[i] = int(r[i])
		except:
			return None
	return r

CBSIZE = 200

class Slic3rCfgDialog(wx.Dialog):
	def __init__(self, slicer):
		self.slicer = slicer
		self.app = slicer.app
		self.settings = slicer.parent.settings
		self.vprinter = self.settings['printer']
		self.printermap = slicer.printermap
		self.printerext = slicer.printerext
		self.nExtr = slicer.printerext[self.vprinter]
		self.vprint = self.settings['print']
		self.printmap = slicer.printmap
		self.vfilament = [i for i in self.settings['filament']]
		self.filmap = slicer.filmap
		self.refreshed = False
		
		pre = wx.PreDialog()
		pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
		pos = wx.DefaultPosition
		sz = wx.DefaultSize
		style = wx.DEFAULT_DIALOG_STYLE
		pre.Create(self.app, wx.ID_ANY, "Slic3r Profiles", pos, sz, style)
		self.PostCreate(pre)
		
		sizer = wx.BoxSizer(wx.VERTICAL)
				
		f = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		dc = wx.WindowDC(self)
		dc.SetFont(f)
		grid = wx.GridBagSizer(vgap=5, hgap=5)
		
		text = " Printer:"
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w,h))
		t.SetFont(f)
		grid.Add(t, pos=(0,0), flag=wx.ALIGN_CENTER)
		
		self.cbPrinter = wx.ComboBox(self, wx.ID_ANY, self.vprinter, 
			(-1, -1), (CBSIZE, -1), self.printermap.keys(), wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbPrinter.SetFont(f)
		self.cbPrinter.SetToolTipString("Choose which printer profile to use")
		grid.Add(self.cbPrinter, pos=(0,1))
		self.cbPrinter.SetStringSelection(self.vprinter)
		self.Bind(wx.EVT_COMBOBOX, self.doChoosePrinter, self.cbPrinter)
		
		text = " Profile:"
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w,h))
		t.SetFont(f)
		grid.Add(t, pos=(0,2), flag=wx.ALIGN_CENTER)
	
		self.cbPrint = wx.ComboBox(self, wx.ID_ANY, self.vprint,
 			(-1, -1), (CBSIZE, -1), self.printmap.keys(), wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbPrint.SetFont(f)
		self.cbPrint.SetToolTipString("Choose which print profile to use")
		grid.Add(self.cbPrint, pos=(0,3))
		self.cbPrint.SetStringSelection(self.vprint)
		self.Bind(wx.EVT_COMBOBOX, self.doChoosePrint, self.cbPrint)
		
		text = " Filament:"
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w,h))
		t.SetFont(f)
		grid.Add(t, pos=(0,4), flag=wx.ALIGN_CENTER)

		self.cbFilament = []
		for i in range(MAX_EXTRUDERS):
			if i < self.nExtr:
				v = self.vfilament[i]
			else:
				v = self.filmap.keys()[0]
			cb = wx.ComboBox(self, BASE_ID+i, v,
 				(-1, -1), (CBSIZE, -1), self.filmap.keys(), wx.CB_DROPDOWN | wx.CB_READONLY)
			cb.SetFont(f)
			cb.SetToolTipString("Choose which filament profile to use")
			grid.Add(cb, pos=(i, 5))
			self.Bind(wx.EVT_COMBOBOX, self.doChooseFilament, cb)
			if i < self.nExtr:
				cb.SetStringSelection(self.vfilament[i])
				cb.Enable(True)
			else:
				cb.Enable(False)
			self.cbFilament.append(cb)

		sizer.Add(grid, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		
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
		
		self.printermap = self.slicer.printermap
		self.printerext = self.slicer.printerext
		self.printmap = self.slicer.printmap
		self.filmap = self.slicer.filmap

		if self.vprinter not in self.printermap.keys():
			self.vprinter = self.printermap.keys()[0]
			
		self.nExtr = self.printerext[self.vprinter]
		
		if self.vprint not in self.printmap.keys():
			self.vprint = self.printmap.keys()[0]
			
		dftFil = self.filmap.keys()[0]
		for i in range(len(self.vfilament)):
			if self.vfilament[i] not in self.filmap.keys():
				self.vfilament[i] = dftFil
				
		self.cbPrinter.SetItems(self.printermap.keys())
		self.cbPrinter.SetStringSelection(self.vprinter)
		
		self.cbPrint.SetItems(self.printmap.keys())
		self.cbPrint.SetStringSelection(self.vprint)
		
		for i in range(len(self.cbFilament)):
			self.cbFilament[i].SetItems(self.filmap.keys())
			if i < self.nExtr:
				self.cbFilament[i].SetStringSelection(self.vfilament[i])
				self.cbFilament[i].Enable(True)
			else:
				self.cbFilament[i].SetStringSelection(dftFil)
				self.cbFilament[i].Enable(False)
	
	def getValues(self):
		return [self.vprinter, self.vprint, self.vfilament, self.refreshed]
		
	def doChoosePrinter(self, evt):
		oldNExtr = self.printerext[self.vprinter]
		self.vprinter = self.cbPrinter.GetValue()
		self.nExtr = self.printerext[self.vprinter]
		
		for i in range(MAX_EXTRUDERS):
			self.cbFilament[i].Enable(i<self.nExtr)
			if i >= oldNExtr:
				self.vfilament.append(self.filmap.keys()[0])

		self.vfilament = self.vfilament[:self.nExtr]

	def doChoosePrint(self, evt):
		self.vprint = self.cbPrint.GetValue()
		
	def doChooseFilament(self, evt):
		myId = evt.GetId() - BASE_ID
		if myId < 0 or myId > 2:
			return

		self.vfilament[myId] = self.cbFilament[myId].GetValue()
	
class Slic3r:
	def __init__(self, app, parent):
		self.app = app
		self.parent = parent
		self.overrides = {}
		self.logger = None

	def setLogger(self, logger):
		self.logger = logger
		
	def log(self, msg):
		if self.logger:
			self.logger.LogMessage(msg)
		else:
			print msg

	def fileTypes(self):
		return "all (*stl, *amf.xml)|*.stl;*.STL;*.amf.xml;*.AMF.XML|" \
			"STL (*.stl)|*.stl;*.STL|" \
			"AMF XML files|*.amf.xml;*.AMF.XML"
		
	def getSettingsKeys(self):
		return ['profiledir', 'print', 'printfile', 'printer', 'printerfile', 'command', 'config'], ['filament', 'filamentfile']
		
	def initialize(self, flag=False):
		if flag:
			self.vprinter = self.parent.settings['printer']
			self.vprint = self.parent.settings['print']
			self.vfilament = [f for f in self.parent.settings['filament']]
			
		self.getPrintOptions()
		self.tempFile = None
		p = self.vprint
		if p in self.printmap.keys():
			self.parent.settings['printfile'] = self.printmap[p]
		else:
			self.parent.settings['printfile'] = None

		self.getFilamentOptions()		
		fl = []
		for p in self.vfilament:
			if p in self.filmap.keys():
				fl.append(self.filmap[p])
			else:
				fl.append(None)
		self.parent.settings['filamentfile'] = fl

		self.getPrinterOptions()		
		p = self.vprinter
		if p in self.printermap.keys():
			self.parent.settings['printerfile'] = self.printermap[p]
		else:
			self.parent.settings['printerfile'] = None
			
	def configSlicer(self):
		self.getPrintOptions()
		self.getPrinterOptions()
		self.getFilamentOptions()
			
		oldNExtr = self.printerext[self.parent.settings['printer']]
		
		dlg = Slic3rCfgDialog(self) #self.app, self.parent.settings, self.printermap, self.printerext,
					#self.printmap, self.filmap)
		dlg.CenterOnScreen()
		val = dlg.ShowModal()
	
		if val != wx.ID_OK:
			dlg.Destroy()
			return False
		
		self.vprinter, self.vprint, self.vfilament, refreshFlag = dlg.getValues()
		dlg.Destroy()
		return self.updateSlicerCfg(refreshFlag, oldNExtr)
		
	def configSlicerDirect(self, cfgopts):
		self.getPrintOptions()
		self.getPrinterOptions()
		self.getFilamentOptions()
		
		if len(cfgopts) == 0 or len(cfgopts) > 3:
			return False, "incorrect number of parameters for configuring slic3r - 1, 2, or 3 expected: printer[/print[/filament[,filament]]]"

		err = False
		msg = ""
		if cfgopts[0] != "" and cfgopts[0] not in self.printermap.keys():
			err = True
			msg += "invalid printer: %s " % cfgopts[0]
		if len(cfgopts) > 1:
			if cfgopts[1] != "" and cfgopts[1] not in self.printmap.keys():
				err = True
				msg += "invalid print: %s " % cfgopts[1]
		if len(cfgopts) > 2:
			if cfgopts[2] != "":
				fl = cfgopts[2]
				if not isinstance(fl, list):
					fl = [ fl ]
				for f in fl:
					if f not in self.filmap.keys():
						err = True
						msg += "invalid filament: %s " % f
			
		if err:
			return False, msg

		oldNExtr = self.printerext[self.parent.settings['printer']]
		if cfgopts[0] != "":
			self.vprinter = cfgopts[0]
		if len(cfgopts) > 1 and cfgopts[1] != "":
			self.vprint = cfgopts[1]
		if len(cfgopts) > 2 and cfgopts[2] != "":
			self.vfilament = fl
			
		self.updateSlicerCfg(False, oldNExtr)
		return True, "success"
		
	def updateSlicerCfg(self, refreshFlag, oldNExtr):
		chg = refreshFlag
		if self.parent.settings['print'] != self.vprint:
			self.parent.settings['print'] = self.vprint
			if self.vprint in self.printmap.keys():
				self.parent.settings['printfile'] = self.printmap[self.vprint]
			else:
				self.parent.settings['printfile'] = None
			chg = True

		if self.parent.settings['printer'] != self.vprinter:
			self.parent.settings['printer'] = self.vprinter
			if self.vprinter in self.printermap.keys():
				self.parent.settings['printerfile'] = self.printermap[self.vprinter]
			else:
				self.parent.settings['printerfile'] = None
			chg = True
		
		if self.vprinter in self.printerext.keys():
			nExtr = self.printerext[self.vprinter]
			if nExtr > oldNExtr:
				a = ["" for i in range(nExtr - oldNExtr)]
				self.parent.settings['filament'].extend(a)
				self.parent.settings['filamentfile'].extend(a)
			for i in range(MAX_EXTRUDERS):
				if i < nExtr:
					if self.parent.settings['filament'][i] != self.vfilament[i]:
						self.parent.settings['filament'][i] = self.vfilament[i]
						if self.vfilament[i] in self.filmap.keys():
							self.parent.settings['filamentfile'][i] = self.filmap[self.vfilament[i]]
						else:
							self.parent.settings['filamentfile'][i] = None
						chg = True
			self.parent.settings['filament'] = self.parent.settings['filament'][:nExtr]	
			self.parent.settings['filamentfile'] = self.parent.settings['filamentfile'][:nExtr]	
			
		if chg:
			self.parent.setModified()
			
		return chg
		
	def getConfigString(self):
		return "(" + str(self.vprinter) + "/" + str(self.vprint) + "/" + ",".join(self.vfilament) + ")"
	
	def getDimensionInfo(self):
		dProfile = {}
		if 'printfile' in self.parent.settings.keys():
			dProfile.update(loadProfiles([self.parent.settings['printfile']], []))
		if 'filamentfile' in self.parent.settings.keys():
			dProfile.update(loadProfiles(self.parent.settings['filamentfile'], 
					['extrusion_multiplier', 'filament_diameter', 'first_layer_temperature', 'temperature']))
		for k in self.overrides.keys():
			if k == 'layerheight':
				dProfile['layer_height'] = self.overrides[k]
			elif k == 'filamentdiam':
				dProfile['filament_diameter'] = self.verifyListLength('filament diameter', self.overrides[k], dProfile['filament_diameter'])
		if 'layer_height' in dProfile.keys() and 'filament_diameter' in dProfile.keys():
			return float(dProfile['layer_height']), [float(x) for x in dProfile['filament_diameter'].split(',')]
		else:
			self.log("Unable to find dimension information in slicer profile files")
			return None, None
	
	def getTempProfile(self):
		dProfile = {}
		if 'filamentfile' in self.parent.settings.keys():
			dProfile.update(loadProfiles(self.parent.settings['filamentfile'], 
					['extrusion_multiplier', 'filament_diameter', 'first_layer_temperature', 'temperature']))
		for k in self.overrides.keys():
			if k == 'temperature':
				dProfile['temperature'] = self.overrides[k]
			if k == 'layer1temperature':
				dProfile['first_layer_temperature'] = self.overrides[k]
			if k == 'bedtemperature':
				dProfile['bed_temperature'] = self.overrides[k]
			if k == 'layer1bedtemperature':
				dProfile['first_layer_bed_temperature'] = self.overrides[k]
		if 'first_layer_bed_temperature' in dProfile.keys() and 'bed_temperature' in dProfile.keys():
			bt = [float(dProfile['first_layer_bed_temperature']), float(dProfile['bed_temperature'])]
		elif 'bed_temperature' in dProfile.keys():
			bt = [float(dProfile['bed_temperature']), float(dProfile['bed_temperature'])]
		else:
			bt = None
			
		flhet = []
		het = []
		if 'first_layer_temperature' in dProfile.keys():
			flhet = [float(x) for x in dProfile['first_layer_temperature'].split(',')]
		if  'temperature' in dProfile.keys():
			het = [float(x) for x in dProfile['temperature'].split(',')]
			
		rhe = []
		for i in range(MAX_EXTRUDERS):
			if i >= len(het):
				rhe.append(None)
			elif i>= len(flhet):
				rhe.append([het[i], het[i]])
			else:
				rhe.append([flhet[i], het[i]])
			
		return bt, rhe
	
	def buildSliceOutputFile(self, fn):
		return fn.split('.')[0] + ".gcode"

	def setOverrides(self, ovr):
		self.overrides = ovr.copy()
		
	def buildSliceCommand(self):
		s = self.parent.settings['command']
		if self.tempFile is not None:
			os.unlink(self.tempFile)
	
		self.mergeProfiles()
		self.parent.settings['configfile'] = self.tempFile
		return os.path.expandvars(os.path.expanduser(self.app.replace(s)))
	
	def getOverrideHelpText(self):
		ht = {}
		ht["filamentdiam"] = "Filament diameter (list)"
		ht["extrusionmult"] = "Extrusion Multiplier (list)"
		ht["layerheight"] = "Used directly as slic3r's layer_height setting"
		ht["extrusionwidth"] = "Used directly as slic3r's extrusion_width setting.  May end with a %"
		ht["infilldensity"] = "Used directly as slic3r's fill_density setting"
		ht["temperature"] = "Used directly as slic3r's temperature setting (list)"
		ht["bedtemperature"] = "Used directly as slic3r's bed_temperature setting"
		ht["layer1temperature"] = "Used directly as slic3r's first_layer_temperature setting (list)"
		ht["layer1bedtemperature"] = "Used directly as slic3r's first_layer_bed_temperature setting"
		ht["printspeed"] = "Used directly as slic3r's perimeter_speed, infill_speed, and solid_infill_speed settings"
		ht["print1speed"] = "Used directly as slic3r's first_layer_speed setting"
		ht["travelspeed"] = "Used directly as slic3r's travel_speed setting"
		ht["skirt"] = "Maps directly to slic3r's skirt setting.  Enable => 2, Disable => 0"
		ht["skirtheight"] = "Used directly as slic3r's skirt height setting."
		ht["support"] = "Maps directly to slic3r's support_material setting.  Enable => 1, Disable => 0"
		ht["adhesion"] = "Chooses between no raft or brim, brim_width=3, and raft_layers=2"
		
		return ht
	
	def mergeProfiles(self):
		dProfile = {}
		if 'printfile' in self.parent.settings.keys():
			dProfile.update(loadProfiles([self.parent.settings['printfile']], []))
		if 'printerfile' in self.parent.settings.keys():
			dProfile.update(loadProfiles([self.parent.settings['printerfile']], []))
		if 'filamentfile' in self.parent.settings.keys():
			dProfile.update(loadProfiles(self.parent.settings['filamentfile'], 
					['extrusion_multiplier', 'filament_diameter', 'first_layer_temperature', 'temperature']))
	
		tfn = tempfile.NamedTemporaryFile(delete=False)
		
		# apply overrides
		for k in self.overrides.keys():
			if k == 'filamentdiam':
				dProfile['filament_diameter'] = self.verifyListLength('filament diameter', self.overrides[k], dProfile['filament_diameter'])
				self.log("Override: filament_diameter = " + dProfile['filament_diameter'])
				
			elif k == 'extrusionmult':
				dProfile['extrusion_multiplier'] = self.verifyListLength('extrusion multiplier', self.overrides[k], dProfile['extrusion_multiplier'])
				self.log("Override: extrusion_multiplier = " + dProfile['extrusion_multiplier'])
				
			elif k == 'layerheight':
				dProfile['layer_height'] = self.overrides[k]
				self.log("Override: layer_height = " + dProfile['layer_height'])
				
			elif k == 'extrusionwidth':
				v = self.overrides[k]
				if not v.endswith("%"):
					try:
						float(v)
					except:
						self.log("Unable to parse (%s) as a float - ignoring" % v)
						v = None
					
				if v is not None:
					dProfile['extrusion_width'] = v
					self.log("Override: extrusion_width = " + dProfile['extrusion_width'])
				
			elif k == 'infilldensity':
				dProfile['fill_density'] = self.overrides[k]
				self.log("Override: fill_density = " + dProfile['fill_density'])
			
			elif k == 'bedtemperature':
				dProfile['bed_temperature'] = self.overrides[k]
				self.log("Override: bed_temperature = " + dProfile['bed_temperature'])
			elif k == 'layer1bedtemperature':
				dProfile['first_layer_bed_temperature'] = self.overrides[k]
				self.log("Override: first_layer_bed_temperature = " + dProfile['first_layer_bed_temperature'])
				
			elif k == 'printspeed':
				dProfile['perimeter_speed'] = self.overrides[k]
				dProfile['infill_speed'] = self.overrides[k]
				dProfile['solid_infill_speed'] = self.overrides[k]
				self.log("Override: perimeter_speed = " + dProfile['perimeter_speed'])
				self.log("Override: infill_speed = " + dProfile['infill_speed'])
				self.log("Override: solid_infill_speed = " + dProfile['solid_infill_speed'])
				
			elif k == 'print1speed':
				dProfile['first_layer_speed'] = self.overrides[k]
				self.log("Override: first_layer_speed = " + dProfile['first_layer_speed'])

			elif k == 'travelspeed':
				dProfile['travel_speed'] = self.overrides[k]
				self.log("Override: travel_speed = " + dProfile['travel_speed'])
				
			elif k == 'temperature':
				dProfile['temperature'] = self.verifyListLength('temperature', self.overrides[k], dProfile['temperature'])
				self.log("Override: temperature = " + dProfile['temperature'])
				
			elif k == 'layer1temperature':
				dProfile['first_layer_temperature'] = self.verifyListLength('first layer temperature', self.overrides[k], dProfile['first_layer_temperature'])
				self.log("Override: first_layer_temperature = " + dProfile['first_layer_temperature'])
				
			elif k == 'skirt':
				if self.overrides[k] == "True":
					dProfile['skirts'] = '2'
				else:
					dProfile['skirts'] = '0'
				self.log("Override: skirts = " + dProfile['skirts'])
				
			elif k == 'skirtheight':
				dProfile['skirt_height'] = self.overrides[k]
				self.log("Override: skirt height = " + dProfile['skirtheight'])
				
			elif k == 'support':
				if self.overrides[k] == "True":
					dProfile['support_material'] = '1'
				else:
					dProfile['support_material'] = '0'
				self.log("Override: support_material = " + dProfile['support_material'])
					
			elif k == 'adhesion':
				if self.overrides[k] == 'Brim':
					dProfile['brim_width'] = '3'
					dProfile['raft_layers'] = '0'
				elif self.overrides[k] == 'Raft':
					dProfile['brim_width'] = '0'
					dProfile['raft_layers'] = '2'
				else:
					dProfile['brim_width'] = '0'
					dProfile['raft_layers'] = '0'
				self.log("Override: brim_width = " + dProfile['brim_width'])
				self.log("Override: raft_layers = " + dProfile['raft_layers'])
				
	
		s = "# generated by reprapnb on " + time.strftime("%c", time.localtime()) + "\n"
		tfn.write(s)
		for k in sorted(dProfile.keys()):
			tfn.write(k + " = " + dProfile[k] + "\n")
		
		tfn.close()
		self.tempFile = tfn.name
		self.parent.settings['configfile'] = tfn.name
		
	def verifyListLength(self, field, newList, currentList):
		nl = newList.split(',')
		cl = currentList.split(',')
		
		if len(nl) == len(cl):
			return newList
		
		self.log("List length mismatch over-riding %s" % field)
		self.log("original list has %d values (%s)" % (len(currentList), currentList))
		self.log("override list has %d values (%s)" % (len(newList), newList))
		if len(nl) < len(cl):
			self.log("not enough override values - using corresponding values from current list")
		else:
			self.log("too many override values specified - ignoring extra")
			
		rl = []
		for i in range(len(cl)):
			if i <= len(nl):
				rl.append(nl[i])
			else:
				rl.append(cl[i])
		rs = ','.join(rl)
		
		self.log("resulting list: %s" % rs)
		return rs
		
	
	def sliceComplete(self):
		if self.tempFile is not None and not SAVE_SETTINGS_FILE:
			os.unlink(self.tempFile)
		self.tempFile = None
		del self.parent.settings['configfile']
		
	def getPrintOptions(self):
		self.printmap = {}
		try:
			pdir = os.path.expandvars(os.path.expanduser(self.parent.settings['profiledir'] + os.path.sep + "print"))
			l = os.listdir(pdir)
		except:
			self.log("Unable to get print profiles from slic3r profile directory: " + self.parent.settings['profiledir'])
			return {}
		r = {}
		for f in sorted(l):
			if not os.path.isdir(f) and f.lower().endswith(".ini"):
				r[os.path.splitext(os.path.basename(f))[0]] = os.path.join(pdir, f)
		self.printmap = r
		return r
			
	def getFilamentOptions(self):
		self.filmap = {}
		try:
			pdir = os.path.expandvars(os.path.expanduser(self.parent.settings['profiledir'] + os.path.sep + "filament"))
			l = os.listdir(pdir)
		except:
			self.log("Unable to get filament profiles from slic3r profile directory: " + self.parent.settings['profiledir'])
			return {}
		r = {}
		for f in sorted(l):
			if not os.path.isdir(f) and f.lower().endswith(".ini"):
				r[os.path.splitext(os.path.basename(f))[0]] = os.path.join(pdir, f)
		self.filmap = r
		return r
			
	def getPrinterOptions(self):
		self.printermap = {}
		self.printerext = {}
		try:
			pdir = os.path.expandvars(os.path.expanduser(self.parent.settings['profiledir'] + os.path.sep + "printer"))
			l = os.listdir(pdir)
		except:
			self.log("Unable to get printer profiles from slic3r profile directory: " + self.parent.settings['profiledir'])
			return {}
		
		r = {}
		for f in sorted(l):
			if not os.path.isdir(f) and f.lower().endswith(".ini"):
				fn = os.path.join(pdir, f)
				k = os.path.splitext(os.path.basename(f))[0]
				r[k] = fn
				
				try:
					idata = list(open(fn))
				except:
					self.log("Unable to open printer settings file" % fn)
					idata = []
			
				for i in idata:
					a = checkTagList(i, "retract_speed = ")
					if a is not None:
						self.printerext[k] = len(a)
				
		self.printermap = r
		return r
