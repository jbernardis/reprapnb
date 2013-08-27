import wx
import os.path
from imagemap import ImageMap
	
#		t = wx.StaticText(self, -1, "(if connected) Move Axes, set temps, extrude/retract, manual G code entry, g code ref", (40,40))
imageMap = [[0,0,92,84,"XH"], [388,0,473,84,"YH"], [0,400,92,473,"ZH"], [388,409,473,473,"AH"],
	[376,232,396,252,"X+3"], [328,232,348,252,"X+2"], [275,232,295,252,"X+1"],
	[173,232,193,252,"X-1"], [126,232,146,252,"X-2"], [78,232,98,252,"X-3"],
	[128,288,148,308,"Y-3"],[163,270,183,290,"Y-2"],[191,253,211,273,"Y-1"],
	[267,206,287,226,"Y+1"],[300,190,320,210,"Y+2"],[327,171,347,191,"Y+3"],
	[227,119,247,139,"Z+2"], [227,175,247,195,"Z+1"],[227,292,247,312,"Z-1"],[227,340,247,360,"Z-2"],
	[160,431,322,477,"STOP"]]


dispatch = { "XH": "G28 X0", "YH": "G28 Y0", "ZH": "G28 Z0", "AH": "G28",
	"X-3": "G1 X-100", "X-2": "G1 X-10", "X-1": "G1 X-1",
	"X+1": "G1 X1",	"X+2": "G1 X10",  "X+3": "G1 X100",
	"Y-3": "G1 Y-100", "Y-2": "G1 Y-10", "Y-1": "G1 Y-1",
	"Y+1": "G1 Y1",	"Y+2": "G1 Y10",  "Y+3": "G1 Y100",
	"Z-2": "G1 Z-10",  "Z-1": "G1 Z-1",  "Z+1": "G1 Z1",  "Z+2": "G1 Z10",
	"STOP": "M84"}

BUTTONDIM = (64, 64)

class MoveAxis(wx.Window): 
	def __init__(self, parent, app):
		self.model = None
		self.parent = parent
		self.app = app
		self.logger = self.app.logger
		self.appsettings = app.settings
		self.settings = app.settings.manualctl

		wx.Window.__init__(self, parent, wx.ID_ANY, size=(-1, -1), style=wx.SIMPLE_BORDER)		

		path = os.path.join(self.settings.cmdfolder, "images", "axis.png")
		bmp = wx.BitmapFromImage(wx.Image(path, wx.BITMAP_TYPE_PNG), -1)
		self.axes = ImageMap(self, bmp)
		self.axes.setHotSpots(self.onImageClick, imageMap)
		
		sizerMoveFrame = wx.GridBagSizer()
		sizerMoveFrame.AddSpacer((20, 20), pos=(0,0))
		sizerMoveFrame.Add(self.axes, pos=(1,1), span=(1,4))
		sizerMoveFrame.AddSpacer((10, 10), pos=(2,0))

		t = wx.StaticText(self, wx.ID_ANY, "mm/min", style=wx.ALIGN_LEFT, size=(160, -1))
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
		t.SetFont(f)
		sizerMoveFrame.Add(t, pos=(3,3))
		
		t = wx.StaticText(self, wx.ID_ANY, "XY Speed:", style=wx.ALIGN_RIGHT, size=(160, -1))
		f = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
		t.SetFont(f)
		sizerMoveFrame.Add(t, pos=(4,2))
		
		self.tXYSpeed = wx.TextCtrl(self, wx.ID_ANY, str(self.settings.xyspeed), size=(80, -1), style=wx.TE_RIGHT)
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
		self.tXYSpeed.SetFont(f)
		sizerMoveFrame.Add(self.tXYSpeed, pos=(4,3))
		self.tXYSpeed.Bind(wx.EVT_KILL_FOCUS, self.evtXYSpeedKillFocus)
		
		sizerMoveFrame.AddSpacer((10, 10), pos=(5,0))
		
		t = wx.StaticText(self, wx.ID_ANY, "Z Speed:", style=wx.ALIGN_RIGHT, size=(160, -1))
		f = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
		t.SetFont(f)
		sizerMoveFrame.Add(t, pos=(6,2))
		
		self.tZSpeed = wx.TextCtrl(self, wx.ID_ANY, str(self.settings.zspeed), size=(80, -1), style=wx.TE_RIGHT)
		f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
		self.tZSpeed.SetFont(f)
		sizerMoveFrame.Add(self.tZSpeed, pos=(6,3))
		self.tZSpeed.Bind(wx.EVT_KILL_FOCUS, self.evtZSpeedKillFocus)
		
		self.SetSizer(sizerMoveFrame)
		self.Layout()
		self.Fit()
	
	def onImageClick(self, label):
		if label in dispatch.keys():
			cmd = dispatch[label]
			if cmd.startswith("G1 "):
				if "X" in label or "Y" in label:
					try:
						v = float(self.tXYSpeed.GetValue())
					except:
						self.logger.LogError("Invalid value for XY Speed: %s" % self.tXYSpeed.GetValue())
						v = 0.0
					speed = " F%.3f" % v
				elif "Z" in label:
					try:
						v = float(self.tZSpeed.GetValue())
					except:
						self.logger.LogError("Invalid value for Z Speed: %s" % self.tZSpeed.GetValue())
						v = 0.0
					speed = " F%.3f" % v
				else:
					speed = ""
				self.app.reprap.send_now("G91")
				self.app.reprap.send_now(cmd + speed)
				self.app.reprap.send_now("G90")
			else:
				self.app.reprap.send_now(cmd)
		else:
			self.logger.LogError("unknown label: (%s)" % label)
			
	def evtXYSpeedKillFocus(self, evt):
		try:
			v = float(self.tXYSpeed.GetValue())
		except:
			self.logger.LogError("Invalid value for XY Speed: %s" % self.tXYSpeed.GetValue())
			
	def evtZSpeedKillFocus(self, evt):
		try:
			v = float(self.tZSpeed.GetValue())
		except:
			self.logger.LogError("Invalid value for Z Speed: %s" % self.tZSpeed.GetValue())
