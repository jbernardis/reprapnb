'''
Created on Jul 3, 2013

@author: Jeff
'''
import wx
import time
import string

class Logger(wx.Frame):
    def __init__(
            self, parent, ID, title, pos=wx.DefaultPosition,
            size=wx.DefaultSize, style=wx.RESIZE_BORDER | wx.CAPTION
            ):
        
        self.traceLevel = 0

        wx.Frame.__init__(self, parent, ID, title, pos, size, style)
        panel = wx.Panel(self, -1)
        
        self.t = wx.TextCtrl(panel, wx.ID_ANY, size=(-1, -1), style=wx.TE_MULTILINE|wx.TE_RICH2)
        sz = wx.GridBagSizer()
        sz.Add(self.t, pos=(0,0), flag=wx.EXPAND | wx.ALL)
        sz.AddGrowableRow(0)
        sz.AddGrowableCol(0)
        panel.SetSizer(sz)
        panel.Layout()
        panel.Fit()

    def setTraceLevel(self, l):
        self.traceLevel = l
        
    def logTrace(self, level, text):
        if level > self.traceLevel:
            return
        
        self.LogMessage(("Trace[%d] - " % level) +string.rstrip(text)+"\n")
       
#FIXIT       
    def LogMessage(self, text):
        s = time.strftime('%H:%M:%S', time.localtime(time.time()))
        self.t.AppendText(s+" - " +string.rstrip(text)+"\n")

    def LogError(self, text):
        self.LogMessage("Error - " +string.rstrip(text)+"\n")

    def LogWarning(self, text):
        self.LogMessage("Warning - " +string.rstrip(text)+"\n")

    def CloseWindow(self, event):
        self.Destroy()