import sys, struct, math

nest = 0

def cross(v1,v2):
	return [v1[1]*v2[2]-v1[2]*v2[1],v1[2]*v2[0]-v1[0]*v2[2],v1[0]*v2[1]-v1[1]*v2[0]]

def genfacet(v):
	veca=[v[1][0]-v[0][0],v[1][1]-v[0][1],v[1][2]-v[0][2]]
	vecb=[v[2][0]-v[1][0],v[2][1]-v[1][1],v[2][2]-v[1][2]]
	vecx=cross(veca,vecb)
	vlen=math.sqrt(sum(map(lambda x:x*x,vecx)))
	if vlen==0:
		vlen=1
	normal=map(lambda x:x/vlen, vecx)
	return [normal,v]

I=[
	[1,0,0,0],
	[0,1,0,0],
	[0,0,1,0],
	[0,0,0,1]
]

def transpose(matrix):
	return zip(*matrix)
	
def multmatrix(vector,matrix):
	return map(sum, transpose(map(lambda x:[x[0]*p for p in x[1]], zip(vector, transpose(matrix)))))
	
def applymatrix(facet,matrix=I):
	return genfacet(map(lambda x:multmatrix(x+[1],matrix)[:3],facet[1]))
	
f=[[0,0,0],[[-3.022642, 0.642482, -9.510565],[-3.022642, 0.642482, -9.510565],[-3.022642, 0.642482, -9.510565]]]
m=[
	[1,0,0,0],
	[0,1,0,0],
	[0,0,1,1],
	[0,0,0,1]
]

def emitstl(filename,facets=[],objname="stltool_export",binary=False):
	if filename is None:
		return False
	if binary:
		try:
			f=open(filename,"wb")
		except:
			return False
		
		buf="".join(["\0"]*80)
		buf+=struct.pack("<I",len(facets))
		facetformat=struct.Struct("<ffffffffffffH")
		for i in facets:
			l=list(i[0][:])
			for j in i[1]:
				l+=j[:]
			l+=[0]
			buf+=facetformat.pack(*l)
		f.write(buf)
		f.close()
		return True
		

	try:
		f=open(filename,"w")
	except:
		return False
	
	f.write("solid "+objname+"\n")
	for i in facets:
		f.write("  facet normal "+" ".join(map(str,i[0]))+"\n   outer loop\n")
		for j in i[1]:
			f.write("	vertex "+" ".join(map(str,j))+"\n")
		f.write("   endloop"+"\n")
		f.write("  endfacet"+"\n")
	f.write("endsolid "+objname+"\n")
	f.close()
	return True
		
class stl:
	def __init__(self, cb=None, filename=None, name=None, zZero=False, xOffset=0, yOffset=0):
		self.facet=[[0,0,0],[[0,0,0],[0,0,0],[0,0,0]]]
		self.facets=[]
		self.volumes=[self]
		self.facetsminz=[]
		self.facetsmaxz=[]
		self.zZero = zZero
		self.xOffset = xOffset
		self.yOffset = yOffset
		
		self.name=name
		self.insolid=0
		self.infacet=0
		self.inloop=0
		self.facetloc=0
		self.translatex = 0
		self.translatey = 0
		self.rotation = 0
		self.scalefactor = 1
		self.id = None
		self.filename = filename

		if filename is not None:
			if cb:
				cb("Reading of %s Starting" % filename)
			try:
				self.f=list(open(filename))
			except:
				if cb:
					cb("Error opening STL file")
				return
			
			if not self.f[0].startswith("solid"):
				if cb:
					cb("Not an ascii stl solid - attempting to parse as binary")
				try:
					f=open(filename,"rb")
				except:
					if cb:
						cb("Error opening STL file")
					return
	
				buf=f.read(84)
				while(len(buf)<84):
					newdata=f.read(84-len(buf))
					if not len(newdata):
						break
					buf+=newdata
				facetcount=struct.unpack_from("<I",buf,80)
				facetformat=struct.Struct("<ffffffffffffH")
				for i in xrange(facetcount[0]):
					buf=f.read(50)
					while(len(buf)<50):
						newdata=f.read(50-len(buf))
						if not len(newdata):
							break
						buf+=newdata
	
					if (i % 100000) == 0 and cb:
						cb("%d facets read" % i)
					
					fd=list(facetformat.unpack(buf))
					self.facet=[fd[:3],[fd[3:6],fd[6:9],fd[9:12]]]
					self.facets+=[self.facet]
					facet=self.facet
					self.facetsminz+=[(min(map(lambda x:x[2], facet[1])),facet)]
					self.facetsmaxz+=[(max(map(lambda x:x[2], facet[1])),facet)]
				f.close()
				if cb:
					cb("Binary read completed: %d facets" % facetcount[0])
			else:
				ctr = 0
				for i in self.f:
					self.parseline(i)
					ctr += 1
					if (ctr % 10000) == 0 and cb:
						cb("%d text lines read" % ctr)
				if cb:
					cb("Text Read Completed")
				
			if cb:
				cb("Calculating Mesh Geometry")
	
			minx = 99999
			maxx = -99999
			miny = 99999
			maxy = -99999
			minz = 99999
			maxz = -99999
			fx = 0
			for f in self.facets:
				minx = min([minx, f[1][0][0], f[1][1][0], f[1][2][0]])
				miny = min([miny, f[1][0][1], f[1][1][1], f[1][2][1]])
				minz = min([minz, f[1][0][2], f[1][1][2], f[1][2][2]])
				maxx = max([maxx, f[1][0][0], f[1][1][0], f[1][2][0]])
				maxy = max([maxy, f[1][0][1], f[1][1][1], f[1][2][1]])
				maxz = max([maxz, f[1][0][2], f[1][1][2], f[1][2][2]])
				fx += 1
				if (fx % 10000 == 0) and cb:
					cb("Processed %d facets" % fx)
					
			if cb:
				cb("Processed %d total facets" % fx)
				
			self.hxCenter = (minx + maxx)/2.0
			self.hyCenter = (miny + maxy)/2.0
			if cb:
				cb("Center=(%f,%f)" % (self.hxCenter, self.hyCenter))
				
			self.hxSize = maxx-minx
			self.hySize = maxy-miny
			self.hArea = self.hxSize * self.hySize
	
			modFacets = False
			if self.zZero and minz != 0:
				if cb:
					cb("Dropping object to z=0 plane from a height of %f" % minz)
				for i in range(len(self.facets)):
					for j in range(3):
						self.facets[i][1][j][2] -= minz
				modFacets = True
				self.zZero = False
				
			if self.xOffset + self.yOffset != 0:
				if cb:
					cb("Translating object (%d, %d)" % (self.xOffset, self.yOffset))
				for i in range(len(self.facets)):
					for j in range(3):
						self.facets[i][1][j][0] += self.xOffset
						self.facets[i][1][j][1] += self.yOffset
				modFacets = True
				self.xOffset = 0
				self.yOffset = 0
	
			if modFacets:
				if cb:
					cb("Adjusting facets")					
				self.facetsminz=[]
				self.facetsmaxz=[]
				for facet in self.facets:
					self.facetsminz+=[(min(map(lambda x:x[2], facet[1])),facet)]
					self.facetsmaxz+=[(max(map(lambda x:x[2], facet[1])),facet)]
			
			if cb:
				cb("STL load completed")
						
	def setId(self, sid):
		self.id = sid
		
	def getId(self):
		return self.id
	
	def translate(self,v=[0,0,0]):
		matrix=[
		[1,0,0,v[0]],
		[0,1,0,v[1]],
		[0,0,1,v[2]],
		[0,0,0,1]
		]
		return self.transform(matrix)
	
	def rotate(self,v=[0,0,0]):
		z=v[2]
		matrix1=[
		[math.cos(math.radians(z)),-math.sin(math.radians(z)),0,0],
		[math.sin(math.radians(z)),math.cos(math.radians(z)),0,0],
		[0,0,1,0],
		[0,0,0,1]
		]
		y=v[0]
		matrix2=[
		[1,0,0,0],
		[0,math.cos(math.radians(y)),-math.sin(math.radians(y)),0],
		[0,math.sin(math.radians(y)),math.cos(math.radians(y)),0],
		[0,0,0,1]
		]
		x=v[1]
		matrix3=[
		[math.cos(math.radians(x)),0,-math.sin(math.radians(x)),0],
		[0,1,0,0],
		[math.sin(math.radians(x)),0,math.cos(math.radians(x)),0],
		[0,0,0,1]
		]
		return self.transform(matrix1).transform(matrix2).transform(matrix3)
	
	def scale(self,v=[0,0,0]):
		matrix=[
		[v[0],0,0,0],
		[0,v[1],0,0],
		[0,0,v[2],0],
		[0,0,0,1]
		]
		return self.transform(matrix)
		
		
	def transform(self,m=I):
		s=stl()
		s.filename = self.filename
		
		s.facets=[applymatrix(i,m) for i in self.facets]
		s.insolid=0
		s.infacet=0
		s.inloop=0
		s.facetloc=0
		s.name=self.name
		for facet in s.facets:
			s.facetsminz+=[(min(map(lambda x:x[2], facet[1])),facet)]
			s.facetsmaxz+=[(max(map(lambda x:x[2], facet[1])),facet)]
		return s
		
		
	def clone(self, name=None):
		s=stl()
		s.filename = self.filename
		
		s.facets=[i for i in self.facets]
		s.insolid=0
		s.infacet=0
		s.inloop=0
		s.facetloc=0
		if name is None:
			s.name=self.name
		else:
			s.name = name
			
		s.facetsminz = [f for f in self.facetsminz]
		s.facetsmaxz = [f for f in self.facetsmaxz]
		
		s.hull = [h for h in self.hull]   #                <==
		s.hxCenter = self.hxCenter
		s.hyCenter = self.hyCenter
		s.hxSize = self.hxSize
		s.hySize = self.hySize
		s.hArea = self.hArea
		
		s.rotation = self.rotation
		s.translatex = self.translatex
		s.translatey = self.translatey
		s.scalefactor = self.scalefactor	

		return s
		
	def export(self,f=sys.stdout):
		f.write("solid "+self.name+"\n")
		for i in self.facets:
			f.write("  facet normal "+" ".join(map(str,i[0]))+"\n")
			f.write("   outer loop"+"\n")
			for j in i[1]:
				f.write("	vertex "+" ".join(map(str,j))+"\n")
			f.write("   endloop"+"\n")
			f.write("  endfacet"+"\n")
		f.write("endsolid "+self.name+"\n")
		f.flush()
		
	def parseline(self,l):
		l=l.strip()
		if l.startswith("solid"):
			self.insolid=1
			
		elif l.startswith("endsolid"):
			self.insolid=0
			return 0
		elif l.startswith("facet normal"):
			l=l.replace(",",".")
			self.infacet=11
			self.facetloc=0
			self.facet=[[0,0,0],[[0,0,0],[0,0,0],[0,0,0]]]
			self.facet[0]=map(float,l.split()[2:])
		elif l.startswith("endfacet"):
			self.infacet=0
			self.facets+=[self.facet]
			facet=self.facet
			self.facetsminz+=[(min(map(lambda x:x[2], facet[1])),facet)]
			self.facetsmaxz+=[(max(map(lambda x:x[2], facet[1])),facet)]
		elif l.startswith("vertex"):
			l=l.replace(",",".")
			self.facet[1][self.facetloc]=map(float,l.split()[1:])
			self.facetloc+=1
		return 1
