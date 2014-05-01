import os
import wx
import shlex, subprocess
import ConfigParser

from settings import BUTTONDIM

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
			print "Cura preferences file %s does not exist.  Using default values" % self.prefFile
		
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
			print "Unable to open Cura preferences file %s for writing" % self.prefFile
			return
		self.prefs.write(cfp)
		cfp.close()
		
	def getConfigString(self):
		return "(" + str(self.vprinter) + "/" + str(self.vprofile) + ")"
	
	def getDimensionInfo(self):
		try:
			d = os.path.expandvars(os.path.expanduser(self.parent.settings['profiledir']))
			fn = os.path.join(d, str(self.vprofile))
			l = list(open(fn))
			d0 = None
			d1 = None
			d2 = None
			d3 = None
			for s in l:
				if s.startswith("layer_height ="):
					lh = float(s[14:].strip())
				elif s.startswith("filament_diameter ="):
					dx = int(s[19:].strip())
					if dx != 0:
						d0 = dx
				elif s.startswith("filament_diameter2 ="):
					dx = int(s[20:].strip())
					if dx != 0:
						d1 = dx
				elif s.startswith("filament_diameter3 ="):
					dx = int(s[20:].strip())
					if dx != 0:
						d2 = dx
				elif s.startswith("filament_diameter4 ="):
					dx = int(s[20:].strip())
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
	
			print "Cura get dimensions returns ", lh, fd						
			return lh, fd
		
		except:
			print "Unable to open/parse cura profile file ", fn
			return None, None
	
	def buildSliceOutputFile(self, fn):
		return fn.split('.')[0] + ".gcode"
		
	def buildSliceCommand(self):
		s = self.parent.settings['command']
		self.parent.settings['configfile'] = self.profilemap[self.parent.settings['profile']]
		return os.path.expandvars(os.path.expanduser(self.app.replace(s)))
	
	def sliceComplete(self):
		pass
			
	def getProfileOptions(self):
		self.profilemap = {}
		try:
			d = os.path.expandvars(os.path.expanduser(self.parent.settings['profiledir']))
			l = os.listdir(d)
		except:
			print "Unable to get listing from cura profile directory: " + self.parent.settings['profiledir']
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
