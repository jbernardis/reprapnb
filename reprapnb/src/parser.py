'''
Created on Jul 18, 2013

@author: jeff
'''
import re

class RepRapParser:
    '''
    Parse a REPRAP message
    '''
    def __init__(self, app):
        self.app = app
        self.rpt1re = re.compile("ok *T: *([0-9\.]+) */ *([0-9\.]+) *B: *([0-9\.]+) */ *([0-9\.]+)")
        self.rptnre = re.compile(" *T:([0-9\.]+) *E:[0-9\.]+ *B:([0-9\.]+)")
        self.rpt2re = re.compile(" *T:([0-9\.]+) *E:[0-9\.]+ *W:.*")
        self.locrptre = re.compile("^X:([0-9\.\-]+)Y:([0-9\.\-]+)Z:([0-9\.\-]+)E:([0-9\.\-]+) *Count")
        self.speedrptre = re.compile("Fan speed:([0-9]+) Feed Multiply:([0-9]+) Extrude Multiply:([0-9]+)")
        
        self.sdre = re.compile("SD printing byte *([0-9]+) *\/ *([0-9]+)")
        self.heaters = {}
        
    def setPrinter(self, htrs, exts):
        self.heaters = {}
        for h in htrs:
            if h[0] == "HE":
                self.heaters['T'] = "HE"
            elif h[0] == "HE0":
                self.heaters['T'] = "HE0"
            elif h[0] == "HE1":
                self.heaters['K'] = "HE1"
            elif h[0] == "HBP":
                self.heaters['B'] = "HBP"
        
        
    def parseMsg(self, msg):
        print "Parsing (%s)" % msg
        m = self.rpt1re.search(msg)
        if m:
            t = m.groups()
            if len(t) >= 1:
                self.app.setHeatTemp(self.heaters['T'], float(t[0]))
            if len(t) >= 2:
                self.app.setHeatTarget(self.heaters['T'], float(t[1]))
            if len(t) >= 3:
                self.app.setHeatTemp(self.heaters['B'], float(t[2]))
            if len(t) >= 4:
                self.app.setHeatTarget(self.heaters['B'], float(t[3]))


        