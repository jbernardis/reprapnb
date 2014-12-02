import time
import marshal
import os

SLICEHISTORYFILE = "./slice.history"
PRINTHISTORYFILE = "./print.history"

class History:
	def __init__(self, hsize):
		self.hsize = hsize
		self.sliceHistory = []
		self.printHistory = []
		self.LoadHistory()
		pass
	
	def SaveHistory(self):
		self.SaveSliceHistory()
		self.SavePrintHistory()
		
	def SaveSliceHistory(self):
		print "save slice history"
		try:
			f = open(SLICEHISTORYFILE, 'wb')
		except:
			print "Error opening slice history file for write"
		else:
			try:
				marshal.dump(self.sliceHistory, f)
			except:
				print "Error saving slice history"
			else:
				f.close()
				print "Slice history save completed"
		
	def SavePrintHistory(self):
		print "save print history"
		try:
			f = open(PRINTHISTORYFILE, 'wb')
		except:
			print "Error opening print history file for write"
		else:
			try:
				marshal.dump(self.printHistory, f)
			except:
				print "Error saving print history"
			else:
				f.close()
				print "Print history save completed"
		
	def LoadHistory(self):
		print "load"
		self.LoadSliceHistory()
		self.LoadPrintHistory()
		
	def LoadSliceHistory(self):
		if not os.path.exists(SLICEHISTORYFILE):
			print "Slice history file does not exist"
			self.sliceHistory = []
			
		try:
			f = open(SLICEHISTORYFILE, 'rb')
		except:
			print "Error opening slice history file"
			self.sliceHistory = []

		try:
			self.sliceHistory = marshal.load(f)
			f.close()
		except:
			print "Error loading slice history"
			self.sliceHistory = []
			f.close()
			
	def LoadPrintHistory(self):
		if not os.path.exists(PRINTHISTORYFILE):
			print "Print history file does not exist"
			self.printHistory = []
			
		try:
			f = open(PRINTHISTORYFILE, 'rb')
		except:
			print "Error opening print history file"
			self.printHistory = []

		try:
			self.printHistory = marshal.load(f)
			f.close()
		except:
			print "Error loading print history"
			self.printHistory = []
			f.close()

	
	def ts(self):
		now = time.time()
		return time.strftime('%H:%M:%S', time.localtime(now))

	def SliceStart(self, fn, cfgstring):
		self.sliceHistory.append([fn, cfgstring, self.ts(), "", "Start"])
		l = len(self.sliceHistory)
		if l > self.hsize:
			self.sliceHistory = self.sliceHistory[l-self.hsize:]
		self.SaveSliceHistory()
		print "Slice start (%s) (%s)" % (fn, cfgstring)
	
	def SliceComplete(self):
		print "slice complete"
		self.sliceHistory[-1][3] = self.ts()
		self.sliceHistory[-1][4] = "Completion"
		self.SaveSliceHistory()
	
	def SliceCancel(self):
		print "Slice cancelled"
		self.sliceHistory[-1][3] = self.ts()
		self.sliceHistory[-1][4] = "Cancel"
		self.SaveSliceHistory()
	
	def BatchSliceStart(self, fn, cfgstring):
		self.sliceHistory.append([fn, cfgstring, self.ts(), "", "Batch Start"])
		l = len(self.sliceHistory)
		if l > self.hsize:
			self.sliceHistory = self.sliceHistory[l-self.hsize:]
		print "batch slice start (%s) (%s)" % (fn, cfgstring)
		self.SaveSliceHistory()
	
	def BatchSliceComplete(self):
		self.sliceHistory[-1][3] = self.ts()
		self.sliceHistory[-1][4] = "Batch Completion"
		print "Batch slice complete"
		self.SaveSliceHistory()
	
	def BatchSliceCancel(self):
		self.sliceHistory[-1][3] = self.ts()
		self.sliceHistory[-1][4] = "Batch Cancel"
		self.SaveSliceHistory()
		print "batch slice cancel"
	

	def PrintStart(self, fn, prtname):
		self.printHistory.append([fn, prtname, self.ts(), "", "Normal"])
		l = len(self.printHistory)
		if l > self.hsize:
			self.printHistory = self.printHistory[l-self.hsize:]
		self.SavePrintHistory()
		print "print start (%s) %s" % (fn, prtname)
	
	def PrintComplete(self, prtname):
		self.printHistory[-1][3] = self.ts()
		self.SavePrintHistory()
		print "print complete %s" % prtname
	
	def SDPrintFromStart(self, fn, prtname):
		self.printHistory.append([fn, prtname, self.ts(), "", "FromSD"])
		l = len(self.printHistory)
		if l > self.hsize:
			self.printHistory = self.printHistory[l-self.hsize:]
		self.SavePrintHistory()
		print "SD print from start (%s) %s" % (fn, prtname)
		
	def SDPrintFromComplete(self, prtname):
		self.printHistory[-1][3] = self.ts()
		self.SavePrintHistory()
		print "SD print from complete %s" % prtname

	def SDPrintToStart(self, fn, prtname):
		self.printHistory.append([fn, prtname, self.ts(), "", "ToSD"])
		l = len(self.printHistory)
		if l > self.hsize:
			self.printHistory = self.printHistory[l-self.hsize:]
		self.SavePrintHistory()
		print "SD print to start (%s) %s" % (fn, prtname)
	
	def SDPrintToComplete(self, prtname):
		self.printHistory[-1][3] = self.ts()
		self.SavePrintHistory()
		print "SD print to complete %s" % prtname
	

		