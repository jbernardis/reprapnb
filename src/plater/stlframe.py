'''
Created on Aug 16, 2012

@author: Jeff
'''

import wx
import math


SHIFT_MASK = 0x0001

class Map:
	def __init__(self, buildarea):
		self.width = int(buildarea[0])
		self.height = int(buildarea[1])
		self.map = [[0 for j in range(self.width)] for i in range(self.height)]
		
	def mark(self, sx, sy, width, height):
		for x in range(int(width)):
			for y in range(int(height)):
				if sx+x >= 0 and sx+x < self.width and sy+y >= 0 and sy+y <self.height:
					self.map[sx+x][sy+y] = 1
					
	def fits(self, x, y, width, height):
		for dx in range(int(width)):
			for dy in range(int(height)):
				if self.map[x+dx][y+dy] != 0:
					return False
		return True
					
	def find(self, width, height):
		for x in range(int(self.width-width)):
			for y in range(int(self.height-height)):
				if self.fits(x, y, width, height):
					return (x,y)
				
		return (None, None)
	
class StlItem():
	def __init__(self, stl, iD):
		self.stl = stl
		self.iD = iD
		self.points = []
		self.selectable = False
		
	def getStl(self):
		return self.stl
		
	def setPoints(self, d):
		self.points = d
		
	def getPoints(self):
		return self.points
	
	def isSelectable(self):
		return self.selectable
	
	def setSelectable(self, flag=True):
		self.selectable = flag
		
	def getId(self):
		return self.iD

class StlFrame(wx.Window):
	def __init__(self, parent, scale=1, buildarea=[200, 200]):
		self.scale = scale
		size=[200*self.scale+13, 200*self.scale+13]
		wx.Window.__init__(self, parent, size=size, style=wx.SIMPLE_BORDER)
		self.parent = parent
		
		self.usebuffereddc = True
		
		self.gridOffset = 5
		self.arrangeMargin = 2
		
		self.startx = 0
		self.starty = 0
		
		self.offsetx = 0
		self.offsety = 0
		self.zoom = 1
		
		self.selection = None
		self.stlItems = []
		self.buildarea = buildarea
		
		self.initBuffer()
		self.Bind(wx.EVT_SIZE, self.onSize)
		self.Bind(wx.EVT_PAINT, self.onPaint)
		self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)
		self.Bind(wx.EVT_LEFT_UP, self.onLeftUp)
		self.Bind(wx.EVT_MOTION, self.onMotion)
		self.Bind(wx.EVT_MOUSEWHEEL, self.onMouseWheel, self)
		self.Bind(wx.EVT_KEY_DOWN, self.onKey)

	def onKey(self, event):
		k = event.GetKeyCode()
		if k == wx.WXK_LEFT:
			self.moveStl(-1, 0)
		elif k == wx.WXK_RIGHT:
			self.moveStl(1, 0)
		elif k == wx.WXK_UP:
			self.moveStl(0, 1)
		elif k == wx.WXK_DOWN:
			self.moveStl(0, -1)
		else:
			event.Skip()
			return
		self.redrawStl()
	
	def onLeftDown(self, event):
		self.startx, self.starty = event.GetPositionTuple()
		nx, ny = self.untransform(self.startx, self.starty)
		ny = self.buildarea[1]-ny
		self.startx = self.startx/float(self.scale)
		self.starty = self.starty/float(self.scale)
		match = False
		for itm in reversed(self.stlItems):
			if itm is None: continue
			if itm.getStl().isInside(nx, ny):
				self.setSelection(itm.getId())
				self.parent.onFrameClick(itm.getId())
				match = True
				break

		if match:				
			self.startOffset = (self.offsetx, self.offsety)
			self.CaptureMouse()
			self.SetFocus()
			self.redrawStl()
		
	def onLeftUp(self, evt):
		if self.HasCapture():
			self.ReleaseMouse()

	def onMotion(self, event):
		if self.HasCapture() and event.Dragging() and event.LeftIsDown():
			x, y = event.GetPositionTuple()
			x = x/float(self.scale)
			y = y/float(self.scale)
			self.moveStl((x - self.startx), (self.starty - y))
			self.startx = x
			self.starty = y
			
		event.Skip()
		
	def onSize(self, evt):
		self.initBuffer()
		
	def onPaint(self, evt):
		if self.usebuffereddc:
			dc = wx.BufferedPaintDC(self, self.buffer)
		else:
			dc = wx.PaintDC(self)
			self.drawStl(dc)
		
	def onMouseWheel(self, event):
		if self.selection is not None:
			if event.GetWheelRotation() < 0:
				if event.ShiftDown():
					deg = 5
				else:
					deg = 1
			else:
				if event.ShiftDown():
					deg = -5
				else:
					deg = -1
			self.rotateStl(deg)
		else:
			event.Skip()
			
	def doRotate(self, deg):
		if self.selection is None:
			return
		self.rotateStl(deg)
			
	def moveStl(self, dx, dy):
		if self.selection is None:
			return
		itm = self.stlItems[self.selection]
		self.parent.setModified(itmId=itm.getId())
		stlObj = itm.getStl()
		stlObj.deltaTranslation(dx, dy)

		d = []
		for x,y in stlObj.hull:
			x += dx
			y += dy
			d.append((x,y))
			
		stlObj.adjustHull(d)
		self.setHull(itm)
		self.redrawStl()
		
	def rotateStl(self, angle):
		if self.selection is None:
			return

		itm = self.stlItems[self.selection]
		self.parent.setModified(itmId=itm.getId())
		stlObj = itm.getStl()
		stlObj.deltaRotation(angle)

		rads = math.radians(angle)
		cos = math.cos(rads)
		sin = math.sin(rads)
		
		d = []
		for x,y in stlObj.hull:
			xp = (x-stlObj.hxCenter)*cos - (y-stlObj.hyCenter)*sin
			xp += stlObj.hxCenter
			
			yp = (x-stlObj.hxCenter)*sin + (y-stlObj.hyCenter)*cos
			yp += stlObj.hyCenter
			d.append((xp,yp))
			
		stlObj.adjustHull(d)
		self.setHull(itm)
		self.redrawStl()

	def scaleStl(self, sf):
		if self.selection is None:
			return
		
		itm = self.stlItems[self.selection]
		self.parent.setModified(itmId=itm.getId())
		stlObj = itm.getStl()
		stlObj.deltaScale(sf)
		
		d = []
		for x,y in stlObj.hull:
			xp = (x-stlObj.hxCenter)*(sf) + stlObj.hxCenter
			yp = (y-stlObj.hyCenter)*(sf) + stlObj.hyCenter
			d.append((xp,yp))

		stlObj.adjustHull(d)
		self.setHull(itm)
		self.redrawStl()
		
	def applyDeltas(self):
		objlist = []
		for itm in self.stlItems:
			if itm is None: continue
			objlist.append(itm.getStl())
							
		for o in objlist:
			itemId = o.getId()
			if itemId is None: continue
			itm = self.stlItems[itemId]
			stlObj = itm.getStl()
			stlObj.applyDeltas()
			self.setHull(itm)
		
	def setSelection(self, itemId):
		if not self.stlItems[itemId].isSelectable():
			return

		if self.selection == itemId:
			return
				
		self.selection = itemId
		self.redrawStl()
		
	def getSelection(self):
		return self.selection
	
	def getSelectedStl(self):
		if self.selection is None:
			return None
		
		return self.stlItems[self.selection].getStl()
	
	def initBuffer(self):
		w, h = self.GetClientSize();
		self.buffer = wx.EmptyBitmap(w, h)
		self.redrawStl()
		
	def redrawStl(self):
		if self.usebuffereddc:
			dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
		else:
			dc = wx.ClientDC(self)

		self.drawStl(dc)

		if self.usebuffereddc:
			del dc
			self.Refresh()
			self.Update()
		
	def drawStl(self, dc):
		dc.SetBackground(wx.Brush("white"))
		dc.Clear()
		
		self.drawGrid(dc)

		dc.SetPen(wx.Pen(wx.BLACK, 1))
		hbrush = wx.Brush(wx.Colour(139,199,164))
		nbrush = wx.Brush(wx.Colour(192,192,192))
		for itm in self.stlItems:
			if itm is None:
				continue
			if itm.getId() == self.selection:
				dc.SetBrush(hbrush)
			else:
				dc.SetBrush(nbrush)
			dc.DrawPolygon(itm.getPoints())

	def drawGrid(self, dc):
		ltGray = wx.Pen(wx.Colour(192,192,192), 1)
		dkGray = wx.Pen(wx.Colour(128,128,128), 1)
		
		yleft = 0

		yright = self.buildarea[1]*self.zoom*self.scale
		if yright > self.buildarea[1]*self.scale: yright = self.buildarea[1]*self.scale

		for x in range(0, self.buildarea[0]+1, 10):
			if x%50 == 0:
				dc.SetPen(dkGray)
			else:
				dc.SetPen(ltGray)
			x = x*self.zoom*self.scale
			if x >= 0 and x <= self.buildarea[0]*self.scale:
				dc.DrawLine(x+self.gridOffset, yleft+self.gridOffset, x+self.gridOffset, yright+self.gridOffset)
			
		xtop = 0

		xbottom = self.buildarea[0]*self.zoom*self.scale
		if xbottom > self.buildarea[0]*self.scale: xbottom = self.buildarea[0]*self.scale

		for y in range(0, self.buildarea[1]+1, 10):
			if y%50 == 0:
				dc.SetPen(dkGray)
			else:
				dc.SetPen(ltGray)
			y = y*self.zoom*self.scale
			if y >= 0 and y <= self.buildarea[1]*self.scale:
				dc.DrawLine(xtop+self.gridOffset, y+self.gridOffset, xbottom+self.gridOffset, y+self.gridOffset)
				
	def setHull(self, itm):
		d = []
		for x,y in itm.stl.hull:
			nx, ny = self.transform(x,self.buildarea[1]-y)
			d.append(wx.Point(nx, ny))
		itm.setPoints(d)
			
	def addStl(self, stlObject, highlight=False):
		itmID = len(self.stlItems)
		stlObject.setId(itmID)
		itm = StlItem(stlObject, itmID)
		self.stlItems.append(itm)
		self.setHull(itm)
		itm.setSelectable()
		if highlight:
			self.setSelection(itmID)
		self.redrawStl()
			
	def delStl(self):
		if self.selection is None:
			return

		self.stlItems[self.selection] = None
		self.selection = None
		if self.countObjects() == 0:
			self.stlItems = []
		self.redrawStl()
		
	def delAll(self):
		self.selection = None
		self.stlItems = []
		self.redrawStl()
		
	def arrange(self):
		def cmpobj(a, b):
			return cmp(b.hArea, a.hArea)
		
		omap = Map(self.buildarea)
		maxx = maxy = -99999
		minx = miny = 99999
		
		rc = True

		objlist = []
		for itm in self.stlItems:
			if itm is None: continue
			objlist.append(itm.getStl())
			
		saveSelection = self.selection
							
		objs = sorted(objlist, cmpobj)
		for o in objs:
			itemId = o.getId()
			if itemId is None: continue
			
			x, y = omap.find(o.hxSize+self.arrangeMargin*2, o.hySize+self.arrangeMargin*2)
			if x is None or y is None:
				rc = False
			else:
				dx = x - o.hxCenter - 0*o.translatex + o.hxSize/2 + self.arrangeMargin
				dy = y - o.hyCenter - 0*o.translatey + o.hySize/2 + self.arrangeMargin
				
				self.setSelection(itemId)
				self.moveStl(dx, dy)
				deltax = o.hxSize+self.arrangeMargin*2
				deltay = o.hySize+self.arrangeMargin*2
				omap.mark(x, y, deltax, deltay)
				if x < minx: minx=x
				if x+deltax > maxx: maxx=x+deltax
				if y < miny: miny=y
				if y+deltay > maxy: maxy=y+deltay
				
		dx = self.buildarea[0]/2-(maxx+minx)/2
		dy = self.buildarea[1]/2-(maxy+miny)/2

		for o in objs:
			itemId = o.getId()
			if itemId is None: continue
		
			self.setSelection(itemId)
			self.moveStl(dx, dy)

		self.setSelection(saveSelection)
		self.redrawStl()
		return rc
			
	def getStls(self):
		objlist = []
		for itm in self.stlItems:
			if itm is None: continue
			objlist.append(itm.getStl())

		return objlist
			
	def countObjects(self):
		n = 0
		for itm in self.stlItems:
			if itm is not None: n += 1
			
		return n

	def transform(self, ptx, pty):
		x = (ptx+self.offsetx)*self.zoom*self.scale+self.gridOffset
		y = (pty-self.offsety)*self.zoom*self.scale+self.gridOffset
		return (x, y)

	def untransform(self, ptx, pty):
		x = (ptx-self.gridOffset)/self.scale/self.zoom-self.offsetx
		y = (pty-self.gridOffset)/self.scale/self.zoom-self.offsety
		return (x, y)
	
	def triangulate(self, p1, p2):
		dx = p2[0] - p1[0]
		dy = p2[1] - p1[1]
		d = math.sqrt(dx*dx + dy*dy)
		return d
		


