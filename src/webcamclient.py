import urllib
import subprocess
import socket

class Webcam:
	def __init__(self, port, directory):
		try:
			subprocess.Popen(["python", "webcamserver.py", "%d" % port, directory],
				shell=False, stdin=None, stdout=None, stderr=None, close_fds=True)
		except:
			print "unable to spawn"
			self.ableToInit = False

		else:
			self.ableToInit = True
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			s.connect(('4.2.2.1', 123))
			self.ip = s.getsockname()[0]
			self.port = port
			self.urlPrefix = "http://%s:%s/" % (self.ip, self.port)
			
	def webCamOK(self):
		return self.ableToInit

	def send(self, url):
		try:
			f = urllib.urlopen(url)
			xml = f.read()
			f.close()
		except:
			return False, None
		
		return True, xml

	def connect(self, device):
		if device.lower().startswith("/dev/video"):
			try:
				devnum = int(device[10:])
			except:
				return False, None
		else:
			return False, None

		url = self.urlPrefix + "connect?device=%d" % devnum
		return  self.send(url)

	def disconnect(self):
		url = self.urlPrefix + "disconnect"
		return  self.send(url)
	
	def getProperties(self):
		url = self.urlPrefix + "getproperties"
		return  self.send(url)
	
	def setProperties(self, vsat, vcon, vbrt):
		args = ""
		if vsat is not None:
			args += "&saturation=%0.5f" % vsat
		if vcon is not None:
			args += "&contrast=%0.5f" % vcon
		if vbrt is not None:
			args += "&brightness=%0.5f" % vbrt
		if args == "":
			return False, None
		url = self.urlPrefix + "setproperties?" + args[1:]
		return self.send(url)
	
	def picture(self, directory=None, prefix=None):
		args = ""
		if directory is not None:
			args += "&directory=%s" % directory
		if prefix is not None:
			args += "&prefix=%s" % prefix

		if args != "":
			url = self.urlPrefix + "picture?" + args[1:]
		else:
			url = self.urlPrefix + "picture"
		return  self.send(url)

	def timelapseStart(self, interval, count=None, duration=None, directory=None, prefix=None):
		if count is None and duration is None:
			return False, None

		args = "interval=%d" % interval
		if count is None:
			args += "&duration=%d" % duration
		else:
			args += "&count=%d" % count
			
		if directory is not None:
			args += "&directory=%s" % directory
		if prefix is not None:
			args += "&prefix=%s" % prefix

		url = self.urlPrefix + "timelapse?" + args
		return self.send(url)
	
	def timelapsePause(self):
		url = self.urlPrefix + "pause"
		return self.send(url)
	
	def timelapseResume(self):
		url = self.urlPrefix + "resume"
		return self.send(url)
	
	def timelapseStop(self):
		url = self.urlPrefix + "stop"
		return self.send(url)
	
	def timelapseStatus(self):
		url = self.urlPrefix + "status"
		return self.send(url)

	def exit(self):
		url = self.urlPrefix + "exit"
		return  self.send(url)
