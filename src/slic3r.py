'''
Created on Jun 20, 2013

@author: ejefber
'''
import os, time, tempfile
import wx
import shlex, subprocess
from reprap import MAX_EXTRUDERS

BUTTONDIM = (48, 48)

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
		return "(" + str(self.vprinter) + "/" + str(self.vprint) + "/" + "-".join(self.vfilament) + ")"
		
	def getSlicerParameters(self):
		heTemps = []
		bedTemp = None
		fl = self.parent.settings['filamentfile']
		for fn in fl:
			if fn is not None:
				try:
					idata = list(open(fn))
				except:
					print "Unable to open Slic3r filament file %s" % fn
					idata = []
			
				for i in idata:
					a = checkTagInt(i, "first_layer_temperature = ")
					if a is not None:
						heTemps.append(a)
					else:
						a = checkTagInt(i, "first_layer_bed_temperature = ")
						if a is not None:
							bedTemp = a
	
		bedSize = None
		nExtruders = None
		f = self.parent.settings['printerfile']
		if f is not None:
			try:
				idata = list(open(f))
			except:
				print "Unable to open Slic3r printer file %s" % f
				idata = []
			
		for i in idata:
			a = checkTagList(i, "bed_size = ")
			if a is not None:
				bedSize = a
			else:
				a = checkTagList(i, "retract_speed = ")
				if a is not None:
					nExtruders = len(a)
		
		if bedSize is None:
			bedSize = [200, 200]
			
		if nExtruders is None or nExtruders < 1:
			nExtruders = 1
		
		if len(heTemps) < nExtruders:
			x = nExtruders-len(heTemps)
			for i in range(x):
				heTemps.append(185)
		
		return [bedSize, nExtruders, heTemps, bedTemp]
	
	def buildSliceOutputFile(self, fn):
		return fn.split('.')[0] + ".gcode"
		
	def buildSliceCommand(self):
		s = self.parent.settings['command']
		if self.tempFile is not None:
			os.unlink(self.tempFile)
	
		self.mergeProfiles()
		self.parent.settings['configfile'] = self.tempFile
		return os.path.expandvars(os.path.expanduser(self.app.replace(s)))
	
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
	
		s = "# generated by reprapnb on " + time.strftime("%c", time.localtime()) + "\n"
		tfn.write(s)
		for k in sorted(dProfile.keys()):
			tfn.write(k + " = " + dProfile[k] + "\n")
		
		tfn.close()
		self.tempFile = tfn.name
		self.parent.settings['configfile'] = tfn.name
	
	def sliceComplete(self):
		if self.tempFile is not None:
			os.unlink(self.tempFile)
		self.tempFile = None
		del self.parent.settings['configfile']
		
	def getPrintOptions(self):
		self.printmap = {}
		try:
			pdir = os.path.expandvars(os.path.expanduser(self.parent.settings['profiledir'] + os.path.sep + "print"))
			l = os.listdir(pdir)
		except:
			print "Unable to get print profiles from slic3r profile directory: " + self.parent.settings['profiledir']
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
			print "Unable to get filament profiles from slic3r profile directory: " + self.parent.settings['profiledir']
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
			print "Unable to get printer profiles from slic3r profile directory: " + self.parent.settings['profiledir']
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
					print "Unable to open printer settings file" % fn
					idata = []
			
				for i in idata:
					a = checkTagList(i, "retract_speed = ")
					if a is not None:
						self.printerext[k] = len(a)
				
		self.printermap = r
		return r