from serial import Serial
import thread
import time
from sys import platform as _platform
if _platform == "linux" or _platform == "linux2":
	import termios

TRACE = False

class Pendant:
	def __init__(self, cb, port, baud=9600):
		self.cb = cb
		self.port = port
		self.baud = baud
		thread.start_new_thread(self.Run, ())
		
	def kill(self):
		self.disconnect()
		self.isRunning = False
		
	def isKilled(self):
		return not self.isRunning
	
	def Run(self):
		self.isRunning = True
		while self.isRunning:
			self.connect()
			if self.pendant is not None:
				self.cb("pendant connected")
			while self.pendant is not None:
				try:
					line=self.pendant.readline()
				except:
					self.cb("pendant disconnected")
					self.disconnect()
					line = ""

				if(len(line)>1):
					if TRACE:
						print "<==", line
					self.cb(line.strip())
			time.sleep(2);

	def connect(self):
		try:
			self.resetPort()
			self.pendant = Serial(self.port, self.baud, timeout=2)
		except:
			self.pendant = None
		
	def resetPort(self):
		if _platform == "linux" or _platform == "linux2":
			fp = open(self.port, "r")
			new = termios.tcgetattr(fp)
			new[2] = new[2] | ~termios.CREAD
			termios.tcsetattr(fp, termios.TCSANOW, new)
			fp.close()

	def disconnect(self):
		try:
			self.pendant.close()
		except:
			pass
		self.pendant = None

