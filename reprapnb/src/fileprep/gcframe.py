'''
Created on Apr 10, 2013

@author: Jeff
'''
import wx, math

MAXZOOM = 10
			
def triangulate(p1, p2):
	dx = p2[0] - p1[0]
	dy = p2[1] - p1[1]
	d = math.sqrt(dx*dx + dy*dy)
	return d

orange = wx.Colour(237, 139, 33)
dk_Gray = wx.Colour(79, 79, 79)
lt_Gray = wx.Colour(138, 138, 138)

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
		self.highlightX = None
		self.shiftX = 0
		self.shiftY = 0
		
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
		if evt.ShiftDown(): # scroll through lines
			if self.model is not None:
				if evt.GetWheelRotation() < 0:
					if self.hilite < self.lastGLine:
						self.hilite += 1
						self.parent.setGCode(self.hilite)
						self.redrawCurrentLayer()
				else:
					if self.hilite > self.firstGLine:
						self.hilite -= 1
						self.parent.setGCode(self.hilite)
						self.redrawCurrentLayer()
						
		elif evt.ControlDown(): # scroll through layers
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
			zoom = self.zoom + 1
			self.setZoom(zoom)

	def zoomOut(self):
		if self.zoom > 1:
			zoom = self.zoom - 1
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
		
		self.layerInfo = self.model.getLayerInfo(lyr)
		if self.layerInfo is None:
			return

		self.hilite = self.layerInfo[4][0]
		self.firstGLine = self.layerInfo[4][0]
		self.lastGLine = self.layerInfo[4][-1]
		
		self.currentlayer = self.model.getLayer(lyr)
		self.currentlx = lyr
		self.redrawCurrentLayer()
		
	def getCurrentLayer(self):
		return self.currentlx

	def setZoom(self, zoom):
		self.zoom = zoom
		if self.offsetx < 0:
			self.offsetx = 0
		if self.offsetx > (self.buildarea[0]-self.buildarea[0]/self.zoom):
			self.offsetx = self.buildarea[0]-self.buildarea[0]/self.zoom
			
		if self.offsety < 0:
			self.offsety = 0
		if self.offsety > (self.buildarea[1]-self.buildarea[1]/self.zoom):
			self.offsety = self.buildarea[1]-self.buildarea[1]/self.zoom

		self.redrawCurrentLayer()

	def setGCode(self, l):
		self.hilite = l
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
		dc.SetBackground(wx.Brush("black"))
		dc.Clear()
		
		self.drawGrid(dc)
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
			else:
				self.drawLine(dc, prev, p, last_e, background=background)
					
				prev = [p[0], p[1], p[2], p[3]]
			
			if prev[3] is not None:
				last_e = prev[3]
				
			p = layer.getNextMove()

	def drawLine(self, dc, prev, p, last_e, background=False):				
		if background and (p[3] is None):
			return
			
		if background:
			c = "gray"
			w = 1.0
			
		elif p[3] is None or p[3] == 0:
			if not self.settings.showmoves:
				return
			
			c = "white"	
			w = 1.0

		else:
			edist = p[3] - last_e
			evolume = edist * 1.5 * 1.5 * 3.14159
			dist = triangulate(prev, p)
				
			if p[4] < 1200:
				c = orange
			elif p[4] < 3000:
						c = "red"
			elif p[4] < 3600:
				c = "blue"
			elif p[4] >= 7200:
				c = "green"
			else:
				c = "purple"

			if dist == 0:
				w = 1.0
			else:				
				w = evolume/dist * 10
				
			w = w * self.zoom
				
		if p[5] == self.hilite:
			w = w * 3

		if (prev[0] != p[0]) or (prev[1] != p[1]):
			(x1, y1) = self.transform(prev[0], self.buildarea[1]-prev[1])
			(x2, y2) = self.transform(p[0], self.buildarea[1]-p[1])

			dc.SetPen(wx.Pen(c, w))
			dc.DrawLine(x1, y1, x2, y2)
			if p[5] == self.hilite:
				dc.SetPen(wx.Pen("white", 1))
				dc.DrawLine(x1, y1, x2, y2)
				
		if p[3] is not None and p[3] < prev[3]:
			(x1, y1) = self.transform(p[0], self.buildarea[1]-p[1])
			dc.SetPen(wx.Pen("white", w))
			dc.DrawLine(x1, y1, x1, y1)
					

	def transform(self, ptx, pty):
		x = (ptx - self.offsetx + self.shiftX)*self.zoom*self.scale
		y = (pty - self.offsety - self.shiftY)*self.zoom*self.scale
		return (x, y)
		
	def setShift(self, sx, sy):
		self.shiftX = sx
		self.shiftY = sy
		self.redrawCurrentLayer()
