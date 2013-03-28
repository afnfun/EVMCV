#!/usr/bin/python

# Author: John-Paul Gignac

# Modified by Jan Karrman to generate XML with ballotxml() and connect with
# the printing routines.
# This version improved by Ali Al-Shammari

# Import Modules
import os
import pygame
import re
import sys
import string
import random
import datetime
#import gnosis
from pygame.locals import *
sys.path.append(os.path.join('..'))
#from evm2003.Print.PaperBallot import PaperBallot
from utils.getxml import ballotxml
#from evm2003.utils.verification import verify
from utils.no_response import no_response
from utils.onscreenkeyboard import OnScreenKeyboard
from gnosis.xml.objectify import XML_Objectify

py_obj = XML_Objectify('coords.xml').make_instance()
settings = XML_Objectify('EVMProSettings.xml').make_instance()


# DRE information, this what will be inseted to vote
VoteNumber=0
ElectionID=py_obj.Election.ElectionID.PCDATA
PollingPlaceID=py_obj.Election.PollingPlaceID.PCDATA
PollingMachineID=py_obj.Election.PollingStationID.PCDATA
BallotID = py_obj.Election.BallotID.PCDATA
#printer output file
psfile = 'ballot.ps'
# FVT : Fleing Voter Time out setting
FVTimeOut=int(settings.FVTimeOut.PCDATA)

# screen configuration
screen_width = 1280
screen_height = 1024
#button_radius = 8

# Functions to create our resources

def blit_alpha(target, source, location, opacity):
	x = location[0]
	y = location[1]
	temp = pygame.Surface((source.get_width(), source.get_height())).convert()
	temp.blit(target, (-x, -y))
	temp.blit(source, (0, 0))
	temp.set_alpha(opacity)
	target.blit(temp, location)

def load_image(name, colorkey=-1, size=None):
# Complete file path
	fullname = os.path.join('graphics', name)
#load ballot image "graphics/name"
	try:
		image = pygame.image.load(fullname) # future work, generate image dynamically from xml file
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

def xml_escape( str):
	str = string.replace( str, "&", "&amp;")
	str = string.replace( str, "<", "&lt;")
	str = string.replace( str, ">", "&gt;")
	str = string.replace( str, '"', "&quot;")
	str = string.replace( str, "'", "&apos;")
	return str

#check if Max number of write-ins are more than it's allocated space in "coords" file
def check_minumum_writein_area(x1,y1,x2,y2,maxWrTn, fontSize):
	line_distance = 1
	area_width = x2-x1
	area_height = y2-y1
	font = pygame.font.SysFont('arial', fontSize)
	xw,yh = font.size("0")
	if ((xw>=area_width+(line_distance*2)+1) or (yh>=area_height+(line_distance*2)+1)):
		return 0
	no_lines = int((area_height-(line_distance*2))/(yh+line_distance))
	character_per_line = int((area_width-(line_distance*2))/xw)
	#print "max write in: " + str(maxWrTn) + "maxAvailable : " + str(no_lines*character_per_line)
	if (maxWrTn<=(no_lines*character_per_line)):
		return 1
	else:
		return 0


class Candidate:
	def __init__(self, contest, x, y, x1, y1, x2, y2, number, VmCandidateId, writein=0):
		self.contest = contest
		self.x = x
		self.y = y
		#self.r = r
		self.activeAreaX1 = x1
		self.activeAreaY1 = y1
		self.activeAreaX2 = x2
		self.activeAreaY2 = y2
		self.number = number
		self.writein = writein
		self.selected = 0
		self.VmCandidateId = VmCandidateId
		

	def draw_button(self):
		if self.contest.ordered == 't':
			#for i in range(self.contest.maxVotes):
			if self.selected:
				width, height = Ballot.box_selected.get_size()
				screen.blit(Ballot.box_selected,(self.x,self.y))
				text_rect = (self.x+(0.180*height),self.y+(0.180*height),10,10) #set the locaton of text rectangle used to print order number
				textobj = Ballot.order_font.render(`self.selected`, 1, (255, 0, 0))
				screen.blit( textobj, text_rect)
				pygame.display.update((self.x,self.y,width, height))
				pygame.display.update(text_rect)

			else:
				width, height = Ballot.box_deselected.get_size()
				screen.blit(Ballot.box_deselected,(self.x,self.y))
				pygame.display.update((self.x,self.y,width, height))

			#text_rect = [self.x+20,self.y,130,16]
		else:
			width, height = Ballot.button_selected.get_size()
			if self.selected:
				screen.blit( Ballot.button_selected,(self.x, self.y))
			else:
				screen.blit( Ballot.button_deselected,(self.x, self.y))
			pygame.display.update((self.x,self.y,width,height))

		if self.writein:
			Ballot.writein_font = pygame.font.SysFont('arial', self.contest.wrtnFontSize)
			text_rect = [self.contest.writeInX1,self.contest.writeInY1, (self.contest.writeInX2-self.contest.writeInX1), (self.contest.writeInY2-self.contest.writeInY1)]
			self.draw_writein(self.contest.ballot.writeins[self.contest.number],text_rect)

	def draw_writein(self, text, text_rect):
		screen.fill( (255,255,255), text_rect)
		if self.selected:
			textobj = Ballot.writein_font.render( text, 0, (255, 0, 0))
			screen.blit( textobj, text_rect)
		pygame.display.update( text_rect)


	def toggle(self, value=1): # select, cancel, change (reset not included)
		#if the selected candidate in ordered contest, then value will be supported (non defaule) = the order of selected candidate
		#if the selected candidate in non ordered contest, value (default) = 1
		if self.selected == value: #it was selected before and now need to be canceled
			self.selected = 0 # change the candidate.selected parameter to be 0
			if int(self.contest.maxVotes)==1:    #for single selection contests
				ballot.votes[self.contest.number] = 0         # remove the vote from votes array
				ballot.vmvotes[self.contest.number] = 0       #remove candidate code from verification module code array
				print 'canceled : ' + str(self.VmCandidateId) # print verification message
			elif int(self.contest.maxVotes)>1 and self.contest.ordered=='f': # for multiple votes non ordered contest
				ballot.votes[self.contest.number].remove(self.number)          #remove the vote from votes array
				ballot.vmvotes[self.contest.number].remove(self.VmCandidateId) #remove candidate code from verification module code array
				print 'canceled : ' + str(self.VmCandidateId)                  #print verification message
			#elif int(self.contest.maxVotes)>1 and self.contest.ordered=='t':# for multiple votes ordered contest
			#	ballot.votes[self.contest.number][value-1] = 0
		#
		else: #it was not selected before, and now selected
			if  self.contest.maxVotes == 1: #for single selection contests
				for candidate in self.contest.candidates: #check if the was previous candidate already selected in same contest. In this case the older selection should be canceled first
					if candidate != self and candidate.selected == value: # if found a previous selection then cancel, preparing to next step (select new one)
						candidate.selected = 0
						candidate.draw_button() # clear the tick, as drawing acandidate with selected=0 leads to clear it's tick
						print 'canceled : ' + str(candidate.VmCandidateId)+"find me"# print verification message
			else: #for multipe selection contests. i.e., maxvotes > 1
				# Make sure there aren't too many selections
				count = 0
				for candidate in self.contest.candidates: # checks how many selected candidates in this contest
					if candidate.selected: count = count + 1
				if count >= self.contest.maxVotes: return # stop as selected candidates more than available ones
			#
			self.selected = value # value = 1 in non ordered contest, value = selection order in ordered contest
			if int(self.contest.maxVotes)==1:                            #for single selection contests
				ballot.votes[self.contest.number] = self.number          #fill the value of votes array (candidate number in the contest)
				ballot.vmvotes[self.contest.number] = self.VmCandidateId #fill the value of verification module array (candidate code)
			elif int(self.contest.maxVotes)>1 and self.contest.ordered=='f':   # for multiple votes non ordered contest
				ballot.votes[self.contest.number].append(self.number)          #append the value of votes array (selected candidate number)
				ballot.vmvotes[self.contest.number].append(self.VmCandidateId) #append the value of verification module array (selected candidate code)
				ballot.votes[self.contest.number].sort()   #sort array
				ballot.vmvotes[self.contest.number].sort() #sort array
			elif int(self.contest.maxVotes)>1 and self.contest.ordered=='t':       # for multiple votes ordered contest
				ballot.votes[self.contest.number][value-1] = self.number           #fill the value of votes array (candidate number in the contest)
				ballot.vmvotes[self.contest.number][value-1] = self.VmCandidateId  #fill the value of verification module array (candidate code)
			if (self.selected==value and (not self.writein)):
				print 'selected : ' + str(self.VmCandidateId) # print verification message (non write in)
			if self.writein:
				self.contest.edit_writein()
				print "write-in : " + str(self.VmCandidateId) +","+ ballot.writeins[self.contest.number] #print verification message (write in)
				#
			#
		self.draw_button() # draw check box after togling

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

	def add_candidate(self, x, y, x1, y1, x2, y2, number, VmCandidateId):
		self.candidates.append( Candidate( self, x, y, x1, y1, x2, y2, number, VmCandidateId))
		# The following hack causes the last option to be treated
		# as a write-in whenever there are three or more options.
		if len(self.candidates) > 2:
			self.candidates[-2].writein = 0
			self.candidates[-1].writein = 1


	def reset(self):
		LastResetedCandidateId=0
		for candidate in self.candidates: # read all candidates of this contest
			#candidate.reset() # old code: reset this candidate
			if candidate.selected: #if this candidate is selected
				candidate.selected = 0 # change the status to be deselected
				ballot.votes[candidate.contest.number].remove(candidate.number) # remove the vote of this candidate
				ballot.votes[candidate.contest.number].append(0) #append 0 value instead of removed one
				ballot.vmvotes[candidate.contest.number].remove(candidate.VmCandidateId) # remove the vmvote for this candidate
				ballot.vmvotes[candidate.contest.number].append(0) #append 0 value instead of removed one
				candidate.draw_button() #redraw this candidate check box
				LastResetedCandidateId=candidate.VmCandidateId #get the Id of this candidate to get contest id later
		if (LastResetedCandidateId!=0):
			print 'reset : ' + LastResetedCandidateId[:12] # print verification message , note: LastResetedCandidateId[:12] = the id without the last 2 digits
		
	def click(self, x, y):
		if self.ordered == 't': # for ordered contests
			# First: check if there is any reset buttom in any ordered contest has been pressed
			if (x >= int(self.resetX1) and x <= int(self.resetX2) and y >= int(self.resetY1) and y <= int(self.resetY2)):
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
						candidate.toggle( SelCandOrder + 1) #toggle selected candidate, the value in toggle = the order of last selected candidate +1
					elif candidate.writein:
						self.edit_writein()
		else: #for non ordered contests
			for candidate in self.candidates:
				if (x >= candidate.activeAreaX1 and
					x < candidate.activeAreaX2 and
					y >= candidate.activeAreaY1 and
					y < candidate.activeAreaY2):
					candidate.toggle() #does not required to have value in toggle
				
	def draw(self):
		for candidate in self.candidates:
			if candidate.selected: candidate.draw_button()

	def edit_writein(self):
		#contname = contnames[self.number]
		keyboard = OnScreenKeyboard(self.maxWriteIn,'Write-in Candidate for contest number '+str(self.number),ballot.writeins[self.number])
		keyboard.edit()
		ballot.writeins[self.number] = keyboard.text
		self.ballot.draw()

class Ballot:
	def __init__(self):
		if(self.load()==0): sys.exit("error during loading the coords file")
	def load( self):
		# declare lists
		self.votes =[] # contains votes per contes, element position= contest number.
		self.writeins = []
		self.vmvotes = []
		self.contests = []

		for cnt0 in py_obj.Contest:
			self.writeins.append('')
			row=[]
			row2=[]
			for w in range(int(cnt0.MaxVotes.PCDATA)):
				if cnt0.Ordered.PCDATA=='f':
					break
				row.append(0)
				row2.append(0)
			if int(cnt0.MaxVotes.PCDATA)>1:
				self.votes.append(row)
				self.vmvotes.append(row2)
			else:
				self.votes.append(0)
				self.vmvotes.append(0)
		#intialized lists will be as the following
		#self.votes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, [], [0, 0, 0, 0, 0, 0, 0, 0]] 
			#note that the elements of votes
			#contest with MaxVotes=1, will get the value 0, later it will contain the order number of selected option. e.g., if second option selected then it's value will be 2.
			#contest with MaxVotes=N>1, will get the value []. Later, value = the order number of selected option, maximum number of elements should not exceed MaxVotes.
			#contest with MaxVotes=N>1 and ordered, will get the value [0,0,0,....,N]. Later, the value of each elements will contains the order number of selected option. elements order refers to selected option preference order. e.g., [3,5,1,2,4,8,7,6].
		#self.vmvotes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, [], [0, 0, 0, 0, 0, 0, 0, 0]]
			#note that the elements of vmvotes
			#elements values will be replaced later by selected option Identifire
		#self.writeins = ['','','','','','','','','','','','','']
			#note that the elements of writeins
			#elements values will be replaced later by writein text if the writein selected in any contest
		#
		#
		# define the structure of date to be read form XML coords file
		headParser = re.compile("([0-9]+) ([0-9]+) ([tf]) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)") # define the structure of contest parameters (minVotes maxVotes ordered (t or f) ReserX1 ResetY1 ReserX2 ResetY2 (reset button coordinates) Maximum writein writeinX1 WriteinY1 writeinX2 WriteinY2 (coordinates of writein area) Write in font size  \n)
		parser = re.compile("([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+) ([A-Z0-9]+)")# define the structure of option parameter (TickX TickY (location of tick image) OptionX1 OptionY1 OptionX2 OptionY2 (coordinates of option active area) Option(candidate)Identifier )
		#load data from coords XML file
		contnum=0
		for cnt in py_obj.Contest:
			#load contest data
			line1 = cnt.MinVotes.PCDATA +" "+ cnt.MaxVotes.PCDATA +" "+ cnt.Ordered.PCDATA +" "+ cnt.Reset.ResetX1.PCDATA+" "+ cnt.Reset.ResetY1.PCDATA+" "+ cnt.Reset.ResetX2.PCDATA+" "+ cnt.Reset.ResetY2.PCDATA+" "+ cnt.WriteIn.MaxWriteIn.PCDATA+" "+ cnt.WriteIn.WriteInX1.PCDATA+" "+ cnt.WriteIn.WriteInY1.PCDATA+" "+ cnt.WriteIn.WriteInX2.PCDATA+" "+ cnt.WriteIn.WriteInY2.PCDATA+" "+cnt.WriteIn.WriteInFontSize.PCDATA
			#print line1
			match = headParser.match(line1) # compare first line structure with headparser style
			if match is None: # the data does not mach with expected structure
				sys.exit("break, there is an error related to the data read from coords.xml file. Please check the structure of stored data. Check line:"+line1)
			(minVotes,maxVotes,ordered,resetX1,resetY1,resetX2,resetY2,maxWriteIn,writeInX1,writeInY1,writeInX2,writeInY2,wrtnFontSize) = match.groups() # move the values of the line to 4 variables
			# Check the rquired area for maximum writeins vs the available predefined area by user (from XML)
			if (check_minumum_writein_area(int(writeInX1),int(writeInY1),int(writeInX2),int(writeInY2),int(maxWriteIn),int(wrtnFontSize)) ==0):
				sys.exit("Maximum write-in characters of contest ("+ str(contnum)+ ") are larger then available space in contest write-in area defined in coords file. Either write-in font size is big or the are is small!!. Exit software...")
			# append parameters to Contest list
			contest = Contest( self, contnum,int(minVotes), int(maxVotes), ordered, int(resetX1),int(resetY1),int(resetX2),int(resetY2),int(maxWriteIn),int(writeInX1),int(writeInY1),int(writeInX2),int(writeInY2),int(wrtnFontSize))
			#load the options data for the contest
			candnum=1
			for option in cnt.Options.Option:
				line2= option.TickX.PCDATA+" "+option.TickY.PCDATA+" "+option.OptionX1.PCDATA+" "+option.OptionY1.PCDATA+" "+option.OptionX2.PCDATA+" "+option.OptionY2.PCDATA+" "+option.CandidateID.PCDATA
				#print line2
				match = parser.match(line2) #match the format of parser
				if match is None: # the data does not mach with expected structure
					sys.exit("break, there is an error related to the data read from coords.xml file. Please check the structure of stored data. Check line:"+line2)
				(x,y,x1,y1,x2,y2,VmCandidateId) = match.groups() # move line values to x,y
				#add option parameter to Contest.Candidate
				contest.add_candidate( int(x), int(y), int(x1),int(y1),int(x2),int(y2), candnum, str(VmCandidateId))
				candnum+=1
			self.contests.append(contest)
			contnum+=1
		# All data (contest and options)loaded from XML coords to the software
		
	def draw( self):
		screen.blit( Ballot.image, (0,0))
		screen.blit(Ballot.button_preview,(210,10))
		#bilt_alpha(screen,Ballot.button_preview,(210,10),128)
		pygame.display.update()

		for contest in self.contests:
			contest.draw()
	def vote(self):
		self.draw() # daraw main ballot
		now1 = datetime.datetime.now() # get time at startup action
		while 1: # voting loop
			now2 = datetime.datetime.now() #read current time
			diff = now2-now1
			if (diff.seconds>=FVTimeOut): #if there is no action for 59 seconds
				action=no_response() # called from utils/no_responce.py
				if action=='canceled_by_officer': #either cancel by officer
					# future work .. (label the vote as canceled and support the reason)
					print "cancelofficer : "+str(VoteNumber)
					reason='text message'
					print "reason : "+reason
					self.cancel_by_officer_screen()
					return
				elif action=='cast_by_officer':  #or cast by officer
					reason="text message"
					self.cast("officer",reason)
					self.cast_by_officer_screen()
					return
				#
			pygame.time.wait(200) # wait for 0.002 sec to read action
			for event in pygame.event.get():
				#broadc('message')
				if event.type is KEYDOWN:
					if event.key == K_ESCAPE: # exit if there is an escape key
						sys.exit(0)
				elif event.type is MOUSEBUTTONUP:
					now1 = datetime.datetime.now() # reset last action timer
					pos = pygame.mouse.get_pos()
					for contest in self.contests:
						# check if there is any active click in any contest
						contest.click( pos[0], pos[1])
					#
					if (pos[0] >= 210 and pos[0] <= (210 + Ballot.button_preview_size[0]) and
						pos[1] >= 10 and pos[1] <= (10 + Ballot.button_preview_size[1]) ) : # Preview

						ver=1
						verArea=[[0,0,0,0]]
						for item in self.contests:
							for cand in item.candidates:
								if cand.selected != 0 :
									verArea.append([cand.activeAreaX1,cand.activeAreaY1,cand.activeAreaX2,cand.activeAreaY2])
						for y in range(Ballot.image_size[1]):
							for x in range(Ballot.image_size[0]):
								if x%2==0 and y%2==1:
									skip=0
									for area in verArea:
										if (x>=int(area[0]) and x<=int(area[2]) and y>=int(area[1]) and y<=int(area[3])):
											skip=1
									if (skip==0): screen.set_at((x, y), (0, 125, 125))
						screen.blit(Ballot.button_back, (210,10))
						screen.blit(Ballot.button_cast, (220+Ballot.button_back_size[0],10))
						pygame.display.update()
						while ver==1:
							for event in pygame.event.get():
								if event.type is MOUSEBUTTONUP:
									pos = pygame.mouse.get_pos()
									if (pos[0] >= 210 and pos[0] < (210 + Ballot.button_back_size[0]) and
										pos[1] >= 10 and pos[1] < (10 + Ballot.button_back_size[1]) ) : # Back and Edit Vote
										self.draw()
										ver=0
									if (pos[0] >= 220+Ballot.button_back_size[0] and pos[0] < (220+Ballot.button_back_size[0]+Ballot.button_cast_size[0]) and
										pos[1] >= 10 and pos[1] <= (10 + Ballot.button_cast_size[1]) ) : # cast vote
										self.cast("voter")
										self.cast_by_voter_screen()
										print ballot.votes
										print ballot.vmvotes
										print ballot.writeins
										for i , code in enumerate(ballot.vmvotes):
											if code == 0: continue
											if type(code) is list and len(code) !=0 and code.count(0) < len(code):
												print i+1
												for x in code:
													if x == 0: continue
													print x
											if type(code) is not list:
												print i+1
												print code
										return
										#self.draw()
									else: continue
								


						# Verification , from verify.py
						#ver = verify (date, country, state, county, VoteNumber, precinct, serial,'voting_machine', ballot.votes, ballot.writeins)
						#if ver=='edit':
						#	self.draw()
						#	break
						#if ver=='cast_by_voter':
						#	self.cast("voter")
						#	self.cast_by_voter_screen()
						#	return
						#if ver=='canceled_by_officer':
						#	print "cancelofficer : "+str(VoteNumber)
						#	reason='text message'
						#	print "reason : "+reason
						#	self.cancel_by_officer_screen()
						#	return
						#if ver=='cast_by_officer':
						#	reason="text message"
						#	self.cast("officer",reason)
						#	self.cast_by_officer_screen()
								
						#
	def cast(self,actor, reason="None"):
		"""Documentation"""
		for item in self.contests: #this loop is to remove any redundent '0' from votes list of any ordered contest
			if item.maxVotes >1 and item.ordered=='t':
				print ballot.votes[item.number]
				for i in range(ballot.votes[item.number].count(0)):
					ballot.votes[item.number].remove(0)
		#Print the ballot
		xml = ballotxml(ElectionID,PollingPlaceID,PollingMachineID, BallotID, VoteNumber, ballot.vmvotes,ballot.writeins)
		xmlfile = re.sub(' ', '_', "-".join(["v", str(ElectionID),str(PollingPlaceID),str(PollingMachineID), str(VoteNumber)]) + ".xml")
		file = open('cast_votes/'+xmlfile, 'w')
		file.write(xml)
		file.close()
		if (actor=="voter"):
			print "votercast : "+str(VoteNumber)
		if (actor=="officer"):
			print "officercast :"+str(VoteNumber)
			print "reason :"+reason
		#p = PaperBallot(xmlfile)
		#p.PostscriptPrint(psfile)
		#del p
		#
	#introduction screen before ballot
	def introduction_screen(self,contImage="continue.png"):
		#introduction screen
		intro_image = load_image(contImage, None)
		screen.blit( intro_image, (0,0))
		pygame.display.update()
		now1 = datetime.datetime.now()
		while 1:
			now2 = datetime.datetime.now()
			diff = now2-now1
			if (diff.seconds==388):
				return 0
			pygame.time.wait(20)
			for event in pygame.event.get():
				if event.type is MOUSEBUTTONDOWN:
					return 0
				if event.type is KEYDOWN:
					if event.key == K_ESCAPE: return 1
					return 0
	def cast_by_voter_screen(self):
		cast= load_image('cast_voter.png', None,(screen_width, screen_height))
		screen.blit( cast, (0,0))
		pygame.display.update()
		pygame.time.delay(6000)
		return
	def cast_by_officer_screen(self):
		cast= load_image('cast_officer.png', None,(screen_width, screen_height))
		screen.blit( cast, (0,0))
		pygame.display.update()
		pygame.time.delay(6000)
		return
	def cancel_by_officer_screen(self):
		cancel= load_image('cancel.png', None,(screen_width, screen_height))
		screen.blit( cancel, (0,0))
		pygame.display.update()
		pygame.time.delay(6000) #need to save log file
		return

						
# Function to set the video mode
def set_video_mode():
	global screen
	Ballot.image_size = Ballot.image.get_size()
	screen = pygame.display.set_mode( (Ballot.image_size[0],Ballot.image_size[1]),0)
	pygame.display.set_caption('EVMPro')
def setup_everything():
	# Initialize the game module
	pygame.init()
	#define ballot image
	#future work: image name comes from EML
	Ballot.image = load_image('ballotmockup3.png',None)
	
	set_video_mode()

	#define images
	# deselected check box
	Ballot.button_deselected = load_image('button-deselected.png',None)
	# selected check box
	Ballot.button_selected = load_image('button-selected.png',None)
	# selected ordered check box
	Ballot.box_selected = load_image('small_rect_full.png',None)
	# deselected ordered check box
	Ballot.box_deselected = load_image('small_rect_empty.png',None)
	#Ballot.box_selected = load_image('small_rect_full.png',None,(Ballot.box_selected.get_size())).convert()
	Ballot.button_preview = load_image('previewbtm.png')
	Ballot.button_preview_size = Ballot.button_preview.get_size()
	Ballot.button_cast = load_image('castbtm.png')
	Ballot.button_cast_size = Ballot.button_cast.get_size()
	Ballot.button_back = load_image('backbtm.png')
	Ballot.button_back_size = Ballot.button_back.get_size()
	
	# Set the size of the text inside order box
	order_box_text_size = Ballot.box_selected.get_size()
	margin = (0.15*order_box_text_size[1])
	# calculate pixile/size ration
	mf = pygame.font.SysFont('arial', 20)
	xw,yh = mf.size("0")
	ratio = yh/20 
	#
	order_font_size = int ((order_box_text_size[1] - (margin*2))/ratio)
	if (order_font_size < 2): order_font_size =2
	Ballot.order_font = pygame.font.SysFont('arial', order_font_size)
	



class SartMachine: #open poll
	def __init__(self, openImage="open.png"):
		self.open_image = load_image(openImage, None)
	def open_poll(self):
		#global screen
		screen.blit( self.open_image, (0,0))
		pygame.display.update()
		while 1:
			pygame.time.wait(20)
			for event in pygame.event.get():
				if event.type is MOUSEBUTTONDOWN:
					pos = pygame.mouse.get_pos()
					if( pos[0] >= 480 and pos[0] < 725
					and pos[1] >= 436 and pos[1] < 545):
						print "openpoll : "+PollingPlaceID+PollingMachineID
						return 1


class ControlElection: #activate vote or close poll
	def __init__(self, controlImage = "controlelection.png"):
		self.control_image = load_image(controlImage, None)
	def control_election(self):
		#global screen
		screen.blit( self.control_image, (0,0))
		pygame.display.update()
		while 1:
			pygame.time.wait(20)
			for event in pygame.event.get():
				if event.type is MOUSEBUTTONDOWN:
					pos = pygame.mouse.get_pos()
					if( pos[0] >= 480 and pos[0] < 725
					and pos[1] >= 436 and pos[1] < 545):
						bn= self.open_vote_cast()
						if (bn!=-2):
							print "opencast : "+str(bn)
						return bn
					if( pos[0] >= 480 and pos[0] < 725
						and pos[1] >= 574 and pos[1] < 683):
							#close=self.close_vote_poll()
							print "closecast : "+PollingPlaceID+PollingMachineID
							#
							return -1
	def open_vote_cast(self): # generate , store and return unique ballot number
		rnd = open("rndballots","r+") # open file to store ballot id
		x=0
		while 1:
			# this loop to, generate random number, check if it used before, store and return number if it is unique,
			# return -2 if it is not possible to find unique number that is not used before
			VoteNumber = random.randint(1000, 9999)
			found=0
			while 1:
				#print "while"
				id=rnd.readline()
				#print id
				if (str(VoteNumber)+"\n"==id):
					#print "equal"
					rnd.seek(0)
					found=1
					x=x+1
					if ( x>=3): return -2
					break
				if (id==""):
					size = rnd.tell()
					#print size
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

class CloseMachine:
	def __init__(self, closeImage = "closeelection.png"):
		self.close_image = load_image(closeImage, None)
	#introduction screen before ballot
	def close_machine(self):
		#introduction screen
		screen.blit(self.close_image, (0,0))
		pygame.display.update()
		now1 = datetime.datetime.now()
		while 1:
			now2 = datetime.datetime.now()
			diff = now2-now1
			if (diff.seconds==380):
				return 0
			pygame.time.wait(20)
			for event in pygame.event.get():
				if event.type is MOUSEBUTTONDOWN:
					return 0


#main code
setup_everything()
startmachine = SartMachine()          #initialize open poll screen
controlelection = ControlElection()   #initialize control election screen (Activate vote, close poll)
closemachine = CloseMachine()         # initialize close poll screem
openpoll = startmachine.open_poll()   # show open poll screen and return 1 if "Open Poll" selected
while (openpoll==1):
	VoteNumber = controlelection.control_election() #show control screen, generate and return ballot number if "Activate Vote" selected, return -1 if "Close Poll" selected.
	if (VoteNumber!=0 and VoteNumber!=-1 and VoteNumber!=-2):
		ballot = Ballot()             #initialize ballot by loading the "coords" file. (see documentation to learn more about the file structure)
		ballot.introduction_screen("continue.png") # show the introduction screen (page at which some introductions or instructions shown to voter before voting)
		ballot.vote()                 # show ballot and cast vote
		VoteNumber=0               # reset ballot number
	if (VoteNumber== -1):          #
		closemachine.close_machine()  # close the election (show close election screen)
		sys.exit(0)
	if (VoteNumber== -2):          #
		#closemachine.close_machine()  # close the election (show close election screen)
		print "rndballots file filled with reach maximum number of allowed ballot numbers"
		sys.exit(0)
