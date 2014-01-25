import xml.parsers.expat

from stltool import genfacet

class AmfXml:
	def __init__(self, filename, addFacet, endVolume):
		self.addFacet = addFacet
		self.endVolume = endVolume
		self.vertices = []
		self.triangles = []
		self.inX = False
		self.inY = False
		self.inZ = False
		self.inV1 = False
		self.inV2 = False
		self.inV3 = False
		p = xml.parsers.expat.ParserCreate()

		p.StartElementHandler = self.start_element
		p.EndElementHandler = self.end_element
		p.CharacterDataHandler = self.char_data

		text = open(filename).read()		
		p.Parse(text,  1)
		
	def start_element(self, name, attrs):
		lname = name.lower()
		if lname == "mesh":
			self.triangles = []
			self.vertices = []
		elif lname == 'volume':
			self.triangles = []
		elif lname == 'x':
			self.inX = True
		elif lname == 'y':
			self.inY = True
		elif lname == 'z':
			self.inZ = True
		elif lname == 'v1':
			self.inV1 = True
		elif lname == 'v2':
			self.inV2 = True
		elif lname == 'v3':
			self.inV3 = True
		
	def end_element(self, name):
		lname = name.lower()
		if lname == "volume":
			for t in self.triangles:
				self.addFacet([self.vertices[t[0]], self.vertices[t[1]], self.vertices[t[2]]])
			self.endVolume()
		
	def char_data(self, data):
		if data.strip() == "":
			return
		if self.inX:
			try:
				n = float(data)
			except:
				n = 0.0
			self.currentVertex = [n, 0, 0]
			self.inX = False
		elif self.inY:
			try:
				n = float(data)
			except:
				n = 0.0
			self.currentVertex[1] = n
			self.inY = False
		elif self.inZ:
			try:
				n = float(data)
			except:
				n = 0.0
			self.currentVertex[2] = n
			self.vertices.append(self.currentVertex)
			self.inZ = False
		elif self.inV1:
			try:
				n = int(data)
			except:
				n = 0
			self.currentTriangle = [n, 0, 0]
			self.inV1 = False
		elif self.inV2:
			try:
				n = int(data)
			except:
				n = 0
			self.currentTriangle[1] = n
			self.inV2 = False
		elif self.inV3:
			try:
				n = int(data)
			except:
				n = 0
			self.currentTriangle[2] = n
			self.triangles.append(self.currentTriangle)
			self.inV3 = False
		
class amfVol:
	def __init__(self, facets):
		self.facets = facets

class amf:
	def __init__(self, filename=None):	
		self.volfacets=[]
		self.volumes = []
	
		AmfXml(filename, self.addFacet, self.endVolume)
		
	def addFacet(self, f):
		self.volfacets.append(genfacet(f))
		
	def endVolume(self):
		self.volumes.append(amfVol(self.volfacets))
		self.volfacets = []
