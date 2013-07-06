'''
Created on Jun 30, 2013

@author: Jeff
'''

import wx
import os

BUTTONDIM = (64, 64)

class Heater(wx.Window):
    def __init__(self, parent, app, idx, name="", shortname="", target=20, range=(0, 100), oncmd = "G104"):
        self.parent = parent
        self.app = app
        self.index = idx
        self.logger = self.app.logger
        self.name = name
        self.shortname = shortname
        self.range = range
        self.onCmd = oncmd
        wx.Window.__init__(self, parent, wx.ID_ANY, size=(-1, -1), style=wx.SIMPLE_BORDER)        
        sizerHtr = wx.GridBagSizer(vgap=5)

        t = wx.StaticText(self, wx.ID_ANY, "Current: ", style=wx.ALIGN_RIGHT, size=(90, -1))
        f = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
        t.SetFont(f)
        sizerHtr.Add(t, pos=(0,2)) 
        
        self.tTemp = wx.TextCtrl(self, wx.ID_ANY, "0", size=(60, -1), style=wx.TE_RIGHT | wx.TE_READONLY)
        f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
        self.tTemp.SetFont(f)
        sizerHtr.Add(self.tTemp, pos=(0,3))

        t = wx.StaticText(self, wx.ID_ANY, "Target: ", style=wx.ALIGN_RIGHT, size=(90, -1))
        f = wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL)
        t.SetFont(f)
        sizerHtr.Add(t, pos=(1,2))
        
        self.tTarget = wx.TextCtrl(self, wx.ID_ANY, "0", size=(60, -1), style=wx.TE_RIGHT | wx.TE_READONLY)
        f = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)
        self.tTarget.SetFont(f)
        sizerHtr.Add(self.tTarget, pos=(1,3))
        
        self.slTarget = wx.Slider(
            self, wx.ID_ANY, target, range[0], range[1], size=(340, -1), 
            style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS 
            )
        self.slTarget.SetTickFreq(5, 1)
        self.slTarget.SetPageSize(1)
        self.slTarget.Bind(wx.EVT_SCROLL_CHANGED, self.onTargetChanged)
        self.slTarget.Bind(wx.EVT_MOUSEWHEEL, self.onTargetWheel)
        sizerHtr.Add(self.slTarget, pos=(2,0), span=(1,5))
                 
        path = os.path.join(self.parent.settings.cmdfolder, "images/heaton.png")    
        png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        mask = wx.Mask(png, wx.BLUE)
        png.SetMask(mask)
        self.bHeatOn = wx.BitmapButton(self, wx.ID_ANY, png, size=BUTTONDIM)
        self.bHeatOn.SetToolTipString("Turn %s heater on" % self.name)
        sizerHtr.Add(self.bHeatOn, pos=(0,0),span=(2,1))
        self.Bind(wx.EVT_BUTTON, self.heaterOn, self.bHeatOn)
                
        path = os.path.join(self.parent.settings.cmdfolder, "images/heatoff.png")    
        png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        mask = wx.Mask(png, wx.BLUE)
        png.SetMask(mask)
        self.bHeatOff = wx.BitmapButton(self, wx.ID_ANY, png, size=BUTTONDIM)
        self.bHeatOff.SetToolTipString("Turn %s heater off" % self.name)
        sizerHtr.Add(self.bHeatOff, pos=(0,1),span=(2,1))
        self.Bind(wx.EVT_BUTTON, self.heaterOff, self.bHeatOff)
                
        path = os.path.join(self.parent.settings.cmdfolder, "images/profile.png")    
        png = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        mask = wx.Mask(png, wx.BLUE)
        png.SetMask(mask)
        self.bProfile = wx.BitmapButton(self, wx.ID_ANY, png, size=BUTTONDIM)
        self.bProfile.SetToolTipString("Import from profile")
        sizerHtr.Add(self.bProfile, pos=(0,4),span=(2,1))
        self.Bind(wx.EVT_BUTTON, self.importProfile, self.bProfile)

        self.SetSizer(sizerHtr)
        self.Layout()
        self.Fit()
        
    def setRange(self, trange):
        self.range = trange
        self.slTarget.SetRange(trange[0], trange[1])
        
    def importProfile(self, evt):
        self.logger.LogMessage("Import for index %d" % self.index)
        t = self.parent.getProfileHeaterValue(self.index)
        self.slTarget.SetValue(t)
       
    def setTemp(self, t):
        try:
            ft = float(t)
            self.tTemp.SetValue("%.1f" % ft)
        except:
            self.logger.LogError("Unknown value for %s temperature: '%s'" % (self.name, t))
        
    def onTargetChanged(self, evt):
        pass
    
    def onTargetWheel(self, evt):
        l = self.slTarget.GetValue()
        if evt.GetWheelRotation() < 0:
            l -= 1
        else:
            l += 1
        if l >= self.range[0] and l <= self.range[1]:
            self.slTarget.SetValue(l)

    
    def heaterOn(self, evt):
        t = self.slTarget.GetValue()
        self.tTarget.SetValue("%d" % t)
        self.app.reprap.send_now("%s S%d" % (self.onCmd, t))
        self.app.setTargetTemp(self.shortname, t)
        
    def heaterOff(self, evt):
        self.tTarget.SetValue("0")
        self.app.reprap.send_now("%s S0" % self.onCmd)
        self.app.setTargetTemp(self.shortname, None)

