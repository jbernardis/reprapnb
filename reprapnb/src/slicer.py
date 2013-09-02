'''
Created on Jun 20, 2013

@author: ejefber
'''
import os, time, tempfile
import wx

BASE_ID = 500

def createSlicerObject(name, app, parent):
	if name == 'slic3r':
		return Slic3r(app, parent)
	
	return None

def loadProfiles(fnames, mergeKeys):
	kdict = {}
	
	for fn in fnames:
		l = list(open(fn))
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

#FIXIT - work with slic3r ini files - 3 files	
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

class Slic3rCfgDialog(wx.Dialog):
	def __init__(self, parent, vprinter, printers, extCount, vprint, prints, vfilament, filaments):
		self.parent = parent
		self.vprinter = vprinter
		self.printers = printers
		self.extCount = extCount
		self.nExtr = extCount[vprinter]
		self.vprint = vprint
		self.prints = prints
		self.vfilament = vfilament
		self.filaments = filaments
		
		pre = wx.PreDialog()
		pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
		pos = wx.DefaultPosition
		sz = wx.DefaultSize
		style = wx.DEFAULT_DIALOG_STYLE
		pre.Create(parent, wx.ID_ANY, "Slic3r Profiles", pos, sz, style)
		self.PostCreate(pre)
		
		sizer = wx.BoxSizer(wx.VERTICAL)

		label = wx.StaticText(self, -1, "Choose settings for Slic3r")
		sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

		box = wx.BoxSizer(wx.HORIZONTAL)



		f = wx.Font(12, wx.SWISS, wx.BOLD, wx.NORMAL)
		dc = wx.WindowDC(self)
		dc.SetFont(f)
		
		text = " Printer:"
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(box, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w,h))
		t.SetFont(f)
		box.Add(t)
		
		self.cbPrinter = wx.ComboBox(box, wx.ID_ANY, self.vprinter, 
			(-1, -1), (100, -1), self.printers.keys(), wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbPrinter.SetFont(f)
		self.cbPrinter.SetToolTipString("Choose which printer profile to use")
		box.Add(self.cbPrinter)
		self.cbPrinter.SetStringSelection(self.vprinter)
		self.Bind(wx.EVT_COMBOBOX, self.doChoosePrinter, self.cbPrinter)
		
		text = " Profile:"
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(box, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w,h))
		t.SetFont(f)
		box.Add(t)
	
		self.cbProfile = wx.ComboBox(box, wx.ID_ANY, self.vprint,
 			(-1, -1), (120, -1), self.prints.keys(), wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbProfile.SetFont(f)
		self.cbProfile.SetToolTipString("Choose which print profile to use")
		box.Add(self.cbProfile)
		self.cbProfile.SetStringSelection(self.vprint)
		self.Bind(wx.EVT_COMBOBOX, self.doChooseProfile, self.cbProfile)
		
		text = " Filament:"
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(box, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w,h))
		t.SetFont(f)
		box.Add(t)

		self.cbFilament = []
		for i in range(3):
			if i < self.nExtr:
				v = self.vfilament[0]
			else:
				v = self.filaments.keys()[0]
			cb = wx.ComboBox(box, BASE_ID+i, v,
 				(-1, -1), (120, -1), self.filaments.keys(), wx.CB_DROPDOWN | wx.CB_READONLY)
			cb.SetFont(f)
			cb.SetToolTipString("Choose which filament profile to use")
			box.Add(cb)
			self.Bind(wx.EVT_COMBOBOX, self.doChooseFilament, cb)
			if i < self.nExtr:
				cb.SetStringSelection(self.vfilament[i])
				cb.Enable(True)
			else:
				cb.Enable(False)
			self.cbFilament.append(cb)

		sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		
		btnsizer = wx.StdDialogButtonSizer()
		
		btn = wx.Button(self, wx.ID_OK)
		btn.SetDefault()
		btnsizer.AddButton(btn)
		
		btn = wx.Button(self, wx.ID_CANCEL)
		btnsizer.AddButton(btn)
		btnsizer.Realize()

		sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

		self.SetSizer(sizer)
		sizer.Fit(self)
		
	def getValues(self):
		return [self.vprinter, self.vprint, self.vfilament]
		
	def doChoosePrinter(self, evt):
		self.vprinter = self.cbPrinter.GetValue()
		self.nExtr = self.extCount[self.vprinter]
		
		for i in range(3):
			self.cbFilament[i].Enable(i<self.nExtr)

	def doChoosePrint(self, evt):
		self.vprint = self.cbPrint.GetValue()
		
	def doChooseFilament(self, evt):
		myId = evt.GetId() - BASE_ID
		if myId < 0 or myId > 2:
			print "ID out of range"
			return
		
		self.vfilament[myId] = self.cbFilament.GetValue()

	
class Slic3r:
	def __init__(self, app, parent):
		self.app = app
		self.logger = self.app.logger
		self.parent = parent
		self.getPrintOptions()
		self.tempFile = None
		p = self.parent.settings['print']
		if p in self.printmap.keys():
			self.parent.settings['printfile'] = self.printmap[p]
		else:
			self.parent.settings['printfile'] = None

		self.getFilamentOptions()		
		pl = self.parent.settings['filament'].split(',')
		fl = []
		for p in pl:
			if p in self.filmap.keys():
				fl.append(self.filmap[p])
			else:
				fl.append(None)
		self.parent.settings['filamentfile'] = fl

		self.getPrinterOptions()		
		p = self.parent.settings['printer']
		if p in self.printermap.keys():
			self.parent.settings['printerfile'] = self.printermap[p]
		else:
			self.parent.settings['printerfile'] = None
			
	def configSlicer(self):
		self.getPrintOptions()
		self.getPrinterOptions()
		self.getFilamentOptions()
		
		dlg = Slic3rCfgDialog(self, self.parent.settings['printer'], self.printermap, self.printerext,
								self.parent.settings['print'], self.printmap,
								self.parent.settings['filament'], self.filmap)
		dlg.CenterOnScreen()
		val = dlg.ShowModal()
	
		if val != wx.ID_OK:
			dlg.Destroy()
			return False
		
		vprinter, vprint, vfilament = dlg.getValues()
		dlg.Destroy()

		chg = False
		if self.parent.settings['print'] != vprint:
			self.parent.settings['print'] = vprint
			if vprint in self.printmap.keys():
				self.parent.settings['printfile'] = self.printmap[vprint]
			else:
				self.parent.settings['printfile'] = None
			chg = True

		if self.parent.settings['printer'] != vprinter:
			self.parent.settings['printer'] = vprinter
			if vprinter in self.printermap.keys():
				self.parent.settings['printerfile'] = self.printermap[vprinter]
			else:
				self.parent.settings['printerfile'] = None
			chg = True

		for i in range(3):
			if i < self.nExtr:
				if self.parent.settings['filament'][i] != vfilament[i]:
					self.parent.settings['filament'][i] = vfilament[i]
					if vfilament[i] in self.filamentmap.keys():
						self.parent.settings['filamentfile'][i] = self.filamentmap[vfilament[i]]
					else:
						self.parent.settings['filamentfile'][i] = None
					chg = True
			
		if chg:
			self.parent.setModified()
			
		return chg
		
	def getConfigString(self):
		return str(self.vprinter) + "/" + str(self.vprint) + "/" + "-".join(self.vfilament)
		
	def getSlicerParameters(self):
		heTemps = []
		bedTemps = []
		fl = self.parent.settings['filamentfile']
		for fn in fl:
			if fn is not None:
				idata = list(open(fn))
			
				for i in idata:
					a = checkTagInt(i, "first_layer_temperature = ")
					if a is not None:
						heTemps.append(a)
					else:
						a = checkTagInt(i, "first_layer_bed_temperature = ")
						if a is not None:
							bedTemps.append(a)
	
		bedSize = None
		nExtruders = None
		f = self.parent.settings['printerfile']
		if f is not None:
			idata = list(open(f))
			
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
		
		if len(bedTemps) < nExtruders:
			x = nExtruders-len(bedTemps)
			for i in range(x):
				bedTemps.append(60)
			
		return [bedSize, nExtruders, heTemps, bedTemps]
	
	def buildSliceOutputFile(self, fn):
		return fn.replace(".stl", ".gcode")
		
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
					['filament_diameter', 'first_layer_temperature', 'temperature']))
	
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
			self.logger.LogError("Unable to get print profiles from slic3r profile directory: " + self.parent.settings['profiledir'])
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
			self.logger.LogError("Unable to get filament profiles from slic3r profile directory: " + self.parent.settings['profiledir'])
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
			self.logger.LogError("Unable to get printer profiles from slic3r profile directory: " + self.parent.settings['profiledir'])
			return {}
		
		r = {}
		for f in sorted(l):
			if not os.path.isdir(f) and f.lower().endswith(".ini"):
				fn = os.path.join(pdir, f)
				k = os.path.splitext(os.path.basename(f))[0]
				r[k] = fn
				
				idata = list(open(fn))
			
				for i in idata:
					a = checkTagList(i, "retract_speed = ")
					if a is not None:
						self.printerext[k] = len(a)
				
		self.printermap = r
		return r