import wx
import os.path
from imagemap import ImageMap
	
#		t = wx.StaticText(self, -1, "(if connected) Move Axes, set temps, extrude/retract, manual G code entry, g code ref", (40,40))
imageMap = [[0,0,92,84,"XH"], [388,0,473,84,"YH"], [0,400,92,473,"ZH"], [388,409,473,473,"AH"],
	[376,232,396,252,"X+3"], [328,232,348,252,"X+2"], [275,232,295,252,"X+1"],
	[173,232,193,252,"X-1"], [126,232,146,252,"X-2"], [78,232,98,252,"X-3"],
	[128,288,148,308,"Y-3"],[163,270,183,290,"Y-2"],[191,253,211,273,"Y-1"],
	[267,206,287,226,"Y+1"],[300,190,320,210,"Y+2"],[327,171,347,191,"Y+3"],
	[227,119,247,139,"Z+2"], [227,175,247,195,"Z+1"],[227,292,247,312,"Z-1"],[227,340,247,360,"Z-2"]]

dispatch = { "XH": "G28 X0", "YH": "G28 Y0", "ZH": "G28 Z0", "AH": "G28",
	"X-3": "G1 X-100", "X-2": "G1 X-10", "X-1": "G1 X-1", "X+1": "G1 X1", "X+2": "G1 X10", "X+3": "G1 X100",
	"Y-3": "G1 Y-100", "Y-2": "G1 Y-10", "Y-1": "G1 Y-1", "Y+1": "G1 Y1", "Y+2": "G1 Y10", "Y+3": "G1 Y100",
	"Z-2": "G1 Z-10", "Z-1": "G1 Z-1", "Z+1": "G1 Z1", "Z+2": "G1 Z10"}

class ManualControl(wx.Panel):
	def __init__(self, parent, app):
		self.model = None
		self.app = app
		self.settings = app.settings

		wx.Panel.__init__(self, parent, wx.ID_ANY, size=(100, 100))
		self.SetBackgroundColour("white")

		path = os.path.join(self.settings.cmdfolder, "images/axis.png")
		bmp = wx.BitmapFromImage(wx.Image(path, wx.BITMAP_TYPE_PNG), -1)
		self.axes = ImageMap(self, bmp)
		self.axes.setHotSpots(self.onImageClick, [[0,0,92,84,"XH"], [388,0,473,84,"YH"], [0,400,92,473,"ZH"], [388,409,473,473,"AH"],
							[376,232,396,252,"X+3"], [328,232,348,252,"X+2"], [275,232,295,252,"X+1"],
							[173,232,193,252,"X-1"], [126,232,146,252,"X-2"], [78,232,98,252,"X-3"],
							[128,288,148,308,"Y-3"],[163,270,183,290,"Y-2"],[191,253,211,273,"Y-1"],
							[267,206,287,226,"Y+1"],[300,190,320,210,"Y+2"],[327,171,347,191,"Y+3"],
							[227,119,247,139,"Z+2"], [227,175,247,195,"Z+1"],[227,292,247,312,"Z-1"],[227,340,247,360,"Z-2"]])
		
		sizerMain = wx.BoxSizer(wx.HORIZONTAL)
		sizerMain.Add(self.axes)
		self.SetSizer(sizerMain)

	def onClose(self, evt):
		return True
	
	def onImageClick(self, label):
		print "CLicked on %s" % label
		if label in dispatch.keys():
			cmd = dispatch[label]
			if cmd.startswith("G1 "):
				self.app.reprap.send_now("G91")
				self.app.reprap.send_now(cmd + " F1800")
				self.app.reprap.send_now("G90")
			else:
				self.app.reprap.send_now(cmd)
		else:
			print "unknows label: (%s)" % label
		
