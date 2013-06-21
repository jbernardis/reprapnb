import wx
	
tadjust = -8

class Gauge(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self,parent,size=(120, 200), style=wx.SIMPLE_BORDER)
		self.Bind(wx.EVT_SIZE, self.onSize)
		self.Bind(wx.EVT_PAINT, self.onPaint)
		
		self.low = 0
		self.current = 0
		self.high = 100
		self.target = 60
		self.thresholds = [[999, wx.RED]]
		self.background = wx.WHITE
		self.foreground = wx.BLACK
		self.tempcolor = wx.RED
		
		self.initBuffer()
		
	def onSize(self, evt):
		self.initBuffer()
		
	def onPaint(self, evt):
		dc = wx.PaintDC(self)
		self.drawGauge(dc)
		
	def setRange(self, l, h):
		self.low = l
		self.high = h
		self.redrawGauge()
		
	def setValue(self, v):
		self.current = v
		self.redrawGauge()
		
	def setTarget(self, t):
		self.target = t
		self.redrawGauge()
		
	def setThresholds(self, thr):
		self.thresholds = thr
		self.redrawGauge()
		
	def setColors(self, fore, back, temp):
		if fore is not None: self.foreground = fore
		if back is not None: self.background = back
		if temp is not None: self.tempcolor = temp
		self.redrawGauge()
			
	def initBuffer(self):
		self.w, self.h = self.GetClientSize();
		self.buffer = wx.EmptyBitmap(self.w, self.h)
		self.redrawGauge()
		
	def redrawGauge(self):
		dc = wx.ClientDC(self)
		self.drawGauge(dc)
		
	def drawGauge(self, dc):
		def temp2scale(t):
			tspread = self.high - self.low
			tnormal = t - self.low
			tratio = tnormal/float(tspread)
			
			r = int(self.h - self.h*tratio)
			if r < 0:
				return 0
			elif r >= self.h:
				return self.h
			else:
				return r
		
		dc.SetBackground(wx.Brush(wx.BLACK))
		dc.Clear()
		
		dc.SetFont(wx.Font(14, wx.TELETYPE, wx.NORMAL, wx.BOLD))
		dc.SetTextBackground(wx.BLACK)
		dc.SetTextForeground(wx.BLACK)
		
		dc.SetPen(wx.Pen(self.background, 1))
		dc.SetBrush(wx.Brush(self.background))
		dc.DrawRectangle(0, 0, self.w, self.h)

		dc.SetPen(wx.TRANSPARENT_PEN)
		meterWidth = int(self.w/3)
		xOffset = meterWidth
		for t in reversed(self.thresholds):	
			nt = temp2scale(t[0])
			dc.SetBrush(wx.Brush(t[1]))
			dc.DrawRectangle(xOffset, nt, meterWidth, self.h)	
			
		dc.SetPen(wx.Pen(wx.WHITE, 1))
		tick = self.low / 10 * 10 + 10
		while tick < self.high:
			nt = temp2scale(tick)
			dc.DrawLine(xOffset+1, nt, xOffset+meterWidth-2, nt)
			dc.DrawText("%3d" % tick, xOffset+meterWidth, nt+tadjust)
			tick += 10
			
		nt = temp2scale(self.target)
		dc.SetPen(wx.Pen(wx.WHITE, 3))
		dc.DrawLine(xOffset+1, nt, xOffset+meterWidth-2, nt)
		dc.DrawText("%3d" % self.target, 0, nt+tadjust)
		
		nt = temp2scale(self.current)
		dc.SetPen(wx.Pen(self.foreground, 1))
		dc.SetBrush(wx.Brush(self.tempcolor))
		dc.DrawRectangle(self.w/2-5, nt, 10, self.h)
		dc.DrawText("%3d" % self.current, xOffset, nt+tadjust-20)

		dc.SetPen(wx.Pen(self.foreground, 2))
		dc.SetBrush(wx.TRANSPARENT_BRUSH)
		dc.DrawRectangle(xOffset, 0, meterWidth, self.h)	

