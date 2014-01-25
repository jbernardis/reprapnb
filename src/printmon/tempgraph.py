import wx

MAXX = 240
MAXY = 250

scale = 1.5
			
dk_Gray = wx.Colour(79, 79, 79)
lt_Gray = wx.Colour(138, 138, 138)

colors = { "Bed": "cyan", "HE0": "red", "HE1": "orange", "HE2": "yellow"}
columns = { "Bed": 150, "HE0": 50, "HE1": 80, "HE2": 110}
rowOffset = { "Bed": 30, "HE0": 0, "HE1": 20, "HE2": 40}

def htrToColor(h):
	if h not in colors.keys():
		return "red"
	else:
		return colors[h]
	
def htrToColumn(h):
	if h not in columns.keys():
		return None
	else:
		return columns[h]

class TempGraph (wx.Window):
	def __init__(self, parent, settings):
		self.settings = settings
		self.parent = parent
		self.font = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		
		self.targets = []
		
		sz = [x * scale + 100 for x in [MAXX, MAXY]]
		wx.Window.__init__(self,parent,wx.ID_ANY,size=sz,style=wx.SIMPLE_BORDER)
		
		self.graph = Graph(self, settings)
		
		self.sizerMain = wx.GridBagSizer()
		self.sizerMain.AddSpacer((10,10), pos=(0,1))
		self.sizerMain.AddSpacer((40,40), pos=(2,0))
		self.sizerMain.AddSpacer((80,40), pos=(2,2))
		self.sizerMain.Add(self.graph, pos=(1,1))
		self.SetSizer(self.sizerMain)
		self.Layout()
		self.Fit()
		self.yLegend()
		self.xLegend()
		
	def yLegend(self):
		for y in range(50, MAXY+1, 50):
			ty = (MAXY - y) * scale
			t = wx.StaticText(self, wx.ID_ANY, "%3d" % y, pos=(5, ty), size=(30, -1), style=wx.ALIGN_RIGHT)
			t.SetFont(self.font)
			
	def xLegend(self):
		xf = int(MAXX/60)
		for x in range(MAXX/60):
			tx = x * scale
			t = wx.StaticText(self, wx.ID_ANY, "%dm" % (x-xf), pos=(tx*60+30, MAXY*scale+10), size=(30, -1), style=wx.ALIGN_CENTER)
			t.SetFont(self.font)
			
	def setHeaters(self, heaters):
		self.heaters = heaters
			
	def setTargets(self, ntargets):
		for i in self.targets:
			i.Destroy()

		tx = MAXX*scale+45
		self.targets = []			
		for tgt in ntargets.keys():
			y = ntargets[tgt]
			if y > 0:
				ty = (MAXY - y) * scale
				t = wx.StaticText(self, wx.ID_ANY, "%3d %s" % (y, tgt), pos=(tx, ty), size=(-1, -1), style=wx.ALIGN_RIGHT)
				t.SetForegroundColour(htrToColor(tgt))
				t.SetFont(self.font)
				self.targets.append(t)
			
		self.graph.updateTargets(ntargets)
		
	def setTemps(self, tempData):
		self.graph.updateData(tempData)

		
class Graph (wx.Window):
	def __init__(self, parent, settings):
		self.parent = parent
		self.settings = settings
		self.targets = {}
		self.tempData = {}
		self.font = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		
		sz = [x * scale for x in [MAXX, MAXY]]
		wx.Window.__init__(self,parent,wx.ID_ANY,size=sz)
		
		self.initBuffer()
		self.Bind(wx.EVT_SIZE, self.onSize)
		self.Bind(wx.EVT_PAINT, self.onPaint)
		
	def onSize(self, evt):
		self.initBuffer()
		
	def onPaint(self, evt):
		dc = wx.BufferedPaintDC(self, self.buffer)

	def initBuffer(self):
		w, h = self.GetClientSize();
		self.buffer = wx.EmptyBitmap(w, h)
		self.redrawGraph()
		
	def updateTargets(self, targets):
		self.targets = targets.copy()
		self.redrawGraph()
	
	def updateData(self, data):
		self.tempData = data.copy()
		self.redrawGraph()
	
	def redrawGraph(self):
		dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
		self.drawGraph(dc)
		del dc
		self.Refresh()
		self.Update()
			
	def drawGraph(self, dc):
		dc.SetBackground(wx.Brush("black"))
		dc.Clear()
		
		self.drawGrid(dc)
		for h in self.tempData.keys():
			self.draw1Graph(dc, h, self.tempData[h])

	def drawGrid(self, dc):
		xleft = 0
		xright = MAXX

		for y in range(0, MAXY, 10):
			if y%50 == 0:
				dc.SetPen(wx.Pen(lt_Gray, 1))
			else:
				dc.SetPen(wx.Pen(dk_Gray, 1))
			if y >= 0 and y <= MAXY:
				self.drawLine(dc, (xleft, y), (xright, y))
			
		ytop = 0
		ybottom = MAXY

		for x in range(0, MAXX, 10):
			if x%60 == 0:
				dc.SetPen(wx.Pen(lt_Gray, 1))
			else:
				dc.SetPen(wx.Pen(dk_Gray, 1))
			#x = MAXX - x
			if x >= 0 and x <= MAXX:
				self.drawLine(dc, (x, ytop), (x, ybottom))
				
		for tgt in self.targets.keys():
			c = htrToColor(tgt)
			dc.SetPen(wx.Pen(c, 1, wx.SHORT_DASH))
			y = self.targets[tgt]
			if y > 0 and y <= MAXY:
				self.drawLine(dc, (xleft, y), (xright, y))
				
	def draw1Graph(self, dc, htr, data):
		c = htrToColor(htr)
		points = []
		lx = len(data)
		for i in range(lx):
			if data[i] is not None:
				points.append(wx.Point((MAXX - lx + i) * scale, (MAXY - data[i]) * scale))
				
		if len(points) < 2: return
		
		hcol = htrToColumn(htr)
		if hcol is not None and data[lx-1] is not None:
			dc.SetFont(self.font)
			dc.SetTextBackground(wx.Colour(255, 255, 255))
			dc.SetTextForeground(c)
			hrow = data[lx-1] + rowOffset[htr]
			dc.DrawText("%s: %.1f" % (htr, data[lx-1]), hcol, (MAXY-hrow) * scale)
		
		dc.SetPen(wx.Pen(c, 3))
		dc.DrawLines(points)

	def drawLine(self, dc, pa, pb):				
		x1 = pa[0] * scale
		y1 = (MAXY-pa[1]) * scale
		x2 = pb[0] * scale
		y2 = (MAXY-pb[1]) * scale

		dc.DrawLine(x1, y1, x2, y2)
