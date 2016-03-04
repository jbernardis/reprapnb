import urlparse
import select
import socket
import time
import os
import sys
from threading import Thread, Timer, Lock
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import cv2


propertyMap = {
	'saturation':cv2.cv.CV_CAP_PROP_SATURATION,
	'contrast':cv2.cv.CV_CAP_PROP_CONTRAST,
	'brightness':cv2.cv.CV_CAP_PROP_BRIGHTNESS}

def quote(s):
	return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def makeXML(d):
	xml = ''
	for k in d.keys():
		if type(d[k]) is dict:
			xml+='<'+k+'>'+makeXML(d[k])+'</'+k+'>'
		elif type(d[k]) is list:
			for i in d[k]:
				xml += '<'+k+'>'+makeXML(i)+'</'+k+'>'
		else:
			xml+='<'+k+'>'+quote(str(d[k]))+'</'+k+'>'
	
	return xml

class Handler(BaseHTTPRequestHandler):
	def do_GET(self):
		app = self.server.getApp()
		
		if '?' in self.path:
			path, opts = self.path.split('?', 1)
			query = urlparse.parse_qs(opts)
		else:
			path = self.path
			query = {}
			
		r, v = app.dispatch(self, path.lower(), query)

		if not r and v is None:
			self.send_response(200)
			self.send_header("Content-type", "text/plain")
			self.end_headers()
			self.wfile.write("Exited Webcam server")
			self.server.shut_down()
		elif not r:
			self.send_response(200)
			self.send_header("Content-type", "text/plain")
			self.end_headers()
			self.wfile.write("Unknown request.  Allowed: /getproperties, /setproperties, /picture, /timelapse, /status")
		
		else:
			self.send_response(200)
			self.send_header("Content-type", "text/xml")
			self.send_header("charset", 'ISO-8859-1')
			self.end_headers()
			self.wfile.write(makeXML(v))

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
	def serve_webcam(self):
		self.haltServer = False
		while self.haltServer == False:
			if select.select([self.socket], [], [], 1)[0]:
				self.handle_request()
				
	def setApp(self, app):
		self.app = app
		
	def getApp(self):
		return self.app
			
	def shut_down(self):
		self.haltServer = True
		
class Webcam:
	def __init__(self):
		self.device = None
		self.connected = False
		self.camera = None
		self.props = {}
		self.pendingProps = {}
		
	def connect(self, device):
		if self.isConnected():
			return {'result': 'not connected'}

		self.device = device		
		self.camera = cv2.VideoCapture(self.device)
		
		self.props = {}
		for p in propertyMap.keys():
			k = propertyMap[p]
			self.props[k] = self.camera.get(k)
		
			
		for p in self.pendingProps.keys():
			self.props[p] = self.pendingProps[p]
			self.camera.set(p, self.props[p])
			
		self.pendingProps = {}
			
		return {'result': 'success'}
	
	def disconnect(self):
		if self.camera is None:
			return False
		
		self.device = None
		del(self.camera)
		self.camera = None
		return {'result': 'success'}
		
	def isConnected(self):
		return self.camera is not None
	
	def setProperty(self, p, v):
		if self.isConnected():
			self.props[p] = v
			self.camera.set(p, v)
		else:
			self.pendingProps[p] = v

		return {'result': 'success', 'value': v}
			
	def getProperties(self):
		if not self.isConnected():
			return {'result': 'not connected'}

		self.props = {}
		for p in propertyMap.keys():
			k = propertyMap[p]
			self.props[k] = self.camera.get(k)
		return {'result': 'success', 'properties': self.props}

	def picture(self, filename):
		if not self.isConnected():
			return {'result': 'not connected'}

		rc, img = self.camera.read()
		if not rc:
			return {'result': 'failure'}

		cv2.imwrite(filename, img)
		return {'result': 'success', 'filename': filename}

class WebcamServer:
	def __init__(self, ipport):
		self.ipport = ipport
		self.tlTimer = None
		self.running = True
		self.cameraFree = Lock()

		self.imgType = "png"

		self.webcam = Webcam()

		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(('4.2.2.1', 123))
		self.ipaddr = s.getsockname()[0]
		
		self.server = ThreadingHTTPServer((self.ipaddr, self.ipport), Handler)
		self.server.setApp(self)
		self.wcThread = Thread(target=self.server.serve_webcam)
		print "HTTP Server started on %s:%d" % (self.ipaddr, self.ipport)
		self.wcThread.start()
	
	def wait(self):
		self.wcThread.join()
		print "HTTP Server ended"
		
	def dispatch(self, cgi, path, query):
		if path == '/connect':
			return True, self.connect(query)
		elif path == "/disconnect":
			return True, self.disconnect(query)
		elif path == '/setproperties':
			return True, self.setProperties(query)
		elif path == "/getproperties":
			return True, self.getProperties(query)
		elif path == "/picture":
			return True, self.picture(query)
		elif path == "/timelapse":
			return True, self.timeLapse(query)
		elif path == "/imagetype":
			return True, self.imageType(query)
		elif path == "/status":
			return True, self.getStatus(query)
		elif path == "/exit":
			self.running = False
			if self.tlTimer is not None:
				try:
					self.tlTimer.cancel()
				except:
					pass
			return False, None
		else:
			return False, {}
		
	def setProperties(self, q):
		#/setproperties?[saturation="x"&brightness="x"&contrast="x"}
		rslt = {}
		for k in propertyMap.keys():
			if k in q.keys():
				rslt["set-%s" % k] =  self.webcam.setProperty(propertyMap[k], float(q[k][0]))

		return {'setproperties' : rslt}
	
	def getProperties(self, q):
		#/getProperties
		p = self.webcam.getProperties()
		if 'properties' in p.keys():
			props = p['properties']
			for k in propertyMap.keys():
				if propertyMap[k] in props.keys():
					props[k] = str(props[propertyMap[k]])
					del(props[propertyMap[k]])

		return {'getProperties': p }
	
	def connect(self, q):
		#/connect?device="dev"
		k = 'device'
		if not k in q.keys():
			return {'connect': 'Missing device name'}

		self.device = int(q[k][0])	
		rslt = self.webcam.connect(self.device)
		return {'connect': rslt}
	
	def disconnect(self, q):
		#/disconnect
		rslt = self.webcam.disconnect()
		self.device = None
		return {'disconnect': rslt}

	def imageType(self, q):
		if 'type' not in q.keys():
			return {'imagetype': 'type missing'}

		newType = q['type'][0].lower()

		if newType not in ['jpg', 'png']:
			return {'imagetype': "unsupported image type: %s" % newType}

		self.imgType = newType
		return {'imagetype': 'success'}
	
	def picture(self, q):
		#/picture?fn=x
		if not self.webcam.isConnected():
			return {'picture': 'not connected'}
		
		if 'prefix' in q.keys():
			prefix = q['prefix'][0]
		else:
			prefix = "img"
			
		if 'directory' in q.keys():
			directory = q['directory'][0]
		else:
			directory = "."

		bn = prefix + time.strftime("-%y-%m-%d-%H-%M-%S", time.localtime(time.time())) + "." + self.imgType

		fn = os.path.join(directory, bn)

		self.cameraFree.acquire()
		rslt = self.webcam.picture(fn)
		self.cameraFree.release()

		return {'picture': rslt}
	
	def timeLapse(self, q):
		#/timelapse?interval=x&count=x&duration=x
		if not self.webcam.isConnected():
			return {'timelapse': 'not connected'}

		if self.tlTimer is not None:
			return {'timelapse': 'timelapse already running'}

		if 'interval' not in q.keys():
			return {'timelapse': 'missing interval'}
		try:
			self.interval = int(q['interval'][0])
		except:
			return {'timelapse': 'invalid interval'}
		if self.interval <= 0:
			return {'timelapse': 'interval must be > 0'}

		if 'count' in q.keys():
			try:
				self.maxIterations = int(q['count'][0])
			except:
				return {'timelapse': 'invalid count value'}
			if self.maxIterations <= 0:
				return {'timelapse': 'count must be > 0'}

		elif 'duration' in q.keys():
			try:
				secs = int(q['duration'][0])
			except:
				return {'timelapse': 'invalid duration value'}
			if secs <= 0:
				return {'timelapse': 'duration must be > 0'}
			self.maxIterations = int(float(secs)/float(self.interval) + 0.5)

		else:
			return {'timelapse': 'missing count or duration'}
		
		if 'prefix' in q.keys():
			self.tlPrefix = q['prefix'][0]
		else:
			self.tlPrefix = "img"
			
		if 'directory' in q.keys():
			self.tlDir = q['directory'][0]
		else:
			self.tlDir = "."

		self.iteration = 0
		if 'immediate' in q.keys():
			self.doInterval()
		else:
			self.tlTimer = Timer(self.interval, self.doInterval)
			self.tlTimer.start()

		return {'timelapse': 'started'}

	def doInterval(self):
		suffix = "-%04d" % self.iteration
		self.iteration += 1

		bn = self.tlPrefix + suffix + "." + self.imgType

		fn = os.path.join(self.tlDir, bn)

		self.cameraFree.acquire()
		self.webcam.picture(fn)
		self.cameraFree.release()

		if self.iteration < self.maxIterations and self.running:
			self.tlTimer = Timer(self.interval, self.doInterval)
			self.tlTimer.start()
		else:
			self.tlTimer = None
	
	def getStatus(self, q):
		#/status
		if self.tlTimer is None:
			return {'status': 'idle'}
		return {'status': 'timelapse running', 'interval': self.interval, 'interations': self.iterations, 'maxiterations': self.maxIterations}
			
			
port = 8887
if len(sys.argv) > 1:
	try:
		port = int(sys.argv[1])
	except:
		port = 8887

a = WebcamServer(port)
a.wait()

