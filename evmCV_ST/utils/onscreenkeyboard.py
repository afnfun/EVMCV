import os, pygame, re, sys, string, random
import datetime
from pygame.locals import *
sys.path.append(os.path.join('..', '..'))
from gnosis.xml.objectify import XML_Objectify
import textrect

settings = XML_Objectify('configuration_files/EVMCVSettings.xml').make_instance()
# screen configuration
#screen_width=int(settings.Screen_Width.PCDATA)
#screen_height=int(settings.Screen_Height.PCDATA)
#screen = pygame.display.set_mode( (screen_width, screen_height),0)
#print screen_width
# Functions to create our resources



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

class OnScreenKeyboard:
	def __init__( self, screen, maxChar, title, text='', show=1):
		self.screen=screen
		self.screen_width, self.screen_height=screen.get_size()

		self.title = title
		self.text = text
		self.text_rect = None
		self.image = load_image('keyboard.png', None, (769, 361));
		self.xpos = (self.screen_width - 769) / 2 # difference between screen and keyboard widthes / 2 (centrelized)
		self.ypos = (self.screen_height - 361) / 2 + 100 # (difference between screen and keyboard hight / 2) + 100 to give space for writ-in text
		self.fontsize = 36
		self.font = pygame.font.SysFont('arial',self.fontsize)
		self.titlefontsize = 32
		self.titlefont = pygame.font.SysFont('arial',self.titlefontsize)
		self.titletop = (self.screen_height - 361) / 2 - 100
		self.texttop = (self.screen_height - 361) / 2
		self.cursor_width = 20
		self.max_length = 24
		self.maxChar = maxChar
		self.show = show
		self.background=self.background=pygame.image.tostring(self.screen, 'RGB')

	
	def draw( self):
		# Clear the screen
		#self.set_video_mode()
		#self.background=pygame.image.tostring(self.screen, 'RGB')
		self.screen.fill((255,255,255))

		# Draw the title
		xw,yh = self.titlefont.size("W")
		x1=(self.screen_width-740)/2
		y1=self.titletop
		x2=self.screen_width-x1
		y2= self.titletop+(yh*2+2)
		title_rec = pygame.Rect(x1,y1,x2,y2)
		rendered_text=textrect.render_textrect(self.title, self.titlefont, title_rec , (0,0,255), (255,255,255),1)
		textpos=rendered_text.get_rect()
		textpos.centerx=self.screen.get_rect().centerx
		textpos[1]=y1
		self.screen.blit(rendered_text,textpos)
		#
		#Draw Input Text Rectangle
		xw,yh = self.font.size("W")
		x1=int ((self.screen_width-750)/2)
		y1=self.texttop-5
		x2=750
		y2= yh+10
		text_rec=pygame.Rect(x1, y1 , x2 , y2 )
		pygame.draw.rect(self.screen,(0,0,0),text_rec, 1)

		# Draw the keyboard
		self.screen.blit( self.image, (self.xpos, self.ypos))
		
		#update the screen
		pygame.display.update()

		self.draw_text()

	def draw_text( self):
		if self.text_rect:
			# Clear the previous text
			self.screen.fill( (255, 255, 255), self.text_rect)

		# Render the text
		if (self.show==0):
			str=""
			for i in self.text:
				str=str+"*"
		else:
			str=self.text



		xw,yh = self.font.size("W")
		char_per_line= int(740/xw)
		
		fit_str=str[-char_per_line:len(str)]
		textobj = self.font.render( fit_str , 0, (0,0,200))

		# Compute the x ccordintate for centering
		textleft = (self.screen_width-textobj.get_width()-self.cursor_width) / 2

		# Draw the text onto the screen
		self.screen.blit( textobj, (textleft, self.texttop))

		# Draw the cursor
		self.screen.fill( (0, 0, 0),
			(textleft+textobj.get_width(),self.texttop,
			self.cursor_width, textobj.get_height()))

		# Record the new text rectangle for later clearing
		new_text_rect = (textleft, self.texttop,
			textobj.get_width() + self.cursor_width, textobj.get_height())

		# Update the display
		pygame.display.update( new_text_rect)
		if self.text_rect:
			pygame.display.update( self.text_rect)

		# Record the new text rect for next time
		self.text_rect = new_text_rect

	def append_char( self, char):
		if len(self.text) < self.maxChar:
			self.text = self.text + char
			self.draw_text()

	def backspace( self):
		self.text = self.text[:-1]
		self.draw_text()

	def edit(self,FVTout=-1):
		self.draw()
		now1 = datetime.datetime.now() #read current time
		while 1:
			now2 = datetime.datetime.now() #read current time
			diff = now2-now1
			if (diff.seconds>=FVTout and FVTout!=-1):
				self.background=pygame.image.fromstring(self.background, self.screen.get_size(), 'RGB')
				self.screen.blit(self.background,(0,0))
				pygame.event.clear(MOUSEBUTTONUP)
				return 'timeout'
			pygame.time.wait(20)
			for event in pygame.event.get():
				now1 = datetime.datetime.now() #reset timeout count
				if event.type is KEYDOWN:
					if event.key == K_ESCAPE:
						self.background=pygame.image.fromstring(self.background, self.screen.get_size(), 'RGB')
						self.screen.blit(self.background,(0,0))
						pygame.event.clear(MOUSEBUTTONUP)
						return
					elif event.key == K_SPACE:
						self.append_char(' ')
					elif event.key >= ord('a') and event.key <= ord('z'):
						self.append_char(chr(event.key-32))
					elif event.key == K_BACKSPACE:
						self.backspace()
					elif event.key == K_RETURN:
						self.background=pygame.image.fromstring(self.background, self.screen.get_size(), 'RGB')
						self.screen.blit(self.background,(0,0))
						pygame.event.clear(MOUSEBUTTONUP)
						return
				elif event.type is MOUSEBUTTONUP:
					pos = pygame.mouse.get_pos()

					# Make sure the mouse is within the bounds of the keyboard
					if( pos[0] >= self.xpos and pos[0] < self.xpos+768 and
						pos[1] >= self.ypos and pos[1] < self.ypos+360):
						# Determine the grid coordinates of the click
						gridx = (pos[0] - self.xpos) / 96
						gridy = (pos[1] - self.ypos) / 90

						# Determine the key being pressed
						if( gridy < 3 or gridx < 2):
							# It's an alphabetic char
							self.append_char( chr(65+gridx+gridy*8))
						elif( gridx < 4):
							# It's the SPACE key
							self.append_char( ' ')
						elif( gridx < 6):
							# It's the backspace key
							self.backspace()
						else:
							# It's the DONE key
							self.background=pygame.image.fromstring(self.background, self.screen.get_size(), 'RGB')
							self.screen.blit(self.background,(0,0))
							pygame.event.clear(MOUSEBUTTONUP)
							return



