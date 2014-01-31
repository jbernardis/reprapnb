import os, thread
import wx
import wx.lib.newevent
from stltool import stl
from amftool import amf
from settings import BUTTONDIM
from wx import glcanvas
from OpenGL.GL import *

FT_STL = 1
FT_AMF = 2

(ReaderEvent, EVT_READER_UPDATE) = wx.lib.newevent.NewEvent()
READER_RUNNING = 1
READER_FINISHED = 2

class ReaderThread:
	def __init__(self, win, fn, ftype):
		self.win = win
		self.fn = fn
		self.ftype = ftype
		self.running = False
		self.cancelled = False
		self.stlObj = None

	def Start(self):
		self.running = True
		self.cancelled = False
		thread.start_new_thread(self.Run, ())

	def Stop(self):
		self.cancelled = True

	def IsRunning(self):
		return self.running
	
	def getStlObj(self):
		return self.stlObj

	def Run(self):
		evt = ReaderEvent(msg = "Reading STL/AMF File...", state = READER_RUNNING)
		wx.PostEvent(self.win, evt)
		
		if self.ftype == FT_STL:
			self.stlObj = stl(cb=self.loadStlEvent, filename=self.fn)
		elif self.ftype == FT_AMF:
			self.stlObj = amf(cb=self.loadStlEvent,filename=self.fn)
		
		evt = ReaderEvent(msg = "completed", state = READER_FINISHED)
		wx.PostEvent(self.win, evt)	
		self.running = False
		
	def loadStlEvent(self, message):
		evt = ReaderEvent(msg = message, state = READER_RUNNING)
		wx.PostEvent(self.win, evt)

InitialLightValue = 100

def vec(*args):
	return (GLfloat * len(args))(*args)

indexColor = 0

colors = [(0.1, 0.6, 0.3, 1), (0.1, 0.6, 0.9, 1), (0.9, 0.6, 0.3, 1), (0.9, 0.6, 0.9, 1), (0.1, 0.8, 0.7, 1)]
white = (1.0, 1.0, 1.0, 1.0)

def color(index):
	i = index % len(colors)
	return colors[i]
	
class StlViewer(wx.Dialog):
	def __init__(self, parent, ysize=800, buildarea=(200, 200, 100)):
		self.parent = parent
		self.logger = self.parent.logger
		self.settings = self.parent.settings
		self.fileList = []
		self.stlList = []
		self.selection = None
		
		border = 15

		pre = wx.PreDialog()
		pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
		pos = wx.DefaultPosition
		style = wx.DEFAULT_DIALOG_STYLE
		pre.Create(self.parent, wx.ID_ANY, "STL/AMF File Viewer", pos, (ysize+border*2+400, ysize), style)
		self.PostCreate(pre)

		self.Bind(wx.EVT_CLOSE, self.onClose)

		box = wx.BoxSizer(wx.HORIZONTAL)

		sz = self.GetClientSize()[1]-2*border
		
		self.canvas = STLCanvas(self, None, drawGrid=self.settings.drawstlgrid)
		self.canvas.SetSize((sz, sz))
		box.Add(self.canvas, 0, wx.ALL, border)

		c2 = wx.BoxSizer(wx.VERTICAL)		
		btn1 = wx.BoxSizer(wx.HORIZONTAL)
		
		self.bAdd = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngAdd, size=BUTTONDIM)
		self.bAdd.SetToolTipString("Add file to the view window")
		btn1.Add(self.bAdd)
		self.Bind(wx.EVT_BUTTON, self.onAddStl, self.bAdd)
		
		self.bDel = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngDel, size=BUTTONDIM)
		self.bDel.SetToolTipString("Remove file from the view window")
		btn1.Add(self.bDel)
		self.Bind(wx.EVT_BUTTON, self.onDelStl, self.bDel)
		self.bDel.Enable(False)
		
		c2.Add(btn1)
		
		self.lb = wx.ListBox(self, wx.ID_ANY, (-1, -1), (400, 120), [], wx.LB_SINGLE)
		c2.Add(self.lb)
		self.Bind(wx.EVT_LISTBOX, self.onLbSelect, self.lb)
		
		c2.AddSpacer((10, 20))
		
		self.slideLights = wx.Slider(
			self, wx.ID_ANY, InitialLightValue, 0, 200, pos=(-1, -1), size=(400, -1),
			style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
		self.slideLights.SetTickFreq(10)
		self.slideLights.Bind(wx.EVT_SCROLL_CHANGED, self.onSliderChange)
		self.slideLights.Bind(wx.EVT_SCROLL_THUMBTRACK, self.onSliderChange)
		c2.Add(self.slideLights)

		c2.AddSpacer((10, 20))
		
		self.cbDrawGrid = wx.CheckBox(self, wx.ID_ANY, "Draw Grid")
		self.cbDrawGrid.SetToolTipString("Turn on/off display of the z=0 grid")
		self.Bind(wx.EVT_CHECKBOX, self.onDrawGrid, self.cbDrawGrid)
		self.cbDrawGrid.SetValue(self.settings.drawstlgrid)
		c2.Add(self.cbDrawGrid)

		c2.AddSpacer((10, 400))
		
		btn2 = wx.BoxSizer(wx.HORIZONTAL)
		
		self.bExit = wx.BitmapButton(self, wx.ID_ANY, self.parent.images.pngExit, size=BUTTONDIM)
		btn2.Add(self.bExit)
		self.Bind(wx.EVT_BUTTON, self.onClose, self.bExit)
		
		c2.Add(btn2)

		box.Add(c2, 0, wx.ALL, border)

		self.Bind(wx.EVT_MOUSEWHEEL, self.onWheel)
		self.SetAutoLayout(True)
		self.SetSizer(box)
		self.Bind(EVT_READER_UPDATE, self.readerUpdate)

	def onSliderChange(self, evt):
		l = evt.EventObject.GetValue()
		self.canvas.animate(l)
		
	def onDrawGrid(self, evt):
		self.settings.drawstlgrid = evt.IsChecked()
		self.settings.setModified()
		self.canvas.setDrawGrid(self.settings.drawstlgrid)

	def onAddStl(self, event):
		dlg = wx.FileDialog(
			self, message="Choose an STL file",
			defaultDir=self.settings.laststldirectory, 
			defaultFile="",
			wildcard="STL (*.stl)|*.stl;*STL|AMF (*.amf.xml, *.amf)|*.amf.xml;*.AMF.XML;*.amf;*.AMF",
			style=wx.FD_OPEN | wx.FD_CHANGE_DIR
			)
		
		if dlg.ShowModal() == wx.ID_OK:
			self.stlPath = dlg.GetPath()
			fn, ext = os.path.splitext(self.stlPath)
			ext = ext.lower()
			ext2 = os.path.splitext(fn)[1].lower()
				
			if ext == ".stl":
				fileType = FT_STL
			elif (ext == ".xml" and ext2 == ".amf") or ext == ".amf":
				fileType = FT_AMF
			else:
				fileType = None
				
			if fileType:
				self.readThread = ReaderThread(self, self.stlPath, fileType)
				self.readThread.Start()
				
		dlg.Destroy()
		
	
	def readerUpdate(self, evt):
		if evt.state == READER_RUNNING:
			if evt.msg is not None:
				self.logger.LogMessage(evt.msg)
				
		elif evt.state == READER_FINISHED:
			if evt.msg is not None:
				self.logger.LogMessage(evt.msg)

			self.continueAddStl()

	def continueAddStl(self):	
		self.stlObj = self.readThread.getStlObj()	
		self.settings.laststldirectory = os.path.dirname(self.stlPath)
		self.settings.setModified()
		self.fileList.append(self.stlPath)
		self.lb.Append(self.stlPath)
		self.selection = len(self.fileList)-1
		self.lb.SetSelection(self.selection)
		self.canvas.addObject(self.stlObj)
		self.bDel.Enable(True)
				
	def onDelStl(self, evt):
		if self.selection is None:
			return
		
		del self.fileList[self.selection]
		self.lb.Delete(self.selection)
		self.canvas.delSelectedStl()
		
		if len(self.fileList) == 0:
			self.selection = None
			self.bDel.Enable(False)
		else:
			if self.selection >= len(self.fileList):
				self.selection = len(self.fileList)-1
			self.lb.SetSelection(self.selection)
			
		self.canvas.setSelection(self.selection)
		
	def onWheel(self, evt):
		self.canvas.OnWheel(evt)
		
	def onLbSelect(self, evt):
		s = evt.GetSelection()
		if s >= 0:
			self.selection = s
			self.canvas.setSelection(self.selection)
		
	def onClose(self, evt):
		try:
			self.parent.stlViewExit()
		except:
			pass
		self.Destroy()

class MyCanvasBase(glcanvas.GLCanvas):
	def __init__(self, parent, wid=-1, buildarea=(200, 200, 100), pos=wx.DefaultPosition,
				 size=(400, 400), style=0, mainwindow=None):
		attribList = (glcanvas.WX_GL_RGBA,  # RGBA
					  glcanvas.WX_GL_DOUBLEBUFFER,  # Double Buffered
					  glcanvas.WX_GL_DEPTH_SIZE, 24)  # 24 bit

		glcanvas.GLCanvas.__init__(self, parent, wid, size=size, style=style, pos=pos, attribList=attribList)
		self.init = False
		# initial mouse position
		self.lastx = self.x = 0
		self.lasty = self.y = 0
		self.anglex = self.angley = 0
		self.transx = self.transy = 0
		self.resetView = True
		self.light0Pos = [0, 0, 150]
		self.light1Pos = [0, 0, 150]
		self.size = None
		self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
		self.Bind(wx.EVT_LEFT_DCLICK, self.OnMouseDouble)
		self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
		self.Bind(wx.EVT_RIGHT_DOWN, self.OnMouseRightDown)
		self.Bind(wx.EVT_MOUSEWHEEL, self.OnWheel)
		self.Bind(wx.EVT_RIGHT_UP, self.OnMouseRightUp)
		self.Bind(wx.EVT_MOTION, self.OnMouseMotion)

	def OnEraseBackground(self, event):
		pass # Do nothing, to avoid flashing on MSW.

	def OnSize(self, event):
		size = self.size = self.GetClientSize()
		if self.GetContext():
			if self.IsShown() and self.GetParent().IsShown():
				self.SetCurrent()
				glViewport(0, 0, size.width, size.height)
		event.Skip()

	def OnPaint(self, event):
		dc = wx.PaintDC(self)
		if self.IsShown():
			self.SetCurrent()
			if not self.init:
				self.InitGL()
				self.init = True
			self.OnDraw()

	def OnMouseDown(self, evt):
		self.SetFocus()
		self.CaptureMouse()
		self.x, self.y = self.lastx, self.lasty = evt.GetPosition()

	def OnMouseRightDown(self, evt):
		self.SetFocus()
		self.CaptureMouse()
		self.x, self.y = self.lastx, self.lasty = evt.GetPosition()

	def OnMouseUp(self, evt):
		if self.HasCapture():
			self.ReleaseMouse()

	def OnMouseRightUp(self, evt):
		if self.HasCapture():
			self.ReleaseMouse()
		
	def OnMouseDouble(self, evt):
		self.resetView = True
		self.setZoom(1.0)
		self.Refresh(False)

	def OnMouseMotion(self, evt):
		if evt.Dragging() and evt.LeftIsDown():
			self.lastx, self.lasty = self.x, self.y
			self.x, self.y = evt.GetPosition()
			self.anglex = self.x - self.lastx
			self.angley = self.y - self.lasty
			self.transx = 0
			self.transy = 0
			self.Refresh(False)

		elif evt.Dragging() and evt.RightIsDown():
			self.lastx, self.lasty = self.x, self.y
			self.x, self.y = evt.GetPosition()
			self.anglex = 0
			self.angley = 0
			self.transx = (self.x - self.lastx)*self.zoom/3.0
			self.transy = -(self.y - self.lasty)*self.zoom/3.0
			self.Refresh(False)
		
	def OnWheel(self, evt):
		z = evt.GetWheelRotation()
		if z < 0:
			zoom = self.zoom*0.9
		else:
			zoom = self.zoom*1.1
				
		self.setZoom(zoom)
		self.Refresh(False)

class GLVolume:
	def __init__(self, v, n, c):
		self.vertices = v
		self.normals = n
		self.colors = c
		self.nvertices = len(v)

class GLObject:
	def __init__(self, stlobj, cx):
		self.volumes = []
		self.origColor = color(cx)
		self.cStart = 0
		self.nColors = 0
		for vol in stlobj.volumes:
			v = [i for f in vol.facets for i in f[1]]
			n = [f[0] for f in vol.facets for i in range(3)]
			c = [color(cx)] * 3 * len(vol.facets)
			self.nColors += len(c)
			self.volumes.append(GLVolume(v, n, c))

class STLCanvas(MyCanvasBase):
	def __init__(self, parent, obj, drawGrid=True, wid=-1, buildarea=(200, 200, 100), pos=wx.DefaultPosition,
				 size=(400, 400), style=0, mainwindow=None):
		self.clientwidth = size[0]
		self.drawGrid = drawGrid
		self.objectList = []
		if obj:
			self.objectList.append(obj)
			self.setSelection(0)
		else:
			self.selection = None
			
		MyCanvasBase.__init__(self, parent, wid, size=size, style=style, pos=pos)
		
	def InitGL(self):
		glClearColor(0, 0, 0, 1)
		glColor3f(1, 0, 0)
		glEnable(GL_DEPTH_TEST)
		glEnable(GL_CULL_FACE)

		glEnable(GL_LIGHTING)
		glEnable(GL_LIGHT0)
		glEnable(GL_LIGHT1)

		glLightfv(GL_LIGHT0, GL_POSITION, vec(.5, .5, 1, 0))
		glLightfv(GL_LIGHT0, GL_SPECULAR, vec(.5, .5, 1, 1))
		glLightfv(GL_LIGHT0, GL_DIFFUSE, vec(1, 1, 1, 1))
		glLightfv(GL_LIGHT1, GL_POSITION, vec(1, 0, .5, 0))
		glLightfv(GL_LIGHT1, GL_DIFFUSE, vec(.5, .5, .5, 1))
		glLightfv(GL_LIGHT1, GL_SPECULAR, vec(1, 1, 1, 1))

		glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, vec(0.5, 0, 0.3, 1))
		glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, vec(1, 1, 1, 1))
		glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 80)
		glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, vec(0, 0.1, 0, 0.9))
		self.setLightPosition(InitialLightValue)
		
		self.setArrays()
		self.setZoom(1.0)

	def setDrawGrid(self, flag):
		self.drawGrid = flag
		self.setArrays()
		self.Refresh(True)
	
	def setLightPosition(self, val):
		self.light0Pos[0] = val-100
		self.light1Pos[0] = 100-val
		self.light0Pos[1] = val
		self.light1Pos[1] = val

		glLightfv(GL_LIGHT0, GL_POSITION, vec(self.light0Pos[0], self.light0Pos[1], self.light0Pos[2], 1))
		glLightfv(GL_LIGHT1, GL_POSITION, vec(self.light1Pos[0], self.light1Pos[1], self.light1Pos[2], 1))

	def animate(self, val):
		self.setLightPosition(val)
		self.Refresh(False)

	def setZoom(self, zoom):
		self.zoom = zoom
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		glFrustum(-0.5*zoom, 0.5*zoom, -0.5*zoom, 0.5*zoom, 1.0, 1000.0)
		glTranslatef(00.0, 0.0, -250)

	def addObject(self, o):
		self.objectList.append(GLObject(o, self.indexColor))
		self.indexColor += 1
		self.setArrays()
		self.setSelection(len(self.objectList)-1)
		self.Refresh(False)
		
	def setArrays(self):
		self.glVertices = []
		self.glNormals = []
		self.glColors = []

		# objects
		objx = 0
		for o in self.objectList:
			o.cStart = len(self.glColors)
			for v in o.volumes:
				self.glVertices.extend(v.vertices)
				self.glNormals.extend(v.normals)
				if objx == self.selection and len(self.objectList) > 1:
					self.glColors.extend([white] * len(v.colors))
				else:
					self.glColors.extend(v.colors)
			objx += 1

		# grid
		lw = 0.25	
		if self.drawGrid:	
			rows = 10
			cols = 10
			for i in xrange(-rows, rows + 1):
				if i % 5 == 0:
					c = [0.6, 0.6, 0.6, 1]
				else:
					c = [0.2, 0.2, 0.2, 1]
				self.glVertices.extend([[10 * -cols, 10 * i-lw, 0], [10*cols, 10*i-lw, 0], [10*cols, 10*i+lw, 0]])
				self.glVertices.extend([[10 * -cols, 10 * i+lw, 0], [10*-cols, 10*i-lw, 0], [10*cols, 10*i+lw, 0]])
				self.glVertices.extend([[10 * -cols, 10 * i-lw, 0], [10*cols, 10*i+lw, 0], [10*cols, 10*i-lw, 0]])
				self.glVertices.extend([[10 * -cols, 10 * i+lw, 0], [10*cols, 10*i+lw, 0], [10*-cols, 10*i-lw, 0]])
				self.glNormals.extend([[0,0,1],[0,0,1],[0,0,1],[0,0,1],[0,0,1],[0,0,1]])
				self.glNormals.extend([[0,0,1],[0,0,1],[0,0,1],[0,0,1],[0,0,1],[0,0,1]])
				self.glColors.extend([c,c,c,c,c,c,c,c,c,c,c,c])
			for i in xrange(-cols, cols + 1):
				if i % 5 == 0:
					c = [0.6, 0.6, 0.6, 1]
				else:
					c = [0.2, 0.2, 0.2, 1]
				self.glVertices.extend([[10 * i-lw, 10 * -rows, 0], [10 * i+lw, 10 * rows, 0], [10 * i-lw, 10 * rows, 0]])
				self.glVertices.extend([[10 * i+lw, 10 * -rows, 0], [10 * i+lw, 10 * rows, 0], [10 * i-lw, 10 * -rows, 0]])
				self.glVertices.extend([[10 * i-lw, 10 * -rows, 0], [10 * i-lw, 10 * rows, 0], [10 * i+lw, 10 * rows, 0]])
				self.glVertices.extend([[10 * i+lw, 10 * -rows, 0], [10 * i-lw, 10 * -rows, 0], [10 * i+lw, 10 * rows, 0]])
				self.glNormals.extend([[0,0,1],[0,0,1],[0,0,1],[0,0,1],[0,0,1],[0,0,1]])
				self.glNormals.extend([[0,0,1],[0,0,1],[0,0,1],[0,0,1],[0,0,1],[0,0,1]])
				self.glColors.extend([c,c,c,c,c,c,c,c,c,c,c,c])
					
			self.glColors.extend([[1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0]])
			self.glVertices.extend([[2,2,0], [-2,2,0], [-2,-2,0]])
			self.glNormals.extend([[0,0,1],[0,0,1],[0,0,1]])
			self.glColors.extend([[1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0]])
			self.glVertices.extend([[2,-2,0], [2,2,0], [-2,-2,0]])
			self.glNormals.extend([[0,0,1],[0,0,1],[0,0,1]])
			self.glColors.extend([[1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0]])
			self.glVertices.extend([[2,2,0], [-2,-2,0], [-2,2,0]])
			self.glNormals.extend([[0,0,1],[0,0,1],[0,0,1]])
			self.glColors.extend([[1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0]])
			self.glVertices.extend([[2,-2,0], [-2,-2,0], [2,2,0]])
			self.glNormals.extend([[0,0,1],[0,0,1],[0,0,1]])

		self.nvertices = len(self.glVertices)
		
		glEnableClientState(GL_VERTEX_ARRAY);
		glVertexPointerf(self.glVertices)
		glEnableClientState(GL_NORMAL_ARRAY);
		glNormalPointerf(self.glNormals)
		glEnableClientState(GL_COLOR_ARRAY);
		glColorPointerf(self.glColors)
		
	def delSelectedStl(self):
		del self.objectList[self.selection]
		self.setArrays()
		if len(self.objectList) == 0:
			self.selection = None
		else:
			if self.selection >= len(self.objectList):
				self.setSelection(len(self.objectList)-1)
			elif len(self.objectList) > 1:
				self.setObjectColor(white)
		self.Refresh(False)
		
	def setSelection(self, sel):
		if self.selection >=0 and self.selection <len(self.objectList):
			self.setObjectColor(self.objectList[self.selection].origColor)
		self.selection = sel
		if len(self.objectList) > 1:
			self.setObjectColor(white)
		self.Refresh(False)
		
	def setObjectColor(self, c):
		o = self.objectList[self.selection]
		self.glColors[o.cStart:o.cStart+o.nColors] = [c] * o.nColors
		glColorPointerf(self.glColors)

	def OnDraw(self):
		glMatrixMode(GL_MODELVIEW)
		if self.resetView:
			glLoadIdentity()
			self.lastx = self.x = 0
			self.lasty = self.y = 0
			self.anglex = self.angley = 0
			self.transx = self.transy = 0
			self.resetView = False
			
		if self.size is None:
			self.size = self.GetClientSize()
		w, h = self.size
		w = max(w, 1.0)
		h = max(h, 1.0)
		xScale = 180.0 / w
		yScale = 180.0 / h
		glRotatef(self.angley * yScale, 1.0, 0.0, 0.0);
		glRotatef(self.anglex * xScale, 0.0, 1.0, 0.0);
		glTranslatef(self.transx, self.transy, 0.0)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

		glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE);
		glEnable(GL_COLOR_MATERIAL);
		glDrawArrays(GL_TRIANGLES, 0, self.nvertices)
			
		self.anglex = self.angley = 0
		self.transx = self.transy = 0
		self.SwapBuffers()
		
