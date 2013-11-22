
import wx
import time
import math

from tools import formatElapsed

filetags = { "filename" : "Name:" }
filetagorder = ["filename"]

layertags = { "layer" : "Layer Number:", "minmaxxy": "Min/Max X,Y:", "filament" : "Filament Usage:", "layertime": "Layer Print Time:", "gclines": "G Code Lines:"}
layertagorder = ["layer", "minmaxxy", "filament", "gclines", "layertime"]

printtags = { "gcode": "Print Position:", "eta": "Print Times:", "eta2": "", "eta3": ""}
printtagorder = ["gcode", "eta", "eta2", "eta3"]


class InfoPane (wx.Window):
	def __init__(self, parent, app):
		self.parent = parent
		self.app = app
		self.logger = self.app.logger
		self.wValues = {}
		
		self.duration = 0
		self.gcount = 0
		self.layers = 0
		self.filament = 0
		self.sdposition = 0
		self.maxsdposition = 0
		self.sdstartTime = None
		self.sdTargetFile = None
		
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

		self.addTags("File Information", filetags, filetagorder)
		self.addTags("Layer Information", layertags, layertagorder)
		self.addTags("Print Status", printtags, printtagorder)

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
		
		stat['filename'] = self.filename
		stat['currentlayer'] = self.layernbr
		stat['currentheight'] = self.z
		stat['position'] = self.position
		stat['gcount'] = self.gcount
		stat['origeta'] = time.strftime('%H:%M:%S', time.localtime(self.eta))
		stat['starttime'] = time.strftime('%H:%M:%S', time.localtime(self.startTime))
		stat['remaining'] = formatElapsed(self.remains)
		stat['duration'] = formatElapsed(self.duration)
		return stat
		
		
	def setFileInfo(self, filename, duration, gcount, layers, filament, layertimes):
		self.setValue("filename", filename)
		self.filename = filename
		self.duration = duration
		self.gcount = gcount
		self.layers = layers
		self.filament = filament
		self.layertimes = [i for i in layertimes]
		t = 0
		self.prevTimes = []
		for i in self.layertimes:
			self.prevTimes.append(t)
			t += i
			
	def setSDTargetFile(self, fn):
		self.sdTargetFile = fn
	
	def setLayerInfo(self, layernbr, z, minxy, maxxy, filament, prevfilament, ltime, gclines):
		self.gclines = gclines
		self.layernbr = layernbr
		self.z = z
		if self.layers == 0:
			self.setValue("layer", "%d (z=%.3f)" % (layernbr+1, z))
		else:
			self.setValue("layer", "%d/%d (z=%.3f)" % (layernbr+1, self.layers, z))
			
		if minxy[0] > maxxy[0] or minxy[1] >maxxy[1]:
			self.setValue("minmaxxy", "")
		else:
			self.setValue("minmaxxy", "(%.3f, %.3f) <-> (%.3f, %.3f)" % (minxy[0], minxy[1], maxxy[0], maxxy[1]))
		
		if self.filament == 0:
			self.setValue("filament", "%.3f (%.3f mm on previous layers)" % (filament, prevfilament))
		else:
			self.setValue("filament", "%.3f/%.3f (%.3f mm on previous layers)" % (filament, self.filament, prevfilament))
		
		self.setValue("gclines", "%d -> %d" % (gclines[0], gclines[1]))
		
		if self.duration == 0:
			self.setValue("layertime", "%s" % formatElapsed(ltime))
		else:
			self.setValue("layertime", "%s/%s" % (formatElapsed(ltime), formatElapsed(self.duration)))
	
	def setSDPrintInfo(self, position, maxposition):
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
		pct = "??"
		if self.gcount != 0:
			pct = "%.2f" % (float(self.position) / float(self.gcount) * 100.0)
		
		self.setValue("gcode", "Line %d/%d total lines (%s%%)" % (position, self.gcount, pct))
		
		start = time.strftime('%H:%M:%S', time.localtime(self.startTime))
		now = time.time()
		elapsed = now - self.startTime
		strElapsed = formatElapsed(elapsed)
		if self.sdTargetFile is None:
			self.remains = self.eta - now
			eta = time.strftime('%H:%M:%S', time.localtime(self.eta))
			self.setValue("eta", "Start: %s  Orig ETA: %s" % (start, eta))
			self.setValue("eta2", "Start: %s  Orig ETA: %s" % (start, eta))

			if layer is not None and layer != 0:
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
				remains = self.eta + diff - now
				self.remains = remains
				strRemains = formatElapsed(remains)
				strNewEta = time.strftime('%H:%M:%S', time.localtime(now+remains))
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

	def setSDPrintComplete(self):		
		self.setValue("gcode", "")
		
		now = time.time()
		strNow = time.strftime('%H:%M:%S', time.localtime(now))
		elapsed = now - self.sdstartTime
		strElapsed = formatElapsed(elapsed)
		self.setValue("eta", "Print completed at %s, elapsed %s" % (strNow, strElapsed))
		self.setValue("eta2", "")
		self.sdstartTime = None


