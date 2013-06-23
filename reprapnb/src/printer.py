'''
Created on Jun 20, 2013

@author: ejefber
'''

def createPrinterObject(name, app, parent):
	if name == 'ob1':
		return OB1(app, parent)
	
	if name == 'delta':
		return Delta(app, parent)
	
	return None
	
	
class OB1:
	def __init__(self, app, parent):
		self.app = app
		self.parent = parent
		self.settings = parent.settings
		
class Delta:
	def __init__(self, app, parent):
		self.app = app
		self.parent = parent
		self.settings = parent.settings
		
