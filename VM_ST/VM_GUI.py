import Tkinter
from Tkinter import *
import Pmw
import sys
import os
sys.path.append(os.path.join('OVVM'))
#from tkFileDialog   import askopenfilename
from OVVM_VM import *
import datetime
import zbar
from sys import argv
import threading
import time

readed_code=''

class VerMod():
	def __init__(self, parent):

		###
                
		self.root=parent
		Pmw.initialise()
		#
		self.balloon = Pmw.Balloon(parent)
		#
		row1=Tkinter.Frame(parent)
		row1.pack(padx = 6, pady = 6,expand = 1, fill=X)
		#
		self.w = Pmw.Group(row1, tag_text='Verification Area')
		self.w.pack( side= LEFT, padx = 0, pady = 0,expand = 1)
		#Verification Text Area
		self.fixedFont = Pmw.logicalfont('Fixed')
		self.st = Pmw.ScrolledText(self.w.interior(),
			labelpos='n',
			borderframe=1,
			label_text='',
			usehullsize = 1,
			hull_width = 850,
			hull_height = 550,
			text_wrap='char',
			text_font = self.fixedFont,
			text_padx = 4,text_pady = 4,)
		self.st.configure(text_state = DISABLED,)
		self.st.pack(side=LEFT, padx = 0, pady = 0, expand = 1)
		# Information Area
		self.ww = Pmw.Group(row1, tag_text='Event Information')
		self.ww.pack( side= LEFT, padx = 0, pady = 0,expand = 1)
		# Election information Text Area
		self.ElectionInfo = Pmw.ScrolledText(self.ww.interior(),
			labelpos='n',
			borderframe=1,
			label_text='',
			usehullsize = 1,
			hull_width = 350,
			hull_height = 550,
			text_wrap='char',
			text_font = self.fixedFont,
			text_padx = 4,text_pady = 4,)
		self.ElectionInfo.configure(text_state = DISABLED,)
		self.ElectionInfo.pack(side=LEFT, padx = 0, pady = 0, expand = 1, fill=X)
		#Status Frame
		row2=Tkinter.Frame(parent)
		row2.pack(padx = 1, pady = 1,expand = 1, fill=X)
		# The Status indicator
		self.C = Tkinter.Canvas(row2, height=15, width=15)
		self.arc = self.C.create_oval(5,5,15,15, fill="red")
		self.C.pack( anchor= SW , side=LEFT, padx = 0, pady = 15)
		# Status Text
		self.messagebar = Pmw.MessageBar(row2, entry_relief=GROOVE,labelpos=W, entry_width=200,label_text='Status')
		self.messagebar.pack( anchor= SW, side=LEFT, fill=X, expand=1, padx=0, pady=11)
		self.messagebar.message("state", "Connection off")
		#
		#
		# Variables initialization
		self.message=''
		# Control level variables
		self.flag =0
		self.connection_setup_time=''
		self.connection_release_time=''

		self.show_Event_info() #this to show blanck event info
		self.now=datetime.datetime.now()
		
        
	def show_Event_info(self):
		"""
		This functions shows Event information in the dedicated area of the VM interface.
		This information got from the VM class variables.
		"""
		self.ElectionInfo.appendtext('Event Name : ' + OVVM.Event_Name +'\n \n')
		self.ElectionInfo.appendtext('Election Name : ' + OVVM.Election_Name +'\n \n')
		self.ElectionInfo.appendtext('Start Date : ' + OVVM.Election_Start_Date +'\n \n')
		self.ElectionInfo.appendtext('End Date : ' + OVVM.Election_End_Date +'\n \n')
                self.ElectionInfo.appendtext('Polling Place : ' + OVVM.Polling_Place_Name +'\n \n')
		self.ElectionInfo.appendtext('Machine ID : ' + str(OVVM.Polling_Station_ID) +'\n \n')
		self.ElectionInfo.appendtext('Machine Connected : at ' + str(self.connection_setup_time) +'\n \n')
		return True



	def add_log(self,text):
		#initiate the log file
		log = open (os.path.join('vm_log','vm_log.txt'),'a+')
		time = datetime.datetime.now()
		log.write(str(time)+' : '+text+' \n')
		log.close()

	
	def verify(self):
		global entryWidget
		#global readed_code
		#verification_message=entryWidget.get().strip()
		#clear screen each 10 sec
		#now2=datetime.datetime.now()
		#diff = now2-self.now
		#if (diff.seconds >= 10):
		#    self.now=datetime.datetime.now()
		#    self.st.clear()
		#if self.message != readed_code: # read the command from global variable
		if self.message != entryWidget.get().strip(): # read the command from EntryWidget
			self.message = entryWidget.get().strip()
			print 'readed '+ self.message
			parse=OVVM.parse_Command(self.message)
			if parse[0]==0:
				self.st.appendtext('message : ' + parse[1] +'\n')
			else: #The command structure is fine, go to verification message routine
				command=parse[0]
				parameter=parse[2]
				#check the logical sequence of the command
				logical=OVVM.check_logical_sequence(command) #check if this command does not conflic with the logical commands sequence
				if logical[0]: #the command is logical at this level
					# check command routin
					# if the command is 'connect' (open poll)
					if (command=='connect'):
						OVVM.accept_Message(self.message) #this to accept the received message, message sequence will be considered
						open_Poll=OVVM.toggle_Poll(parameter,'connect') #connect the poll
						self.st.clear()
						if open_Poll[0] ==0:
							self.st.appendtext('Error!! : ' + str(open_Poll) +'\n')
						else: # Poll Opened
							self.connection_setup_time= datetime.datetime.now() #set connection time
							self.messagebar.message("state", "Poll Opened") #change the status message
							self.ElectionInfo.clear() #clear the election information text area
							self.show_Event_info() #show new data in the election information area
							self.messagebar.message("state", "Connected..")
							self.arc = self.C.create_oval(5,5,15,15, fill="green")#change indication bubble color to green
							self.st.appendtext('Message : Connected. \n') # show connection message
					#
					# if the command is 'close' poll command
					elif (command=='close'): 
						OVVM.accept_Message(self.message) #this to accept the received message, message sequence will be considered
						close_Poll = OVVM.toggle_Poll(parameter,'close') #close the poll
						if close_Poll[0]==0:
							self.st.appendtext('Error!! : ' + str(close_Poll) +'\n')
						else:
							self.connection_release_time=datetime.datetime.now()#set the connection release time
							self.ElectionInfo.appendtext('Machine Closed : at ' + str(self.connection_release_time) +'\n \n')# show closing time in the election information text area
							self.messagebar.message("state", "Closed..") #change status bar
							self.arc = self.C.create_oval(5,5,15,15, fill="red") #change indication bubble color to red
							self.st.clear()
							self.st.appendtext('Message : The poll has been closed. \n')
					#
					# if the command is 'report' (get votes summary) command
					elif (command=='report'): 
						OVVM.accept_Message(self.message) #this to accept the received message, message sequence will be considered
						report=OVVM.votes_summary(parameter) # get the votes summary
						self.st.clear()
						if report[0]==0:
							self.st.appendtext(report[1])
						else:
							self.st.appendtext(report[1]) # show votes summary
					#
					# if the command is 'activate' (activate cast session)
					elif (command=='activate'): 
						OVVM.accept_Message(self.message) #this to accept the received message, message sequence will be considered
						vote_ID=int(parse[2])
						print vote_ID
						activate=OVVM.activate_vote(vote_ID) #activate vote cast session
						self.st.clear()
						if activate[0]==0:
							self.st.appendtext(str(activate[1]) +'\n')
						else:
							self.messagebar.message("state", "Connected.. Vote cast session activated..") #change the status bar
							self.st.appendtext('Message : Vote cast session activated. \n')
					#
					# if the command is 'select'
					elif (command=='select'): 
						if self.flag==1:
						    self.st.clear()
						    self.flag=0
						OVVM.accept_Message(self.message) #this to accept the received message, message sequence will be considered
						add= OVVM.add_selected_option(parameter)
						#self.st.clear()
						if add[0]==0:
							self.st.appendtext(add[1] +'\n')
						else:
							self.st.appendtext('\nFor the Election :' + add[0] +'\n')
							self.st.appendtext(  'And the Contest  :' + add[1] +'\n')
							self.st.appendtext('You have selected the option : ' +add[2] +'\n \n')
					# if the command is 'writein'
					elif (command=='writein'): #
						if self.flag==1:
						    self.st.clear()
						    self.flag=0
						OVVM.accept_Message(self.message) #this to accept the received message, message sequence will be considered
						writein= parse[4]
						add= OVVM.add_selected_option(parameter, writein)
						#self.st.clear()
						if add[0]==0:
							self.st.appendtext(add[1] +'\n')
						else:
							self.st.appendtext('\nFor the Election : ' + add[0] +'\n')
							self.st.appendtext(  'And the Contest  : ' + add[1] +'\n')
							self.st.appendtext('You have selected the Writein : ' + add[3] +'\n \n')
					#
					# if the command is 'cancel'
					elif (command=='cancel'): 
						if self.flag==1:
						    self.st.clear()
						    self.flag=0
						OVVM.accept_Message(self.message) #this to accept the received message, message sequence will be considered
						remove= OVVM.remove_selected_option(parameter)
						#self.st.clear()
						if remove[0]==0:
							self.st.appendtext(remove[1] +'\n')
						#
						else:
							self.st.appendtext('\nFor the Election : ' + str(remove[0]) +'\n')
							self.st.appendtext(  'And the Contest  : ' + str(remove[1]) +'\n')
							if remove[3]==None: # The removed option is note writein
								self.st.appendtext('You have canceled the Option : ' + str(remove[2]) +'\n \n')
							elif remove[3]!=None:
								self.st.appendtext('You have canceled the Writein : ' + remove[3] +'\n \n')
					#
					#if the command is 'reset' (reset contest selections)
					elif (command=='reset'): 
						if self.flag==1:
						    self.st.clear()
						    self.flag=0
						OVVM.accept_Message(self.message) #this to accept the received message, message sequence will be considered
						Contest_ID=parameter[0:6]
						reset=OVVM.reset_contest(Contest_ID)
						#self.st.clear()
						if (reset[0]==0):
							self.st.appendtext(reset[1] +'\n')
						else:
							self.st.appendtext('\nFor the Election : ' + reset[0] +'\n')
							self.st.appendtext( 'And the Contest   : ' + reset[1] +'\n')
							self.st.appendtext('You have reset all of the selected options. \n \n')
					#
					#if the command is 'review' (review vote summary)
					elif (command=='review'): #
						OVVM.accept_Message(self.message) #this to accept the received message, message sequence will be considered
						summary= OVVM.review()
						self.st.clear()
						self.st.appendtext(summary)
						self.flag=1
					#
					#if the command is 'reason' supply reason for last action and add it to the log file)
					elif (command=='reason'): #
						OVVM.accept_Message(self.message) #this to accept the received message, message sequence will be considered
						reason_ID = parameter[6:8]
						reason=OVVM.get_Reason(reason_ID)
						self.st.clear()
						self.st.appendtext('Message : The reason is : '+ reason +' \n')
					elif (command=='calibrate'): #
						OVVM.accept_Message(self.message) #this to accept the received message, message sequence will be considered
						text = writein= parse[4]
						#self.st.clear()
						self.st.appendtext('Message : Connection Calibration is Ok. Text message : '+ text+' \n')
					#
					#if the command is 'votercast' (cast the vote by voter)
					elif (command=='votercast'): #
						OVVM.accept_Message(self.message) #this to accept the received message, message sequence will be considered
						cast=OVVM.cast(parameter, 'voter')
						self.st.clear()
						if cast[0]==0:
							self.st.appendtext(cast[1])
						else:
							self.st.appendtext('Message : The vote cast by the voter. \n')
							self.st.appendtext('Message : Vote cast session closed. \n')
						self.messagebar.message("state", "Connected..")
					#
					#if the command is 'officercast' (cast the vote by officer)
					elif (command=='officercast'): #
						OVVM.accept_Message(self.message) #this to accept the received message, message sequence will be considered
						if (len(parse)>3):
							cast=OVVM.cast(parameter, 'officer', parse[3])
						else:
							cast=OVVM.cast(parameter, 'officer')
						self.st.clear()
						if cast[0]==0:
							self.st.appendtext(cast[1])
						else:
							self.st.appendtext('Message : The vote cast by the officer. \n')
							self.st.appendtext('Message : Vote cast session closed. \n')
						self.messagebar.message("state", "Connected..")
					#
					#if the command is 'officercancel' (cancel the vote by officer)
					elif (command=='officercancel'): #
						OVVM.accept_Message(self.message) #this to accept the received message, message sequence will be considered
						self.st.clear()
						if (len(parse)>3):
							cancel=OVVM.cancel_vote_officer(parameter, parse[3])
						else:
							cancel=OVVM.cancel_vote_officer(parameter)
						#self.st.appendtext(cancel[1])
						self.st.appendtext('Message : The vote canceled by the officer.\n')
						self.st.appendtext('Message : Vote cast session closed. \n')
						self.messagebar.message("state", "Connected..")
					#
				#
				#if the command arrives with non logical sequence
				if not logical[0]:
					self.st.appendtext(logical[1])




		self.root.after(50,self.verify) # run the verify function each two seconds
	

	def exit(self):
		self.root.destroy()

class MyTkApp(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def callback(self):
       self.root.quit()
    def run(self):
        #global entryWidget
	global OVVM
        global proc
        self.root=Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        OVVM=VM()
	#modify the window
	self.root.title("VM V.10")
	self.root.geometry("1280x800")
	# Create a text frame to hold the text Label and the Entry widget
	#textFrame = Frame(self.root)
	#Create a Label in textFrame
	#entryLabel = Label(textFrame)
	#entryLabel["text"] = "Enter the text:"
	#entryLabel.pack(side=LEFT)
	#
	#textFrame.pack()
	myApp = VerMod(self.root)
	#run the function each 500 ms
        self.root.after(50,myApp.verify)
        self.root.mainloop()





class ScanThread(threading.Thread):
	def __init__(self, mode, image):
		self.quit = False
		self.mode = mode
		self.image = image
		if mode == 'wait':
			self.task = self.task_wait
		elif mode == 'one':
			self.task = self.task_one
		elif mode == 'image':
			self.task = self.task_image
		else:
			self.task = self.task_normal
		threading.Thread.__init__(self)

	def run(self):
		self.task()

	def terminate(self):
		if hasattr(self, 'proc'):
			self.proc.active = False
		self.quit = True

	def init_processor(self):
		#initialize the zbar processor and cam device
                self.proc = zbar.Processor()
                # configure the Processor
                self.proc.parse_config('enable')
                # initialize the Processor
                device = '/dev/video1'
                #device='/dev/usb/hiddev0'
		if len(argv) > 1:
                    device = argv[1]
                self.proc.init(device)
                self.proc.set_data_handler(self.process_data)
                # enable the preview window
                self.proc.visible = True
                # initiate scanning
                self.proc.active = True
                time.sleep(0.5)
	def start_processor(self):
		#self.proc.init('/dev/video0')
		self.proc.init('/dev/usb/hiddev0')
		self.proc.active = True

	def task_normal(self):
		self.init_processor()
		# thread is finished here

	def task_wait(self):
		self.init_processor()
		self.proc.user_wait() # 

	def task_one(self):
		self.init_processor()
		while not self.quit:
			self.proc.process_one(3)

	def task_image(self):
		scanner = zbar.ImageScanner()
		scanner.parse_config('disable')
		scanner.parse_config('qrcode.enable')
		while not self.quit:
			pil = Image.open(self.image).convert('L')
			width, height = pil.size
			raw = pil.tostring()
			image = zbar.Image(width, height, 'Y800', raw)
			scanner.scan(image)
			for symbol in image:
				print symbol.data
			del(image)
			del(pil)
			time.sleep(0.5)

	def process_data(self, proc, image, closure):
		global readed_code
		for symbol in image:
			if not symbol.count:
                            readed_code= '%s' % symbol.data
                            print readed_code
                            time.sleep(0.3)



# main
#if __name__=='__main__':
    
    #reader=Reader()
    #image = None
    #mode='one'
    #zbar_thread = ScanThread(mode, image)
    #zbar_thread.start()
    #
    #tk_thread=MyTkApp()
    #tk_thread.start()

    

    #Qr=QR()
    #x=Qr.decode_webcam()
    #print x

	#--------------
def main():
	global entryWidget
	global OVVM
	#
	OVVM=VM()
	#OVVM.add_private_log=True
	root = Tk()
	#modify the window
	root.title("VM V.10")
	root.geometry("1280x800")
	# Create a text frame to hold the text Label and the Entry widget
	textFrame = Frame(root)
	#Create a Label in textFrame
	entryLabel = Label(textFrame)
	entryLabel["text"] = "Enter the text:"
	entryLabel.pack(side=LEFT)
	# Create an Entry Widget in textFrame
	entryWidget = Entry(textFrame)
	entryWidget["width"] = 50
	entryWidget.pack(side=LEFT)
	#
	textFrame.pack()
	myApp = VerMod(root)
	#run the function each 500 ms
	root.after(500,myApp.verify)
	root.mainloop()


# main
if __name__=='__main__':
	main()
