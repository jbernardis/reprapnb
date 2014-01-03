import wx
import os.path
from imagemap import ImageMap
	
#		t = wx.StaticText(self, -1, "(if connected) Move Axes, set temps, extrude/retract, manual G code entry, g code ref", (40,40))
imageMap = [[0,0,92,84,"XH"], [388,0,473,84,"YH"], [0,400,92,473,"ZH"], [388,409,473,473,"AH"],
	[376,231,396,252,"X+4"], [343,231,363,252,"X+3"], [309,231,329,252,"X+2"], [276,231,296,252,"X+1"],
	[173,231,193,252,"X-1"], [141,231,162,252,"X-2"], [109,231,129,252,"X-3"], [77,231,97,252,"X-4"],
	[127,290,147,310,"Y-4"], [149,277,169,297,"Y-3"], [171,265,191,285,"Y-2"], [194,251,214,271,"Y-1"],
	[266,208,286,228,"Y+1"], [286,196,306,216,"Y+2"], [306,184,326,204,"Y+3"], [326,172,346,192,"Y+4"],
	[227,85,247,105,"Z+3"], [227,137,247,157,"Z+2"], [227,187,247,207,"Z+1"],
	[227,280,247,302,"Z-1"], [227,330,247,350,"Z-2"], [227,377,247,397,"Z-3"],
	[160,431,322,477,"STOP"]]


dispatch = { "XH": "G28 X0", "YH": "G28 Y0", "ZH": "G28 Z0", "AH": "G28",
	"X-4": "G1 X-100", "X-3": "G1 X-10", "X-2": "G1 X-1", "X-1": "G1 X-0.1",
	"X+1": "G1 X0.1", "X+2": "G1 X1",	"X+3": "G1 X10",  "X+4": "G1 X100",
	"Y-4": "G1 Y-100", "Y-3": "G1 Y-10", "Y-2": "G1 Y-1", "Y-1": "G1 Y-0.1",
	"Y+1": "G1 Y0.1",	"Y+2": "G1 Y1",	"Y+3": "G1 Y10",  "Y+4": "G1 Y100",
	"Z-3": "G1 Z-10", "Z-2": "G1 Z-1",  "Z-1": "G1 Z-0.1",
	"Z+1": "G1 Z0.1",  "Z+2": "G1 Z1", "Z+3": "G1 Z10",
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

		self.font12bold = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		self.font12 = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		
		t = wx.StaticText(self, wx.ID_ANY, "mm/min", style=wx.ALIGN_LEFT, size=(160, -1))
		t.SetFont(self.font12bold)
		sizerMoveFrame.Add(t, pos=(3,3))
		
		t = wx.StaticText(self, wx.ID_ANY, "XY Speed:", style=wx.ALIGN_RIGHT, size=(160, -1))
		t.SetFont(self.font12)
		sizerMoveFrame.Add(t, pos=(4,2))
		
		self.tXYSpeed = wx.TextCtrl(self, wx.ID_ANY, str(self.settings.xyspeed), size=(80, -1), style=wx.TE_RIGHT)
		self.tXYSpeed.SetFont(self.font12)
		sizerMoveFrame.Add(self.tXYSpeed, pos=(4,3))
		self.tXYSpeed.Bind(wx.EVT_KILL_FOCUS, self.evtXYSpeedKillFocus)
		
		sizerMoveFrame.AddSpacer((10, 10), pos=(5,0))
		
		t = wx.StaticText(self, wx.ID_ANY, "Z Speed:", style=wx.ALIGN_RIGHT, size=(160, -1))
		t.SetFont(self.font12)
		sizerMoveFrame.Add(t, pos=(6,2))
		
		self.tZSpeed = wx.TextCtrl(self, wx.ID_ANY, str(self.settings.zspeed), size=(80, -1), style=wx.TE_RIGHT)
		self.tZSpeed.SetFont(self.font12)
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
