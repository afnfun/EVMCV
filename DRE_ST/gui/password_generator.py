#!/usr/bin/python

# Author: John-Paul Gignac

# Modified by Jan Karrman to generate XML with ballotxml() and connect with
# the printing routines.
# This version improved by Ali Al-Shammari

# Import Modules
from Crypto.Hash import SHA512
from gnosis.xml.objectify import XML_Objectify
import sys


settings = XML_Objectify('configuration_files/EVMCVSettings.xml').make_instance()



# read the old passwords
primary_password=settings.Primary_Password.PCDATA
secondary_password=settings.Secondary_Password.PCDATA
FVTimeOut=settings.FVTimeOut.PCDATA
Intro_Time=settings.Intro_Time.PCDATA
Screen_Width=settings.Screen_Width.PCDATA
Screen_Height=settings.Screen_Height.PCDATA

# Functions to create our resources



#update setting file
def update(): #
	global primary_password
	global secondary_password
	global FVTimeOut
	global Intro_Time
	global Screen_Width
	global Screen_Height
	f = open("configuration_files/EVMCVSettings.xml","r+")
	lines = f.readlines()
	f.close()
	f = open("configuration_files/EVMCVSettings.xml","w")
	for line in lines:
		if 'Primary_Password' in line:
			line = '	<Primary_Password>'+primary_password+'</Primary_Password>\n'
			f.write(line)
		elif 'Secondary_Password' in line:
			line = '	<Secondary_Password>'+secondary_password+'</Secondary_Password>\n'
			f.write(line)
		elif 'FVTimeOut' in line:
			line = '	<FVTimeOut>'+FVTimeOut+'</FVTimeOut>\n'
			f.write(line)
		elif 'Intro_Time' in line:
			line = '	<Intro_Time>'+Intro_Time+'</Intro_Time>\n'
			f.write(line)
		elif 'Screen_Width' in line:
			line = '	<Screen_Width>'+Screen_Width+'</Screen_Width>\n'
			f.write(line)
		elif 'Screen_Height' in line:
			line = '	<Screen_Height>'+Screen_Height+'</Screen_Height>\n'
			f.write(line)
		else:
			f.write(line)
	f.close()
	return



	

if __name__=='__main__':
	primary=raw_input('Please enter the primary password (to skip, press enter):')
	if primary!='':
		hash = SHA512.new()
		hash.update(primary)
		if hash.hexdigest()==primary_password:
			while 1:
				new=raw_input('Please enter the new primary password:')
				if len(new)<4:
					print 'Password must be at least four characters length'
					continue
				else:
					hash = SHA512.new()
					hash.update(new)
					primary_password=hash.hexdigest()
					print 'Primary password update successfuly.'
					break
		else:
			print 'Wrong primary password ! Password is not updated.'
	#
	secondary=raw_input('Please enter the secondary password (to skip, press enter):')
	if secondary!='':
		hash = SHA512.new()
		hash.update(secondary)
		if hash.hexdigest()==secondary_password:
			while 1:
				new=raw_input('Please enter the new secondary password:')
				if len(new)<4:
					print 'Password must be at least four characters length'
					continue
				else:
					hash = SHA512.new()
					hash.update(new)
					secondary_password=hash.hexdigest()
					print 'Secondary password update successfuly.'
					break
		else:
			print 'Wrong secondary password ! Password is not updated.'
	#
	timeout=raw_input('Please enter the fleeing voter timeout (to skip, press enter):')
	if timeout!='':
		FVTimeOut=timeout
	introtime=raw_input('Please enter the introduction time (to skip, press enter):')
	if introtime!='':
		Intro_Time=introtime
	width=raw_input('Please enter the screen width (to skip, press enter):')
	if width!='':
		Screen_Width=width
	height=raw_input('Please enter the screen height (to skip, press enter):')
	if height!='':
		Screen_Height=height
	update()

	sys.exit(0)
