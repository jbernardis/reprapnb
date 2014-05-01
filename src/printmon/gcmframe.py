import wx

MAXZOOM = 10
ZOOMDELTA = 0.1
			
dk_Gray = wx.Colour(79, 79, 79)
lt_Gray = wx.Colour(138, 138, 138)

def setColor(a,b):
	res = []
	for i in range(101):
		x = [a[j] - b[j] * i / 100 for j in range(3)]
		res.append(x)
	return res

dcMat = [setColor([255,0,0], [135,0,0]), setColor([253,111,17], [72,36,15]), setColor([253,245,30], [54,54,27])]
	
def drawnColor(tool, distance):
	d = distance
	if d > 100:
		d = 100
	return dcMat[tool][d]

# dcm = [
# 		[ [255, 0, 0], [135, 0, 0] ],     # red family - for tool 0
# 		[ [253, 111, 17], [72, 36, 15] ], # orange family - for tool 1
# 		[ [253, 245, 30], [54, 54, 27] ]  # yellow family - for tool 2
# 	]
# 
# def drawnColor(tool, distance):
# 	if distance > 100: 
# 		return [dcm[tool][0][i] - dcm[tool][1][i] for i in range(3)]
# 	else:	
# 		return [dcm[tool][0][i] - distance * dcm[tool][1][i] / 100 for i in range(3)]


undrawnColors = ["blue", "green", "cyan"]

class GcmFrame (wx.Window):
	def __init__(self, parent, model, settings, buildarea):
		self.parent = parent
		self.settings = settings
		self.scale = self.settings.gcodescale
		self.zoom = 1
		self.offsety = 0
		self.offsetx = 0
		self.startPos = (0, 0)
		self.startOffset = (0, 0)
		self.buildarea = buildarea
		self.gcode = None
		self.model = None
		self.currentlayer = None
		self.currentlx = 0
		self.shiftX = 0
		self.shiftY = 0
		self.printPosition = 0
		
		sz = [x * self.scale for x in self.buildarea]
		
		wx.Window.__init__(self,parent,size=sz)
		
		self.initBuffer()
		self.Bind(wx.EVT_SIZE, self.onSize)
		self.Bind(wx.EVT_PAINT, self.onPaint)
		self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)
		self.Bind(wx.EVT_LEFT_UP, self.onLeftUp)
		self.Bind(wx.EVT_MOTION, self.onMotion)
		self.Bind(wx.EVT_MOUSEWHEEL, self.onMouseWheel, self)

		if model != None:
			self.loadModel(model)
		
	def onSize(self, evt):
		self.initBuffer()
		
	def onPaint(self, evt):
		if self.settings.usebuffereddc:
			dc = wx.BufferedPaintDC(self, self.buffer)
		else:
			dc = wx.PaintDC(self)
			self.drawGraph(dc, self.currentlayer)
		
	def onLeftDown(self, evt):
		self.startPos = evt.GetPositionTuple()
		self.startOffset = (self.offsetx, self.offsety)
		self.CaptureMouse()
		self.SetFocus()
		
	def onLeftUp(self, evt):
		if self.HasCapture():
			self.ReleaseMouse()
			
	def onMotion(self, evt):
		if evt.Dragging() and evt.LeftIsDown():
			x, y = evt.GetPositionTuple()
			dx = x - self.startPos[0]
			dy = y - self.startPos[1]
			self.offsetx = self.startOffset[0] - dx/(2*self.zoom)
			if self.offsetx < 0:
				self.offsetx = 0
			if self.offsetx > (self.buildarea[0]-self.buildarea[0]/self.zoom):
				self.offsetx = self.buildarea[0]-self.buildarea[0]/self.zoom
				
			self.offsety = self.startOffset[1] - dy/(2*self.zoom)
			if self.offsety < 0:
				self.offsety = 0
			if self.offsety > (self.buildarea[1]-self.buildarea[1]/self.zoom):
				self.offsety = self.buildarea[1]-self.buildarea[1]/self.zoom

			self.redrawCurrentLayer()
			
		evt.Skip()
		
	def onMouseWheel(self, evt):
		if evt.ControlDown(): # scroll through layers
			if self.model is not None:
				if evt.GetWheelRotation() < 0:
					if self.currentlx < self.layercount-1:
						lx = self.currentlx + 1
						self.parent.setLayer(lx)
						self.setLayer(lx)
				else:
					if self.currentlx > 0:
						lx = self.currentlx - 1
						self.parent.setLayer(lx)
						self.setLayer(lx)
						
		else: # zoom in or out
			if evt.GetWheelRotation() < 0:
				self.zoomIn()
			else:
				self.zoomOut()
					
	def zoomIn(self):
		if self.zoom < MAXZOOM:
			zoom = self.zoom + ZOOMDELTA
			self.setZoom(zoom)

	def zoomOut(self):
		if self.zoom > 1:
			zoom = self.zoom - ZOOMDELTA
			self.setZoom(zoom)

	def loadModel(self, model, layer=0, zoom=1):
		self.model = model
		self.shiftX = 0
		self.shiftY = 0
		self.printPosition = 0
		self.currentlx = layer
		self.currentlayer = self.model.getLayer(self.currentlx)
		self.layercount = self.model.countLayers()
		
		self.layerInfo = self.model.getLayerInfo(self.currentlx)
		if self.layerInfo is None:
			return

		self.hilite = self.layerInfo[4][0]
		self.firstGLine = self.layerInfo[4][0]
		self.lastGLine = self.layerInfo[4][-1]

		self.zoom = zoom
		if zoom == 1:
			self.offsetx = 0
			self.offsety = 0

		self.redrawCurrentLayer()

	def initBuffer(self):
		w, h = self.GetClientSize();
		self.buffer = wx.EmptyBitmap(w, h)
		self.redrawCurrentLayer()
		
	def setLayer(self, lyr):
		if self.model is None:
			return
		
		self.parent.setLayer(lyr)
		
		self.layerInfo = self.model.getLayerInfo(lyr)
		if self.layerInfo is None:
			return

		self.firstGLine = self.layerInfo[4][0]
		self.lastGLine = self.layerInfo[4][-1]
		
		self.currentlayer = self.model.getLayer(lyr)
		self.currentlx = lyr
		self.redrawCurrentLayer()
		
	def getCurrentLayer(self):
		return self.currentlx

	def setZoom(self, zoom):
		if zoom > self.zoom:
			oldzoom = self.zoom
			self.zoom = zoom
			cx = self.offsetx + self.buildarea[0]/oldzoom/2.0
			cy = self.offsety + self.buildarea[1]/oldzoom/2.0
			self.offsetx = cx - self.buildarea[0]/self.zoom/2.0
			self.offsety = cy - self.buildarea[1]/self.zoom/2.0
		else:
			oldzoom = self.zoom
			self.zoom = zoom
			cx = self.offsetx + self.buildarea[0]/oldzoom/2.0
			cy = self.offsety + self.buildarea[1]/oldzoom/2.0
			self.offsetx = cx - self.buildarea[0]/self.zoom/2.0
			self.offsety = cy - self.buildarea[1]/self.zoom/2.0
			if self.offsetx < 0:
				self.offsetx = 0
			if self.offsetx > (self.buildarea[0]-self.buildarea[0]/self.zoom):
				self.offsetx = self.buildarea[0]-self.buildarea[0]/self.zoom
				
			if self.offsety < 0:
				self.offsety = 0
			if self.offsety > (self.buildarea[1]-self.buildarea[1]/self.zoom):
				self.offsety = self.buildarea[1]-self.buildarea[1]/self.zoom

		self.redrawCurrentLayer()
	
	def setPrintPosition(self, p, sync=True):
		if self.model is None:
			return
		l = self.model.findLayerByLine(p)
		if l is None:
			return

		self.printPosition = p
		if l == self.currentlx:
			self.redrawCurrentLayer()
		elif sync:
			self.setLayer(l)
		
	def redrawCurrentLayer(self):
		if self.settings.usebuffereddc:
			dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
		else:
			dc = wx.ClientDC(self)

		self.drawGraph(dc, self.currentlayer)

		if self.settings.usebuffereddc:
			del dc
			self.Refresh()
			self.Update()
			
	def eraseGraph(self):
		if self.settings.usebuffereddc:
			dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
		else:
			dc = wx.ClientDC(self)
			
		self.clearGraph(dc)
		
	def clearGraph(self, dc):
		dc.SetBackground(wx.Brush("black"))
		dc.Clear()
		
		self.drawGrid(dc)
		
		
	def drawGraph(self, dc, lyr):
		self.clearGraph(dc)
		self.drawLayer(dc, lyr)

	def drawGrid(self, dc):
		yleft = (0 - self.offsety)*self.zoom*self.scale
		if yleft < 0: yleft = 0

		yright = (self.buildarea[1] - self.offsety)*self.zoom*self.scale
		if yright > self.buildarea[1]*self.scale: yright = self.buildarea[1]*self.scale

		for x in range(0, self.buildarea[0], 10):
			if x%50 == 0:
				dc.SetPen(wx.Pen(lt_Gray, 1))
			else:
				dc.SetPen(wx.Pen(dk_Gray, 1))
			x = (x - self.offsetx)*self.zoom*self.scale
			if x >= 0 and x <= self.buildarea[0]*self.scale:
				dc.DrawLine(x, yleft, x, yright)
			
		xtop = (0 - self.offsetx)*self.zoom*self.scale
		if xtop <0: xtop = 0

		xbottom = (self.buildarea[0] - self.offsetx)*self.zoom*self.scale
		if xbottom > self.buildarea[0]*self.scale: xbottom = self.buildarea[0]*self.scale

		for y in range(0, self.buildarea[1], 10):
			if y%50 == 0:
				dc.SetPen(wx.Pen(lt_Gray, 1))
			else:
				dc.SetPen(wx.Pen(dk_Gray, 1))
			y = (y - self.offsety)*self.zoom*self.scale
			if y >= 0 and y <= self.buildarea[1]*self.scale:
				dc.DrawLine(xtop, y, xbottom, y)
			
	def drawLayer(self, dc, layer):
		if layer is None:
			return
		
		pl = layer.getPrevLayer()
		if pl and self.settings.showprevious:
			self.drawOneLayer(dc, pl, background=True)
		
		self.drawOneLayer(dc, layer)
		
	def drawOneLayer(self, dc, layer, background=False):
		if layer is None:
			return
		
		prev = [None, None, None, None]

		p = layer.getLayerStart()
		last_e = p[3]
		if last_e is None:
			last_e = 0
		while p:
			if prev == [None, None, None, None]:
				prev = [p[0], p[1], p[2], p[3]]
			elif p[7]: # axis reset
				prev = [p[0], p[1], p[2], p[3]]
				last_e = p[3]
			else:
				tool = p[4]
				self.drawLine(dc, prev, p, last_e, tool, p[8], background=background)
					
				prev = [p[0], p[1], p[2], p[3]]
			
			if prev[3] is not None:
				last_e = prev[3]
				
			p = layer.getNextMove()

	def drawLine(self, dc, prev, p, last_e, tool, lw, background=False):				
		if background and (p[3] is None):
			return

		t = tool
		if t < 0 or t > 2:
			t = 0
			
		if p[3] is None or p[3] == 0:
			if not self.settings.showmoves:
				return
			if p[6] <= self.printPosition:
				c = "dimgray"	
			else:
				c = "white"

		elif p[6] <= self.printPosition:
			c = drawnColor(t, self.printPosition - p[6])
		else:
			c = undrawnColors[t]
					
		if background:
			c = "dimgray"
			
		w = lw * self.zoom * self.scale

		if (prev[0] != p[0]) or (prev[1] != p[1]):
			(x1, y1) = self.transform(prev[0], self.buildarea[1]-prev[1])
			(x2, y2) = self.transform(p[0], self.buildarea[1]-p[1])

			dc.SetPen(wx.Pen(c, w))
			dc.DrawLine(x1, y1, x2, y2)
				
		if p[3] is not None and p[3] < prev[3] and self.settings.showmoves:
			(x1, y1) = self.transform(p[0], self.buildarea[1]-p[1])
			dc.SetPen(wx.Pen("white", w))
			dc.DrawLine(x1, y1, x1, y1)
					

	def transform(self, ptx, pty):
		x = (ptx - self.offsetx + self.shiftX)*self.zoom*self.scale
		y = (pty - self.offsety - self.shiftY)*self.zoom*self.scale
		return (x, y)
