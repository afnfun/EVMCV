import sys
if sys.platform != 'win32':
    sys.path.append('../..')
else:
    sys.path.append('..\\..')
from evm2003.data.contests import cont
from evm2003.utils.no_response import no_response
import os, pygame, re, sys, string, random, datetime
from pygame.locals import *


#def verify(Ballot):
	
"""
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


length = [8, 8, 3, 3, 4, 3, 4, 3, 2, 2, 2, 10, 8]
writein = [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1]
contest_title = ["Presidency", "Senator", "U.S. Representative", "Treasurer", "Attorney General", "Commis. of Education", "State Senate", "State Assembly", "Transportation Initiative", "Health care initiative", "Term limits", "Cat Catcher", "County Commissioner"]

# screen configuration
screen_width = 1280
screen_height = 1024
screen = pygame.display.set_mode( (screen_width, screen_height),0)



def verify(date, country, State, county, ballot_number, precinct, serial,
              source, sel, writeins):
    n = 0
    vs=35
    ie=0
    vscount=105
    loop=1
    global screen
    screen.fill( (255,255,255))
    # Verification
    #font = pygame.font.Font(None, 40)
    #text1 = font.render('Please verify your selection before casting your vote', 1, (10, 10, 10))
    #screen.blit(text1, (100,35))
    Verify= load_image('verify.png', None,(screen_width, screen_height))
    screen.blit( Verify, (0,0))
    pygame.display.update()
    font = pygame.font.Font(None, 36)
    for name in ["Presidency", "Senator", "U.S. Representative", "Treasurer", "Attorney General", "Commis. of Education", "State Senate", "State Assembly", "Transportation Initiative", "Health care initiative", "Term limits", "Cat Catcher", "County Commissioner"]:
        if n == 0:
            if sel[n] == 0:
                Text=contest_title[n] + ' : ' + 'President : No preference indicated'
                Text = font.render(Text,1, (10, 10, 10))
                screen.blit(Text, (100,vscount+n*vs))
                pygame.display.update()
                Text= contest_title[n] + ' : ' + 'Vice President : No preference indicated'
                Text = font.render(Text,1, (10, 10, 10))
                vscount=vscount+vs
                screen.blit(Text, (100,vscount+n*vs))
                pygame.display.update()
            elif sel[n] < length[n]:
                Text= contest_title[n] + ' : ' + 'President : '+ cont[name][sel[n]-1][0]
                Text = font.render(Text,1, (10, 10, 10))
                screen.blit(Text, (100,vscount+n*vs))
                pygame.display.update()
                Text= contest_title[n] + ' : ' + 'Vice President : '+ cont[name][sel[n]-1][1]
                Text = font.render(Text,1, (10, 10, 10))
                vscount=vscount+vs
                screen.blit(Text, (100,vscount+n*vs))
                pygame.display.update()
            else:
                Text= contest_title[n] + ' : ' + 'President : '+ writeins[n]
                Text = font.render(Text,1, (10, 10, 10))
                screen.blit(Text, (100,vscount+n*vs))
                pygame.display.update()
                Text = contest_title[n] + ' : ' + 'Vice President : '+ writeins[n]
                Text = font.render(Text,1, (10, 10, 10))
                vscount=vscount+vs
                screen.blit(Text, (100,vscount+n*vs))
                pygame.display.update()
                vscount=vscount+vs
        elif n < 11:
            if sel[n] == 0:
                Text= contest_title[n] + ' : ' + 'No preference indicated'
                Text = font.render(Text,1, (10, 10, 10))
                screen.blit(Text, (100,vscount+n*vs))
                pygame.display.update()
            elif sel[n] < length[n] or writein[n] == 0:
                Text= contest_title[n] + ' : ' + cont[name][sel[n]-1]
                Text = font.render(Text,1, (10, 10, 10))
                screen.blit(Text, (100,vscount+n*vs))
                pygame.display.update()
            else:
                Text= contest_title[n] + ' : ' + writeins[n]
                Text = font.render(Text,1, (10, 10, 10))
                screen.blit(Text, (100,vscount+n*vs))
                pygame.display.update()
        elif sel[n] == []: # if no cat catcher has selected
            Text= contest_title[n] + ' : ' + 'No preference indicated'
            Text = font.render(Text,1, (10, 10, 10))
            vscount=vscount+vs
            screen.blit(Text, (100,vscount+n*vs))
            pygame.display.update()
        else:
            order=0
            for i in sel[n]:
                ie=ie+1
                if i < length[n] and cont[name][i-1] :
                    order=order+1
                    Text= str(order) + ' : ' + contest_title[n] + ' : ' + cont[name][i-1]
                    Text = font.render(Text,1, (10, 10, 10))
                    screen.blit(Text, (100,vscount+n*vs+ie*vs))
                    pygame.display.update()
                elif i >= length[n]:
                    order=order+1
                    Text= str(order) + ' : ' + contest_title[n] + ' : ' + writeins[n]
                    Text = font.render(Text,1, (10, 10, 10))
                    screen.blit(Text, (100,vscount+n*vs+ie*vs))
                    pygame.display.update()
            if order==0:
                Text= contest_title[n] + ' : ' + 'No preference indicated'
                Text = font.render(Text,1, (10, 10, 10))
                screen.blit(Text, (100,vscount+n*vs+vs))
                pygame.display.update()
        n += 1
    #pygame.time.delay(5000)
    now1 = datetime.datetime.now()
    while loop==1:
        now2 = datetime.datetime.now()
        diff = now2-now1
        if (diff.seconds>=100):
            action=no_response()
            return action # return 'cast_by_officer' or 'canceled_by_officer'    
        for event in pygame.event.get():
            if event.type is MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                if (pos[0] >= 995 and pos[0] <= 1260 and pos[1] >= 163 and pos[1] <= 248):
                    loop=0
                    return 'cast_by_voter'
                elif (pos[0] >= 995 and pos[0] <= 1260 and pos[1] >= 310 and pos[1] <= 395):
                    loop=0
                    return 'edit' 
    #return True
"""