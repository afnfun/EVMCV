import os, pygame, re, sys, string, random
from pygame.locals import *
sys.path.append(os.path.join('..', '..'))

# screen configuration
screen_width = 1280
screen_height = 1024
screen = pygame.display.set_mode( (screen_width, screen_height),0)

# Functions to create our resources
def load_image(name, colorkey=-1, size=None):
# Complete file path
	fullname = os.path.join('graphics', name)
#load ballot image "graphics/ballot-mockup3.png"
	try:
		image = pygame.image.load(fullname) # future work, generate image dynamically from xml file
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
	def __init__( self, title, text=''):
		self.title = title
		self.text = text
		self.text_rect = None

	def draw( self):
		# Clear the screen
		screen.fill( (255, 255, 255))

		# Draw the title
		titleobj = self.titlefont.render( 'There was no responce from voter during last 30 seconds.', 1, (200,0,0))

		# Center it at the top of the screen
		titleleft = (screen_width - titleobj.get_width()) / 2
		screen.blit( titleobj, (titleleft, self.titletop))
                titleobj2 = self.titlefont.render( 'To cancel vote casting, enter security code:', 1, (200,0,0))
                screen.blit( titleobj2, (titleleft, self.titletop+35))
                

		# Draw the keyboard
		screen.blit( self.image, (self.xpos, self.ypos))

		pygame.display.update()

		self.draw_text()

	def draw_text( self):
		if self.text_rect:
			# Clear the previous text
			screen.fill( (255, 255, 255), self.text_rect)

		# Render the text
		textobj = self.font.render( self.text, 0, (0,0,200))

		# Compute the x ccordintate for centering
		textleft = (screen_width-textobj.get_width()-self.cursor_width) / 2

		# Draw the text onto the screen
		screen.blit( textobj, (textleft, self.texttop))

		# Draw the cursor
		screen.fill( (0, 0, 0),
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
		if len(self.text) < self.max_length:
			self.text = self.text + char
			self.draw_text()

	def backspace( self):
		self.text = self.text[:-1]
		self.draw_text()

	def edit( self):
		self.draw()

		while 1:
			pygame.time.wait(20)
			for event in pygame.event.get():
				if event.type is KEYDOWN:
					if event.key == K_ESCAPE:
						return
					elif event.key == K_SPACE:
						self.append_char(' ')
					elif event.key >= ord('a') and event.key <= ord('z'):
						self.append_char(chr(event.key-32))
					elif event.key == K_BACKSPACE:
						self.backspace()
					elif event.key == K_RETURN:
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
							return