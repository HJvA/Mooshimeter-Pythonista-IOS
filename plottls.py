""" genral purpose tools for drawing to canvas
    including mapping of coordinate systems
"""
from __future__ import division
import canvas
import ui

class canvas_context(object):
	""" maps user coordinates to world (e.g. ios pixel canvas) coordinates
	"""
	def __init__(self, wrld_frame=None, user_frame=(0.0,0.0, 1.0,1.0)):
		if wrld_frame is None:
			w,h = canvas.get_size()
			self.wrld = (0.0,0.0,w,h)
		else:
			self.wrld=wrld_frame
		self.loca=list(user_frame)
		print('wrld:%s loca:%s' % (self.wrld,self.loca))
	
	def set_size(self,width,height):
		self.loca[2] = width
		self.loca[3] = height
		
	def get_size():
		return self.loca[2],self.loca[3]
		
	def get_origin():
		return self.loca[0],self.loca[1]
				
	def xyWorld(self,xUser,yUser):
		xt = self.wrld[0] + (xUser-self.loca[0]) / (self.loca[2]/self.wrld[2])
		yt = self.wrld[1] + (yUser-self.loca[1]) / (self.loca[3]/self.wrld[3])
		return xt,yt
		
	def whWorld(self,w,h):
		wt = w/ (self.loca[2]/self.wrld[2])
		ht = h/ (self.loca[3]/self.wrld[3])
		return wt,ht
		
	def whUser(self,wWorld,hWorld):
		wt = w* (self.loca[2]/self.wrld[2])
		ht = h* (self.loca[3]/self.wrld[3])
		return wt,ht
		
	def sub_frame(self, loc_frame):
		loca = list(loc_frame)
		loca[0],loca[1] = self.xyWorld(loc_frame[0],loc_frame[1])
		loca[2],loca[3] = self.whWorld(loc_frame[2],loc_frame[3])
		return tuple(loca)
		
	def draw_rect(self,x,y,width,height):
		#print('x,y:%f,%f' % (self.xyTrans(x,y)))
		#print('w,h:%f,%f' % (self.whTrans(width,height)))
		return canvas.draw_rect(*self.xyWorld(x,y),*self.whWorld(width,height))
		
	def draw_line(self,x1,y1,x2,y2):
		return canvas.draw_line(*self.xyWorld(x1,y1),*self.xyWorld(x2,y2))
		
	def draw_dashed_line(self,x1, y1, x2, y2, ndashes=43):
	
		'''Draw a dashed line from (x1,y1) to (x2,y2)'''
		
		dx = float(x2 - x1)
		dy = float(y2 - y1)
		kx = dx / ndashes
		ky = dy / ndashes
	
		self.move_to(x1, y1)
		for i in range(1,ndashes+1):					
			if i % 2 == 1:
				self.add_line(x1 +i*kx, y1 + i*ky)
			else:
				self.move_to(x1 +i*kx, y1 + i*ky)		
		canvas.draw_path()
		
	def draw_text(self,text, x, y, font_name='Helvetica', font_size=16.0):
		canvas.draw_text(text, *self.xyWorld(x,y), font_name, font_size)
		
	def move_to(self,x,y):
		canvas.move_to(*self.xyWorld(x,y))
	
		
	def add_line(self,x,y):
		canvas.add_line(*self.xyWorld(x,y))
		
	def add_curve(cp1x, cp1y, cp2x, cp2y, x, y):
		canvas.add_curve(*self.xyWorld(cp1x,cp1y), *self.xyWorld(cp2x,cp2y), *self.xyWorld(x,y))
	
	def get_text_size(self, text, font_name='Helvetica', font_size=16.0):
		''' size of text string in user coordinates '''
		return self.whUser(*canvas.get_text_size(text, font_name, font_size))
		
if __name__ == "__main__":
	canvas.set_size(*ui.get_screen_size())
	cnvs = canvas_context( user_frame=(-100,-100,200,200))
	cnvs.draw_rect(10,10,80,80)
	subfrm = canvas_context(cnvs.sub_frame((10,10,80,80)), (-5,-5,10,10))
	for i in range(-4,5,1):
		subfrm.draw_dashed_line(*(i,-5,i,5))
		pass
