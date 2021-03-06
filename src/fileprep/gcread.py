import math
import re
import time

YIELDTHRESHOLD = 100

filrad = 1.5
lh = 0.2

from settings import MAX_EXTRUDERS

gcRegex = re.compile("[-]?\d+[.]?\d*")

class Line(object):
	def __init__(self,l):
		self._x = None
		self._y = None
		self._z = None
		self.e = None
		self.f = 0
		
		self.orig = l
		
		self.raw = l.lstrip()
		self.imperial = False
		self.relative = False
		self.relative_e = False
		
		if ";" in self.raw:
			self.raw = self.raw.split(";")[0]
			
		if self.raw.startswith("M117"):
			self.raw += " "
		
		if self.movement(self.raw):
			self._parse_coordinates()
			
	def movement(self, s):
		ls = s.strip()
		if ls.startswith("G1 "): return True
		if ls.startswith("G2 "): return True
		if ls.startswith("G3 "): return True
		if ls.startswith("G0 "): return True
		if ls.startswith("G28 "): return True
		if ls.startswith("G92 "): return True
		
		return False
		
	def _to_mm(self,v):
		if v and self.imperial:
			return v*25.4
		return v
		
	def _getx(self):
		return self._to_mm(self._x)
			
	def _setx(self,v):
		self._x = v

	def _gety(self):
		return self._to_mm(self._y)

	def _sety(self,v):
		self._y = v

	def _getz(self):
		return self._to_mm(self._z)

	def _setz(self,v):
		self._z = v

	def _gete(self):
		return self._to_mm(self._e)

	def _sete(self,v):
		self._e = v
		
	def setRelative(self, r):
		self.relative = r
		self.relative_e = r

	def setRelativeE(self, r):
		self.relative_e = r

	x = property(_getx,_setx)
	y = property(_gety,_sety)
	z = property(_getz,_setz)
	e = property(_gete,_sete)
	
		
	def command(self):
		try:
			return self.raw.split(" ")[0]
		except:
			return ""
			
	def _get_float(self,which):
		return float(gcRegex.findall(self.raw.split(which)[1])[0])
		
		
	def _parse_coordinates(self):
		if "X" in self.raw:
			self._x = self._get_float("X")
			
		if "Y" in self.raw:
			self._y = self._get_float("Y")

		if "Z" in self.raw:
			self._z = self._get_float("Z")

		if "E" in self.raw:
			self.e = self._get_float("E")

		if "F" in self.raw:
			self.f = self._get_float("F")

		
	def is_move(self):
		return "G1" in self.raw or "G0" in self.raw

class Layer:
	def __init__(self, model, x=0, y=0, z=0, e=0, tool=0, speed=0, prev=None, ln=0, lx=0):
		self.prevLayer = prev
		self.model = model
		self.currentx = self.startx = x
		self.currenty = self.starty = y
		self.currentz = self.startz = z
		self.currente = self.starte = e
		self.currentspeed = self.startspeed = speed
		self.currenttool = tool
		self.moves = []
		self.layernumber = ln
		self.startlx = lx
		
	def addMove(self, x=None, y=None, z=None, e=None,  tool=0, speed=None, relative=False, relative_e=False, line=0):
		if x is None:
			cx = self.currentx
		elif relative:
			cx = self.currentx + x
		else:
			cx = x
				
		if y is None:
			cy = self.currenty
		elif relative:
			cy = self.currenty + y
		else:
			cy = y

		if z is None:
			cz = self.currentz
		elif relative:
			cz = self.currentz + z
		else:
			cz = z
			
		ce = e
		lw = 0.5
		
		if ce is not None:		
			dist = math.fabs(math.hypot(self.currentx - cx, self.currenty - cy))
			if relative:
				vol = ce * self.model.getFilamentRad(tool)
			else:
				vol = (ce - self.currente) * self.model.getFilamentRad(tool)
			if dist != 0.0:
				lw = vol/(dist * self.model.getLayerHeight())
			
		cspeed = speed
		if speed is None or speed == 0.0:
			cspeed = self.currentspeed
			
		self.moves.append([cx, cy, cz, ce, tool, cspeed, line, False, lw])
		
		self.currentx = cx
		self.currenty = cy
		self.currentz = cz
		if ce is not None:
			self.currente = ce
		self.currenttool = tool
		self.currentspeed = cspeed
		
	def getLayerZ(self):
		return self.startz
	
	def getLayerNumber(self):
		return self.layernumber
		
	def getLayerStart(self):
		self.mx = -1
		return (self.startx, self.starty, self.startz, self.starte, self.currenttool, self.startspeed, self.startlx, False, 0.5)
	
	def getNextMove(self):
		self.mx += 1
		if self.mx >= len(self.moves):
			return None
		return self.moves[self.mx]
	
	def getMoveByGcodeLine(self, lx):
		miA = self.getLayerStart()
		miB = None
		while lx > miA[6]:
			miB = self.getNextMove()
			if miB is None:
				return None
			if miB[6] > lx:
				return miA
			
			miA = miB
			
		return None
	
	def getPrevLayer(self):
		return self.prevLayer
		
		
	def resetAxis(self, x=None, y=None, z=None, e=None, tool=None, line=0):
		if x is not None:
			self.currentx = x
			
		if y is not None:
			self.currenty = y
		
		if z is not None:
			self.currentz = z
			
		if e is not None:
			self.currente = e
		
		if tool is not None:
			self.currenttool = tool
		
		self.moves.append([self.currentx, self.currenty, self.currentz,
			self.currente, self.currenttool, self.currentspeed, line, True, 0.5])
					

class GCode(object):
	def __init__(self, data, lh, fd, acceleration=1500, retractiontime=0):
		self.lh = lh
		self.frad = [x/2 * x/2 * math.pi for x in fd]
		self.acceleration = acceleration
		self.retractiontime = retractiontime
		self.lines = []
		self.pendingPauseLayers = []
		self.immediatePauseLayers = []
		self.yieldCounter = 0
		
		self.sampleCount = -10 # skip the first 10 samples
		self.rateValue = 0.0
		
		for i in data:
			self.lines.append(Line(i))
			
		self.process()
			
	def metaCommand(self, cmd, layernbr, linenbr):
		l = cmd.split()
		nl = len(l)
		
		if nl < 1:
			return
		
		nl -= 1
		verb = l[0]
		l = l[1:]
		
		values = {}
		
		for term in l:
			try:
				name, val = term.split("=")
				values[name.lower()] = val
			except:
				pass
		
		if verb.lower() == "@pause":
			if 'layer' in values.keys():
				try:
					x = int(values['layer'])
					lift = None
					if 'lift' in values.keys():
						lift = float(values['lift'])
					self.pendingPauseLayers.append((x-1, lift))

				except:
					pass
				
			else:
				self.immediatePauseLayers.append((layernbr, linenbr))

				
	def checkPendingPause(self, layer):
		for i in range(len(self.pendingPauseLayers)):
			ln = self.pendingPauseLayers[i][0]
			if ln == layer:
				return True
			
		return False
		
	def checkImmediatePause(self, layer):
		rv = []
		for ln, lx in self.immediatePauseLayers:
			if ln == layer:
				rv.append(lx)
			
		return rv
		
	def checkYield(self):
		self.yieldCounter += 1
		if self.yieldCounter > YIELDTHRESHOLD:
			self.yieldCounter = 0
			time.sleep(0)
		
	def getLayerHeight(self):
		return self.lh
	
	def getTemps(self):
		return (self.bedTemp, self.heTemps)
	
	def getFilamentRad(self, tool):
		return self.frad[tool]
		
	def __iter__(self):
		self.__lx__ = 0
		return self
	
	def next(self):
		if self.__lx__ < self.__len__():
			i = self.__lx__
			self.__lx__ += 1
			return self.lines[i]

		raise StopIteration
	
	def __len__(self):
		return len(self.lines)
		
	def insertGCode(self, line, g):
		nl = []
		for l in g:
			nl.append(Line(l))
			
		self.lines[line:line] = nl
		self.process()
		
	def process(self):			
		lnbr = 0
		self.pendingPauseLayers = []
		self.immediatePauseLayers = []
		self.currenttool = 0
		self.layers = []
		self.layerlines = []
		self.bedTemp = None
		self.heTemps = [None] * MAX_EXTRUDERS
		
		lyr = Layer(self, ln = lnbr, lx=0, tool=0)
		self.currentheight = 0.0
		self.layers.append(lyr)
		
		lx = -1
		layerstartx = 0
		
		relative = False
		relative_e = False
		for ln in self.lines:
			self.checkYield()
			lx += 1
			
			if ln.raw.startswith('@'):
				self.metaCommand(ln.raw, lnbr, lx)
			elif ln.command() == "G91":
				relative = True
				relative_e = True
			elif ln.command() == "G90":
				relative = False
				relative_e = False
			elif ln.command() == "M82":
				relative_e = False
			elif ln.command() == "M83":
				relative_e = True
			elif ln.command() == "G92":
				lyr.resetAxis(ln.x, ln.y, ln.z, ln.e, lx)
			elif ln.command() == "M140" or ln.command() == "M190":
				if self.bedTemp is None:
					if "S" in ln.raw:
						self.bedTemp = ln._get_float("S")
			elif ln.command() == "M104" or ln.command() == "M109":
				if self.heTemps[self.currenttool] is None:
					if "S" in ln.raw:
						self.heTemps[self.currenttool] = ln._get_float("S")
			elif ln.command().startswith("T"):
				try:
					t = int(ln.command()[1:])
				except:
					t = None

				if t is not None:
					self.currenttool = t

			elif ln.is_move():
				ln.setRelative(relative)
				ln.setRelativeE(relative_e)
				if ln.z is not None and ((not relative and ln.z != self.currentheight) or (relative and ln.z != 0)):
					if ln.x is None:
						cx = lyr.currentx
					else:
						cx = ln.x
						
					if ln.y is None:
						cy = lyr.currenty
					else:
						cy = ln.y
						
					if ln.e is None:
						ce = lyr.currente
					else:
						ce = ln.e
						
					if ln.f is None:
						cf = lyr.currentspeed
					else:
						cf = ln.f

					olyr = lyr
					lnbr += 1						
					if relative:
						self.currentheight += ln.z
					else:
						self.currentheight = ln.z

					lyr = Layer(self, cx, cy, self.currentheight, ce, self.currenttool, cf, prev=olyr, ln=lnbr, lx=lx)
					self.layers.append(lyr)
					self.layerlines.append([layerstartx, lx-1])
					layerstartx = lx
				else:
					lyr.addMove(ln.x, ln.y, ln.z, ln.e, self.currenttool, ln.f, relative, relative_e, lx)

		self.layerlines.append([layerstartx, lx])	
						
		self.measure()
		self.filament_length()
		self.time()
		
	def countLayers(self):
		return len(self.layers)
	
	def findEValue(self, lx):
		if lx < 0 or lx >= len(self.lines):
			return 0.00
		
		x = lx
		while self.lines[x].e is None:
			x -= 1
			if x < 0:
				return 0.00
			
		return self.lines[x].e
	
	def findLayerByLine(self, lx):
		for i in range(len(self.layerlines)):
			s = self.layerlines[i]
			if lx >= s[0] and lx <= s[1]:
				return i
		
		return None
	
	def findToolByLine(self, lx):
		lyx = self.findLayerByLine(lx)
		if lyx is None:
			return None
		
		lyr = self.getLayer(lyx)
		if lyr is None:
			return None
		
		mi = lyr.getMoveByGcodeLine(lx)
		if mi is None:
			return None
		
		return mi[4]

	
	def getLayerName(self, x):
		return "Layer " + str(x)
	
	def firstLayer(self):
		self.lx = 0
		if self.lx >= len(self.layers):
			return None
		
		return self.layers[self.lx]
	
	def prevLayer(self):
		if self.lx == 0:
			return None
		
		self.lx -= 1
		return self.layers[self.lx]
	
	def nextLayer(self):
		self.lx += 1
		if self.lx >= len(self.layers):
			return None
		
		return self.layers[self.lx]
	
	def getLayer(self, n):
		if n < 0 or n >= len(self.layers):
			return None
		
		return self.layers[n]
	
	def measure(self):
		xmin = 999999999
		ymin = 999999999
		zmin = 0
		xmax = -999999999
		ymax = -999999999
		zmax = -999999999
		
		layer_x_max = -99999999
		layer_y_max = -99999999
		layer_x_min = 99999999
		layer_y_min = 99999999
		
		self.layer_max = []
		self.layer_min = []
		self.layer_z = []
		
		current_x = 0
		current_y = 0
		current_z = 0

		for line in self.lines:
			self.checkYield()
			if line.command() == "G92":
				if line.x is not None: current_x = line.x
				if line.y is not None: current_y = line.y
				if line.z is not None: current_z = line.z

			if line.is_move():
				layer_z = current_z
				
				x = line.x 
				y = line.y
				z = line.z
				
				if line.relative:
					x = current_x + (x or 0)
					y = current_y + (y or 0)
					z = current_z + (z or 0)
					
				if z is not None and (layer_z != z):
					self.layer_z.append(layer_z)
					self.layer_min.append([layer_x_min, layer_y_min])
					self.layer_max.append([layer_x_max, layer_y_max])
					layer_x_max = -99999999
					layer_y_max = -99999999
					layer_x_min = 99999999
					layer_y_min = 99999999
				
				if x and line.e:
					if x < xmin:
						xmin = x
					if x > xmax:
						xmax = x
						
					if x < layer_x_min:
						layer_x_min = x
					if x > layer_x_max:
						layer_x_max = x
						
				if y and line.e:
					if y < ymin:
						ymin = y
					if y > ymax:
						ymax = y
						
					if y < layer_y_min:
						layer_y_min = y
					if y > layer_y_max:
						layer_y_max = y
						
				if z:
					if z < zmin:
						zmin = z
					if z > zmax:
						zmax = z
				
				if x is not None: current_x = x
				if y is not None: current_y = y
				if z is not None: current_z = z
				
		self.xmin = xmin
		self.ymin = ymin
		self.zmin = zmin
		self.xmax = xmax
		self.ymax = ymax
		self.zmax = zmax
		
		self.layer_z.append(layer_z)
		self.layer_min.append([layer_x_min, layer_y_min])
		self.layer_max.append([layer_x_max, layer_y_max])
		
		self.width = xmax-xmin
		self.depth = ymax-ymin
		self.height = zmax-zmin
		
	def filament_length(self):
		self.total_e = [0] * MAX_EXTRUDERS
		cur_e = [0] * MAX_EXTRUDERS
		segment_e = [0] * MAX_EXTRUDERS
		segment_start_e = [0] * MAX_EXTRUDERS
		layer_e = [0] * MAX_EXTRUDERS

		cur_z = 0
		self.layer_e = []
		self.layer_e_end = []
		self.layer_e_start = [[0 for i in range(MAX_EXTRUDERS)]]
		currentTool = 0

		lx = 0	
		for line in self.lines:
			self.checkYield()
			lx += 1
			if line.command() == "G92":
				if line.e != None:
					layer_e[currentTool] += (cur_e[currentTool] - segment_start_e[currentTool])
					cur_e[currentTool] = line.e
					segment_e[currentTool] = cur_e[currentTool]
					segment_start_e[currentTool] = cur_e[currentTool]
					
			elif line.command().startswith("T"):
				try:
					t = int(line.command()[1:])
				except:
					t = None

				if t is not None:
					currentTool = t
					
			elif line.is_move():
				if line.z and line.z != cur_z:
					layer_e[currentTool] += (cur_e[currentTool] - segment_start_e[currentTool])
					s = [e for e in layer_e]
					self.layer_e.append(s)
					for i in range(MAX_EXTRUDERS):
						self.total_e[i] += layer_e[i]
						layer_e[i] = 0
						segment_start_e[i] = cur_e[i]
					
					s = [e for e in self.total_e]
					self.layer_e_start.append(s)
					self.layer_e_end.append(s)
					cur_z = line.z
				
				if line.e:
					if line.relative_e:
						cur_e[currentTool] += line.e
					else:
						cur_e[currentTool] = line.e

		layer_e[currentTool] += (cur_e[currentTool] - segment_start_e[currentTool])
		self.total_e[currentTool] += layer_e[currentTool]
		self.layer_e_end.append(self.total_e)
		self.layer_e.append(layer_e)
		
	def _get_float(self,raw,which):
		l = raw.split(which)
		if len(l) < 2:
			return None
		return float(gcRegex.findall(l[1])[0])
	
	def time(self):
		
		lastx = lasty = lastz = laste = lastf = lastdx = lastdy = 0.0
		x = y = z = e = f = 0.0
		currenttravel = 0.0
		moveduration = 0.0
		layerbeginduration = 0.0
		layercount=0
		retractioncount = 0
		relative=False
		relative_e=False
		
		self.duration = 0.0
		self.layer_time = []

		for line in self.lines:
			self.checkYield()
			if "G90" in line.raw:
				relative = False
				relative_e = False
				
			elif "G91" in line.raw:
				relative = True
				relative_e = True
				
			elif "M82" in line.raw:
				relative_e = False
				
			elif "M83" in line.raw:
				relative_e = True
				
			elif "G92" in line.raw:
				if line.x: lastx = x
				if line.y: lasty = y
				if line.z: lastz = z
				if line.e: laste = e
				
			elif "G28" in line.raw:
				if line.x: lastx = 0
				if line.y: lasty = 0
				if line.z: lastz = 0
				
				if line.x is None and line.y is None and line.z is None:
					lastx = lasty = lastz = 0
				
			elif "G4" in line.raw:
				moveduration = self._get_float(line.raw, "P")
				if moveduration is None:
					moveduration = self._get_float(line.raw, "S")
					if moveduration == None:
						continue
				else:
					moveduration /= 1000.0
					
				self.duration += moveduration
				
			elif "G0" in line.raw or "G1" in line.raw:
				x = line.x
				if x is None: 
					x=lastx
				elif relative:
					x+=lastx
					
				y = line.y
				if y is None:
					y=lasty
				elif relative:
					y+=lasty
					
				z = line.z
				if z is None:
					z=lastz
				elif relative:
					z+=lastz
					
				e = line.e
				if e is None:
					e=laste
				elif relative_e:
					e+=laste
				retraction = False
				if e < laste:
					retraction = True
					retractioncount += 1
					
				f = line.f
				if f is None or f == 0: 
					f=lastf
				else:
					f /= 60.0 # mm/s vs mm/m
				
				# given last feedrate and current feedrate calculate the distance needed to achieve current feedrate.
				# if travel is longer than req'd distance, then subtract distance to achieve full speed, and add the time it took to get there.
				# then calculate the time taken to complete the remaining distance
				
				dx = x - lastx
				dy = y - lasty
				if dx * lastdx + dy * lastdy <= 0:
					lastf = 0

				moveduration = 0.0
				currenttravel = math.hypot(dx, dy)
				if line.e is None:
					currentextrude = 0.0
				elif line.relative_e:
					currentextrude = abs(line.e)
				else:
					currentextrude =  abs(line.e - laste)
					
				if currenttravel == 0:
					if line.z is not None:
						currenttravel = abs(line.z) if line.relative else abs(line.z - lastz)
					elif line.e is not None:
						currenttravel = currentextrude
						
				elif line.z is None and currentextrude != 0:
					# we've moved horizontally and extruded at the same time - figure out extrusion rate
					self.tallyExtrusionRate(currentextrude/currenttravel)
					
				# Feedrate hasn't changed, no acceleration/decceleration planned
				if f == lastf:
					moveduration = currenttravel / f if f != 0 else 0.
				else:
					# FIXME: review this better
					# this looks wrong : there's little chance that the feedrate we'll decelerate to is the previous feedrate
					# shouldn't we instead look at three consecutive moves ?
					distance = 2 * abs(((lastf + f) * (f - lastf) * 0.5) / self.acceleration)  # multiply by 2 because we have to accelerate and decelerate
					if distance <= currenttravel and lastf + f != 0 and f != 0:
						moveduration = 2 * distance / (lastf + f)  # This is distance / mean(lastf, f)
						moveduration += (currenttravel - distance) / f
					else:
						moveduration = 2 * currenttravel / (lastf + f)  # This is currenttravel / mean(lastf, f)
						# FIXME: probably a little bit optimistic, but probably a much better estimate than the previous one:
						# moveduration = math.sqrt(2 * distance / acceleration) # probably buggy : not taking actual travel into account

				lastdx = dx
				lastdy = dy
						
				self.duration += moveduration
	
				if z != lastz:
					self.duration += (retractioncount * self.retractiontime)/1000.0
					layertime = self.duration - layerbeginduration
					self.layer_time.append(layertime)
					layerbeginduration = self.duration
					print "layer %d time %d includes %d milliseconds/retraction for %d retractions" % (
								layercount, layertime, self.retractiontime, retractioncount)
					retractioncount = 0
					layercount +=1
	
				if x is not None: lastx = x
				if y is not None: lasty = y
				if z is not None: lastz = z
				if e is not None: laste = e
				if f is not None: lastf = f
				
		self.duration += (retractioncount * self.retractiontime)/1000.0
		layertime = self.duration - layerbeginduration
		self.layer_time.append(layertime)
		print "final layer %d time %d includes %d milliseconds/retraction for %d retractions" % (
					layercount, layertime, self.retractiontime, retractioncount)
		
	def tallyExtrusionRate(self, rate):
		self.sampleCount += 1
		if self.sampleCount > 0:
			self.rateValue += rate
			
	def getExtrusionRate(self):
		if self.sampleCount <= 0:
			return None
		return self.rateValue/self.sampleCount
		
	def getLayerZ(self, lx):
		if lx < 0 or lx >= len(self.layer_e):
			return None
		
		return self.layer_z[lx]
		
		
	def getLayerInfo(self, lx):
		if lx < 0 or lx >= len(self.layer_e):
			return None
		
		return [self.layer_z[lx], self.layer_min[lx], self.layer_max[lx], self.layer_e[lx], self.layerlines[lx], self.layer_time[lx], self.layer_e_start[lx]]
