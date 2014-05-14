import os
import pygame
import sys
from pygame.locals import *
sys.path.append(os.path.join('..', '..'))
import textrect


def load_image(name, colorkey=-1, size=None):
# Complete file path
	fullname = os.path.join('graphics', name)
	try:
		image = pygame.image.load(fullname) 
	except pygame.error, message:
		print 'Cannot load image:', fullname
		raise SystemExit, message

	if size is not None:
		image = pygame.transform.scale( image, size)
	image = image.convert()

	if colorkey is not None:
		if colorkey is -1:
			colorkey = image.get_at((0,0))
		image.set_colorkey(colorkey, RLEACCEL)
	return image

class Dialogue:
	def __init__( self):
		self.Yes_Button = load_image('yes.png')
		self.Yes_Button_size = self.Yes_Button.get_size()
		self.Yes_Button_x = 0
		self.Yes_Button_y = 0
		self.No_Button = load_image('no.png')
		self.No_Button_size = self.No_Button.get_size()
		self.No_Button_x = 0
		self.No_Button_y = 0
		
		

	
	def responce(self, screen, title, text=''):
		background=pygame.image.tostring(screen, 'RGB')
		#clear screen
		screen.fill((255,255,255))
		# Draw the title text
		font = pygame.font.SysFont('arial',20)
		title_pixels = font.size(title)
		y=float(title_pixels[0])/500
		if y >int(y):
			y=int(y)+1
		y = (y * (title_pixels[1]+2))+4
		#
		title_rec = pygame.Rect(0,0,500,y)
		title_rec.centerx=screen.get_rect().centerx
		title_rec[1]=200
		rendered_text=textrect.render_textrect(title, font, title_rec , (255,255,255), (0,0,255),1)
		screen.blit(rendered_text,title_rec)
		#
		# Draw the message text
		text_pixels = font.size(text)
		y=float(text_pixels[0])/500
		if y>int(y): y=int(y)+1
		y+=1
		y = (y * (text_pixels[1]+2))+ 4 + (30+self.Yes_Button_size[1]) #text rect which includes area for buttons
		#
		text_rec = pygame.Rect(0,0,500,y)
		text_rec.centerx=screen.get_rect().centerx
		text_rec[1]=title_rec[1]+title_rec[3]
		rendered_text=textrect.render_textrect('\n'+text, font, text_rec , (0,0,0), (224,249,255),1)
		screen.blit(rendered_text,text_rec)
		#
		#Draw Input Text Rectangle
		self.Yes_Button_x = text_rec[0]+10
		self.No_Button_x = self.Yes_Button_x + self.Yes_Button_size[0] + 70
		self.Yes_Button_y = text_rec[1] + text_rec[3] - (10+self.Yes_Button_size[1])
		self.No_Button_y = text_rec[1] + text_rec[3] - (10+self.No_Button_size[1])

		# Draw the keyboard
		screen.blit( self.Yes_Button, (self.Yes_Button_x, self.Yes_Button_y))
		screen.blit( self.No_Button, (self.No_Button_x, self.No_Button_y))

		#update the screen
		pygame.display.update()
		while 1:
			pygame.time.wait(20)
			for event in pygame.event.get():
				if event.type is MOUSEBUTTONUP:
					pos = pygame.mouse.get_pos()
					# Make sure the mouse is within the bounds of the keyboard
					if( pos[0] >= self.Yes_Button_x and pos[0] < self.Yes_Button_x+self.Yes_Button_size[0] and
						pos[1] >= self.Yes_Button_y and pos[1] < self.Yes_Button_y+self.Yes_Button_size[1]):
						# Determine the grid coordinates of the click
						background=pygame.image.fromstring(background, screen.get_size(), 'RGB')
						screen.blit(background,(0,0))
						pygame.event.clear(MOUSEBUTTONUP)
						return 1
					if( pos[0] >= self.No_Button_x and pos[0] < self.No_Button_x+self.No_Button_size[0] and
						pos[1] >= self.No_Button_y and pos[1] < self.No_Button_y+self.No_Button_size[1]):
						# Determine the grid coordinates of the click
						background=pygame.image.fromstring(background, screen.get_size(), 'RGB')
						screen.blit(background,(0,0))
						pygame.event.clear(MOUSEBUTTONUP)
						return 0

						



