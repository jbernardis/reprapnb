import wx
	
class ImageMap(wx.Panel):
	def __init__(self, parent, bmp):
		self.bmp = bmp
		self.mask = wx.Mask(self.bmp, wx.BLUE)
		self.bmp.SetMask(self.mask)
		wx.Panel.__init__(self,parent,size=(self.bmp.GetWidth(), self.bmp.GetHeight()), style=wx.SIMPLE_BORDER)
		self.Bind(wx.EVT_SIZE, self.onSize)
		self.Bind(wx.EVT_PAINT, self.onPaint)
		self.Bind(wx.EVT_MOTION, self.onMouseMove)
		self.Bind(wx.EVT_LEFT_DOWN, self.onMouseClick)
		
		self.hotspots = []
		self.handler = None
		
		self.initBuffer()
		
	def onSize(self, evt):
		self.initBuffer()
		
	def onPaint(self, evt):
		dc = wx.PaintDC(self)
		self.drawImage(dc)
		
	def onMouseMove(self, evt):
		x, y = evt.GetPosition()
		if self.inHotSpot(x,y) is not None:
			self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
		else:
			self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
		
	def onMouseClick(self, evt):
		if self.handler is not None:
			x, y = evt.GetPosition()
			l = self.inHotSpot(x,y)
			if l is not None:
				self.handler(l)
		evt.Skip()
		
	def inHotSpot(self, x, y):
		for r in self.hotspots:
			if x > r[0] and x < r[2] and y > r[1] and y < r[3]:
				return r[4]
			
		return None
		
	def setHotSpots(self, handler, hs):
		self.handler = handler
		self.hotspots = hs
		
	def initBuffer(self):
		self.w, self.h = self.GetClientSize();
		self.buffer = wx.EmptyBitmap(self.w, self.h)
		self.redrawImage()
		
	def redrawImage(self):
		dc = wx.ClientDC(self)
		self.drawImage(dc)
		
	def drawImage(self, dc):
		dc.DrawBitmap(self.bmp, 0, 0, False)

