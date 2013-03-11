import sys
if sys.platform != 'win32':
    sys.path.append('../..')
else:
    sys.path.append('..\\..')
from evm2003.data.contests import cont
from evm2003.utils.onscreenkeyboard import OnScreenKeyboard
import os, pygame, re, sys, string, random, datetime
from pygame.locals import *

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


# screen configuration
screen_width = 1280
screen_height = 1024
screen = pygame.display.set_mode( (screen_width, screen_height),0)



def no_response():
    loop=1
    global screen
    no_response= load_image('no_response.png', None,(screen_width, screen_height))
    screen.blit( no_response, (0,0))
    pygame.display.update()
    while loop==1:
	for event in pygame.event.get():
	    if event.type is MOUSEBUTTONUP:
		pos = pygame.mouse.get_pos()
		if (pos[0] >= 238 and pos[0] <= 500 and pos[1] >= 557 and pos[1] <= 642):
		    action='cast'
		    loop=0
		elif (pos[0] >= 694 and pos[0] <= 957 and pos[1] >= 557 and pos[1] <= 642):
		    action='cancel'
		    loop=0
    OnScreenKeyboard.image = load_image('keyboard.png', None, (769, 361));
    OnScreenKeyboard.xpos = (screen_width - 769) / 2 # difference between screen and keyboard widthes / 2 (centrelized)
    OnScreenKeyboard.ypos = (screen_height - 361) / 2 + 100 # (difference between screen and keyboard hight / 2) + 100 to give space for writ-in text
    OnScreenKeyboard.fontsize = 50
    OnScreenKeyboard.font = pygame.font.SysFont('arial',OnScreenKeyboard.fontsize)
    OnScreenKeyboard.texttop = 300
    OnScreenKeyboard.titlefontsize = 36
    OnScreenKeyboard.titlefont = pygame.font.SysFont('arial',OnScreenKeyboard.titlefontsize)
    OnScreenKeyboard.titletop = 150
    OnScreenKeyboard.cursor_width = 20
    OnScreenKeyboard.max_length = 24
    while True:
	keyboard = OnScreenKeyboard('','')
	keyboard.edit()
        code = keyboard.text
        if (code=='AAAA' and action=='cancel'):
            return 'canceled_by_officer'
	elif (code=='AAAA' and action=='cast'):
            return 'cast_by_officer'    
    #
