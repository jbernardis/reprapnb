import wx
import time
import math
import os

from tools import formatElapsed
from settings import MAX_EXTRUDERS

filetags = { "filename" : "Name:", "slicecfg" : "Slicing Config:", "filament" : "Filament:", "temps" : "Temperatures:", "slicetime": "Slice Time:"}
layertags = { "layer" : "Layer Number:", "minmaxxy": "Min/Max X,Y:", "filament0" : "Filament Usage:", "layertime": "Layer Print Time:", "timeuntil": "Time Until:", "gclines": "G Code Lines:"}
printtags = { "gcode": "Print Position:", "eta": "Print Times:", "eta2": "", "eta3": ""}

MODE_NORMAL = 0
MODE_TO_SD = 1
MODE_FROM_SD = 2


class InfoPane (wx.Window):
	def __init__(self, parent, app):
		self.parent = parent
		self.app = app
		self.logger = self.app.logger
		self.wValues = {}
		
		self.mode = MODE_NORMAL
		self.duration = 0
		self.gcount = 0
		self.layers = 0
		self.filament = 0
		self.sdposition = 0
		self.maxsdposition = 0
		self.sdstartTime = None
		self.sdTargetFile = None
		self.newEta = None
		self.printLayer = 0
		
		self.filetagorder = ["filename", "slicecfg", "filament", "temps", "slicetime"]
		self.layertagorder = ["layer", "minmaxxy"]
		for i in range(MAX_EXTRUDERS):
			tag = "filament%d" % i
			self.layertagorder.append(tag)
			if i != 0:
				layertags[tag] = ""

		self.layertagorder.extend(["gclines", "layertime", "timeuntil"])
		self.printtagorder = ["gcode", "eta", "eta2", "eta3"]
			
		wx.Window.__init__(self, parent, wx.ID_ANY, size=(400, -1), style=wx.SIMPLE_BORDER)		
		self.sizerInfo = wx.BoxSizer(wx.HORIZONTAL)
		self.sizerTag = wx.BoxSizer(wx.VERTICAL)
		self.sizerValue = wx.BoxSizer(wx.VERTICAL)
		
		self.font8 = wx.Font (8, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		self.font12 = wx.Font (12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		self.font12bold = wx.Font (12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		
		self.dc = wx.WindowDC(self)
		self.dc.SetFont(self.font8)
		self.h8point = self.dc.GetTextExtent("ABCDEFGHIJ")[1]
		self.dc.SetFont(self.font12)
		self.h12point = self.dc.GetTextExtent("ABCDEFGHIJ")[1]

		self.sizerTag.AddSpacer((2,2))
		self.sizerValue.AddSpacer((2,2))

		self.addTags("File Information", filetags, self.filetagorder)
		self.addTags("Layer Information", layertags, self.layertagorder)
		self.addTags("Print Status", printtags, self.printtagorder)

		self.sizerInfo.AddSpacer((5,5))
		self.sizerInfo.Add(self.sizerTag, flag=wx.EXPAND)
		self.sizerInfo.AddSpacer((5,5))
		self.sizerInfo.Add(self.sizerValue, flag=wx.EXPAND)
		self.sizerInfo.AddSpacer((5,5))
		self.SetSizer(self.sizerInfo)
		self.Layout()
		self.Fit()

	def addTags(self, title, tags, tagorder):
		self.dc.SetFont(self.font12bold)
		w = self.dc.GetTextExtent(title)[0]
		t = wx.StaticText(self, wx.ID_ANY, title, style=wx.ALIGN_RIGHT, size=(w, self.h12point+5))
		t.SetFont(self.font12bold)
		self.sizerTag.Add(t, flag=wx.ALIGN_LEFT | wx.TOP, border=0)
		self.sizerValue.AddSpacer((w, self.h12point+5))

		self.dc.SetFont(self.font8)
		for t in tagorder:
			text = tags[t]
			w = self.dc.GetTextExtent(text)[0]

			st = wx.StaticText(self, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w, self.h8point+5))
			st.SetFont(self.font8)
			self.sizerTag.Add(st, flag=wx.ALIGN_RIGHT | wx.TOP, border=0)
			self.sizerTag.AddSpacer((2,2))
	
			self.wValues[t] = wx.StaticText(self, wx.ID_ANY, "", size=(310, self.h8point+5), style=wx.ALIGN_LEFT)
			self.wValues[t].SetFont(self.font8)
			self.sizerValue.Add(self.wValues[t])
			self.sizerValue.AddSpacer((2,2))

	def setValue(self, tag, value):
		if tag not in self.wValues.keys():
			return

		self.wValues[tag].SetLabel(value)
		
	def getStatus(self):
		stat = {}
		
		if self.mode == MODE_NORMAL:
			stat['printmode'] = "Normal Print"
			stat['filename'] = self.filename
			stat['slicecfg'] = self.slicecfg
			stat['filament'] = self.slicefil
			stat['temps'] = self.temps
			stat['slicetime'] = self.sliceTime

			stat['currentlayer'] = self.layernbr
			stat['layers'] = self.layers
			stat['currentheight'] = self.z
			
			gcode = {}
			gcode['position'] = self.position
			gcode['linecount'] = self.gcount
			if self.gcount != 0:
				stat['percent'] = "%.2f%%" % (float(self.position) / float(self.gcount) * 100.0)
			stat['gcode'] = gcode
			
			times = {}
			times['starttime'] = time.strftime('%H:%M:%S', time.localtime(self.startTime))
			times['expectedduration'] = formatElapsed(self.duration)
			times['origeta'] = time.strftime('%H:%M:%S', time.localtime(self.eta))
			times['remaining'] = formatElapsed(self.remains)
			times['neweta'] = time.strftime('%H:%M:%S', time.localtime(self.newEta)) 
			elapsed = time.time() - self.startTime
			times['elapsed'] = formatElapsed(elapsed)
			stat['times'] = times
			
		elif self.mode == MODE_TO_SD:
			stat['printmode'] = "Print to SD"
			stat['targetfile'] = self.sdTargetFile
			
			times = {}
			times['starttime'] = time.strftime('%H:%M:%S', time.localtime(self.startTime))
			elapsed = time.time() - self.startTime
			times['elapsed'] = formatElapsed(elapsed)
			stat['times'] = times

		elif self.mode == MODE_FROM_SD:
			stat['printmode'] = "Print from SD"
			gcode = {}
			gcode['position'] = self.sdposition
			gcode['maxposition'] = self.maxsdposition
			if self.maxsdposition != 0:
				gcode['percent'] = "%.2f%%" % (float(self.sdposition) / float(self.maxsdposition) * 100.0)
			stat['gcode'] = gcode
			
			times = {}
			times['starttime'] = time.strftime('%H:%M:%S', time.localtime(self.sdstartTime))
			elapsed = time.time() - self.sdstartTime
			times['elapsed'] = formatElapsed(elapsed)
			stat['times'] = times
		
		return stat
	
	def setMode(self, mode):
		if mode not in [MODE_NORMAL, MODE_TO_SD, MODE_FROM_SD]:
			return
		
		self.mode = mode
		for t in self.filetagorder:
			self.setValue(t, "")
		for t in self.layertagorder:
			self.setValue(t, "")
		for t in self.printtagorder:
			self.setValue(t, "")
		
	def clearFileInfo(self):
		self.setValue("filename", "")
		self.setValue("slicecfg", "")
		self.setValue("filament", "")
		self.setValue("temps", "")
		self.setValue("slicetime", "")
		
	def showFileInfo(self):
		self.setValue("filename", self.filename)
		self.setValue("slicecfg", self.slicecfg)
		self.setValue("filament", self.slicefil)
		self.setValue("temps", self.temps)
		self.setValue("slicetime", self.sliceTime)
		
	def setFileInfo(self, filename, slcfg, slfil, sltemp, sltime, duration, gcount, layers, zmax, filament, layertimes):
		if len(filename) > 60:
			lfn = os.path.basename(filename)
		else:
			lfn = filename

		self.setValue("filename", lfn)
		self.filename = lfn

		if slcfg is None:
			self.slicecfg = ""
		else:
			self.slicecfg = slcfg
		self.setValue("slicecfg", self.slicecfg)
			
		if slfil is None:
			self.slicefil = ""
		else:
			self.slicefil = slfil
		self.setValue("filament", self.slicefil)
			
		if sltemp is None:
			self.temps = ""
		else:
			self.temps = str(sltemp)
		self.setValue("temps", self.temps)
		
		self.sliceTime = sltime
		self.setValue("slicetime", self.sliceTime)

		self.duration = duration
		self.gcount = gcount
		self.layers = layers
		self.zmax = zmax
		self.filament = filament
		self.layertimes = [i for i in layertimes]
		t = 0
		self.prevTimes = []
		for i in self.layertimes:
			self.prevTimes.append(t)
			t += i

	def timeUntil(self, futureLayer):
		if self.printLayer is None:
			self.printLayer = 0

		if self.printLayer >= (futureLayer-1):
			return 0

		tm = 0
		cl = self.printLayer + 1
		while (cl < futureLayer):
			tm += self.layertimes[cl]
			cl += 1

		return tm
			
	def setSDTargetFile(self, fn):
		self.sdTargetFile = fn
		
	def clearLayerInfo(self):
		self.setValue("layer", "")
		self.setValue("minmaxxy", "")
		for i in range(MAX_EXTRUDERS):
			tag = "filament%d" % i
			self.setValue(tag, "")
		
		self.setValue("gclines", "")
		self.setValue("layertime", "")
	
	def setLayerInfo(self, layernbr, z, minxy, maxxy, filament, prevfilament, ltime, gclines):
		self.gclines = gclines
		self.layernbr = layernbr
		self.z = z
		if self.layers == 0:
			self.setValue("layer", "%d (z=%.3f)" % (layernbr+1, z))
		else:
			self.setValue("layer", "%d/%d (z=%.3f/%.3f)" % (layernbr+1, self.layers, z, self.zmax))
			
		if minxy[0] > maxxy[0] or minxy[1] >maxxy[1]:
			self.setValue("minmaxxy", "")
		else:
			self.setValue("minmaxxy", "(%.3f, %.3f) <-> (%.3f, %.3f)" % (minxy[0], minxy[1], maxxy[0], maxxy[1]))

		for i in range(MAX_EXTRUDERS):
			tag = "filament%d" % i
			s = "T%d: %.3f/%.3f (%.3f)" % (i, filament[i], self.filament[i], prevfilament[i])
			self.setValue(tag, s)
		
		self.setValue("gclines", "%d -> %d" % (gclines[0], gclines[1]))
		
		if self.duration == 0:
			self.setValue("layertime", "%s" % formatElapsed(ltime))
		else:
			self.setValue("layertime", "%s/%s" % (formatElapsed(ltime), formatElapsed(self.duration)))
			
		self.updateUntilTime()
			
			
	def updateUntilTime(self):
		t = self.timeUntil(self.layernbr)
		if t == 0:
			self.setValue("timeuntil", "")
		else:
			self.setValue("timeuntil", "%s" % formatElapsed(self.timeUntil(self.layernbr)))
	
	def setSDPrintInfo(self, position, maxposition):  # printing FROM SD card
		self.sdposition = position
		self.maxsdposition = maxposition
		pct = "??"
		if self.maxsdposition != 0:
			pct = "%.2f" % (float(self.sdposition) / float(self.maxsdposition) * 100.0)
		
		self.setValue("gcode", "SD Byte %d/%d total (%s%%)" % (position, maxposition, pct))
		
		if self.sdstartTime != None:
			start = time.strftime('%H:%M:%S', time.localtime(self.sdstartTime))
			elapsed = time.time() - self.sdstartTime
			strElapsed = formatElapsed(elapsed)
			self.setValue("eta", "Start: %s  Elapsed: %s" % (start, strElapsed))
		else:
			self.setValue("eta", "")
			
		self.setValue("eta2", "")
		self.setValue("eta3", "")
		
	def setPrintInfo(self, position, layer, gcodelines, layertime):
		self.position = position
		self.printLayer = layer
		pct = "??"
		if self.gcount != 0:
			pct = "%.2f" % (float(self.position) / float(self.gcount) * 100.0)
		
		self.setValue("gcode", "Line %d/%d total lines (%s%%)" % (position, self.gcount, pct))
		
		start = time.strftime('%H:%M:%S', time.localtime(self.startTime))
		now = time.time()
		elapsed = now - self.startTime
		strElapsed = formatElapsed(elapsed)
		if self.sdTargetFile is None:  # printing TO SD card
			self.remains = self.eta - now
			eta = time.strftime('%H:%M:%S', time.localtime(self.eta))
			self.setValue("eta", "Start: %s  Orig ETA: %s" % (start, eta))

			if layer is not None:
				expectedTime = self.prevTimes[layer]
				delta = 0
				if position >= gcodelines[0] and position <= gcodelines[1]:
					lct = gcodelines[1] - gcodelines[0]
					if lct != 0:
						lpos = position - gcodelines[0]
						lpct = float(lpos)/float(lct)
						delta = layertime * lpct
				expectedTime += delta
				self.revisedeta = expectedTime
				
				diff = elapsed - expectedTime
				try:
					lateness = float(elapsed) / float(expectedTime)
				except:
					lateness = 1.0
					
				remains = self.eta + diff - now
				self.remains = remains
				strRemains = formatElapsed(remains)
				self.newEta = now+(remains * lateness)
				strNewEta = time.strftime('%H:%M:%S', time.localtime(self.newEta))
				self.setValue("eta2", "Remaining: %s  New ETA: %s" % (strRemains, strNewEta))
				
				pctDiff = float(elapsed + remains)/float(self.duration) * 100.0
				secDiff = math.fabs(elapsed + remains - self.duration)
				strDiff = formatElapsed(secDiff)
				if pctDiff < 100:
					schedule = "%s ahead of sched (%.2f%%)" % (strDiff, (100.0-pctDiff))
				elif pctDiff >100:
					schedule = "%s behind sched (%.2f%%)" % (strDiff, (pctDiff - 100))
				else:
					schedule = "on schedule"
				self.setValue("eta3", "Elapsed: %s - %s" % (strElapsed, schedule))
			else:
				self.setValue("eta2", "")
				self.setValue("eta3", "")
		else:
			self.setValue("eta", "Start: %s" % start)
			self.setValue("eta2", "Elapsed: %s" % strElapsed)
			self.setValue("eta3", "Target File: %s" % self.sdTargetFile)
			
	
	def setStartTime(self, start):
		self.startTime = start
		self.eta = start + self.duration
		
	def setSDStartTime(self, start):
		self.sdstartTime = start
		
	def setPrintComplete(self):
		end = time.time();
		strEnd = time.strftime('%H:%M:%S', time.localtime(end))
		
		elapsed = end - self.startTime
		strElapsed = formatElapsed(elapsed)
		
		diff = elapsed - self.duration
		pctDiff = float(diff) / float(self.duration) * 100.0
		
		self.setValue("gcode", "")
		self.setValue("eta", "Print completed at %s, elapsed %s (%.2f%%)" % (strEnd, strElapsed, pctDiff))
		self.setValue("eta2", "")
		self.setValue("eta3", "")

	def setSDPrintComplete(self):		
		self.setValue("gcode", "")
		
		now = time.time()
		strNow = time.strftime('%H:%M:%S', time.localtime(now))
		elapsed = now - self.sdstartTime
		strElapsed = formatElapsed(elapsed)
		self.setValue("eta", "Print completed at %s, elapsed %s" % (strNow, strElapsed))
		self.setValue("eta2", "")
		self.setValue("eta3", "")
		self.sdstartTime = None
