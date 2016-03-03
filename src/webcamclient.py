import urllib

class Webcam:
	def __init__(self, ip, port):
		self.ip = ip
		self.port = port
		self.urlPrefix = "http://%s:%s/" % (ip, port)

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
	
	def fnpicture(self, directory=None, prefix=None, base=None):
		args = ""
		if directory is not None:
			args += "&directory=%s" % directory
		if prefix is not None:
			args += "&prefix=%s" % prefix
		if base is not None:
			args += "&base=%s" % base

		if args != "":
			url = self.urlPrefix + "fnpicture?" + args[1:]
			return self.send(url)

		return False, None

	def fntimelapse(self, directory=None, prefix=None, base=None):
		args = ""
		if directory is not None:
			args += "&directory=%s" % directory
		if prefix is not None:
			args += "&prefix=%s" % prefix
		if base is not None:
			args += "&base=%s" % base

		if args != "":
			url = self.urlPrefix + "fntimelapse?" + args[1:]
			return self.send(url)

		return False, None

	def picture(self):
		url = self.urlPrefix + "picture"
		return  self.send(url)

	def timelapse(self, interval, count=None, duration=None):
		if count is None and duration is None:
			return False, None

		args = "interval=%d" % interval
		if count is None:
			args += "&duration=%d" % duration
		else:
			args += "&count=%d" % count

		url = self.urlPrefix + "timelapse?" + args
		return self.send(url)

	def exit(self):
		url = self.urlPrefix + "exit"
		return  self.send(url)
