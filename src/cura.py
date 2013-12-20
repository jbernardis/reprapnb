'''
Created on Jun 20, 2013

@author: ejefber
'''
import os
import wx
import shlex, subprocess
import ConfigParser

BUTTONDIM = (48, 48)
CBSIZE = 200

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
		prf = wx.BoxSizer(wx.HORIZONTAL)
		
		text = " Profile:"
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w,h))
		t.SetFont(f)
		prf.Add(t, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.TOP, 10)
	
		self.cbProfile = wx.ComboBox(self, wx.ID_ANY, self.vprofile,
 			(-1, -1), (CBSIZE, -1), self.profilemap.keys(), wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbProfile.SetFont(f)
		self.cbProfile.SetToolTipString("Choose which cura profile to use")
		prf.Add(self.cbProfile, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		self.cbProfile.SetStringSelection(self.vprofile)
		self.Bind(wx.EVT_COMBOBOX, self.doChooseProfile, self.cbProfile)

		sizer.Add(prf, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

		prt = wx.BoxSizer(wx.HORIZONTAL)
		
		text = " Printer:"
		w, h = dc.GetTextExtent(text)
		t = wx.StaticText(self, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w,h))
		t.SetFont(f)
		prt.Add(t, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.TOP, 10)
	
		self.cbPrinter = wx.ComboBox(self, wx.ID_ANY, self.vprofile,
 			(-1, -1), (CBSIZE, -1), self.printermap.keys(), wx.CB_DROPDOWN | wx.CB_READONLY)
		self.cbPrinter.SetFont(f)
		self.cbPrinter.SetToolTipString("Choose which cura printer to use")
		prt.Add(self.cbPrinter, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		self.cbPrinter.SetStringSelection(self.vprinter)
		self.Bind(wx.EVT_COMBOBOX, self.doChoosePrinter, self.cbPrinter)

		sizer.Add(prt, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
		
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
		return "STL (*.stl)|*.[sS][tT][lL]|" \
			"AMF (*.amf)|*.[aA][mM][fF]|" \
			"STL or AMF (*.stl, *amf)|*.[sS][tT][lL];*.[aA][mM][fF]"
		
	def getSettingsKeys(self):
		return ['curapreferences', 'profiledir', 'profile', 'printer', 'command', 'config'], []
		
	def initialize(self, flag=False):
		if flag:
			self.vprinter = self.parent.settings['printer']
			self.vprofile = self.parent.settings['profile']

		self.prefs = ConfigParser.ConfigParser()
		self.prefs.optionxform = str
		self.prefFile = self.parent.settings['curapreferences']
		if not self.prefs.read(self.prefFile):
			self.showWarning("Cura preferences file %s does not exist.  Using default values" % self.prefFile)
			
		self.getProfileOptions()
		p = self.vprofile
		if p in self.profilemap.keys():
			self.parent.settings['profile'] = p
		else:
			self.parent.settings['profile'] = None
			
		self.getPrinterOptions()		
		p = self.vprinter
		if p in self.printermap.keys():
			self.parent.settings['printer'] = self.printermap[p]
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
		self.prefs.set("preferences", "active_machine", n)
		
		try:		
			cfp = open(self.prefFile, 'wb')
		except:
			print "Unable to open Cura preferences file %s for writing" % self.prefFile
			return
		self.prefs.write(cfp)
		cfp.close()
		
	def getConfigString(self):
		return "(" + str(self.vprinter) + "/" + str(self.vprofile) + ")"
		
	def getSlicerParameters(self):
		heTemps = [185]
		bedTemp = 60
		nExtruders = 1
		bedSize = [200, 200]
		if self.prefs.has_option('preferences', 'extruder_amount'):
			nExtruders = self.prefs.getint('preferences', 'extruder_amount')
			
		if self.parent.settings['printer'] in self.printermap.keys():
			p = self.parent.settings['printer']
			bedSize = self.printermap[p][1:3]

		if self.parent.settings['profile'] in self.profilemap.keys():
			fn = self.profilemap[self.parent.settings['profile']]
					
			try:
				prof = ConfigParser.ConfigParser()
				prof.optionxform = str
				if prof.read(fn):
					if prof.has_option('preferences', 'print_bed_temperature'):
						bedTemp = prof.getfloat('preferences', 'print_bed_temperature')
	
					heTemps = []
					for i in range(nExtruders):
						key = 'print_temperature'
						t = 185
						if i > 0:
							key += ("%d" % i+1)
							if prof.has_option('preferences', key):
								t = prof.getfloat('preferences', key)
						heTemps.append(t)
			except:
				print "Unable to process cura profile file %s: " % fn
	
		return [bedSize, nExtruders, heTemps, bedTemp]
	
	def buildSliceOutputFile(self, fn):
		return fn.split('.')[0] + ".gcode"
		
	def buildSliceCommand(self):
		s = self.parent.settings['command']
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
			ext = os.path.splitext(f)[1]
			if ext in [".ini", ".INI"]:
				p = os.path.join(d, f)
				r[f] = p
				
		self.profilemap = r
		return r
			
	def getPrinterOptions(self):
		self.printermap = {}
		r = {}
		self.vxprinter = 0
		if self.prefs.has_option('preferences', 'active_machine'):
			self.vxprinter = self.prefs.getint('preferences', 'active_machine')
		for ix in range(5):
			section = "machine_%d" % ix
			if self.prefs.has_section(section):
				if self.prefs.has_option(section, 'machine_name'):
					name = self.prefs.get(section, 'machine_name')
				else:
					name = section
					
				if self.prefs.has_option(section, 'machine_width'):
					width = self.prefs.get(section, 'machine_width')
				else:
					width = 200
					
				if self.prefs.has_option(section, 'machine_depth'):
					depth = self.prefs.get(section, 'machine_depth')
				else:
					depth = 200
					
				r[name] = (ix, width, depth)
				
		self.printermap = r
		return r
