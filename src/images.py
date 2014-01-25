import wx
import os

class Images:
	def __init__(self, idir):
		try:
			pdir = os.path.expandvars(idir)
			l = os.listdir(pdir)
		except:
			print "Unable to get listing from directory: ", idir
			return

		for f in l:
			if not os.path.isdir(f) and f.lower().endswith(".png"):
				b = os.path.splitext(os.path.basename(f))[0]

				fp =  os.path.join(pdir, f)	
				png = wx.Image(fp, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
				mask = wx.Mask(png, wx.BLUE)
				png.SetMask(mask)
	
				setattr(self, 'png'+b.capitalize(), png)
