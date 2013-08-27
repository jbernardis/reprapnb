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
		self.trpt1re = re.compile("ok *T: *([0-9\.]+) */ *([0-9\.]+) *B: *([0-9\.]+) */ *([0-9\.]+)")
		self.trpt2re = re.compile(" *T:([0-9\.]+) *E:[0-9\.]+ *B:([0-9\.]+)")
		self.trpt3re = re.compile(" *T:([0-9\.]+) *E:[0-9\.]+ *W:.*")
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
				#FIXIT - need to know axis number for second hot end
				self.heaters['K'] = "HE1"
			elif h[0] == "HBP":
				self.heaters['B'] = "HBP"
		
		
	def parseMsg(self, msg):
		self.app.logger.LogMessage("Parsing MSG: " + msg)
		m = self.trpt1re.search(msg)
		if m:
			self.app.logger.LogMessage("Match temperature report 1")
			t = m.groups()
			if len(t) >= 1:
				self.app.logger.LogMessage("0: " + t[0])
				self.app.setHeatTemp(self.heaters['T'], float(t[0]))
			if len(t) >= 2:
				self.app.logger.LogMessage("1: " + t[1])
				self.app.setHeatTarget(self.heaters['T'], float(t[1]))
			if len(t) >= 3:
				self.app.logger.LogMessage("2: " + t[2])
				self.app.setHeatTemp(self.heaters['B'], float(t[2]))
			if len(t) >= 4:
				self.app.logger.LogMessage("3: " + t[3])
				self.app.setHeatTarget(self.heaters['B'], float(t[3]))
			if self.app.M105pending:
				self.app.M105pending = False
				return True
			else:
				return False
		
		m = self.trpt2re.search(msg)
		if m:
			self.app.logger.LogMessage("Match temperature report 2")
			t = m.groups()
			if len(t) >= 1:
				self.app.logger.LogMessage("0: " + t[0])
				self.app.setHeatTemp(self.heaters['T'], float(t[0]))
			if len(t) >= 2:
				self.app.logger.LogMessage("1: " + t[1])
				self.app.setHeatTemp(self.heaters['B'], float(t[1]))
			return True
		
		m = self.trpt3re.search(msg)
		if m:
			self.app.logger.LogMessage("Match temperature report 3")
			t = m.groups()
			if len(t) >= 1:
				self.app.logger.LogMessage("0: " + t[0])
				self.app.setHeatTemp(self.heaters['T'], float(t[0]))
			return True
		
		return False


		