'''
Created on Jun 20, 2013

@author: ejefber
'''

FirmwareSettings = ['m92_x', 'm92_y', 'm92_z', 'm92_e',
		'm201_x', 'm201_y', 'm201_z', 'm201_e', 
		'm203_x', 'm203_y', 'm203_z', 'm203_e',
		'm204_s', 'm204_t',
		'm205_s', 'm205_t', 'm205_b', 'm205_x', 'm205_z', 'm205_e', 
		'm206_x', 'm206_y', 'm206_z',
		'm301_p', 'm301_i', 'm301_d']

PLABEL = 0
PWIDTH = 1
pinfo = {'m92_x' : ['X', 6], 'm92_y' : ['Y', 6], 'm92_z' : ['Z', 6], 'm92_e' : ['E', 6],
		'm201_x' : ['X', 8], 'm201_y' : ['Y', 8], 'm201_z' : ['Z', 8], 'm201_e' : ['E', 8], 
		'm203_x' : ['X', 6], 'm203_y' : ['Y', 6], 'm203_z' : ['Z', 6], 'm203_e' : ['E', 6],
		'm204_s' : ['Normal', 9], 'm204_t' : ['Retraction', 9],
		'm205_s' : ['Min Feed', 9], 'm205_t' : ['Min Travel', 9], 'm205_b' : ['Min Seg Time', 9],
		'm205_x' : ['Max XY Jerk', 9], 'm205_z' : ['Max Z Jerk', 9], 'm205_e' : ['Max E Jerk', 9], 
		'm206_x' : ['X', 6], 'm206_y' : ['Y', 6], 'm206_z' : ['Z', 6],
		'm301_p' : ['P', 6], 'm301_i' : ['I', 6], 'm301_d' : ['D', 6]}

GRPLABEL = 0
GRPOFFSET = 1
grpinfo = {'m92' : ['Steps per Unit - M92', 0], 'm201' : ['Max Acceleration (mm/s2) - M201', 0], 'm203' : ['Max Feed Rates (mm/s) - M203', -10],
			'm204' : ['Acceleration - M204', -8], 'm205' : ['Advanced - M205', 0], 'm206' : ['Home offset - M206', 0], 'm301' : ['PID - M301', -15]}

grporder = ['m92', 'm201', 'm203', 'm204', 'm205', 'm206', 'm301']

class param:
	def __init__(self, tag, label, fmt="%7.2f", flashVal = None, eepVal = None, profVal = None, width=8):
		self.tag = tag
		self.label = label
		self.format = fmt
		self.flashVal = flashVal
		self.eepVal = eepVal
		self.profVal = profVal
		self.width = width
		
	def getTag(self):
		return self.tag
	
	def getLabel(self):
		return self.label
	
	def getWidth(self):
		return self.width
		
	def setFlash(self, val):
		self.flashVal = val
		print "flash value for ", self.tag, " set to ", val
		
	def getFlash(self):
		return self.flashVal
	
	def displayFlash(self):
		if self.flashVal == None:
			return " "
		return self.format % self.flashVal
		
	def setEEProm(self, val):
		self.eepVal = val
		
	def getEEProm(self):
		return self.eepVal
	
	def displayEEProm(self):
		if self.eepVal == None:
			return " "
		return self.format % self.eepVal
		
	def setProf(self, val):
		self.profVal = val
		
	def getProf(self):
		return self.profVal
	
	def displayProf(self):
		if self.profVal == None:
			return " "
		return self.format % self.profVal
	
class paramGroup:
	def __init__(self, tag, label):
		self.tag = tag
		self.label = label
		self.params = []
		
	def getTag(self):
		return self.tag
	
	def getLabel(self):
		return self.label
	
	def addParam(self, p):
		self.params.append(p)
		
	def __iter__(self):
		self.__pindex__ = 0
		return self
	
	def next(self):
		if self.__pindex__ < self.__len__():
			i = self.__pindex__
			self.__pindex__ += 1
			return self.params[i]

		raise StopIteration
	
	def __len__(self):
		return len(self.params)

class Firmware:
	def __init__(self, app, reprap):
		self.app = app
		self.logger = self.app.logger
		self.reprap = reprap

		self.got92 = False
		self.got201 = False
		self.got203 = False
		self.got204 = False
		self.got205 = False
		self.got206 = False
		self.got301 = False
		
		self.readingFirmware = False
		
		self.parameters = {}
		self.groups = {}
		groups = []
		for s in FirmwareSettings:
			grp = s.split('_')[0]
			if grp not in groups:
				if grp not in grporder:
					print "Unknown group: %s" % grp
				else:
					groups.append(grp)
					g = self.groups[grp] = paramGroup(grp, grpinfo[grp][GRPLABEL])
			else:
				g = self.groups[grp]
				
			p = self.parameters[s] = param(s, pinfo[s][PLABEL], eepVal = self.settings.firmware[s], width=pinfo[s][PWIDTH])
			g.addParam(p)

	def start(self):
		self.got92 = False
		self.got201 = False
		self.got203 = False
		self.got204 = False
		self.got205 = False
		self.got206 = False
		self.got301 = False
		
		self.readingFirmware = True 
		self.reprap.send_now("M503")
		
	def checkComplete(self):
		if self.got92 and self.got201 and self.got203 and self.got204 and self.got204 and self.got206 and self.got301:
			if self.readingFirmware:
				self.reportComplete()
			return True
		else:
			return False
	
	def m92(self, x, y, z, e):
		self.parameters['m92_x'].setFlash(x)
		self.parameters['m92_y'].setFlash(y)
		self.parameters['m92_z'].setFlash(z)
		self.parameters['m92_e'].setFlash(e)
		self.got92 = True
		return self.checkComplete()
		
	def m201(self, x, y, z, e):
		self.parameters['m201_x'].setFlash(x)
		self.parameters['m201_y'].setFlash(y)
		self.parameters['m201_z'].setFlash(z)
		self.parameters['m201_e'].setFlash(e)
		self.got201 = True
		return self.checkComplete()
		
	def m203(self, x, y, z, e):
		self.parameters['m203_x'].setFlash(x)
		self.parameters['m203_y'].setFlash(y)
		self.parameters['m203_z'].setFlash(z)
		self.parameters['m203_e'].setFlash(e)
		self.got203 = True
		return self.checkComplete()
		
	def m204(self, s, t):
		self.parameters['m204_s'].setFlash(s)
		self.parameters['m204_t'].setFlash(t)
		self.got204 = True
		return self.checkComplete()
		
	def m205(self, s, t, b, x, z, e):
		self.parameters['m205_s'].setFlash(s)
		self.parameters['m205_t'].setFlash(t)
		self.parameters['m205_b'].setFlash(b)
		self.parameters['m205_x'].setFlash(x)
		self.parameters['m205_z'].setFlash(z)
		self.parameters['m205_e'].setFlash(e)
		self.got205 = True
		return self.checkComplete()

	def m206(self, x, y, z):
		self.parameters['m206_x'].setFlash(x)
		self.parameters['m206_y'].setFlash(y)
		self.parameters['m206_z'].setFlash(z)
		self.got206 = True
		return self.checkComplete()

	def m301(self, p, i, d):
		self.parameters['m301_p'].setFlash(p)
		self.parameters['m301_i'].setFlash(i)
		self.parameters['m301_d'].setFlash(d)
		self.got301 = True
		return self.checkComplete()

	def reportComplete(self):
		self.readingFirmware = False
		self.logger.LogMessage("Firmware Reporting completed")
		print "Firmware reporting completed"

