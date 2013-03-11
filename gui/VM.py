#!/usr/bin/python

# Author: John-Paul Gignac

# Modified by Jan Karrman to generate XML with ballotxml() and connect with
# the printing routines.

# Import Modules
import os, pygame, re, sys, string, random, datetime
from pygame.locals import *
sys.path.append(os.path.join('..', '..'))
from evm2003.utils.getxml import ballotxml
import socket
#
HOST = '192.168.39.181'                 # Symbolic name meaning the local host
#HOST='<broadcast>'
PORT = 50007              # Arbitrary non-privileged port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# DRE information, this what will be inseted to vote
country = ""
state = ""
county = ""
ballot_number = ""
precinct = ""
date = ""
serial = ""

# screen configuration
screen_width = 1280
screen_height = 1024
button_radius = 8

# Functions to create our resources
def load_image(name, colorkey=-1, size=None):
# Complete file path
	fullname = os.path.join('vm_graphics', name)
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




	

def setup_everything():
	# Initialize the game module
	pygame.init()

	global screen

	screen = pygame.display.set_mode( (screen_width, screen_height),
		0)
	pygame.display.set_caption('VM: ICT4G Version')

	

def run_vm():
	global screen

	main_image = load_image('vm_main.png', None)
	screen.blit( main_image, (0,0))
	pygame.display.update()
	s.bind((HOST, PORT))
	
	while 1:
		pygame.time.wait(20)
		s.listen(1)
		data = conn.recv(1024)
		if data:
			textobj = Ballot.writein_font.render( 'event', 0, (255, 0, 0))
			screen.blit( textobj, (100,100))
			pygame.display.update( (100,100))
		for event in pygame.event.get():
			if event.type is KEYDOWN:
				if event.key == K_ESCAPE: sys.exit()
				return 0

setup_everything()
run_vm()

