'''
Created on Jun 23, 2013

@author: Jeff
'''
from serial import Serial, SerialException
from threading import Thread
from select import error as SelectError
import time

class RepRap:
	def __init__(self):
		self.printer = None
		self.online = False
		self.printing = False

	def connect(self, port, baud):
		if(self.printer is not None):
			self.disconnect()

		self.port=port
		self.baud=baud
		
		if self.port is not None and self.baud is not None:
			self.printer=Serial(self.port,self.baud,timeout=5)
			Thread(target=self._listen).start()

	def disconnect(self):
		if(self.printer):
			self.printer.close()
		self.printer=None
		self.online=False
		self.printing=False
		
	def _listen(self):
		time.sleep(1.0)
		self.send_now("M105")
		while(True):
			if(not self.printer or not self.printer.isOpen):
				break
			try:
				line=self.printer.readline()
			except SelectError, e:
				if 'Bad file descriptor' in e.args[1]:
					print "Can't read from printer (disconnected?)."
					break
				else:
					raise
				
			except SerialException, e:
				print "Can't read from printer (disconnected?)."
				break
			except OSError, e:
				print "Can't read from printer (disconnected?)."
				break

			if(len(line)>1):
				print "RECV: ",line.rstrip()
				
	def _send(self, command, lineno=0, calcchecksum=False):
		if(calcchecksum):
			prefix="N"+str(lineno)+" "+command
			command=prefix+"*"+str(self._checksum(prefix))
		if(self.printer):

			print "SENT: ",command
			try:
				self.printer.write(str(command+"\n"))
			except SerialException, e:
				print "Can't write to printer (disconnected?)."

