import wx, math

MAXZOOM = 10
ZOOMDELTA = 0.1
			
def triangulate(p1, p2):
	dx = p2[0] - p1[0]
	dy = p2[1] - p1[1]
	d = math.sqrt(dx*dx + dy*dy)
	return d

#orange = wx.Colour(237, 139, 33)
dk_Gray = wx.Colour(224, 224, 224)
lt_Gray = wx.Colour(128, 128, 128)
black = wx.Colour(0, 0, 0)

toolColor = ["blue", "green", "cyan"]

class GcFrame (wx.Window):
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
		self.drawGCFirst = None
		self.drawGCLast = None
		self.highlightX = None
		self.shiftX = 0
		self.shiftY = 0
		self.toolPathsOnly = self.settings.toolpathsonly
		
		sz = [(x+1) * self.scale for x in self.buildarea]
		
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
		if evt.ShiftDown(): # scroll through lines
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
		self.currentlx = layer
		self.currentlayer = self.model.getLayer(self.currentlx)
		self.layercount = self.model.countLayers()
		
		self.layerInfo = self.model.getLayerInfo(self.currentlx)
		if self.layerInfo is None:
			return

		self.firstGLine = self.layerInfo[4][0]
		self.lastGLine = self.layerInfo[4][-1]
		self.drawGCFirst = self.layerInfo[4][0]
		self.drawGCLast = self.layerInfo[4][-1]

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
		
		self.layerInfo = self.model.getLayerInfo(lyr)
		if self.layerInfo is None:
			return

		self.firstGLine = self.layerInfo[4][0]
		self.lastGLine = self.layerInfo[4][-1]
		self.drawGCFirst = self.layerInfo[4][0]
		self.drawGCLast = self.layerInfo[4][-1]
		
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
		
	def setToolPathsOnly(self, flag):
		self.toolPathsOnly = flag
		self.redrawCurrentLayer()

	def setGCode(self, newFirst, newLast):
		self.drawGCFirst = newFirst
		self.drawGCLast = newLast
		self.redrawCurrentLayer()
		
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
		
	def drawGraph(self, dc, lyr):
		dc.SetBackground(wx.Brush(wx.Colour(255, 255, 255)))
		dc.Clear()
		
		self.drawGrid(dc)
		self.drawLayer(dc, lyr)

	def drawGrid(self, dc):
		yleft = (0 - self.offsety)*self.zoom*self.scale
		if yleft < 0: yleft = 0

		yright = (self.buildarea[1] - self.offsety)*self.zoom*self.scale
		if yright > self.buildarea[1]*self.scale: yright = self.buildarea[1]*self.scale

		for x in range(0, self.buildarea[0]+1, 10):
			if x == 0 or x == self.buildarea[0]:
				dc.SetPen(wx.Pen(black, 1))
			elif x%50 == 0:
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

		for y in range(0, self.buildarea[1]+1, 10):
			if y == 0 or y == self.buildarea[1]:
				dc.SetPen(wx.Pen(black, 1))
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
		layerNumber = layer.getLayerNumber();
		pendingPause = self.model.checkPendingPause(layerNumber)
		pauseLines = self.model.checkImmediatePause(layerNumber)
		markers = []
		
		if last_e is None:
			last_e = 0
		nn = 0
		while p:
			if prev == [None, None, None, None]:
				prev = [p[0], p[1], p[2], p[3]]
				if pendingPause and (p[6] >= self.drawGCFirst and p[6] <= self.drawGCLast):
					markers.append((prev[0], prev[1], True))
					
			elif p[7]: # axis reset
				prev = [p[0], p[1], p[2], p[3]]
				last_e = p[3]
			else:
				tool = p[4]
				if background or (p[6] >= self.drawGCFirst and p[6] <= self.drawGCLast):
					self.drawLine(dc, prev, p, last_e, tool, nn, p[8], background=background)
					if p[6]-1 in pauseLines:
						markers.append((prev[0], prev[1], False))
					
				prev = [p[0], p[1], p[2], p[3]]
			
			if prev[3] is not None:
				last_e = prev[3]
				
			p = layer.getNextMove()
			nn += 1

		for px, py, pendingFlag in markers:
			(xc, yc) = self.transform(px, self.buildarea[1]-py)
			(xt, yt) = self.transform(px-0.354, self.buildarea[1]-(py-0.354))
			(xb, yb) = self.transform(px+0.354, self.buildarea[1]-(py+0.354))
			dc.SetPen(wx.Pen("black", 2))
			dc.DrawLine(xc, yt, xc, yb)
			dc.DrawLine(xt, yc, xb, yc)
			dc.DrawLine(xt, yt, xb, yb)
			dc.DrawLine(xt, yb, xb, yt)

	def drawLine(self, dc, prev, p, last_e, tool, ln, lw, background=False):				
		if background and (p[3] is None):
			return

		t = tool
		if t < 0 or t > 2:
			t = 0
			
		if background:
			c = "gray"
			
		elif p[3] is None or p[3] == 0:
			if not self.settings.showmoves:
				return
			
			c = "black"	

		else:
			c = toolColor[t]

		w = lw * self.zoom * self.scale
		if self.toolPathsOnly:
			w = 1
			
		if (prev[0] != p[0]) or (prev[1] != p[1]):
			(x1, y1) = self.transform(prev[0], self.buildarea[1]-prev[1])
			(x2, y2) = self.transform(p[0], self.buildarea[1]-p[1])

			dc.SetPen(wx.Pen(c, w))
			dc.DrawLine(x1, y1, x2, y2)
				
		if p[3] is not None and p[3] < prev[3]: # retraction
			(x1, y1) = self.transform(p[0], self.buildarea[1]-p[1])
			dc.SetPen(wx.Pen("black", w))
			dc.DrawLine(x1, y1, x1, y1)

	def transform(self, ptx, pty):
		x = (ptx - self.offsetx + self.shiftX)*self.zoom*self.scale
		y = (pty - self.offsety - self.shiftY)*self.zoom*self.scale
		return (x, y)
		
	def setShift(self, sx, sy):
		self.shiftX = sx
		self.shiftY = sy
		self.redrawCurrentLayer()
