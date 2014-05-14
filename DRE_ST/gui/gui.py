# Author: John-Paul Gignac
# Modified by Jan Karrman to generate XML with ballotxml() and connect with
# the printing routines.
# This version (EVMCV) improved by Ali Al-Shammari

# Import Modules
import os
import pygame
import re
import sys
import random
import datetime
import shutil
from pygame.locals import *
sys.path.append(os.path.join('OVVM'))
from OVVM_DRE import OVVM_DRE
sys.path.append(os.path.join('..'))
sys.path.append(os.path.join('..'))
from utils.getxml import ballotxml
from utils.qrtools import QR
from utils.onscreenkeyboard import OnScreenKeyboard
from utils.dialogue import Dialogue
from gnosis.xml.objectify import XML_Objectify
from os.path import isfile
from Crypto.Hash import SHA512

#
# get data instances from xml configuration files
coordinates = XML_Objectify('configuration_files/coords.xml').make_instance()
settings = XML_Objectify('configuration_files/EVMCVSettings.xml').make_instance()
#
# Set election information that read from the configuration files
EventID=coordinates.Election.EventID.PCDATA
PollingPlaceID=coordinates.Election.PollingPlaceID.PCDATA
PollingMachineID=coordinates.Election.PollingStationID.PCDATA
BallotID = coordinates.Election.BallotID.PCDATA
ballot_image=coordinates.Election.BallotImage.PCDATA
#
# set the file names for Tick image for both ordered and non ordered contests
if isfile(os.path.join('configuration_files',coordinates.Election.TickImage_Selected.PCDATA)):
	TickImage_Selected=coordinates.Election.TickImage_Selected.PCDATA
else: TickImage_Selected=''
if isfile(os.path.join('configuration_files',coordinates.Election.TickImage_Blank.PCDATA)):
	TickImage_Blank=coordinates.Election.TickImage_Blank.PCDATA
else: TickImage_Blank=''
if isfile(os.path.join('configuration_files',coordinates.Election.TickImageOrdered_Selected.PCDATA)):
	TickImageOrdered_Selected=coordinates.Election.TickImageOrdered_Selected.PCDATA
else: TickImageOrdered_Selected=''
if isfile(os.path.join('configuration_files',coordinates.Election.TickImageOrdered_Blank.PCDATA)):
	TickImageOrdered_Blank=coordinates.Election.TickImageOrdered_Blank.PCDATA
else: TickImageOrdered_Blank=''
#
#Initialize global variables
VoteNumber=0 # ballot number
FVTimeOut=int(settings.FVTimeOut.PCDATA) # FVT : Fleing Voter Time out setting
introduction_time=int(settings.Intro_Time.PCDATA) # time to show the introduction screen before showing the ballot on screen
# screen configuration
dre_pannel_height = 120 # the DRE main pannel, this is the area to be showed up the ballot at which the control buttons are shown
dre_pannel_width=0
screen_height=dre_pannel_height + int(settings.Screen_Height.PCDATA) # screen height
screen_width=int(settings.Screen_Width.PCDATA) # screen width
#
#
#screen = pygame.display.set_mode( (screen_width, screen_height),pygame.BLEND_ADD | pygame.SRCALPHA | pygame.FULLSCREEN,0) # set the pygame global screen
screen = pygame.display.set_mode( (screen_width, screen_height),pygame.SRCALPHA,0) # set the pygame global screen
bar_x=8
bar_y=8
#
layer= pygame.Surface((screen_width, screen_height),pygame.SRCALPHA)
primary_password=settings.Primary_Password.PCDATA
secondary_password=settings.Secondary_Password.PCDATA
#
# Different functions and classes

# Verification Interface Functions
def verification_qr_message(verification_message):
	print 'the message is ........ : ' + verification_message
	#capture the baground image
	background=pygame.image.tostring(screen, 'RGB')
	# generate and show the QR code image
	qr = QR(data=verification_message, pixel_size=2, level='Q', margin_size=1)
	qr.encode(filename='graphics/tmp/message_code.png')
	qrcode = load_image('tmp/message_code.png')#here the path without 'graphics' as it will be set inside the load_image function
	screen.blit( qrcode,(bar_x,bar_y))
	pygame.display.update()
	#show vweification bar, this will force wait time = 2 sec
	Bar_Width= 150
	Bar_Height =15
	BarX=(screen.get_rect().centerx)-(Bar_Width/2)
	BarY=10
	#
	pygame.draw.rect(screen, (0,0,0), pygame.Rect(BarX-1, BarY-1, Bar_Width+1, Bar_Height+1),1)
	screen.blit(control.VerificationMessage, (BarX,BarY+Bar_Height+2) )
	for i in range(11): # 10 steps * 200 ms (2 sec)
		if i==0: continue
		progress = float(i)/10
		pygame.draw.rect(screen, (0,0,255), pygame.Rect(BarX,BarY,Bar_Width*progress,Bar_Height))
		pygame.display.update()
		pygame.time.wait(90)
	# redraw the origional background
	background=pygame.image.fromstring(background, screen.get_size(), 'RGB')
	screen.blit( background,(0,0))
	pygame.display.update()
	pygame.event.clear(MOUSEBUTTONUP)
	return 1
#
#
def password_check(type):
	''' Password check '''
	#return 1
	global screen
	if type =='primary':
		keyboard = OnScreenKeyboard(screen,32,'Please enter primary password: ( demo password= AAAA )','',0)
		keyboard.edit()
		code = keyboard.text
		hash = SHA512.new()
		hash.update(code)
		password=hash.hexdigest()
		if (password==primary_password):
			return 1
		else:
			return 0
	if type =='secondary':
		keyboard = OnScreenKeyboard(screen,32,'Please enter secondary password: ( demo password= BBBB )','',0)
		keyboard.edit()
		code = keyboard.text
		hash = SHA512.new()
		hash.update(code)
		password=hash.hexdigest()
		if (password==secondary_password):
			return 1
		else:
			return 0
#
#
#delete a specific ballot number
def del_ballot_no(number): # generate , store and return unique ballot number
	f = open("rndballots","r+")
	lines = f.readlines()
	f.close()
	f = open("rndballots","w")
	for line in lines:
		if not (str(number)+"\n"==line):
			f.write(line)
	f.close()

#create a unique vote number
def open_vote_cast(): # generate , store and return unique ballot number
	rnd = open("rndballots","r+") # open file to store ballot id
	x=0
	while 1:
		# this loop to, generate random number, check if it used before, store and return number if it is unique,
		# return -2 if it is not possible to find unique number that is not used before
		VoteNumber = random.randint(1000, 9999)
		found=0
		while 1:
			id=rnd.readline()
			if (str(VoteNumber)+"\n"==id):
				rnd.seek(0)
				found=1
				x=x+1
				if ( x>=3): return -2
				break
			if (id==""):
				size = rnd.tell()
				rnd.seek(size)
				rnd.write(str(VoteNumber)+"\n")
				rnd.close()
				break
		if (found !=1): break
	###
	# sort ballots id numbers in the file to hide order
	f = open("rndballots","r+")
	lines = f.readlines()
	lines.sort()
	f.seek(0)
	for line in lines: f.write(line)
	f.close()
	####
	return VoteNumber
#
#
def touch_votes():
	xml_votes_list=[]
	for file in os.listdir('cast_votes'):
		if file.endswith('.xml'):
			xml_votes_list.append(file)
	xml_votes_list.sort()
	# read vote files
	for castvote in xml_votes_list:
		shutil.copy(os.path.join('cast_votes',castvote),os.path.join('cast_votes',castvote+'c'))
		shutil.move(os.path.join('cast_votes',castvote+'c'),os.path.join('cast_votes',castvote))
#
#
def message_bar(text = None, color=(255,255,255)):
	'''Shows single line message in the DRE pannel'''
	global screen
	if text!=None:
		font = pygame.font.SysFont('arial', 20)
		text = font.render(text, 1, (0,0,125), color)
		textpos = text.get_rect()
		textpos.centerx = screen.get_rect().centerx
		textpos[1]=80
		screen.blit(text, textpos)
	else:
		screen.fill((255,255,255),pygame.Rect(150,80, screen_width, dre_pannel_height-80))
	pygame.display.update()#
#
def load_image(name, colorkey=-1, size=None):
	"""
	This function loads any given image
	"""
	# Complete image path (either in configuration_files\ or in graphics\ )
	if (name == ballot_image
	or name== 'ballot_introduction.png'
	or name == TickImage_Selected
	or name == TickImage_Blank
	or name == TickImageOrdered_Selected
	or name == TickImageOrdered_Blank):
		fullname = os.path.join('configuration_files', name)
	else:
		fullname = os.path.join('graphics', name)
	#load ballot image "graphics/name"
	try:
		image = pygame.image.load(fullname).convert()
	except pygame.error, message:
		print 'Cannot load image:', fullname
		raise SystemExit, message
	#if there is no need to resize image
	if size is not None:
		image = pygame.transform.scale( image, size)
	image = image.convert()
	#if colorkey not None then make image transperant
	if colorkey is not None:
		if colorkey is -1:
			colorkey = image.get_at((0,0))
		image.set_colorkey(colorkey, RLEACCEL)
	return image
#
#
def check_minumum_writein_area(x1,y1,x2,y2,maxWrTn,fontSize):
	'''checks if a given number of characters with a specific font size can fits in the x1,y1,x2,y2 area'''
	'''this is useful to checks if Max number of writein characters can fits in the allocated writein space that is defined in the "coords" file'''
	line_distance = 1
	area_width = x2-x1
	area_height = y2-y1
	font = pygame.font.SysFont('arial', fontSize)
	xw,yh = font.size("W")
	if ((xw>=area_width+(line_distance*2)+1) or (yh>=area_height+(line_distance*2)+1)):
		message = 'Error !! writein area are smaller than single character !!'
		print message
		return 0
	no_lines = int((area_height-(line_distance*2))/(yh+line_distance))
	character_per_line = int((area_width)/xw)
	if (maxWrTn <= (no_lines*character_per_line)):
		return 1
	else:
		message = '\nWrtiein configuration error... \nThere is no enough room for the maximun writein for one of the given contests in the defined writein area. \n'
		message+= 'Area coordinates: ('+str(x1)+','+str(y1)+','+str(x2)+','+str(y2)+') \n'
		message+= 'Writein area width : '+str(area_width)+ 'Writein area height : '+str(area_height) +'\n'
		message+= 'Character width : '+str(xw) +'Character height : '+str(yh) +'\n'
		message+= 'Character per line : '+str(character_per_line) +'\n'
		message+= 'Max writein : '+str(maxWrTn) +'\n'
		message+= 'No of lines     '+str(no_lines) +'\n'
		print message
		return 0
#
#
#
# DRE machine core classes
class Candidate:
	def __init__(self, contest, x, y, x1, y1, x2, y2, OptionID, writein=0):
		self.contest = contest
		self.x = x
		self.y = y
		self.activeAreaX1 = x1
		self.activeAreaY1 = y1
		self.activeAreaX2 = x2
		self.activeAreaY2 = y2
		self.writein = writein
		self.selected = 0
		self.OptionID = OptionID
#
	def draw_button(self):
		'''to draw the selection image next to selected option'''
		if self.contest.ordered == 't':
			if self.selected:
				width, height = control.TickImageOrderedSelected.get_size()
				screen.blit(control.TickImageOrderedSelected,(self.x,self.y))
				text_rect = (self.x+(0.180*height),self.y+(0.180*height),10,10) #set the locaton of text rectangle used to print order number
				textobj = control.order_font.render(`self.selected`, 1, (255, 0, 0))
				screen.blit( textobj, text_rect)
				pygame.display.update((self.x,self.y,width, height))
				pygame.display.update(text_rect)

			else:
				width, height = control.TickImageOrderedBlank.get_size()
				screen.blit(control.TickImageOrderedBlank,(self.x,self.y))
				pygame.display.update((self.x,self.y,width, height))
		else:
			width, height = control.TickImageSelected.get_size()
			if self.selected:
				screen.blit( control.TickImageSelected,(self.x, self.y))
			else:
				screen.blit( control.TickImageBlank,(self.x, self.y))
			pygame.display.update((self.x,self.y,width,height))
		if self.writein:
			Ballot.writein_font = pygame.font.SysFont('arial', self.contest.wrtnFontSize)
			text_rect = [self.contest.writeInX1,self.contest.writeInY1, (self.contest.writeInX2-self.contest.writeInX1), (self.contest.writeInY2-self.contest.writeInY1)]
			self.draw_writein(self.contest.ballot.writeins[self.contest.number],text_rect)
#
	def draw_writein(self, text, text_rect):
		'''to draw the writein text for the selected writein option'''
		screen.fill( (255,255,255), text_rect)
		mf = pygame.font.SysFont('arial', self.contest.wrtnFontSize)
		xw,yh = mf.size("W")
		if self.selected:
			character_per_row = int(text_rect[2]/xw)+1
			text_length = len(text)
			num_rows = int(text_length/character_per_row)
			for i in range(num_rows+1):
				textobj = Ballot.writein_font.render( text[(character_per_row*i):(character_per_row*(i+1))], 0, (255, 0, 0))
				screen.blit( textobj, [text_rect[0],text_rect[1]+(yh*i+1),text_rect[2],yh])
			pygame.display.update( text_rect)
#
	def toggle(self, value=1): # select, cancel, change (reset not included)
		'''This funcction to add selection, or cancel previous and add new (if both in the same contest)'''
		'''if the selected candidate in ordered contest, then value will be supported (non defaule) = the order of selected candidate'''
		'''if the selected candidate in non ordered contest, value (default) = 1'''
		if self.selected == value: #it was selected before and now need to be canceled
			self.selected = 0 # change the candidate.selected parameter to be 0
			if int(self.contest.maxVotes)==1:    #for single selection contests
				ballot.codes[self.contest.number] = 0       #remove candidate code from verification module code array
				self.draw_button() # draw check box after togling
				# VM
				message=VM.get_verification_message('cancel',self.OptionID)
				verification_qr_message(message)
				#
			elif int(self.contest.maxVotes)>1 and self.contest.ordered=='f': # for multiple votes non ordered contest
				ballot.codes[self.contest.number].remove(self.OptionID) #remove candidate code from verification module code array
				self.draw_button() # draw check box after togling
				# VM
				message=VM.get_verification_message('cancel',self.OptionID)
				verification_qr_message(message)
		#
		else: #it was not selected before, and now selected
			if  self.contest.maxVotes == 1: #for single selection contests
				for candidate in self.contest.candidates: #check if the was previous candidate already selected in same contest. In this case the older selection should be canceled first
					if candidate != self and candidate.selected == value: # if found a previous selection then cancel, preparing to next step (select new one)
						candidate.selected = 0
						candidate.draw_button() # clear the tick, as drawing acandidate with selected=0 leads to clear it's tick
						# VM
						message=VM.get_verification_message('cancel',candidate.OptionID)
						verification_qr_message(message)
						#
			else: #for multipe selection contests. i.e., maxvotes > 1
				# Make sure there aren't too many selections
				count = 0
				for candidate in self.contest.candidates: # checks how many selected candidates in this contest
					if candidate.selected: count = count + 1
				if count >= self.contest.maxVotes:
					message_bar('You can not select more than ('+str(self.contest.maxVotes)+') options !!', (255,100,100))
					return # stop as selected candidates more than available ones
			#
			self.selected = value # value = 1 in non ordered contest, value = selection order in ordered contest
			if int(self.contest.maxVotes)==1:                            #for single selection contests
				ballot.codes[self.contest.number] = self.OptionID #fill the value of verification module array (candidate code)
			elif int(self.contest.maxVotes)>1 and self.contest.ordered=='f':   # for multiple votes non ordered contest
				ballot.codes[self.contest.number].append(self.OptionID) #append the value of verification module array (selected candidate code)
				ballot.codes[self.contest.number].sort() #sort array
			elif int(self.contest.maxVotes)>1 and self.contest.ordered=='t':       # for multiple votes ordered contest
				ballot.codes[self.contest.number][value-1] = self.OptionID  #fill the value of verification module array (candidate code)
			if (self.selected==value and (not self.writein)):
				self.draw_button() # draw check box after togling
				# VM
				message=VM.get_verification_message('select',self.OptionID)
				verification_qr_message(message)
				#
			if self.writein:
				status= self.contest.edit_writein()
				if status ==1:
					self.draw_button() # draw check box after togling
					writein_ID=self.OptionID[0:6]
					writein_ID=writein_ID+'00'
					self.OptionID=writein_ID
					# VM
					message=VM.get_verification_message('writein',writein_ID,ballot.writeins[self.contest.number])
					verification_qr_message(message)
					#
				if status ==0:
					return 0
				#
			#
		self.draw_button() # draw check box after togling
#
class Contest:
	def __init__(self, ballot, number, minVotes, maxVotes, ordered, resetX1,resetY1,resetX2,resetY2,maxWriteIn,writeInX1,writeInY1,writeInX2,writeInY2,wrtnFontSize):
		self.ballot = ballot
		self.number = number
		self.minVotes = minVotes
		self.maxVotes = maxVotes
		self.ordered = ordered
		self.resetX1 = resetX1
		self.resetY1 = resetY1
		self.resetX2 = resetX2
		self.resetY2 = resetY2
		self.maxWriteIn = maxWriteIn
		self.writeInX1 = writeInX1
		self.writeInY1 = writeInY1
		self.writeInX2 = writeInX2
		self.writeInY2 = writeInY2
		self.wrtnFontSize = wrtnFontSize
		self.candidates = []

	def add_candidate(self, x, y, x1, y1, x2, y2, OptionID):
		self.candidates.append( Candidate( self, x, y, x1, y1, x2, y2, OptionID))
		# The following hack causes the last option to be treated
		# as a write-in whenever there are three or more options.
		if self.maxWriteIn > 0: # if the contest supports writeins, otherwise keep it as default (writein=0)
			if len(self.candidates) > 2:
				self.candidates[-2].writein = 0
				self.candidates[-1].writein = 1

	def reset(self):
		LastResetedCandidateId=0
		for candidate in self.candidates: # read all candidates of this contest
			#candidate.reset() # old code: reset this candidate
			if candidate.selected: #if this candidate is selected
				candidate.selected = 0 # change the status to be deselected
				ballot.codes[candidate.contest.number].remove(candidate.OptionID) # remove the vmvote for this candidate
				ballot.codes[candidate.contest.number].append(0) #append 0 value instead of removed one
				candidate.draw_button() #redraw this candidate check box
				LastResetedCandidateId=candidate.OptionID #get the Id of this candidate to get contest id later
		if (LastResetedCandidateId!=0):
			# VM
			message=VM.get_verification_message('reset',LastResetedCandidateId)
			verification_qr_message(message)
#
	def click(self, x, y):
		if self.ordered == 't': # for ordered contests
			# First: check if there is any reset buttom in any ordered contest has been pressed
			if (x >= int(self.resetX1) and x <= int(self.resetX2) and y >= int(self.resetY1) and y <= int(self.resetY2)):
				print 'reset'
				ballot.contests[self.number].reset()
			# process candidate selection
			for candidate in self.candidates:
				if (x >= candidate.activeAreaX1 and
					x < candidate.activeAreaX2 and
					y >= candidate.activeAreaY1 and
					y < candidate.activeAreaY2):
					if candidate.selected == 0: #if candidate was not selected
						# Make this candidate the next selection
						SelCandOrder = 0
						for cand in self.candidates: # get the order of last selected candidate
							if cand.selected > SelCandOrder: SelCandOrder = cand.selected # check the latest order and put in SelCandOrder
						status=candidate.toggle( SelCandOrder + 1) #toggle selected candidate, the value in toggle = the order of last selected candidate +1
						if status==0: return 0
		else: #for non ordered contests
			for candidate in self.candidates:
				if (x >= candidate.activeAreaX1 and
					x < candidate.activeAreaX2 and
					y >= candidate.activeAreaY1 and
					y < candidate.activeAreaY2):
					status=candidate.toggle() #does not required to have value in toggle
					if status==0: return 0
		return 1
#
	def draw(self):
		for candidate in self.candidates:
			if candidate.selected: candidate.draw_button()
#
	def edit_writein(self):
		global screen
		keyboard = OnScreenKeyboard(screen,self.maxWriteIn,'Write-in for contest number '+str(self.number+1),ballot.writeins[self.number])
		remain_time = keyboard.edit(FVTimeOut)
		if remain_time == 'timeout':
			if int(self.maxVotes)==1:    #for single selection contests
				ballot.codes[self.number] = 0       #remove candidate code from verification module code array
			elif int(self.maxVotes)>1 and self.ordered=='f': # for multiple votes non ordered contest
				ballot.codes[self.number].remove(Candidate.OptionID) #remove candidate code from verification module code array
				#
			now =datetime.datetime.now()
			ballot.timeout(now,now,1)
			return 0
		else:
			ballot.writeins[self.number] = keyboard.text
			self.ballot.draw()
			return 1
#
#
class Ballot:
	def __init__(self):
		if(self.load()==0): sys.exit("error during loading the coords file")
#
	def load( self):
		global dre_pannel_width
		# declare lists
		self.writeins = [] #contains the writein text
		self.codes = [] # contains the selected codes
		self.contests = [] # the set of contest

		for cnt0 in coordinates.Contest:
			self.writeins.append('')
			row=[]
			row2=[]
			for w in range(int(cnt0.MaxVotes.PCDATA)):
				if cnt0.Ordered.PCDATA=='f':
					break
				row.append(0)
				row2.append(0)
			if int(cnt0.MaxVotes.PCDATA)>1:
				self.codes.append(row2)
			else:
				self.codes.append(0)
		#
		# define the structure of date to be read form XML coords file
		headParser = re.compile("([0-9]+) ([0-9]+) ([tf]) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)") # define the structure of contest parameters (minVotes maxVotes ordered (t or f) ReserX1 ResetY1 ReserX2 ResetY2 (reset button coordinates) Maximum writein writeinX1 WriteinY1 writeinX2 WriteinY2 (coordinates of writein area) Write in font size  \n)
		parser = re.compile("([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([A-Z0-9]+)")# define the structure of option parameter (TickX TickY (location of tick image) OptionX1 OptionY1 OptionX2 OptionY2 (coordinates of option active area) Option(candidate)Identifier )
		#load data from coords XML file
		contnum=0
		for cnt in coordinates.Contest:
			#load contest data
			line1 = cnt.MinVotes.PCDATA +" "+ cnt.MaxVotes.PCDATA +" "+ cnt.Ordered.PCDATA +" "+ cnt.Reset.ResetX1.PCDATA+" "+ cnt.Reset.ResetY1.PCDATA+" "+ cnt.Reset.ResetX2.PCDATA+" "+ cnt.Reset.ResetY2.PCDATA+" "+ cnt.WriteIn.MaxWriteIn.PCDATA+" "+ cnt.WriteIn.WriteInX1.PCDATA+" "+ cnt.WriteIn.WriteInY1.PCDATA+" "+ cnt.WriteIn.WriteInX2.PCDATA+" "+ cnt.WriteIn.WriteInY2.PCDATA+" "+cnt.WriteIn.WriteInFontSize.PCDATA
			match = headParser.match(line1) # compare first line structure with headparser style
			if match is None: # the data does not mach with expected structure
				sys.exit("break, there is an error related to the data read from coords.xml file. Please check the structure of stored data. Check line:"+line1)
			(minVotes,maxVotes,ordered,resetX1,resetY1,resetX2,resetY2,maxWriteIn,writeInX1,writeInY1,writeInX2,writeInY2,wrtnFontSize) = match.groups() # move the values of the line to 4 variables
			# Check the rquired area for maximum writeins vs the available predefined area by user (from XML)
			if (check_minumum_writein_area(int(writeInX1),int(writeInY1),int(writeInX2),int(writeInY2),int(maxWriteIn),int(wrtnFontSize)) ==0):
				sys.exit("Bad write-in configuration for contest number ("+ str(contnum)+ ") !!. Exit software...")
			# append parameters to Contest list
			contest = Contest( self, contnum,int(minVotes), int(maxVotes), ordered, int(resetX1)+dre_pannel_width,int(resetY1)+dre_pannel_height,int(resetX2)+dre_pannel_width,int(resetY2)+dre_pannel_height,int(maxWriteIn),int(writeInX1)+dre_pannel_width,int(writeInY1)+dre_pannel_height,int(writeInX2)+dre_pannel_width,int(writeInY2)+dre_pannel_height,int(wrtnFontSize))
			#load the options data for the contest
			#candnum=1
			for option in cnt.Options.Option:
				line2= option.TickX.PCDATA+" "+option.TickY.PCDATA+" "+option.OptionX1.PCDATA+" "+option.OptionY1.PCDATA+" "+option.OptionX2.PCDATA+" "+option.OptionY2.PCDATA+" "+option.CandidateID.PCDATA
				match = parser.match(line2) #match the format of parser
				if match is None: # the data does not mach with expected structure
					sys.exit("break, there is an error related to the data read from coords.xml file. Please check the structure of stored data. Check line:"+line2)
				(x,y,x1,y1,x2,y2,OptionID) = match.groups() # move line values to x,y
				#add option parameter to Contest.Candidate
				contest.add_candidate( int(x)+dre_pannel_width, int(y)+dre_pannel_height, int(x1)+dre_pannel_width,int(y1)+dre_pannel_height,int(x2)+dre_pannel_width,int(y2)+dre_pannel_height, str(OptionID))
			#	candnum+=1
			self.contests.append(contest)
			contnum+=1
		# All data (contest and options)loaded from XML coords to the software
		
	def draw(self):
		screen.fill((255,255,255),screen.get_rect())
		#show ballot image
		screen.blit( control.BallotImage, (dre_pannel_width,dre_pannel_height))
		# Show preview button
		control.ButtonPreviewPos=control.ButtonPreview.get_rect()
		control.ButtonPreviewPos.centerx=screen.get_rect().right
		control.ButtonPreviewPos[1]=10
		control.ButtonPreviewPos[0]= control.ButtonPreviewPos[0] - (control.ButtonPreviewPos[2]/2) - 15
		screen.blit( control.ButtonPreview, control.ButtonPreviewPos)
		pygame.display.update()
		#Draw selected ticks for selected contests
		for contest in self.contests:
			contest.draw()
	def timeout(self,time1,time2,force=0):
		diff = time2-time1
		if (diff.seconds>=FVTimeOut or force==1): #if there is no action for 59 seconds
			action= control.no_response()
			if action=='canceled_by_officer': #either cancel by officer
				# future work .. (label the vote as canceled and support the reason)
				reason='01'
				control.message_screen(control.CastV_message,5,'officercancel',str(VoteNumber).zfill(8),reason)
				return 1
			elif action=='cast_by_officer':  #or cast by officer
				reason="01"
				self.cast("officer")
				control.message_screen(control.CastV_message,5,'officercast',str(VoteNumber).zfill(8),reason)
				return 1
		return 0
	def preview(self,under_vote_contest):
		global layer
		ver=1
		verArea_green=[]
		verArea_red=[]
		# Show Loading message
		loadingpos=control.loading.get_rect()
		loadingpos.centerx=screen.get_rect().centerx
		loadingpos[1]=10
		screen.blit( control.loading, loadingpos)
		print datetime.datetime.now()
		pygame.display.update()
		for item in self.contests:
			under_vote=0
			if under_vote_contest !=[]:
				for under in under_vote_contest:
					if item.number == under.number:
						under_vote=1
						break
			for cand in item.candidates:
				if cand.selected != 0 :
					verArea_green.append([cand.activeAreaX1,cand.activeAreaY1,cand.activeAreaX2,cand.activeAreaY2])
			if under_vote ==1:
				for cand in item.candidates:
					if cand.selected == 0 :
						verArea_red.append([cand.activeAreaX1,cand.activeAreaY1,cand.activeAreaX2,cand.activeAreaY2])
		#show the green and red shades on selection or undervote contests
		for area in verArea_green:
			layer.fill((0,230,0,80),( area[0], area[1], area[2]-area[0], area[3]-area[1] ))
		for area in verArea_red:
			layer.fill((255,0,0,80),( area[0], area[1], area[2]-area[0], area[3]-area[1] ))
		
		#
		screen.blit(layer,(0,0))
		pygame.draw.rect(screen, (255,255,255), (0,0,screen_width,dre_pannel_height))
		#
		# Show cast button
		control.ButtonCastPos=control.ButtonCast.get_rect()
		control.ButtonCastPos.centerx=screen.get_rect().right
		control.ButtonCastPos[1]=10
		control.ButtonCastPos[0]= control.ButtonCastPos[0] - (control.ButtonCastPos[2]/2) - 15
		screen.blit( control.ButtonCast,control.ButtonCastPos)
		#disable cast button if the ballot is undervote
		if under_vote_contest !=[]: # Show cast button only if the vote is not under vote
			message_bar('Under Vote Ballot, You Must Select One or More Option From the Red Shaded Area !!',(255,100,100))
			layer.fill((163,163,163,120),control.ButtonCastPos)
			screen.blit(layer,(0,0))
		else:
			message_bar('Correct Vote, Please Check Your Vote Carefuly Before Cast.',(0,250,0))


		pygame.display.update()
		#
		# Show back button
		control.ButtonBackPos=control.ButtonBack.get_rect()
		control.ButtonBackPos.centerx=screen.get_rect().right
		control.ButtonBackPos[1]=10
		control.ButtonBackPos[0]= control.ButtonCastPos[0] - 15 - (control.ButtonBackPos[2])
		screen.blit( control.ButtonBack,control.ButtonBackPos)
		pygame.display.update()
		#
		pygame.display.flip()
		# VM
		message=VM.get_verification_message('review','00000000')
		verification_qr_message(message)
		#
		now1 = datetime.datetime.now() #read current time
		while ver==1:
			now2 = datetime.datetime.now() #read current time
			if (self.timeout(now1, now2)): return 'timeout'
			for event in pygame.event.get():
				if event.type is MOUSEBUTTONUP:
					now1 = datetime.datetime.now() # reset last action timer
					pos = pygame.mouse.get_pos()
					if (pos[0] >= control.ButtonBackPos[0] and pos[0] < (control.ButtonBackPos[0] + control.ButtonBackPos[2])
					and pos[1] >= control.ButtonBackPos[1] and pos[1] < (control.ButtonBackPos[1] + control.ButtonBackPos[3]) ) : # Back and Edit Vote
						layer.fill((0,0,0,0))
						screen.blit(layer,(0,0))
						return 'back'
						#ver=0
					if (pos[0] >= control.ButtonCastPos[0] and pos[0] < (control.ButtonCastPos[0]+control.ButtonCastPos[2])
					and pos[1] >= control.ButtonCastPos[1] and pos[1] <= (control.ButtonCastPos[1] + control.ButtonCastPos[3])
					and under_vote_contest ==[]) : # cast vote
						layer.fill((0,0,0,0))
						screen.blit(layer,(0,0))
						return 'cast'
					else: continue
	def vote(self):
		self.draw() # daraw main ballot
		now1 = datetime.datetime.now() # get time at startup action
		while 1: # voting loop
			now2 = datetime.datetime.now() #read current time
			if (self.timeout(now1, now2)): return
				#
			pygame.time.wait(200) # wait for 0.002 sec to read action
			for event in pygame.event.get():
				#broadc('message')
				if event.type is KEYDOWN:
					if event.key == K_ESCAPE: # exit if there is an escape key
						sys.exit(0)
				elif event.type is MOUSEBUTTONUP:
					message_bar()
					now1 = datetime.datetime.now() # reset last action timer
					pos = pygame.mouse.get_pos()
					for contest in self.contests:
						# check if there is any active click in any contest
						status=contest.click( pos[0], pos[1])
						if status==0: return 0
						else: now1 = datetime.datetime.now() # reset last action timer
					#
					if (pos[0] >= control.ButtonPreviewPos[0] and pos[0] <= (control.ButtonPreviewPos[0] + control.ButtonPreviewPos[2])
					and pos[1] >= control.ButtonPreviewPos[1] and pos[1] <= (control.ButtonPreviewPos[1] + control.ButtonPreviewPos[3]) ) : # Preview
						#
						under_vote_contest=self.check_under_vote()
						prev = self.preview(under_vote_contest)
						if prev=='back':
							self.draw()
							now1 = datetime.datetime.now() # reset last action time
						if prev=='cast':
							self.cast("voter")
							control.message_screen(control.CastV_message,5,'votercast',str(VoteNumber).zfill(8))
							return
						if prev=='timeout':
							return
						#
	def check_under_vote(self):
		under_vote_contest=[]
		for contest in self.contests:
			if contest.maxVotes==1:
				if self.codes[contest.number] < contest.minVotes:
					under_vote_contest.append(contest)
			if contest.maxVotes>1 and contest.ordered=='f':
				if len(self.codes[contest.number])< contest.minVotes:
					under_vote_contest.append(contest)
			if contest.maxVotes>1 and contest.ordered=='t':
				if (len(self.codes[contest.number])-self.codes[contest.number].count(0))< contest.minVotes:
					under_vote_contest.append(contest)
		if under_vote_contest==[]:
			return []
		else:
			return under_vote_contest


	def cast(self,actor):
		"""cast the vote in xml file"""
		xml = ballotxml(EventID,PollingPlaceID,PollingMachineID, BallotID, VoteNumber, ballot.codes,ballot.writeins)
		xmlfile = re.sub(' ', '_', "-".join(["v", str(EventID),str(PollingPlaceID),str(PollingMachineID), str(VoteNumber)]) + ".xml")
		file = open('cast_votes/'+xmlfile, 'w')
		file.write(xml)
		file.close()
		touch_votes()
		
class Control_Machine:

	def __init__(self):
		#load ballot image
		self.BallotImage = load_image(ballot_image,None) #load ballot image
		self.IntroImage = load_image('ballot_introduction.png', None) #load ballot introduction image
		#loads tick images for ordered and non ordered contests.
		if TickImage_Selected !='': self.TickImageSelected = load_image(TickImage_Selected,None)
		if TickImage_Blank !='': self.TickImageBlank = load_image(TickImage_Blank,None)
		if TickImageOrdered_Selected !='': self.TickImageOrderedSelected = load_image(TickImageOrdered_Selected,None)
		if TickImageOrdered_Blank !='': self.TickImageOrderedBlank = load_image(TickImageOrdered_Blank,None)
		#load different messages images
		self.MachineExit_message = load_image('machine_exit_message.png', None)#load load election message image
		self.CastV_message= load_image('cast_voter_message.png', None)#load cast vote message image
		self.CastO_message= load_image('cast_officer_message.png', None)#load cast by officer message image
		self.CancelO_message= load_image('cancel_message.png', None)#load cancel by officer message image
		self.no_responce_message= load_image('no_responce_message.png', None)#load no responce message image
		self.verification_module_connect=load_image('VM_connect.png', None) #load the VM connect message
		self.loading= load_image('loading.png', None)#load no responce message image
		self.VerificationMessage= load_image('verification_message.png') # load the verification message that will appears under the loading bar
		#load buttons images
		self.ButtonPreview = load_image('previewbtn.png')
		self.ButtonCast = load_image('castbtn.png')
		self.ButtonBack = load_image('backbtn.png')
		self.ButtonOpen = load_image('openbtn.png')
		self.ButtonActive = load_image('activebtn.png')
		self.ButtonClose = load_image('closebtn.png')
		self.ButtonCastO = load_image('castobtn.png')
		self.ButtonCancelO = load_image('cancelobtn.png')
		self.ButtonExitMachine = load_image('exitbtn.png')
		#VM Control Buttons
		self.ButtonShowReport = load_image('reportbtn.png')
		self.ButtonCalibrate = load_image('calibratebtn.png')
		self.ButtonMVControl = load_image('vmcontrolbtn.png')
		self.ButtonForceCast = load_image('forcecastbtn.png')
		self.ButtonForceCancel = load_image('forcecancelbtn.png')
		self.ButtonBack2 = load_image('back2btn.png')
		self.Calibrate = load_image('calibrate.png')
		#load logo image
		self.Logo = load_image('logo1.png')
		self.dg = Dialogue ()

#
	def set_video_mode(self):
		global screen
		#
		self.screen_size = [screen_width,screen_height] #set screen size based on the values read from EVMCVSetting.xml
		#screen = pygame.display.set_mode([0,0],pygame.BLEND_ADD | pygame.SRCALPHA | pygame.FULLSCREEN,0)#set main window mode
		pygame.display.set_caption('EVMCV')#set window caption
		screen.fill((255,255,255))#set background to white
		
		
	def setup_everything(self):
		global dre_pannel_width #set global when you want to let this function changes the value of this global variable
		#initialize pygame
		self.set_video_mode()
		pygame.init()
		#calculate the size of ballot image
		BallotImageSize = self.BallotImage.get_size()
		self.BallotImage_size = list(BallotImageSize)
		dre_pannel_width = (screen_width - self.BallotImage_size[0])/2
		#self.BallotImage_size[0] = self.BallotImage_size[0] + dre_pannel_width # this to add to voting pannel size
		#self.BallotImage_size[1] = self.BallotImage_size[1] + dre_pannel_height # this to add to voting pannel size
		#
		#calculate the size of control buttons
		#self.ButtonPreviewPos = self.ButtonPreview.get_rect()
		#self.ButtonCastPos = self.ButtonPreview.get_rect()
		#self.ButtonBackPos = self.ButtonPreview.get_rect()
		#
		# Set the size of the text to be inside Tick Image for ordered contest
		if TickImageOrdered_Selected !='':
			order_box_text_size = control.TickImageOrderedSelected.get_size()
			margin = (0.15*order_box_text_size[1])
			# calculate pixile/size ration
			mf = pygame.font.SysFont('arial', 20)
			xw,yh = mf.size("0")
			ratio = yh/20
			order_font_size = int ((order_box_text_size[1] - (margin*2))/ratio)
			if (order_font_size < 2): order_font_size =2
			self.order_font = pygame.font.SysFont('arial', order_font_size)

	def open_poll(self):
		""" First Screen: Open poll screen"""
		screen.fill((255,255,255),screen.get_rect())
		#global screen
		# Show Logo
		logopos=self.Logo.get_rect()
		logopos.centerx=screen.get_rect().centerx
		logopos[1]=100
		screen.blit( self.Logo, logopos)
		# Show open poll button
		ButtonOpen_position=self.ButtonOpen.get_rect()
		ButtonOpen_position.centerx=screen.get_rect().centerx
		ButtonOpen_position[1]=logopos[1]+logopos[3]+100
		screen.blit( self.ButtonOpen, ButtonOpen_position)
		# Show VM Calibrate button
		ButtonCalibrate_position=self.ButtonCalibrate.get_rect()
		ButtonCalibrate_position.centerx=screen.get_rect().centerx
		ButtonCalibrate_position[1]=ButtonOpen_position[1]+ButtonOpen_position[3]+ 30
		screen.blit( self.ButtonCalibrate, ButtonCalibrate_position)
		pygame.display.flip()
		while 1:
			pygame.time.wait(200)
			for event in pygame.event.get():
				if event.type is MOUSEBUTTONUP:
					pos = pygame.mouse.get_pos()
					if( pos[0] >= ButtonOpen_position[0] and pos[0] < (ButtonOpen_position[0]+ButtonOpen_position[2])
					and pos[1] >= ButtonOpen_position[1] and pos[1] < (ButtonOpen_position[1]+ButtonOpen_position[3])):
						while 1:
							#ask for primary password
							Auth=password_check('primary')
							if (Auth==1):
								screen.fill((255,255,255)) #clear screen
								# Show VM connect message
								message_image_position=self.verification_module_connect.get_rect()
								message_image_position.center=screen.get_rect().center
								screen.blit( self.verification_module_connect, message_image_position)
								pygame.display.flip()
								# get VMSetting_ID
								VMSettingID=VM.get_VM_Setting_ID(EventID,PollingPlaceID,PollingMachineID)
								# VM
								message=VM.get_verification_message('connect',VMSettingID)
								verification_qr_message(message) #send the VM message
								#
								res = self.dg.responce(screen, 'VM Connection Confirmation !','Does the VM recieved the open poll message ?')
								if res:
									return 1
								if not res:
									if int(VM.Sequence)!=0:
										VM.Sequence=VM.Sequence-1 #reduce the sequence as VM does not recieved the last message
									else:
										VM.Sequence=15
									return 0
							else:
								res = self.dg.responce(screen, 'Wrong Password','Would you like to try again ?')
								if res:
									continue
								if not res:
									break
						return 0
					if( pos[0] >= ButtonCalibrate_position[0] and pos[0] < (ButtonCalibrate_position[0]+ButtonCalibrate_position[2])
					and pos[1] >= ButtonCalibrate_position[1] and pos[1] < (ButtonCalibrate_position[1]+ButtonCalibrate_position[3])):
						# show calibration barcode
						message=VM.get_verification_message('calibrate','00000000','DRE is Connected!')
						verification_qr_message(message)
					


	#VM
	def vm_control(self):
		""" VM Control Screen"""
		#capture the baground image
		background=pygame.image.tostring(screen, 'RGB')
		screen.fill((255,255,255))
		# Show Logo
		logopos=self.Logo.get_rect()
		logopos.centerx=screen.get_rect().centerx
		logopos[1]=100
		screen.blit( self.Logo, logopos)
		# Show Force Cast button
		ButtonForceCast_position=self.ButtonForceCast.get_rect()
		ButtonForceCast_position.centerx=screen.get_rect().centerx
		ButtonForceCast_position[1]=logopos[1]+logopos[3]+100
		screen.blit( self.ButtonForceCast, ButtonForceCast_position)
		# Show Force Cancel button
		ButtonForceCancel_position=self.ButtonForceCancel.get_rect()
		ButtonForceCancel_position.centerx=screen.get_rect().centerx
		ButtonForceCancel_position[1]=ButtonForceCast_position[1]+ButtonForceCast_position[3]+ 30
		screen.blit( self.ButtonForceCancel, ButtonForceCancel_position)
		# Show VM Calibrate button
		ButtonCalibrate_position=self.ButtonCalibrate.get_rect()
		ButtonCalibrate_position.centerx=screen.get_rect().centerx
		ButtonCalibrate_position[1]=ButtonForceCancel_position[1]+ButtonForceCancel_position[3]+ 30
		screen.blit( self.ButtonCalibrate, ButtonCalibrate_position)
		# Show VM Calibrate button
		ButtonBack2_position=self.ButtonBack2.get_rect()
		ButtonBack2_position.centerx=screen.get_rect().centerx
		ButtonBack2_position[1]=ButtonCalibrate_position[1]+ButtonCalibrate_position[3]+ 30
		screen.blit( self.ButtonBack2, ButtonBack2_position)
		pygame.display.flip()
		while 1:
			pygame.time.wait(200)
			for event in pygame.event.get():
				if event.type is MOUSEBUTTONUP:
					pos = pygame.mouse.get_pos()
					if( pos[0] >= ButtonForceCast_position[0] and pos[0] < (ButtonForceCast_position[0]+ButtonForceCast_position[2])
					and pos[1] >= ButtonForceCast_position[1] and pos[1] < (ButtonForceCast_position[1]+ButtonForceCast_position[3])):
						while 1:
							Auth=password_check('secondary')
							if (Auth==1):# force cast by officer
								message=VM.get_verification_message('officercast','00000000','02')
								verification_qr_message(message)
								print VM.Sequence
								#
								res = self.dg.responce(screen, 'Cast by officer Confirmation !','Does the VM recieved the force cast message ?')
								if res:
									pygame.display.update()
									break
								if not res:
									if int(VM.Sequence)!=0:
										VM.Sequence=VM.Sequence-1 #reduce the sequence as VM does not recieved the last message
									else:
										VM.Sequence=15
									res = self.dg.responce(screen, 'Bad Connection','Would you like to try again ?')
									if res:
										continue
									if not res:
										pygame.display.update()
										break
							else:
								res = self.dg.responce(screen, 'Wrong Password','Would you like to try again ?')
								if res:
									continue
								if not res:
									pygame.display.update()
									break
						#
					if( pos[0] >= ButtonForceCancel_position[0] and pos[0] < (ButtonForceCancel_position[0]+ButtonForceCancel_position[2])
					and pos[1] >= ButtonForceCancel_position[1] and pos[1] < (ButtonForceCancel_position[1]+ButtonForceCancel_position[3])):
						# force cancel by officer
						while 1:
							Auth=password_check('secondary')
							if (Auth==1):# force cast by officer
								message=VM.get_verification_message('officercancel','00000000','02')
								verification_qr_message(message)
								res = self.dg.responce(screen, 'Cast by officer Confirmation !','Does the VM recieved the force cast message ?')
								if res:
									pygame.display.update()
									break
								if not res:
									if int(VM.Sequence)!=0:
										VM.Sequence=VM.Sequence-1 #reduce the sequence as VM does not recieved the last message
									else:
										VM.Sequence=15
									res = self.dg.responce(screen, 'Bad Connection','Would you like to try again ?')
									if res:
										continue
									if not res:
										pygame.display.update()
										break
							else:
								if int(VM.Sequence)!=0:
									VM.Sequence=VM.Sequence-1 #reduce the sequence as VM does not recieved the last message
								else:
									VM.Sequence=15
								res = self.dg.responce(screen, 'Wrong Password','Would you like to try again ?')
								if res:
									continue
								if not res:
									pygame.display.update()
									break
					if( pos[0] >= ButtonCalibrate_position[0] and pos[0] < (ButtonCalibrate_position[0]+ButtonCalibrate_position[2])
					and pos[1] >= ButtonCalibrate_position[1] and pos[1] < (ButtonCalibrate_position[1]+ButtonCalibrate_position[3])):
						# show calibration barcode
						message=VM.get_verification_message('calibrate','00000000','DRE is Connected!')
						verification_qr_message(message)
						
						#
					if( pos[0] >= ButtonBack2_position[0] and pos[0] < (ButtonBack2_position[0]+ButtonBack2_position[2])
					and pos[1] >= ButtonBack2_position[1] and pos[1] < (ButtonBack2_position[1]+ButtonBack2_position[3])):
						# redraw the origional background
						background=pygame.image.fromstring(background, screen.get_size(), 'RGB')
						screen.blit( background,(0,0))
						pygame.display.update()
						pygame.event.clear(MOUSEBUTTONUP)
						return 0



	def control_election(self):
		"""
		Second Screen: Control election, either activate vote (Go for introduction_screen()) or close poll (go for close_poll())
		"""
		screen.fill((255,255,255),screen.get_rect())
		# Show Logo
		logopos=self.Logo.get_rect()
		logopos.centerx=screen.get_rect().centerx
		logopos[1]=100
		screen.blit( self.Logo, logopos)
		# Show Activate vote button
		ButtonActive_position=self.ButtonActive.get_rect()
		ButtonActive_position.centerx=screen.get_rect().centerx
		ButtonActive_position[1]=logopos[1]+logopos[3]+100
		screen.blit( self.ButtonActive, ButtonActive_position)
		#
		# Show close poll button
		ButtonClose_position=self.ButtonClose.get_rect()
		ButtonClose_position.centerx=screen.get_rect().centerx
		ButtonClose_position[1]=ButtonActive_position[1]+ButtonActive_position[3]+ 30
		screen.blit( self.ButtonClose, ButtonClose_position)
		# Show VM Control  button
		ButtonMVControl_position=self.ButtonMVControl.get_rect()
		ButtonMVControl_position.centerx=screen.get_rect().centerx
		ButtonMVControl_position[1]=ButtonClose_position[1]+ButtonClose_position[3]+ 30
		screen.blit( self.ButtonMVControl, ButtonMVControl_position)
		#
		pygame.display.update()
		while 1:
			pygame.time.wait(200)
			for event in pygame.event.get():
				if event.type is MOUSEBUTTONUP:
					pos = pygame.mouse.get_pos()
					if( pos[0] >= ButtonActive_position[0] and pos[0] < (ButtonActive_position[0]+ButtonActive_position[2])
						and pos[1] >= ButtonActive_position[1] and pos[1] < (ButtonActive_position[1]+ButtonActive_position[3])):
						bn= open_vote_cast()
						if (bn==-2):
							return bn
						while 1:
							#ask for primary password
							Auth=password_check('secondary')
							if (Auth==1):
								screen.fill((255,255,255)) #clear screen
								# Show VM connect message
								message_image_position=self.verification_module_connect.get_rect()
								message_image_position.center=screen.get_rect().center
								screen.blit( self.verification_module_connect, message_image_position)
								pygame.display.flip()
								# VM
								message=VM.get_verification_message('activate',str(bn).zfill(8))
								verification_qr_message(message)
								#
								res = self.dg.responce(screen, 'VM Open Cast Confirmation !','Does the VM recieved the open cast message ?')
								if res:
									return bn
								if not res:
									if int(VM.Sequence)!=0:
										VM.Sequence=VM.Sequence-1 #reduce the sequence as VM does not recieved the last message
									else:
										VM.Sequence=15
									res = self.dg.responce(screen, 'Bad Connection','Would you like to try again ?')
									if res:
										continue
									if not res:
										del_ballot_no(str(bn))
										break
							else:
								res = self.dg.responce(screen, 'Wrong Password','Would you like to try again ?')
								if res:
									continue
								if not res:
									del_ballot_no(str(bn))
									break
						return 0

					#
					if( pos[0] >= ButtonClose_position[0] and pos[0] < (ButtonClose_position[0]+ButtonClose_position[2])
						and pos[1] >= ButtonClose_position[1] and pos[1] < (ButtonClose_position[1]+ButtonClose_position[3])):
							#ask for primary password
							while 1:
								Auth=password_check('primary')
								if (Auth==1):
									screen.fill((255,255,255)) #clear screen
									# Show VM connect message
									message_image_position=self.verification_module_connect.get_rect()
									message_image_position.center=screen.get_rect().center
									screen.blit( self.verification_module_connect, message_image_position)
									pygame.display.flip()

									#Close the poll
									VMSettingID=VM.get_VM_Setting_ID(EventID,PollingPlaceID,PollingMachineID)
									# VM
									message=VM.get_verification_message('close',VMSettingID)
									verification_qr_message(message)
									#
									res = self.dg.responce(screen, 'VM Close Poll Confirmation !','Does the VM recieved the close poll message ?')
									if res:
										return -1
									if not res:
										if int(VM.Sequence)!=0:
											VM.Sequence=VM.Sequence-1 #reduce the sequence as VM does not recieved the last message
										else:
											VM.Sequence=15
										res = self.dg.responce(screen, 'Bad Connection','Would you like to try again ?')
										if res:
											continue
										if not res:
											break
								else:
									res = self.dg.responce(screen, 'Wrong Password','Would you like to try again ?')
									if res:
										continue
									if not res:
										break
							return 0
					if( pos[0] >= ButtonMVControl_position[0] and pos[0] < (ButtonMVControl_position[0]+ButtonMVControl_position[2])
					and pos[1] >= ButtonMVControl_position[1] and pos[1] < (ButtonMVControl_position[1]+ButtonMVControl_position[3])):
						# call VM Control
						self.vm_control()


	def close_poll(self):
		#global screen
		screen.fill((255,255,255),screen.get_rect())
		# Show Logo
		logopos=self.Logo.get_rect()
		logopos.centerx=screen.get_rect().centerx
		logopos[1]=100
		screen.blit( self.Logo, logopos)
		# Show Exit Machine poll button
		ButtonExitMachine_position=self.ButtonExitMachine.get_rect()
		ButtonExitMachine_position.centerx=screen.get_rect().centerx
		ButtonExitMachine_position[1]=logopos[1]+logopos[3]+ 100
		screen.blit( self.ButtonExitMachine, ButtonExitMachine_position)
		# Show Show Report vote button
		ButtonShowReport_position=self.ButtonShowReport.get_rect()
		ButtonShowReport_position.centerx=screen.get_rect().centerx
		ButtonShowReport_position[1]=ButtonExitMachine_position[1]+ButtonExitMachine_position[3]+30
		screen.blit( self.ButtonShowReport, ButtonShowReport_position)
		#
		pygame.display.update()
		while 1:
			pygame.time.wait(200)
			for event in pygame.event.get():
				if event.type is MOUSEBUTTONUP:
					pos = pygame.mouse.get_pos()
					if( pos[0] >= ButtonShowReport_position[0] and pos[0] < (ButtonShowReport_position[0]+ButtonShowReport_position[2])
						and pos[1] >= ButtonShowReport_position[1] and pos[1] < (ButtonShowReport_position[1]+ButtonShowReport_position[3])):
						while 1:
								Auth=password_check('secondary')
								if (Auth==1):
									#Close the poll
									VMSettingID=VM.get_VM_Setting_ID(EventID,PollingPlaceID,PollingMachineID)
									# VM
									message=VM.get_verification_message('report',VMSettingID)
									verification_qr_message(message)
									#
									break
								else:
									res = self.dg.responce(screen, 'Wrong Password','Would you like to try again ?')
									if res:
										continue
									if not res:
										pygame.display.update()
										break
					#
					if( pos[0] >= ButtonExitMachine_position[0] and pos[0] < (ButtonExitMachine_position[0]+ButtonExitMachine_position[2])
						and pos[1] >= ButtonExitMachine_position[1] and pos[1] < (ButtonExitMachine_position[1]+ButtonExitMachine_position[3])):
							while 1:
								Auth=password_check('primary')
								if (Auth==1):
									#Exist the machine
									self.close_machine()
									return 0
								else:
									res = self.dg.responce(screen, 'Wrong Password','Would you like to try again ?')
									if res:
										continue
									if not res:
										pygame.display.update()
										break
							
	#introduction screen before ballot
	def introduction_screen(self):
		#introduction screen
		screen.fill((255,255,255),screen.get_rect())
		# Show Logo
		IntroImagePos=self.IntroImage.get_rect()
		IntroImagePos.center=screen.get_rect().center
		screen.blit( self.IntroImage, IntroImagePos)
		#
		pygame.display.update()
		now1 = datetime.datetime.now()
		while 1:
			now2 = datetime.datetime.now()
			diff = now2-now1
			if (diff.seconds==introduction_time):
				return 
			pygame.time.wait(200)
			for event in pygame.event.get():
				if event.type is MOUSEBUTTONUP:
					return 
	#this functions shows an image mesaage in screen
	def message_screen(self,message_image,message_period,command=None,parameter=None,reason=None):
		screen.fill((255,255,255),screen.get_rect())
		# Show Logo
		logopos=self.Logo.get_rect()
		logopos.centerx=screen.get_rect().centerx
		logopos[1]=100
		screen.blit( self.Logo, logopos)
		# Show Logo
		message_image_position=message_image.get_rect()
		message_image_position.centerx=screen.get_rect().centerx
		message_image_position[1]=logopos[1]+logopos[3]+100
		screen.blit( message_image, message_image_position)
		#
		pygame.display.update()
		if (command!=None):
			# VM
			message=VM.get_verification_message(command,parameter,reason)
			verification_qr_message(message)
			#
		now1 = datetime.datetime.now()
		while 1:
			now2 = datetime.datetime.now()
			diff = now2-now1
			if (diff.seconds>=message_period):
				return (message_image_position[1]+message_image_position[3])
			pygame.time.wait(20)
			for event in pygame.event.get():
				if event.type is MOUSEBUTTONUP:
					pygame.event.clear(MOUSEBUTTONUP)
					return (message_image_position[1]+message_image_position[3])
		

	def close_machine(self):
		#close machine screen
		self.message_screen(self.MachineExit_message,5)
		return 0
	def no_response(self):
		ref= self.message_screen(self.no_responce_message,0)
		# Show Show Report vote button
		ButtonCastO_position=self.ButtonCastO.get_rect()
		ButtonCastO_position.centerx=screen.get_rect().centerx
		ButtonCastO_position[1]=ref + 30
		screen.blit( self.ButtonCastO, ButtonCastO_position)
		# Show Show Report vote button
		ButtonCancelO_position=self.ButtonCancelO.get_rect()
		ButtonCancelO_position.centerx=screen.get_rect().centerx
		ButtonCancelO_position[1]=ButtonCastO_position[1] + ButtonCastO_position[3] + 50
		screen.blit( self.ButtonCancelO, ButtonCancelO_position)
		#
		pygame.display.update()
		loop=1
		while loop==1:
			pygame.time.wait(200)
			for event in pygame.event.get():
				if event.type is MOUSEBUTTONUP:
					pos = pygame.mouse.get_pos()
					if (pos[0] >= ButtonCastO_position[0] and pos[0] <= ButtonCastO_position[0]+ButtonCastO_position[2]
						and pos[1] >= ButtonCastO_position[1] and pos[1] <= ButtonCastO_position[1]+ButtonCastO_position[3]):
						action='cast'
						loop=0
					if (pos[0] >= ButtonCancelO_position[0] and pos[0] <= ButtonCancelO_position[0]+ButtonCancelO_position[2]
						and pos[1] >= ButtonCancelO_position[1] and pos[1] <= ButtonCancelO_position[1]+ButtonCancelO_position[3]):
						action='cancel'
						loop=0
		# Password
		Auth=password_check('primary')
		if (Auth==1 and action=='cancel'):
			return 'canceled_by_officer'
		elif (Auth==1 and action=='cast'):
			return 'cast_by_officer'

	
#main code

VM=OVVM_DRE()
control = Control_Machine()          #initialize open poll screen
control.setup_everything()
openpoll= 0
while (not openpoll): openpoll=control.open_poll()   # show open poll screen and return 1 if "Open Poll" selected

while (openpoll==1):
	VoteNumber = control.control_election() #show control screen, generate and return ballot number if "Activate Vote" selected, return -1 if "Close Poll" selected.
	if (VoteNumber!=0 and VoteNumber!=-1 and VoteNumber!=-2):
		control.introduction_screen() # show the introduction screen (page at which some introductions or instructions shown to voter before voting)
		ballot = Ballot()             #initialize ballot by loading the "coords" file. (see documentation to learn more about the file structure)
		ballot.vote()                 # show ballot and cast vote
		VoteNumber=0               # reset ballot number
	if (VoteNumber== -1):          #
		control.close_poll()  # close the election (show close election screen)
		pygame.quit()
		sys.exit(0)
	if (VoteNumber== -2):          #
		#exit software if there are no available ballot numbers
		print "rndballots file filled with reach maximum number of allowed ballot numbers"
		sys.exit(0)
