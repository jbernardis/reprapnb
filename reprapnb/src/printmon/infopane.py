
import wx
import time

from tools import formatElapsed

filetags = { "filename" : "Name:" }
filetagorder = ["filename"]

layertags = { "layer" : "Layer Number:", "minmaxxy": "Min/Max X,Y:", "filament" : "Filament Usage:", "layertime": "Layer Print Time:", "gclines": "G Code Lines:"}
layertagorder = ["layer", "minmaxxy", "filament", "gclines", "layertime"]

printtags = { "gcode": "Print Position:", "eta": "Print Times:"}
printtagorder = ["gcode", "eta"]


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

		wx.Window.__init__(self, parent, wx.ID_ANY, size=(400, -1), style=wx.SIMPLE_BORDER)		
		self.sizerInfo = wx.BoxSizer(wx.HORIZONTAL)
		self.sizerTag = wx.BoxSizer(wx.VERTICAL)
		self.sizerValue = wx.BoxSizer(wx.VERTICAL)
		
		self.dc = wx.WindowDC(self)
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
		self.dc.SetFont(f)

		self.sizerTag.AddSpacer((3,3))
		self.sizerValue.AddSpacer((3,3))

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

		self.setValue("layer", "Layer number/total layers (z height)")
		self.setValue("minmaxxy", "(minx, miny) - (maxx, maxy)")
		self.setValue("filament", "used in layer/totao used (used in previous)")
		self.setValue("gclines", "first gc line/last gc line in layer")
		self.setValue("layertime", "time in layer/total print duration")
		self.setValue("gcode", "Print pos/total lines (%done)")
		self.setValue("eta", "Start time, elapsed time, ETA, % ahead/behind")

	def addTags(self, title, tags, tagorder):
		f = wx.Font(16, wx.SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD)
		self.dc.SetFont(f)
		w, h = self.dc.GetTextExtent(title)
		t = wx.StaticText(self, wx.ID_ANY, title, style=wx.ALIGN_RIGHT, size=(w, h+5))
		t.SetFont(f)
		self.sizerTag.Add(t, flag=wx.ALIGN_LEFT | wx.TOP, border=5)
		self.sizerValue.AddSpacer((w, h+10))

		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
		self.dc.SetFont(f)
		for t in tagorder:
			text = tags[t]
			w, h = self.dc.GetTextExtent(text)

			st = wx.StaticText(self, wx.ID_ANY, text, style=wx.ALIGN_RIGHT, size=(w, h+5))
			st.SetFont(f)
			self.sizerTag.Add(st, flag=wx.ALIGN_RIGHT | wx.TOP, border=5)
			self.sizerTag.AddSpacer((3,3))
	
			self.wValues[t] = wx.TextCtrl(self, wx.ID_ANY, "", size=(400, h+10), style=wx.TE_LEFT)
			self.wValues[t].SetFont(f)
			self.sizerValue.Add(self.wValues[t])
			self.sizerValue.AddSpacer((3,3))

	def setValue(self, tag, value):
		if tag not in self.wValues.keys():
			print "bad key ", tag
			return

		self.wValues[tag].SetValue(value)
		
	def setFileInfo(self, filename, duration, gcount, layers, filament, layertimes):
		self.setValue("filename", filename)
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
			
	
		
	def setLayerInfo(self, layernbr, z, minxy, maxxy, filament, prevfilament, ltime, gclines):
		self.gclines = gclines
		self.layernbr = layernbr
		if self.layers == 0:
			self.setValue("layer", "%d (%.2f)" % (layernbr, z))
		else:
			self.setValue("layer", "%d/%d (%.2f)" % (layernbr, self.layers, z))
			
		self.setValue("minmaxxy", "(%.2f, %.2f) <-> (%.2f, %.2f)" % (minxy[0], minxy[1], maxxy[0], maxxy[1]))
		if self.filament == 0:
			self.setValue("filament", "%.2f (%.2f)" % (filament, prevfilament))
		else:
			self.setValue("filament", "%.2f/%.2f (%.2f)" % (filament, self.filament, prevfilament))
		self.setValue("gclines", "%d -> %d" % (gclines[0], gclines[1]))
		if self.duration == 0:
			self.setValue("layertime", "%s" % formatElapsed(ltime))
		else:
			self.setValue("layertime", "%s/%s" % (formatElapsed(ltime), formatElapsed(self.duration)))
	
	def setPrintInfo(self, position, layer, gcodelines, layertime):
		self.position = position
		pct = "??"
		if self.gcount != 0:
			pct = "%.2f" % (float(self.position) / float(self.gcount) * 100.0)
		
		self.setValue("gcode", "Line %d/%d total lines (%s%%)" % (position, self.gcount, pct))
		start = time.strftime('%H:%M:%S', time.localtime(self.startTime))
		elapsed = formatElapsed(time.time() - self.startTime)
		eta = time.strftime('%H:%M:%S', time.localtime(self.eta))
		
		self.setValue("eta", "Start: %s  Elapsed: %s  ETA: %s" % (start, elapsed, eta))
		
		if layer is not None:
			expectedTime = self.prevTimes[layer]
			delta = 0
			print "Expected time to start of layer: ", expectedTime
			if position >= gcodelines[0] and position <= gcodelines[1]:
				lct = gcodelines[1] - gcodelines[0]
				lpos = position - gcodelines[0]
				lpct = float(lpos)/float(lct)
				print "Percent through current layer = ", lpct * 100.0
				
				delta = layertime * lpct
			print "delta = ", delta
			expectedTime += delta
			print "Expected total elapsed time: ", expectedTime
			
			diff = elapsed - expectedTime
			pctDiff = float(diff) / float(expectedTime) * 100.0
			print "PCT diff = ", pctDiff
		
	
	def setStartTime(self, start):
		self.startTime = start
		self.eta = start + self.duration
		self.setPrintInfo(0)
		
	def setPrintComplete(self):
		end = time.time();
		strEnd = time.strftime('%H:%M:%S', time.localtime(end))
		
		elapsed = end - self.startTime
		strElapsed = formatElapsed(elapsed)
		
		diff = elapsed - self.duration
		pctDiff = float(diff) / float(self.duration) * 100.0
		
		self.setValue("gcode", "")
		self.setValue("eta", "Print completed at %s, elapsed %s (%.2f%%)" % (strEnd, strElapsed, pctDiff))


