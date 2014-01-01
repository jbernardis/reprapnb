import os
import wx
from stltool import stl

from wx import glcanvas
from OpenGL.GL import *

BUTTONDIM = (48, 48)
InitialLightValue = 100

def vec(*args):
	return (GLfloat * len(args))(*args)

colors = [vec(0.1, 0.6, 0.3, 1), vec(0.1, 0.6, 0.9, 1), vec(0.9, 0.6, 0.3, 1), vec(0.9, 0.6, 0.9, 1), vec(0.1, 0.8, 0.7, 1)]

def color(index):
	i = index % len(colors)
	return colors[i]
	
class StlViewer(wx.Dialog):
	def __init__(self, parent, title, ysize=800, buildarea=(200, 200, 100)):
		self.parent = parent
		self.settings = self.parent.settings
		self.fileList = []
		self.stlList = []
		self.selection = None
		
		border = 15

		pre = wx.PreDialog()
		pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
		pos = wx.DefaultPosition
		style = wx.DEFAULT_DIALOG_STYLE
		pre.Create(self.parent, wx.ID_ANY, "STL File Viewer", pos, (ysize+border*2+400, ysize), style)
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
			wildcard="STL (*.stl)|*.[sS][tT][lL]",
			style=wx.FD_OPEN | wx.FD_CHANGE_DIR
			)
		
		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()
			self.settings.laststldirectory = os.path.dirname(path)
			self.settings.setModified()
			self.fileList.append(path)
			self.lb.Append(path)
			self.selection = len(self.fileList)-1
			self.lb.SetSelection(self.selection)
			s = stl(filename=path)
			self.canvas.addObject(s)
			self.bDel.Enable(True)
				
		dlg.Destroy()
		
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
		self.light0Pos = []
		self.light1Pos = []
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

class STLCanvas(MyCanvasBase):
	def __init__(self, parent, obj, drawGrid=True, wid=-1, buildarea=(200, 200, 100), pos=wx.DefaultPosition,
				 size=(400, 400), style=0, mainwindow=None):
		self.clientwidth = size[0]
		self.drawGrid = drawGrid
		self.objectList = []
		if obj:
			self.objectList.append(obj)
			self.selection = 0
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
		self.setZoom(1.0)
		
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
		
	def setDrawGrid(self, flag):
		self.drawGrid = flag
		self.Refresh(False)

	def addObject(self, o):
		self.objectList.append(o)
		self.selection = len(self.objectList)-1
		self.Refresh(False)
		
	def delSelectedStl(self):
		del self.objectList[self.selection]
		if len(self.objectList) == 0:
			self.selection = None
		else:
			if self.selection >= len(self.objectList):
				self.selection = len(self.objectList)-1
		self.Refresh(False)
		
	def setSelection(self, sel):
		self.selection = sel
		self.Refresh(False)

	def OnDraw(self):
		# clear color and depth buffers
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
		if self.drawGrid:
			self.doDrawGrid()
		
		index = 0
		for o in self.objectList:
			self.draw_object(o, index)
			index += 1
			
		self.anglex = self.angley = 0
		self.transx = self.transy = 0
		self.SwapBuffers()
		
	def draw_object(self, obj, index):
		c = color(index)
		glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, c)
	
		glBegin(GL_TRIANGLES)
		for f in obj.facets:
			glNormal3f(f[0][0], f[0][1], f[0][2])
			for i in range(3):
				glVertex3f(f[1][i][0], f[1][i][1], f[1][i][2])
		glEnd()
		
		if len(self.objectList) > 1 and index == self.selection:
			glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, vec(1,1,1,1))
			glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
		
			glBegin(GL_TRIANGLES)
			for f in obj.facets:
				glNormal3f(f[0][0], f[0][1], f[0][2])
				for i in range(3):
					glVertex3f(f[1][i][0], f[1][i][1], f[1][i][2])
			glEnd()
			glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
		
	def doDrawGrid(self):
		glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, vec(0.2, 0.2, 0.2, 1))
		glBegin(GL_LINES)
		glNormal3f(0, 0, 1)
		rows = 10
		cols = 10
		for i in xrange(-rows, rows + 1):
			if i % 5 == 0:
				glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, vec(0.6, 0.6, 0.6, 1))
			else:
				glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, vec(0.2, 0.2, 0.2, 1))
			glVertex3f(10 * -cols, 10 * i, 0)
			glVertex3f(10 * cols, 10 * i, 0)
		for i in xrange(-cols, cols + 1):
			if i % 5 == 0:
				glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, vec(0.6, 0.6, 0.6, 1))
			else:
				glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, vec(0.2, 0.2, 0.2, 1))
			glVertex3f(10 * i, 10 * -rows, 0)
			glVertex3f(10 * i, 10 * rows, 0)
		glEnd()
		
		glBegin(GL_TRIANGLES)
		glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, vec(1, 0, 0, 1))
		glNormal3f(0, 0, 1)
		glVertex3f(2, 2, 0)
		glVertex3f(-2, 2, 0)
		glVertex3f(-2, -2, 0)
		glVertex3f(2, -2, 0)
		glVertex3f(2, 2, 0)
		glVertex3f(-2, -2, 0)
		glEnd()
