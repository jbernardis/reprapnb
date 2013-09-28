'''
Created on Jun 20, 2013

@author: ejefber
'''
import os
import wx
import shlex, subprocess

BUTTONDIM = (48, 48)
CBSIZE = 200

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
		
	def getSlicerParameters(self):
		heTemps = [185]
		bedTemps = [60]
		nExtruders = 1
		bedSize = [200, 200]
		if self.parent.settings['profile'] in self.profilemap.keys():
			path = self.profilemap[self.parent.settings['profile']]
			
			fn = os.path.join(path, "chamber.csv");		
			try:
				l = list(open(fn))
				for s in l:
					if s.startswith("Bed Temperature (Celcius):"):
						try:
							sval = s.split('\t')[1]
							bedTemps[0] = float(sval)
						except:
							bedTemps[0] = 60
					
			except:
				print "Unable to open skeinforge chamber.csv file for profile %s reading: " % self.parent.settings['profile']
				bedTemps[0] = 60
	
			fn = os.path.join(path, "temperature.csv");
			try:
				l = list(open(fn))
				for s in l:
					if s.startswith("Object First Layer Perimeter Temperature (Celcius):"):
						try:
							sval = s.split('\t')[1]
							heTemps[0] = float(sval)
						except:
							heTemps[0] = 185
					
			except:
				print "Unable to open skeinforge temperature.csv file for profile %s reading: " % self.parent.settings['profile']
				heTemps[0] = 185

		return [bedSize, nExtruders, heTemps, bedTemps]
	
	def buildSliceOutputFile(self, fn):
		return fn.replace(".stl", "_export.gcode")
		
	def buildSliceCommand(self):
		s = self.parent.settings['command']
		return os.path.expandvars(os.path.expanduser(self.app.replace(s)))
	
	def sliceComplete(self):
		pass
	
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
			print "Unable to open skeinforge profile file for reading: " + self.parent.settings['profilefile']
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
			print "Unable to open skeinforge profile file for writing: " + self.parent.settings['profilefile']
			
	def getProfileOptions(self):
		self.profilemap = {}
		try:
			d = os.path.expandvars(os.path.expanduser(self.parent.settings['profiledir']))
			l = os.listdir(d)
		except:
			print "Unable to get listing from skeinforge profile directory: " + self.parent.settings['profiledir']
			return {}
		r = {}
		for f in sorted(l):
			p = os.path.join(d, f)
			if os.path.isdir(p):
				r[f] = p
				
		self.profilemap = r
		return r
