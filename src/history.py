import time
import marshal
import os

class History:
	def __init__(self, settings):
		self.hsize = settings.historysize
		self.slicehistoryfile = settings.slicehistoryfile
		self.printhistoryfile = settings.printhistoryfile
		self.slicers = settings.fileprep.slicersettings
		self.sliceHistory = []
		self.printHistory = []
		self.logger = None
		self.LoadHistory()
		pass
	
	def SetLogger(self, logger):
		self.logger = logger
		
	def logError(self, msg):
		if self.logger is None:
			print msg
		else:
			self.logger.LogError(msg)
		
	def logWarning(self, msg):
		if self.logger is None:
			print msg
		else:
			self.logger.LogWarning(msg)
	
	def GetSliceHistory(self):
		return self.sliceHistory[:]
	
	def GetPrintHistory(self):
		return self.printHistory[:]
	
	def SaveHistory(self):
		self.SaveSliceHistory()
		self.SavePrintHistory()
		
	def SaveSliceHistory(self):
		try:
			f = open(self.slicehistoryfile, 'wb')
		except:
			self.logError("Error opening slice history file for write")
		else:
			try:
				marshal.dump(self.sliceHistory, f)
			except:
				self.logError("Error saving slice history")
			else:
				f.close()
		
	def SavePrintHistory(self):
		try:
			f = open(self.printhistoryfile, 'wb')
		except:
			self.logError("Error opening print history file for write")
		else:
			try:
				marshal.dump(self.printHistory, f)
			except:
				self.logError("Error saving print history")
			else:
				f.close()
		
	def LoadHistory(self):
		self.LoadSliceHistory()
		self.LoadPrintHistory()
		
	def LoadSliceHistory(self):
		if not os.path.exists(self.slicehistoryfile):
			self.logWarning("Slice history file does not exist - creating empty")
			self.sliceHistory = []
			return
			
		try:
			f = open(self.slicehistoryfile, 'rb')
		except:
			self.logWarning("Error opening slice history file - assumed empty")
			self.sliceHistory = []
			return

		try:
			self.sliceHistory = marshal.load(f)
			f.close()
		except:
			self.logWarning("Error loading slice history - assumed empty")
			self.sliceHistory = []
			f.close()
			
	def LoadPrintHistory(self):
		if not os.path.exists(self.printhistoryfile):
			self.logWarning("Print history file does not exist - creating empty")
			self.printHistory = []
			return
			
		try:
			f = open(self.printhistoryfile, 'rb')
		except:
			self.logWarning("Error opening print history file - assumed empty")
			self.printHistory = []
			return

		try:
			self.printHistory = marshal.load(f)
			f.close()
		except:
			self.logWarning("Error loading print history - assumed empty")
			self.printHistory = []
			f.close()
	
	def ts(self):
		now = time.time()
		return time.strftime('%y/%m/%d-%H:%M:%S', time.localtime(now))
	
	def FindInSliceHistory(self, fn):
		for h in self.sliceHistory[::-1]:
			for sl in self.slicers:
				slin = sl.buildSliceOutputFile(h[0])
				if fn == slin:
					return h
			
		return None

	def SliceStart(self, fn, cfgstring, filament, temps):
		self.sliceHistory.append([fn, cfgstring, filament, temps, self.ts(), "", "Start"])
		l = len(self.sliceHistory)
		if l > self.hsize:
			self.sliceHistory = self.sliceHistory[l-self.hsize:]
		self.SaveSliceHistory()
	
	def SliceComplete(self):
		self.sliceHistory[-1][4] = self.ts()
		self.sliceHistory[-1][5] = "Completion"
		self.SaveSliceHistory()
	
	def SliceCancel(self):
		self.sliceHistory[-1][4] = self.ts()
		self.sliceHistory[-1][5] = "Cancel"
		self.SaveSliceHistory()
	
	def BatchSliceStart(self, fn, cfgstring, filament, temps):
		self.sliceHistory.append([fn, cfgstring, filament, temps, self.ts(), "", "Batch Start"])
		l = len(self.sliceHistory)
		if l > self.hsize:
			self.sliceHistory = self.sliceHistory[l-self.hsize:]
		self.SaveSliceHistory()
	
	def BatchSliceComplete(self):
		self.sliceHistory[-1][4] = self.ts()
		self.sliceHistory[-1][5] = "Batch Completion"
		self.SaveSliceHistory()
	
	def BatchSliceCancel(self):
		self.sliceHistory[-1][4] = self.ts()
		self.sliceHistory[-1][5] = "Batch Cancel"
		self.SaveSliceHistory()

	def PrintStart(self, fn, prtname):
		self.printHistory.append([fn, prtname, self.ts(), "", "Normal"])
		l = len(self.printHistory)
		if l > self.hsize:
			self.printHistory = self.printHistory[l-self.hsize:]
		self.SavePrintHistory()
	
	def PrintComplete(self, prtname):
		self.printHistory[-1][3] = self.ts()
		self.SavePrintHistory()
	
	def SDPrintFromStart(self, fn, prtname):
		self.printHistory.append([fn, prtname, self.ts(), "", "FromSD"])
		l = len(self.printHistory)
		if l > self.hsize:
			self.printHistory = self.printHistory[l-self.hsize:]
		self.SavePrintHistory()
		
	def SDPrintFromComplete(self, prtname):
		self.printHistory[-1][3] = self.ts()
		self.SavePrintHistory()

	def SDPrintToStart(self, fn, prtname):
		self.printHistory.append([fn, prtname, self.ts(), "", "ToSD"])
		l = len(self.printHistory)
		if l > self.hsize:
			self.printHistory = self.printHistory[l-self.hsize:]
		self.SavePrintHistory()
	
	def SDPrintToComplete(self, prtname):
		self.printHistory[-1][3] = self.ts()
		self.SavePrintHistory()
	

		
