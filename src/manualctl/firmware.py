import os
import wx
import wx.lib.newevent
import ConfigParser

(FirmwareEvent, EVT_FIRMWARE) = wx.lib.newevent.NewEvent()
wildcard="Firmware Files (*.fw)|*.fw|All Files (*.*)|*.*"


grpinfo = {'m92' : ['Steps per Unit - M92', 4, ['x', 'y', 'z', 'e'], ['X Steps', 'Y Steps', 'Z Steps', 'E Steps']],
		'm201' : ['Max Acceleration (mm/s2) - M201', 4, ['x', 'y', 'z', 'e'], ['X Maximum Acceleration', 'Y Maximum Acceleration', 'Z Maximum Acceleration', 'E Maximum Acceleration']],
		'm203' : ['Max Feed Rates (mm/s) - M203', 4, ['x', 'y', 'z', 'e'], ['X Maximum Feed Rate', 'Y Maximum Feed Rate', 'Z Maximum Feed Rate', 'E Maximum Feed Rate']],
		'm204' : ['Acceleration - M204', 2, ['s', 't'], ['Maximum Normal Acceleration', 'Maximum Retraction Acceleration']],
		'm205' : ['Advanced - M205', 6, ['s', 't', 'b', 'x', 'z', 'e'], ['Minimum Feed Rate', 'Minimum Travel', 'Minimum Segment Time', 'Maximum XY Jerk', 'Maximum Z Jerk', 'Maximum E Jerk']],
		'm206' : ['Home offset - M206', 3, ['x', 'y', 'z'], ['X Home Offset', 'Y Home Offset', 'Z Home Offset']],
		'm301' : ['PID - M301', 3, ['p', 'i', 'd'], ['Proportional Value', 'Integral Value', 'Derivative Value']]}

grporder = ['m92', 'm201', 'm203', 'm204', 'm205', 'm206', 'm301']

EEPROMFILE = "settings.eep"

def getFirmwareProfile(fn, container):
	cfg = ConfigParser.ConfigParser()

	if not cfg.read(fn):
		return False, "Firmware profile settings file %s does not exist." % fn

	section = "Firmware"
	if not cfg.has_section(section):
		return False, "Firmware profile file %s does not have %s section." % (fn, section)
	
	for g in grporder:
		for i in grpinfo[g][2]:
			k = "%s_%s" % (g, i)
			if not cfg.has_option(section, k):
				v = None
			else:
				v = str(cfg.get(section, k))
				
			container.setValue(k, v)
	return True, "Firmware profile file %s successfully read" % fn

def putFirmwareProfile(fn, container):
	cfg = ConfigParser.ConfigParser()
	
	section = "Firmware"
	cfg.add_section(section)
	for g in grporder:
		for i in grpinfo[g][2]:
			k = "%s_%s" % (g, i)
			v = container.getValue(k)
			if v is not None:
				cfg.set(section, k, str(v))
			else:
				try:
					cfg.remove_option(section, k)
				except:
					pass

	try:				
		with open(fn, 'wb') as configfile:
			cfg.write(configfile)
	except:
		return False, "Error saving firmware profile to %s" % fn
		
	return True, "Firmware profile successfully saved to %s" % fn

class FwSettings:
	def __init__(self):
		self.values = {}
		
	def setValue(self, tag, val):
		self.values[tag] = val
		
	def getValue(self, tag):
		if tag not in self.values.keys():
			return None
		
		return self.values[tag]
	
class Firmware:
	def __init__(self, app, reprap):
		self.app = app
		self.reprap = reprap
		self.logger = app.logger
		
		self.dlgVisible = False
		self.wDlg = None

		self.got92 = False
		self.got201 = False
		self.got203 = False
		self.got204 = False
		self.got205 = False
		self.got206 = False
		self.got301 = False
		
		self.readingFirmware = False
		
		self.flash = FwSettings()
		self.eeprom = FwSettings()
		
		getFirmwareProfile(EEPROMFILE, self.eeprom)
		
	def start(self):
		self.got92 = False
		self.got201 = False
		self.got203 = False
		self.got204 = False
		self.got205 = False
		self.got206 = False
		self.got301 = False
		
		self.readingFirmware = True 
		self.reprap.send_now("M503")
		
	def checkComplete(self):
		if self.got92 and self.got201 and self.got203 and self.got204 and self.got204 and self.got206 and self.got301:
			if self.readingFirmware:
				self.reportComplete()
			return True
		else:
			return False
	
	def m92(self, x, y, z, e):
		self.flash.setValue('m92_x', x)
		self.flash.setValue('m92_y', y)
		self.flash.setValue('m92_z', z)
		self.flash.setValue('m92_e', e)
		self.got92 = True
		return self.checkComplete()
		
	def m201(self, x, y, z, e):
		self.flash.setValue('m201_x', x)
		self.flash.setValue('m201_y', y)
		self.flash.setValue('m201_z', z)
		self.flash.setValue('m201_e', e)
		self.got201 = True
		return self.checkComplete()
		
	def m203(self, x, y, z, e):
		self.flash.setValue('m203_x', x)
		self.flash.setValue('m203_y', y)
		self.flash.setValue('m203_z', z)
		self.flash.setValue('m203_e', e)
		self.got203 = True
		return self.checkComplete()
		
	def m204(self, s, t):
		self.flash.setValue('m204_s', s)
		self.flash.setValue('m204_t', t)
		self.got204 = True
		return self.checkComplete()
		
	def m205(self, s, t, b, x, z, e):
		self.flash.setValue('m205_s', s)
		self.flash.setValue('m205_t', t)
		self.flash.setValue('m205_b', b)
		self.flash.setValue('m205_x', x)
		self.flash.setValue('m205_z', z)
		self.flash.setValue('m205_e', e)
		self.got205 = True
		return self.checkComplete()

	def m206(self, x, y, z):
		self.flash.setValue('m206_x', x)
		self.flash.setValue('m206_y', y)
		self.flash.setValue('m206_z', z)
		self.got206 = True
		return self.checkComplete()

	def m301(self, p, i, d):
		self.flash.setValue('m301_p', p)
		self.flash.setValue('m301_i', i)
		self.flash.setValue('m301_d', d)
		self.got301 = True
		return self.checkComplete()

	def reportComplete(self):
		self.readingFirmware = False
		self.logger.LogMessage("Firmware Reporting completed")
		if self.dlgVisible:
			evt = FirmwareEvent(completed=True)
			wx.PostEvent(self.wDlg, evt)
		
	def show(self):
		if self.dlgVisible:
			return
		
		self.dlgVisible = True
		self.wDlg = FirmwareDlg(self, self.flash, self.eeprom) 
		self.wDlg.CenterOnScreen()
		self.wDlg.Show(True)
		
	def hide(self):
		if not self.dlgVisible:
			return
		
		self.wDlg.Destroy()
		self.setHidden()
		
	def setHidden(self):
		self.dlgVisible = False
		self.wDlg = None

class TextBox(wx.PyWindow):
	def __init__(self, parent, text, pos=wx.DefaultPosition, size=wx.DefaultSize):
		wx.PyWindow.__init__(self, parent, -1,
							 #style=wx.RAISED_BORDER
							 #style=wx.SUNKEN_BORDER
							 style=wx.SIMPLE_BORDER
							 )
		self.text = str(text)
		if size != wx.DefaultSize:
			self.bestsize = size
		else:
			self.bestsize = (250,25)
		self.SetSize(self.GetBestSize())
		
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.Bind(wx.EVT_LEFT_UP, self.OnCloseParent)
		
	def setText(self, text):
		self.text = str(text)
		self.Refresh()
		
	def getText(self):
		return self.text

	def OnPaint(self, evt):
		sz = self.GetSize()
		dc = wx.PaintDC(self)
		w,h = dc.GetTextExtent(self.text)
		dc.Clear()
		dc.DrawText(self.text, (sz.width-w)/2, (sz.height-h)/2)

	def OnSize(self, evt):
		self.Refresh()

	def OnCloseParent(self, evt):
		p = wx.GetTopLevelParent(self)
		if p:
			p.Close()			

	def DoGetBestSize(self):
		return self.bestsize
	
BSIZE = (140, 40)
class FirmwareDlg(wx.Dialog):
	def __init__(self, parent, flash, eeprom):
		self.parent = parent
		self.app = parent.app
		self.logger = parent.logger
		self.reprap = parent.reprap
		self.flash = flash
		self.eeprom = eeprom
		self.working = FwSettings()
		
		pre = wx.PreDialog()
		pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
		pos = wx.DefaultPosition
		sz = (950, 780)
		style = wx.DEFAULT_DIALOG_STYLE
		pre.Create(self.app, wx.ID_ANY, "Firmware Parameters", pos, sz, style)
		self.PostCreate(pre)
		
		self.sizer = wx.GridBagSizer()

		row = 1
		btnBase = 5000
		grpBase = 6000
		self.itemMap = {}
		self.buttonMap = {}
		self.groupMap = {}
		
		font = wx.Font (12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		
		t = wx.StaticText(self, wx.ID_ANY, "FLASH")
		t.SetFont(font)
		self.sizer.Add(t, pos=(0, 6), flag=wx.ALIGN_CENTER)

		t = wx.StaticText(self, wx.ID_ANY, "EEPROM")
		t.SetFont(font)
		self.sizer.Add(t, pos=(0, 7), flag=wx.ALIGN_CENTER)

		for g in grporder:
			t = TextBox(self, grpinfo[g][0])
			self.sizer.Add(t, pos=(row, 1), span=(grpinfo[g][1], 1), flag=wx.EXPAND)
			for i in range(grpinfo[g][1]):
				itemKey = g + '_' + grpinfo[g][2][i]
				
				t = TextBox(self, grpinfo[g][2][i] + ':', size=(20, 25))
				self.sizer.Add(t, pos=(row+i, 2), flag=wx.EXPAND)
				
				tv = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_CENTER, size=(140, 25))
				tv.SetFont(font)
				tv.SetToolTipString(grpinfo[g][3][i])
				self.sizer.Add(tv, pos=(row+i, 3), flag=wx.EXPAND)
				
				b = wx.Button(self, btnBase+row+i, "-->")
				self.buttonMap[btnBase+row+i] = itemKey
				self.Bind(wx.EVT_BUTTON, self.onItemCopy, b)
				self.sizer.Add(b, pos=(row+i, 4), flag=wx.EXPAND)
				
				v = self.flash.getValue(itemKey)
				if v is None: v = ""
				tf = TextBox(self, v, size=(100, 25))
				self.sizer.Add(tf, pos=(row+i, 6), flag=wx.EXPAND)
				
				v = self.eeprom.getValue(itemKey)
				if v is None: v = ""
				te = TextBox(self, v, size=(100, 25))
				self.sizer.Add(te, pos=(row+i, 7), flag=wx.EXPAND)
				
				self.itemMap[itemKey] = [tv, tf, te]
				
			b = wx.Button(self, grpBase, "-->")
			self.groupMap[grpBase] = g
			self.Bind(wx.EVT_BUTTON, self.onGroupCopy, b)
			self.sizer.Add(b, pos=(row, 5), span=(grpinfo[g][1], 1), flag=wx.EXPAND)
			grpBase += 1
			
			row += grpinfo[g][1]

		btnSizer = wx.BoxSizer(wx.VERTICAL)

		btnSizer.AddSpacer((10, 40))

		self.buttons = []		
		btn = wx.Button(self, wx.ID_ANY, "Load Profile", size=BSIZE)
		self.Bind(wx.EVT_BUTTON, self.onLoadProf, btn)
		btnSizer.Add(btn, 0, wx.ALL, 10)
		self.buttons.append(btn)
		
		btn = wx.Button(self, wx.ID_ANY, "Save Profile", size=BSIZE)
		self.Bind(wx.EVT_BUTTON, self.onSaveProf, btn)
		btnSizer.Add(btn, 0, wx.ALL, 10)
		self.buttons.append(btn)
		
		btnSizer.AddSpacer((10, 100))
		
		btn = wx.Button(self, wx.ID_ANY, "All -> FLASH", size=BSIZE)
		self.Bind(wx.EVT_BUTTON, self.onCopyAllToFlash, btn)
		btnSizer.Add(btn, 0, wx.ALL, 10)
		self.buttons.append(btn)
		
		btn = wx.Button(self, wx.ID_ANY, "FLASH -> EEPROM", size=BSIZE)
		self.Bind(wx.EVT_BUTTON, self.onCopyFlashToEEProm, btn)
		btnSizer.Add(btn, 0, wx.ALL, 10)
		self.buttons.append(btn)
		
		btn = wx.Button(self, wx.ID_ANY, "EEPROM -> FLASH", size=BSIZE)
		self.Bind(wx.EVT_BUTTON, self.onCopyEEPromToFlash, btn)
		btnSizer.Add(btn, 0, wx.ALL, 10)
		self.buttons.append(btn)
		
		btn = wx.Button(self, wx.ID_ANY, "Flash -> Working", size=BSIZE)
		self.Bind(wx.EVT_BUTTON, self.onCopyFlashToWork, btn)
		btnSizer.Add(btn, 0, wx.ALL, 10)
		self.buttons.append(btn)
		
		btnSizer.AddSpacer((10, 100))
		
		btn = wx.Button(self, wx.ID_ANY, "Close", size=BSIZE)
		self.Bind(wx.EVT_BUTTON, self.onClose, btn)
		btnSizer.Add(btn, 0, wx.ALL, 10)
		self.buttons.append(btn)
		
		self.sizer.Add(btnSizer, pos=(0,0), span=(25,1))

		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.Bind(EVT_FIRMWARE, self.copyEEPromToFlashResume)

		self.SetSizer(self.sizer)
		self.SetAutoLayout(True)
		
	def enableButtons(self, flag):
		for b in self.buttons:
			b.Enable(flag)
		
	def onItemCopy(self, event):
		wid = event.GetId()
		if wid not in self.buttonMap.keys():
			self.logger.LogMessage("Unknown widget ID: %s" % wid)
			
		ik = self.buttonMap[wid]
		wVal = self.itemMap[ik][0]
		val = wVal.GetValue().strip()
		
		if val != "":
			cmd = "%s%s" % (ik.upper().replace('_', ' '), val)
			self.reprap.send_now(cmd)
		
			wFlash = self.itemMap[ik][1]
			wFlash.setText(val)
			self.flash.setValue(ik, val)
			
	def onGroupCopy(self, event):
		wid = event.GetId()
		if wid not in self.groupMap.keys():
			self.logger.LogMessage("Unknown widget ID: %s" % wid)
			
		gk = self.groupMap[wid]
		self.sendGroupToFlash(gk)
		
	def sendGroupToFlash(self, gk):
		cmd = gk.upper()
		nterms = 0
		for gi in grpinfo[gk][2]:
			ik = gk + '_' + gi
			
			wVal = self.itemMap[ik][0]
			val = wVal.GetValue().strip()
			
			if val != "":
				nterms += 1
				cmd += " %s%s" % (gi.upper(), val)
				wFlash = self.itemMap[ik][1]
				wFlash.setText(val)
				self.flash.setValue(ik, val)
				
		if nterms != 0:
			self.reprap.send_now(cmd)
			
	def onCopyAllToFlash(self, evt):
		for g in grporder:
			self.sendGroupToFlash(g)
			
	def onCopyFlashToEEProm(self, evt):
		self.reprap.send_now("M500")
		for i in self.itemMap.keys():
			v = self.itemMap[i][1].getText()
			self.itemMap[i][2].setText(v)
			self.eeprom.setValue(i, v)

		putFirmwareProfile(EEPROMFILE, self.eeprom)
			
	def onCopyEEPromToFlash(self, evt):
		self.enableButtons(False)
		self.reprap.send_now("M501")
		self.parent.start()
		
	def copyEEPromToFlashResume(self, evt):
		self.logger.LogMessage("Resuming copy of EEProm settings to firmware")
		for i in self.itemMap.keys():
			v = self.flash.getValue(i)
			self.itemMap[i][2].setText(v)
			self.itemMap[i][1].setText(v)
			self.eeprom.setValue(i, v)

		putFirmwareProfile(EEPROMFILE, self.eeprom)
		self.enableButtons(True)
			
	def onCopyFlashToWork(self, evt):
		for i in self.itemMap.keys():
			v = self.itemMap[i][1].getText()
			self.itemMap[i][0].SetValue(v)
			self.working.setValue(i, v)
			
	def onLoadProf(self, event):
		dlg = wx.FileDialog(
			self, message="Choose a firmware file",
			defaultDir=os.getcwd(), 
			defaultFile="",
			wildcard=wildcard,
			style=wx.FD_OPEN | wx.FD_CHANGE_DIR
			)
		
		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()
			rc, msg = getFirmwareProfile(path, self.working)
			self.logger.LogMessage(msg)
			if rc:
				for k in self.itemMap.keys():
					wVal = self.itemMap[k][0]
					val = self.working.getValue(k)
					if val is None: val = ""
					wVal.SetValue(val)
				
		dlg.Destroy()
		
	def onSaveProf(self, event):
		dlg = wx.FileDialog(
			self, message="Save firmware profile as...",
			defaultDir=os.getcwd(), 
			defaultFile="",
			wildcard=wildcard,
			style=wx.FD_SAVE | wx.FD_CHANGE_DIR | wx.FD_OVERWRITE_PROMPT
			)
		
		v = dlg.ShowModal()
		if v != wx.ID_OK:
			dlg.Destroy()
			return
		
		path = dlg.GetPath()
		dlg.Destroy()
		
		ext = os.path.splitext(os.path.basename(path))[1]
		if ext == "":
			path += ".fw"
			
		msg = putFirmwareProfile(path, self.working)[1]
		self.logger.LogMessage(msg)
				
	def onClose(self, event):
		self.parent.setHidden()
		self.Destroy()
		
					
		
		


