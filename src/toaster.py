import wx

TB_UPPERLEFT = 0
TB_UPPERRIGHT = 1
TB_LOWERLEFT = 2
TB_LOWERRIGHT = 3
TB_CENTER = 4
TB_UPPERCENTER = 5
TB_LOWERCENTER = 6
TB_CENTERLEFT = 7
TB_CENTERRIGHT = 8

locString = ["ul", "ur", "ll", "lr", "c", "uc", "lc", "cl", "cr"]

TB_DEFAULT_STYLE = 0x2008002
TB_CAPTION = 0x22009806

class Toaster(wx.Frame):
	def __init__(self, title="", size=(600, 180), pos=(100,100), style=TB_DEFAULT_STYLE):
		self.size = size
		wx.Frame.__init__(self, None, -1, title, size=size, pos=pos, style=style | wx.CLIP_CHILDREN | wx.STAY_ON_TOP)

		panel = wx.Panel(self, wx.ID_ANY, size=size, pos=(0,0))
		lbsize = self.GetClientSize()
		self.lb = wx.ListBox(panel, wx.ID_ANY, (0, 0), lbsize, [], wx.LB_SINGLE)
		self.showTime = 4000
		self.Timers = []
		self.lct = 0
		self.Hide()
		
	def SetPositionByCorner(self, pos):
		w, h = wx.GetDisplaySize()
		
		if pos in [TB_UPPERLEFT, TB_CENTERLEFT, TB_LOWERLEFT]:
			px = 0
		elif pos in [TB_UPPERCENTER, TB_CENTER, TB_LOWERCENTER]:
			px = (w-self.size[0])/2
		else:
			px = w-self.size[0]
			
		if pos in [TB_UPPERLEFT, TB_UPPERCENTER, TB_UPPERRIGHT]:
			py = 0
		elif pos in [TB_CENTERLEFT, TB_CENTER, TB_CENTERRIGHT]:
			py = (h-self.size[1])/2
		else:
			py = h-self.size[1]

		self.SetPosition(wx.Point(px, py))
			
	def SetShowTime(self, t):
		self.showTime = t
		
	def checkShow(self):
		if len(self.Timers) >= 1:
			self.Show()
		
	def Append(self, v, onLoggerPage = False):
		self.lb.Append(v)
		timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.onTimer, timer)  
		timer.Start(self.showTime, True) 

		self.Timers.append(timer)
		if len(self.Timers) >= 1 and not onLoggerPage:
			self.Show()
		
	def onTimer(self, evt):
		del self.Timers[0]
		self.lb.Delete(0)
		if len(self.Timers) == 0:
			self.Hide()
		
	def Close(self):
		for t in self.Timers:
			try:
				t.Stop()
			except:
				pass
		self.Destroy()
