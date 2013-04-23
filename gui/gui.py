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
#from utils.no_response import no_response
from utils.onscreenkeyboard import OnScreenKeyboard
from gnosis.xml.objectify import XML_Objectify
from os.path import isfile

py_obj = XML_Objectify('configuration_files/coords.xml').make_instance()
settings = XML_Objectify('configuration_files/EVMCVSettings.xml').make_instance()


# DRE information, this what will be inseted to vote
VoteNumber=0
ElectionID=py_obj.Election.ElectionID.PCDATA
PollingPlaceID=py_obj.Election.PollingPlaceID.PCDATA
PollingMachineID=py_obj.Election.PollingStationID.PCDATA
BallotID = py_obj.Election.BallotID.PCDATA
ballot_image=py_obj.Election.BallotImage.PCDATA
if isfile(os.path.join('configuration_files',py_obj.Election.TickImage_Selected.PCDATA)):
	TickImage_Selected=py_obj.Election.TickImage_Selected.PCDATA
else: TickImage_Selected=''
if isfile(os.path.join('configuration_files',py_obj.Election.TickImage_Blank.PCDATA)):
	TickImage_Blank=py_obj.Election.TickImage_Blank.PCDATA
else: TickImage_Blank=''
if isfile(os.path.join('configuration_files',py_obj.Election.TickImageOrdered_Selected.PCDATA)):
	TickImageOrdered_Selected=py_obj.Election.TickImageOrdered_Selected.PCDATA
else: TickImageOrdered_Selected=''
if isfile(os.path.join('configuration_files',py_obj.Election.TickImageOrdered_Blank.PCDATA)):
	TickImageOrdered_Blank=py_obj.Election.TickImageOrdered_Blank.PCDATA
else: TickImageOrdered_Blank=''

#printer output file
psfile = 'ballot.ps'
# FVT : Fleing Voter Time out setting
FVTimeOut=int(settings.FVTimeOut.PCDATA)
introduction_time=int(settings.Intro_Time.PCDATA)
screen_width=int(settings.Screen_Width.PCDATA)
screen_height=int(settings.Screen_Height.PCDATA)
# screen configuration
dre_pannel_height = 100

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
	if name == ballot_image or name== 'ballot_introduction.png' or name == TickImage_Selected or name == TickImage_Blank or name == TickImageOrdered_Selected or name == TickImageOrdered_Blank:
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
	#
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

	def draw_writein(self, text, text_rect):
		screen.fill( (255,255,255), text_rect)
		mf = pygame.font.SysFont('arial', self.contest.wrtnFontSize)
		xw,yh = mf.size("M")
		if self.selected:
			character_per_row = int(text_rect[2]/xw)+1
			text_length = len(text)
			num_rows = int(text_length/character_per_row)
			for i in range(num_rows+1):
				textobj = Ballot.writein_font.render( text[(character_per_row*i):(character_per_row*(i+1))], 0, (255, 0, 0))
				screen.blit( textobj, [text_rect[0],text_rect[1]+(yh*i+1),text_rect[2],yh])
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
						print 'canceled : ' + str(candidate.VmCandidateId)# print verification message
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
				status= self.contest.edit_writein()
				print "write-in : " + str(self.VmCandidateId) +","+ ballot.writeins[self.contest.number] #print verification message (write in)
				if status ==0: return 0
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
						status=candidate.toggle( SelCandOrder + 1) #toggle selected candidate, the value in toggle = the order of last selected candidate +1
						if status==0: return 0
					#elif candidate.writein:
					#	self.edit_writein()
		else: #for non ordered contests
			for candidate in self.candidates:
				if (x >= candidate.activeAreaX1 and
					x < candidate.activeAreaX2 and
					y >= candidate.activeAreaY1 and
					y < candidate.activeAreaY2):
					status=candidate.toggle() #does not required to have value in toggle
					if status==0: return 0
		return 1
	def draw(self):
		for candidate in self.candidates:
			if candidate.selected: candidate.draw_button()

	def edit_writein(self):
		#contname = contnames[self.number]
		keyboard = OnScreenKeyboard(self.maxWriteIn,'Write-in Candidate for contest number '+str(self.number+1),ballot.writeins[self.number])
		remain_time = keyboard.edit(FVTimeOut)
		ballot.writeins[self.number] = keyboard.text
		if remain_time == 0:
			now =datetime.datetime.now()
			ballot.timeout(now,now,1)
			return 0
		else:
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
			contest = Contest( self, contnum,int(minVotes), int(maxVotes), ordered, int(resetX1),int(resetY1)+dre_pannel_height,int(resetX2),int(resetY2)+dre_pannel_height,int(maxWriteIn),int(writeInX1),int(writeInY1)+dre_pannel_height,int(writeInX2),int(writeInY2)+dre_pannel_height,int(wrtnFontSize))
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
				contest.add_candidate( int(x), int(y)+dre_pannel_height, int(x1),int(y1)+dre_pannel_height,int(x2),int(y2)+dre_pannel_height, candnum, str(VmCandidateId))
				candnum+=1
			self.contests.append(contest)
			contnum+=1
		# All data (contest and options)loaded from XML coords to the software
		
	def draw(self):
		control.set_video_mode(control.BallotImage)
		screen.blit( control.BallotImage, (0,dre_pannel_height))
		screen.blit( control.ButtonPreview,(210,10))
		pygame.display.update()

		for contest in self.contests:
			contest.draw()
	def timeout(self,time1,time2,force=0):
		diff = time2-time1
		if (diff.seconds>=FVTimeOut or force==1): #if there is no action for 59 seconds
			action= control.no_response()
			if action=='canceled_by_officer': #either cancel by officer
				# future work .. (label the vote as canceled and support the reason)
				print "cancelofficer : "+str(VoteNumber)
				reason='text message'
				print "reason : "+reason
				control.cancel_by_officer_screen()
				return 1
			elif action=='cast_by_officer':  #or cast by officer
				reason="text message"
				self.cast("officer",reason)
				control.cast_by_officer_screen()
				return 1
		return 0
	def preview(self):
		ver=1
		verArea=[[0,0,0,0]]
		for item in self.contests:
			for cand in item.candidates:
				if cand.selected != 0 :
					verArea.append([cand.activeAreaX1,cand.activeAreaY1,cand.activeAreaX2,cand.activeAreaY2])
		for y in range(control.BallotImage_size[1]):
			for x in range(control.BallotImage_size[0]):
				if x%2==0 and y%2==1:
					skip=0
					for area in verArea:
						if (x>=int(area[0]) and x<=int(area[2]) and y>=int(area[1]) and y<=int(area[3])):
							skip=1
					if (skip==0): screen.set_at((x, y), (0, 125, 125))
		screen.blit(control.ButtonBack, (210,10))
		screen.blit(control.ButtonCast, (220+control.ButtonBack_size[0],10))
		pygame.display.update()
		now1 = datetime.datetime.now() #read current time
		while ver==1:
			now2 = datetime.datetime.now() #read current time
			if (self.timeout(now1, now2)): return 'timeout'
			for event in pygame.event.get():
				if event.type is MOUSEBUTTONUP:
                    now1 = datetime.datetime.now() #reset timeout
					pos = pygame.mouse.get_pos()
					if (pos[0] >= 210 and pos[0] < (210 + control.ButtonBack_size[0]) and
						pos[1] >= 10 and pos[1] < (10 + control.ButtonBack_size[1]) ) : # Back and Edit Vote
						return 'back'
						#ver=0
					if (pos[0] >= 220+control.ButtonBack_size[0] and pos[0] < (220+control.ButtonBack_size[0]+control.ButtonCast_size[0]) and
						pos[1] >= 10 and pos[1] <= (10 + control.ButtonCast_size[1]) ) : # cast vote
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
					now1 = datetime.datetime.now() # reset last action timer
					pos = pygame.mouse.get_pos()
					for contest in self.contests:
						# check if there is any active click in any contest
						status=contest.click( pos[0], pos[1])
						if status==0: return 0
						else: now1 = datetime.datetime.now() # reset last action timer
					#
					if (pos[0] >= 210 and pos[0] <= (210 + control.ButtonPreview_size[0]) and
						pos[1] >= 10 and pos[1] <= (10 + control.ButtonPreview_size[1]) ) : # Preview
						#
						prev = self.preview()
						if prev=='back':
							self.draw()
							return
						if prev=='cast':
							self.cast("voter")
							control.cast_by_voter_screen()
							return
						if prev=='timeout':
							return

						
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

class Control_Machine: #open poll
# Function to set the video mode
	#load ballot image
	BallotImage = load_image(ballot_image,None)
	#load ballot introduction
	IntroImage = load_image('ballot_introduction.png', None)
	#load tick images for ordered and non ordered contests
	if TickImage_Selected !='': TickImageSelected = load_image(TickImage_Selected,None)
	if TickImage_Blank !='': TickImageBlank = load_image(TickImage_Blank,None)
	if TickImageOrdered_Selected !='': TickImageOrderedSelected = load_image(TickImageOrdered_Selected,None)
	if TickImageOrdered_Blank !='': TickImageOrderedBlank = load_image(TickImageOrdered_Blank,None)

	#load different screens images
	CloseImage_message = load_image('closeelection_message.png', None)
	CastV_message= load_image('cast_voter_message.png', None)
	CastO_message= load_image('cast_officer_message.png', None)
	CancelO_message= load_image('cancel_message.png', None)
	no_responce_message= load_image('no_responce_message.png', None)
	#buttons
	ButtonPreview = load_image('previewbtn.png')
	ButtonCast = load_image('castbtn.png')
	ButtonBack = load_image('backbtn.png')
	ButtonOpen = load_image('openbtn.png')
	ButtonActive = load_image('activebtn.png')
	ButtonClose = load_image('closebtn.png')
	ButtonCastO = load_image('castobtn.png')
	ButtonCancelO = load_image('cancelobtn.png')
	#logo
	Logo = load_image('logo1.png')
	

	def set_video_mode(self,image=''):
		global screen
		#
		self.screen_size = [screen_width,screen_height]
		if image == self.BallotImage or image == self.IntroImage:
			x,y = image.get_size()
			if image == self.BallotImage: y=y+dre_pannel_height
		else:
			x,y=self.screen_size
		screen = pygame.display.set_mode([x,y],pygame.BLEND_ADD,0)
		pygame.display.set_caption('EVMCV')
		screen.fill((255,255,255))
		
	def setup_everything(self):
		# Initialize the game module
		os.environ['SDL_VIDEO_CENTERED'] = '1'
		pygame.init()
		#calculate the size of ballot image
		BallotImageSize = self.BallotImage.get_size()
		self.BallotImage_size = list(BallotImageSize)
		self.BallotImage_size[1] = self.BallotImage_size[1] + dre_pannel_height # this to add to voting pannel sise
		#
		#calculate the size of control buttons
		self.ButtonPreview_size = self.ButtonPreview.get_size()
		self.ButtonCast_size = self.ButtonCast.get_size()
		self.ButtonBack_size = self.ButtonBack.get_size()
		self.Logo_size = self.Logo.get_size()
		self.ButtonOpen_size = self.ButtonOpen.get_size()
		self.ButtonActive_size = self.ButtonActive.get_size()
		self.ButtonClose_size = self.ButtonClose.get_size()
		self.ButtonCastO_size = self.ButtonCastO.get_size()
		self.ButtonCancelO_size = self.ButtonCancelO.get_size()

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
		#global screen
		self.set_video_mode()
		logo_pos=[((self.screen_size[0]/2)-(self.Logo_size[0]/2)),50]
		ButtonOpen_position=[((self.screen_size[0]/2)-(self.ButtonOpen_size[0]/2)),(50+self.Logo_size[1]+100)]
		screen.blit( self.Logo, (logo_pos[0],logo_pos[1]))
		screen.blit( self.ButtonOpen, (ButtonOpen_position[0],ButtonOpen_position[1]))
		pygame.display.flip()
		while 1:
			pygame.time.wait(20)
			for event in pygame.event.get():
				if event.type is MOUSEBUTTONDOWN:
					pos = pygame.mouse.get_pos()
					if( pos[0] >= ButtonOpen_position[0] and pos[0] < (ButtonOpen_position[0]+self.ButtonOpen_size[0])
					and pos[1] >= ButtonOpen_position[1] and pos[1] < (ButtonOpen_position[1]+self.ButtonOpen_size[1])):
						print "openpoll : "+PollingPlaceID+PollingMachineID
						return 1
	#introduction screen before ballot
	def introduction_screen(self):
		#introduction screen
		self.set_video_mode(self.IntroImage)
		screen.blit( self.IntroImage,(0,0))
		pygame.display.update()
		now1 = datetime.datetime.now()
		while 1:
			now2 = datetime.datetime.now()
			diff = now2-now1
			if (diff.seconds==introduction_time):
				return 
			pygame.time.wait(20)
			for event in pygame.event.get():
				if event.type is MOUSEBUTTONDOWN:
					return 
	#this functions shows an image mesaage in screen
	def message_screen(self,message,message_period):
		self.set_video_mode()
		message_size = message.get_size()
		logo_pos=[((self.screen_size[0]/2)-(self.Logo_size[0]/2)),50]
		message_position=[((self.screen_size[0]/2)-(message_size[0]/2)),(50+self.Logo_size[1]+100)]
		screen.blit( self.Logo, (logo_pos[0],logo_pos[1]))
		screen.blit( message, (message_position[0],message_position[1]))
		pygame.display.update()
		now1 = datetime.datetime.now()
		while 1:
			now2 = datetime.datetime.now()
			diff = now2-now1
			if (diff.seconds>=message_period):
				return (50+self.Logo_size[1]+100+message_size[1])
			pygame.time.wait(20)
			for event in pygame.event.get():
				if event.type is MOUSEBUTTONDOWN:
					return (50+self.Logo_size[1]+100+message_size[1])
		

	def close_machine(self):
		#close machine screen
		self.message_screen(self.CloseImage_message,5)
		return 0
	def cast_by_voter_screen(self):
		self.message_screen(self.CastV_message,5)
		return
	def cast_by_officer_screen(self):
		self.message_screen(self.CastO_message,5)
		return
	def cancel_by_officer_screen(self):
		self.message_screen(self.CancelO_message,5)
		return
	def no_response(self):
		ref= self.message_screen(self.no_responce_message,0)
		ButtonCastO_position=[((self.screen_size[0]/2)-(self.ButtonActive_size[0]/2)),(ref+50)]
		ButtonCancelO_position=[((self.screen_size[0]/2)-(self.ButtonActive_size[0]/2)),(ref+50+self.ButtonCastO_size[1]+50)]
		screen.blit( self.ButtonCastO, (ButtonCastO_position[0],ButtonCastO_position[1]))
		screen.blit( self.ButtonCancelO, (ButtonCancelO_position[0],ButtonCancelO_position[1]))
		pygame.display.update()
		loop=1
		while loop==1:
			pygame.time.wait(20)
			for event in pygame.event.get():
				if event.type is MOUSEBUTTONDOWN:
					pos = pygame.mouse.get_pos()
					if (pos[0] >= ButtonCastO_position[0] and pos[0] <= ButtonCastO_position[0]+self.ButtonCastO_size[0]
						and pos[1] >= ButtonCastO_position[1] and pos[1] <= ButtonCastO_position[1]+self.ButtonCastO_size[1]):
						action='cast'
						loop=0
					if (pos[0] >= ButtonCancelO_position[0] and pos[0] <= ButtonCancelO_position[0]+self.ButtonCancelO_size[0]
						and pos[1] >= ButtonCancelO_position[1] and pos[1] <= ButtonCancelO_position[1]+self.ButtonCancelO_size[1]):
						action='cancel'
						loop=0
		keyboard = OnScreenKeyboard(32,'Please enter admin password: ( test password= AAAA )','',0)
		keyboard.edit()
		code = keyboard.text
		if (code=='AAAA' and action=='cancel'):
			return 'canceled_by_officer'
		elif (code=='AAAA' and action=='cast'):
			return 'cast_by_officer'

	def control_election(self):
		#global screen
		self.set_video_mode()
		logo_pos=[((self.screen_size[0]/2)-(self.Logo_size[0]/2)),50]
		ButtonActive_position=[((self.screen_size[0]/2)-(self.ButtonActive_size[0]/2)),(50+self.Logo_size[1]+100)]
		ButtonClose_position=[((self.screen_size[0]/2)-(self.ButtonActive_size[0]/2)),(ButtonActive_position[1]+self.ButtonActive_size[1]+50)]
		screen.blit( self.Logo, (logo_pos[0],logo_pos[1]))
		screen.blit( self.ButtonActive, (ButtonActive_position[0],ButtonActive_position[1]))
		screen.blit( self.ButtonClose, (ButtonClose_position[0],ButtonClose_position[1]))
		pygame.display.update()
		while 1:
			pygame.time.wait(20)
			for event in pygame.event.get():
				if event.type is MOUSEBUTTONDOWN:
					pos = pygame.mouse.get_pos()
					if( pos[0] >= ButtonActive_position[0] and pos[0] < (ButtonActive_position[0]+self.ButtonActive_size[0])
						and pos[1] >= ButtonActive_position[1] and pos[1] < (ButtonActive_position[1]+self.ButtonActive_size[1])):
						bn= self.open_vote_cast()
						if (bn!=-2):
							print "opencast : "+str(bn)
						return bn
					if( pos[0] >= ButtonClose_position[0] and pos[0] < (ButtonClose_position[0]+self.ButtonClose_size[0])
						and pos[1] >= ButtonClose_position[1] and pos[1] < (ButtonClose_position[1]+self.ButtonClose_size[1])):
							#close=self.close_vote_poll()
							print "closecast : "+PollingPlaceID+PollingMachineID
							#
							return -1

	#create a unique vote number
	def open_vote_cast(self): # generate , store and return unique ballot number
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

	
#main code
control = Control_Machine()          #initialize open poll screen
control.setup_everything()
openpoll = control.open_poll()   # show open poll screen and return 1 if "Open Poll" selected
while (openpoll==1):
	VoteNumber = control.control_election() #show control screen, generate and return ballot number if "Activate Vote" selected, return -1 if "Close Poll" selected.
	if (VoteNumber!=0 and VoteNumber!=-1 and VoteNumber!=-2):
		control.introduction_screen() # show the introduction screen (page at which some introductions or instructions shown to voter before voting)
		ballot = Ballot()             #initialize ballot by loading the "coords" file. (see documentation to learn more about the file structure)
		ballot.vote()                 # show ballot and cast vote
		VoteNumber=0               # reset ballot number
	if (VoteNumber== -1):          #
		control.close_machine()  # close the election (show close election screen)
		pygame.quit()
		sys.exit(0)
	if (VoteNumber== -2):          #
		#exit software if there are no available ballot numbers
		print "rndballots file filled with reach maximum number of allowed ballot numbers"
		sys.exit(0)
