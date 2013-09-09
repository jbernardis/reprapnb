
import wx

filetags = { "filename" : "Name:" }
filetagorder = ["filename"]

layertags = { "layer" : "Layer Number:", "minmaxxy": "Min/Max X,Y:", "filament" : "Filament Usage:", "layertime": "Layer Print Time:"}
layertagorder = ["layer", "minmaxxy", "filament", "layertime"]

printtags = { "gcode": "Print Position:", "eta": "Print Times:"}
printtagorder = ["gcode", "eta"]


class InfoPane (wx.Window):
	def __init__(self, parent, app):
		self.parent = parent
		self.app = app
		self.logger = self.app.logger
		self.wValues = {}

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


