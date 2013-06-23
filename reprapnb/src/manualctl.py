import wx
import os.path
from imagemap import ImageMap
	
#		t = wx.StaticText(self, -1, "(if connected) Move Axes, set temps, extrude/retract, manual G code entry, g code ref", (40,40))

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
		
