'''
Created on Apr 10, 2013

@author: Jeff
'''
import wx
import os

MAXZOOM = 10
MAXX = 240
MAXY = 250

scale = 1.5
			
dk_Gray = wx.Colour(79, 79, 79)
lt_Gray = wx.Colour(138, 138, 138)

class TempGraph (wx.Window):
	def __init__(self, parent, settings):
		self.settings = settings
		self.parent = parent
		
		self.targets = []
		
		sz = [x * scale + 100 for x in [MAXX, MAXY]]
		wx.Window.__init__(self,parent,wx.ID_ANY,size=sz,style=wx.SIMPLE_BORDER)
		
		self.graph = Graph(self, settings, self.parent.printersettings)
		
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
		#FIXIT
		self.setTargets([[60, "HBP", "blue"], [235, "HE1", "red"]])
		
	def yLegend(self):
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
		for y in range(50, MAXY+1, 50):
			ty = (MAXY - y) * scale
			t = wx.StaticText(self, wx.ID_ANY, "%3d" % y, pos=(5, ty), size=(30, -1), style=wx.ALIGN_RIGHT)
			t.SetFont(f)
			
	def xLegend(self):
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
		xf = int(MAXX/60)
		for x in range(MAXX/60):
			tx = x * scale
			t = wx.StaticText(self, wx.ID_ANY, "%dm" % (x-xf), pos=(tx*60+30, MAXY*scale+10), size=(30, -1), style=wx.ALIGN_CENTER)
			t.SetFont(f)
			
	def setTargets(self, newTargets):
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
		for i in self.targets:
			i.Destroy()

		tx = MAXX*scale+45
		self.targets = []			
		for tgt in newTargets:
			ty = (MAXY - tgt[0]) * scale
			t = wx.StaticText(self, wx.ID_ANY, "%3d %s" % (tgt[0], tgt[1]), pos=(tx, ty), size=(-1, -1), style=wx.ALIGN_RIGHT)
			t.SetForegroundColour(tgt[2])
			t.SetFont(f)
			self.targets.append(t)
			
		self.graph.updateTargets(newTargets)

	#FIXIT			
	def getProfileHeaterValue(self, idx=None):
		self.temperatures = self.app.slicer.type.getProfileTemps()
		maxExt = self.printersettings.settings['extruders']
		if len(self.temperatures) < 2:
			self.logger.LogError("No hot end temperatures configured in your profile")
		if len(self.temperatures) != maxExt+1:
			self.logger.LogWarning("Your profile does not have the same number of extruders configured")
			t = self.temperatures[1]
			ntemps = len(self.temperatures)
			for i in range(maxExt - ntemps + 1):
				self.temperatures.append(t)
		if idx is not None:
			return self.temperatures[idx]
		
class Graph (wx.Window):
	def __init__(self, parent, settings, printersettings):
		self.parent = parent
		self.settings = settings
		self.printersettings = printersettings
		self.targets = []
		
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
		
	def updateTargets(self, newTargets):
		self.targets = newTargets[:]
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
				
		for tgt in self.targets:
			dc.SetPen(wx.Pen(tgt[2], 2))
			y = tgt[0]
			if y >= 0 and y <= MAXY:
				self.drawLine(dc, (xleft, y), (xright, y))

	def drawLine(self, dc, pa, pb):				
		(x1, y1) = self.transform(pa[0], MAXY-pa[1])
		(x2, y2) = self.transform(pb[0], MAXY-pb[1])

		dc.DrawLine(x1, y1, x2, y2)

	def transform(self, ptx, pty):
		x = ptx * scale
		y = pty * scale
		return (x, y)
