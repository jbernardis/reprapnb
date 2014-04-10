import os
import time
import cgi
import select
import socket
from threading import Thread
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import pygame

webbase = "/var/www/images"

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
			query = cgi.parse_qs(opts)
		else:
			path = self.path
			query = {}
			
		r, v = app.dispatch(self, path.lower(), query)

		if not r:
			self.send_response(200)
			self.send_header("Content-type", "text/plain")
			self.end_headers()
			self.wfile.write("Unknown request")
		
		else:
			self.send_response(200)
			self.send_header("Content-type", "text/xml")
			self.send_header("charset", 'ISO-8859-1')
			self.end_headers()
			self.wfile.write(makeXML(v))

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
	def serve_reprap(self):
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

class RepRapServer:
	def __init__(self, app, settings, log):
		self.app = app
		self.settings = settings
		self.log = log
		self.port = settings.port
		if self.port == 0:
			return

		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(('4.2.2.1', 123))
		self.ipaddr = s.getsockname()[0]
		
		self.server = ThreadingHTTPServer((self.ipaddr, self.port), Handler)
		self.server.setApp(self)
		Thread(target=self.server.serve_reprap).start()
		self.log.LogMessage("HTTP Server started on %s:%d" % (self.ipaddr, self.port))
		
	def dispatch(self, cgi, path, query):
		if path == '/status':
			return True, self.queryStatus(query)
		elif path == "/stop":
			return True, self.stopPrint(query)
		elif path == "/temps":
			return True, self.getTemps(query)
		elif path == "/picture":
			return True, self.getPicture(query)
		else:
			return False, None
		
	def queryStatus(self, q):
		return {'status' : self.app.getStatus()}
	
	def stopPrint(self, q):
		return {'stop': self.app.stopPrint()}
	
	def getTemps(self, q):
		return {'temps': self.app.getTemps()}
	
	def getPicture(self, q):
		pic = self.app.snapShot()
		if pic is None:
			return {'picture': 'false'}
		else:
			fbn = "img%s.jpg" % time.strftime('%y-%m-%d-%H-%M-%S', time.localtime(time.time()))
			fn = os.path.join("reprap", fbn)
			path = os.path.join(webbase, fn)
			pygame.image.save(pic, path)
			return {'picture': 'true', 'file': fn}
	
	def close(self):
		if self.port != 0:
			self.server.shut_down()

