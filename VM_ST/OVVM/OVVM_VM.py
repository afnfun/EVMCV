from gnosis.xml.objectify import *
import datetime
from collections import *
import os
import codecs

class VM():
	def __init__(self):
		self.VMS =XML_Objectify('EML_files/VmSettings710.xml').make_instance()
		self.Ballot =XML_Objectify('EML_files/Ballots410.xml').make_instance()
		self.Election_Event =XML_Objectify('EML_files/ElectionEvent110.xml').make_instance()
		#check the status of the VmSettings710.xml
		if (self.VMS.ns1_EMLHeader.ns1_OfficialStatusDetail.ns1_OfficialStatus.PCDATA != 'approved'):
				return 0 , 'error!! VmSettings710.xml is not approved, Contact election official'
		if (self.Election_Event.ns1_EMLHeader.ns1_OfficialStatusDetail.ns1_OfficialStatus.PCDATA != 'approved'):
				return 0 , 'error!! Election_Event110.xml is not approved, Contact election official'
		if (self.Ballot.ns1_EMLHeader.ns1_OfficialStatusDetail.ns1_OfficialStatus.PCDATA != 'approved'):
				return 0 , 'error!! Ballot410.xml is not approved, Contact election official'
		self.commands={'0':'calibrate', '1':'connect','2':'close','3':'report','4':'activate','5':'votercast','6':'officercast','7':'officercancel','8':'select','9':'cancel','A':'writein','B':'reset','C':'review','D':'reason'}
		self.Event_Name=''
		self.Event_ID=''
		self.Election_Name=''
		self.Election_Start_Date=''
		self.Election_End_Date=''
		self.Polling_Place_Name=''
		self.Polling_Place_ID=''
		self.Polling_Station_ID=''
		self.Vm_ID='v001'
		self.Ballot_ID=''
		self.VMSetting_ID=''
		self.contests=[]
		self.vote_options=[]
		self.vote_options_writein=[]
		self.add_private_log=False
		self._Vote_ID=0
		self._last_command=''     #value between 0-15
		self._last_sequence = '-1'
		self._last_command_time =''
		self._current_command=''  #value between 0-15
		self._current_sequence='0'
		self._current_command_time=''
		self.level_flag='00'

	
	def check_logical_sequence(self,command):
		if not command in self.commands.values(): #check if the command exist in the commands dictionary
			error='Error (106)!! Bad command used in the "check_logical_sequence" function!'
			self.add_log(error)
			return False, error
		if (command=='connect' or command=='report') and self.level_flag=='00':
			return True, 'Command sequence is logical.'
		if (command=='close' or command=='activate') and self.level_flag=='10':
			return True, 'Command sequence is logical.'
		if (command=='votercast'
		or command=='officercast'
		or command=='officercancel'
		or command=='select'
		or command=='cancel'
		or command=='writein'
		or command=='reset'
		or command=='review') and self.level_flag=='11':
			return True, 'Command sequence is logical.'
		if (command=='reason' or command=='calibrate'):
			return True, 'Command sequence is logical.'
		else:
			if (command=='connect'):
				if self.level_flag=='10':
					message='Message : You can not run ('+command+') command while the VM is connected! Disconnect first. \n'
				if self.level_flag=='11':
					message='Message : You can not run ('+command+') command while you are in vote cast session! Exit the vote cast session first.\n'
			if (command=='close' or command=='activate'):
					if self.level_flag=='00':
						message='Message : You can not run ('+command+') command while the VM not connected yet! Connect First.\n'
					if self.level_flag=='11':
						message='Message : You can not run ('+command+') command while you are in vote cast session! Exit the vote cast session first. \n'
			if (command=='select'
			or command=='writein'
			or command=='cancel'
			or command=='reset'
			or command=='review'
			or command=='votercast'
			or command=='officercast'
			or command=='officercancel'):
				if self.level_flag=='00':
					message='Message : You can not run ('+command+') command while the VM is not connected!  Connect it first, and activate cast session \n'
				if self.level_flag=='10':
					message='Message : You can not run ('+command+') command  while the vote cast session is not activated! Activate cast session first.\n'

			error= 'Error(103)!! Non logical sequence. The command '+command+' cannot come after ('+str(self._last_command)+') that arrived recently at ('+str(self._last_command_time)+').\n'
			error= error + message
			self.add_log(error)
			return False, error



	def is_Command(self,message):
		#check the minimum allowed size for the command
		#the default size must be 10 (or 11 but ends with comma ','), some commands may take larger size
		if len(message) < 10 or ( len(message) == 10 and message[9:10]==','): #message is shorter than expected.
			error='Error (102)!! Bad verification message. Message length is under the acceptable one!'
			self.add_log(error)
			return 0, error
		#Get command digit, convert it, if it is not digit, to uppercase (only if it is lower)
		Command=message[0:1]
		if (not Command.isdigit() and Command.islower()):
			Command=Command.upper()
		# Check if the command character exist in the self.commands dictionary
		#if exits, set Command to the command key, otherwise update log and return error.
		if self.commands.has_key(Command):
			Command=self.commands[Command]
		else:
			error='Error (102)!! Bad verification message. Command digit is out of range!'
			self.add_log(error)
			return 0, error
		#
		if (Command=='officercast' or Command=='officercancel'):
			if len(message)>10 and message[10:11]==':':
				if len(message)>13 and not (len( message)==14 and message[13:14]==',' ) :
					error='Error (102)!! Bad verification message. Message length is above the acceptable one!'
					self.add_log(error)
					return 0, error
				if len(message)<13:
					error='Error (102)!! Bad verification message. Message length is under the acceptable one!'
					self.add_log(error)
					return 0, error
		elif (Command=='writein' or Command=='calibrate'):
			if not (len(message)>10 and message[10:11]==':'):
				error='Error (102)!! Bad verification message. Message length is under the acceptable one!'
				self.add_log(error)
				return 0, error
		elif len(message)>10 and not ( len(message) == 11 and message[10:11]==','):
			error='Error (102)!! Bad verification message. Message length is above the acceptable one!'
			self.add_log(error)
			return 0, error
		#Get sequence digit, convert it, if it is not digit, to uppercase (only if it is lower)
		Sequence=message[1:2]
		if (not Sequence.isdigit() and Sequence.islower()):
			Sequence=Sequence.upper()
		# check if sequence digit is valid hex digit
		if not message[1:2] in ['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']:
			error='Error (102)!! Bad verification messaget. Sequence digit out of range!'
			self.add_log(error)
			return 0, error
		return 1,'Command Structure is fine.'


	def parse_Command(self,message):
		#check command structure
		isCommand = self.is_Command(message)
		if isCommand[0]==0:
			return isCommand
		# get the command from dictionary
		Command=message[0:1]
		Command=self.commands[Command]
		#This sequence retrieve the parameters from verification message
		Reason_Code=None
		Writein_Text=None
		Parameter=message[2:10]
		Sequence=message[1:2]
		if (Command=='officercast' or Command=='officercancel'):
			if (len(message)>11 and message[10:11]==':'):
				Reason_Code=message[11:13]
		if (Command=='writein' or Command=='calibrate'):
			Writein_Text=message[11:]
			if Writein_Text[-1]==',':
			    Writein_Text=Writein_Text[:-1]
			if len(Writein_Text)==0:
				Writein_Text='-'
		return Command, Sequence, Parameter, Reason_Code, Writein_Text


	def add_log(self,text):
		"""
		This function add the text parameter to the log file (vm_log/vm_log.txt).
		"""
		# creat log directory if it is not exists
		if not os.path.exists('OVVM_VM_log'):
		    os.makedirs('OVVM_VM_log')
		log = open (os.path.join('OVVM_VM_log','vm_log.txt'),'a+')
		time = datetime.datetime.now()
		log.write(str(time)+' : '+text+' \n')
		log.close()
		return True

	def _check_message_sequence(self):
		"""

		"""
		seq = int(self._current_sequence)-int(self._last_sequence)
		if seq==1 or seq==-15: #if the difference is 1 then it is ok.
			self._last_sequence=self._current_sequence #set last sequence as the current one and continue
			self._last_command=self._current_command#set the last command as current command and continue
			self._last_command_time=self._current_command_time
			return True
		else: #otherwise, report the difference and return 0
			if seq == 0:
				missed=16
			elif seq >0:
				missed=seq-1
			elif seq <0:
				missed=16+seq-1
			error= 'Error(101)!! There was '+str(missed)+' messages missing between the last command ('+str(self._last_command)+') at ('+str(self._last_command_time)+') and current command ('+str(self._current_command)+') at ('+str(self._current_command)+').'
			self.add_log(error)
			self._last_sequence=self._current_sequence #set last sequence as the current one and continue
			self._last_command=self._current_command#set the last command as current command and continue
			return False

	def accept_Message(self,message):
		Command=self.parse_Command(message)
		if Command[0]==0:
			return Command
		#set current accepted command
		self._current_command=Command[0]
		# set current accepted command time
		self._current_command_time=datetime.datetime.now()
		#convert the Sequence to decimal value (between 0-15)
		Sequence=int('0x'+Command[1],0)
		# set current sequence
		self._current_sequence=Sequence
		# compare current sequence with last one, add log and return 0 if there was missing messages
		self._check_message_sequence()
		return True

	def set_Vm_ID(self,VMID):
		"""
		This function sets the Vm_ID variable which will be used by the
		VM.emlBallot function to add VM Id to the cast vote XML file.
		"""
		self.Vm_ID=VMID
		return True

	def get_VMSetting_Information(self,VMSetting_ID):
		"""
		This function returns more information about the event and polling place that stored in the
		EML file (VmSettings710.xml). These information are: Event_Id,Polling_Place_ID,Polling_Station_ID,Ballot_ID.
		"""
		if len(VMSetting_ID)!=8: #this to verify parameter size (must be 8 characters)
			error='Error (104)!! Bad parameter size. VMSettingID size is not equal to 8.'
			self.add_log(error)
			return 0,error
		Setting_Exist=False
		#check the VmSettings710.xml to find if there is a match
		for VMSet in self.VMS.ns1_VmSettings:
			for Set in VMSet.ns1_Settings:
				if (Set.IdNumber==VMSetting_ID):
					Setting_Exist=True
					Event_Id=VMSet.ns1_EventIdentifier.OVVM_ID
					Polling_Place_ID=Set.ns1_PollingPlaceID.PCDATA
					Polling_Station_ID=Set.ns1_PollingStationID.PCDATA
					Ballot_ID=Set.ns1_BallotIdentifireID.PCDATA
					self.Polling_Station_ID=Polling_Station_ID
					self.Polling_Place_ID=Polling_Place_ID
					break
		#
		if (Setting_Exist==False): #if there was no match
			error='Error (105)!! The received  VMSetting identifier is not included in the VMSetting.xml file, machine must exit !'
			self.add_log(error)
			return 0, error
		else:
			return Event_Id,Polling_Place_ID,Polling_Station_ID,Ballot_ID

	def get_Reason(self,Reason_ID):
		"""
		This function search the reason text based on the reason ID (2 characters) in the VmSettings710.xml.
		and retrun the reason text if found.
		"""
		if len(Reason_ID)!=2: #this to verify parameter size (must be 2 characters)
			error='Error (104)!! Bad parameter size. Reason ID size is not equal to 2.'
			self.add_log(error)
			return 0,error
		Reason_Exist=False
		for Reason in self.VMS.ns1_Reasons.ns1_Reason:
			if (Reason_ID==str(Reason.IdNumber)):
					Reason_Text=Reason.PCDATA
                                        Reason_Exist=True
					break
		#
		if (Reason_Exist==False): #if there was no match
			error='Error (106)!! The received  Reason identifeir is not included in the VMSetting.xml file.'
			self.add_log(error)
			return 0, error
		else:
			return 1, Reason_Text

	def get_Event_Information(self,Event_Id,Polling_Place_ID):
		if not isinstance(Event_Id, str):
			Event_Id=str(Event_Id).zfill(2)
		if not isinstance(Polling_Place_ID, str):
			Polling_Place_ID=str(Polling_Place_ID).zfill(4)

		Event_Exist=False
		Poll_Exist=False
		for Event in self.Election_Event.ns1_ElectionEvent:
			if (Event.ns1_ElectionControl.ns1_EventIdentifier.IdNumber==Event_Id):
				Event_Exist=True
				for Election in Event.ns1_Election:
					for Contest in Election.ns1_Contest:
						for PollingPlace in Contest.ns1_PollingPlace:
							if PollingPlace.IdNumber==Polling_Place_ID:
								Poll_Exist=True
								Event_Name=Event.ns1_ElectionControl.ns1_EventIdentifier.ns1_EventName.PCDATA
								Election_Name=Event.ns1_ElectionControl.ns1_ElectionIdentifier.ns1_ElectionName.PCDATA
                                                                Election_Start_Date=Event.ns1_EventDate.ns1_Start.PCDATA
								Election_End_Date=Event.ns1_EventDate.ns1_End.PCDATA
								Polling_Place_Name=PollingPlace.ns1_PhysicalLocation.ns1_PlaceName.PCDATA
                                                                return Event_Name, Election_Name, Election_Start_Date, Election_End_Date, Polling_Place_Name
		#
		if (Event_Exist==False):
			return 0, 'Error!! The Event ID does not match any event in ElectionEvent.xml file, machine exit !'
		elif (Poll_Exist==False):
			return 0, 'Error!! The Polling Place ID does not match any poll in ElectionEvent.xml file, machine exit !'


	def get_Option_Information(self,Ballot_Identifier,Option_Identifier,writein=False):
		if len(Option_Identifier)!=8:
			error='Error (104)!! Bad parameter size. The size of option ID, which used in aget_Option_Information, is not equal to 8 characters!'
			self.add_log(error)
			return 0,error
		#
		Event_ID=Option_Identifier[0:2]
		Election_ID=Option_Identifier[2:4]
		Contest_ID=Option_Identifier[4:6]
		Option_ID=Option_Identifier[6:8]
		if Option_ID=='00': #this is a writein option
			writein=True
		Ballot_Exist=False
		Election_Exist=False
		Contest_Exist=False
		Option_Exist=False
		if (self.Ballot.ns1_Ballots.ns1_EventIdentifier.IdNumber!=Event_ID):
			error='Error (109)!! The Event ID specified in load_ballot function does not match the event in the Ballot.xml file, machine must exit !'
			self.add_log(error)
			return 0, error
		#
		for Balt in self.Ballot.ns1_Ballots.ns1_Ballot:
			if (Balt.ns1_BallotIdentifier.IdNumber==Ballot_Identifier):
				Ballot_Exist=True
				for Election in Balt.ns1_Election:
					if (Election.ns1_ElectionIdentifier.IdNumber==Election_ID):
						Election_Exist=True
						for Cont in Election.ns1_Contest:
							if Cont.ns1_ContestIdentifier.IdNumber==Contest_ID:
								Contest_Exist=True
								Election_Name=Election.ns1_ElectionIdentifier.ns1_ElectionName.PCDATA
								Contest_Name=Cont.ns1_ContestIdentifier.ns1_ContestName.PCDATA
								if (writein):
									Option_Name='Writein'
									Option_Type='WriteinCandidateName'
									return Election_Name, Contest_Name, Option_Name, Option_Type
								for Option in children(Cont.ns1_BallotChoices):
									if 'Candidate' in str(Option):
										if (Option.ns1_CandidateIdentifier.IdNumber==Option_ID):
											Option_Exist=True
											Option_Type='CandidateIdentifier'
											Option_Name=Option.ns1_CandidateIdentifier.ns1_CandidateName.PCDATA
									if 'Affiliation' in str(Option):
										if (Option.ns1_AffiliationIdentifier.IdNumber==Option_ID):
											Option_Exist=True
											Option_Type='AffiliationIdentifier'
											Option_Name=Option.ns1_AffiliationIdentifier.ns1_RegisteredName.PCDATA
                                                                        if 'ReferendumOptionIdentifier' in str(Option):
										if (Option.IdNumber==Option_ID):
											Option_Exist=True
											Option_Type='ReferendumOptionIdentifier'
											Option_Name=Option.PCDATA
                                                                        if Option_Exist==True:
										return Election_Name, Contest_Name, Option_Name, Option_Type
										
		# if ballot ID does not exist
		if (Ballot_Exist==False):
			error='Error (110)!! The Ballot ID specified in load_ballot function does not match any ballot identifier in the Ballot.xml file, machine must exit !'
			self.add_log(error)
			return 0, error
		elif (Election_Exist==False or Contest_Exist==False or Option_Exist==False):
			error='Error (120)!! The Option ID ('+str(Option_Identifier)+') does not match any Option in the Ballot.xml file!'
			self.add_log(error)
			return 0, error

	def get_Contest_Information(self,Ballot_ID,contest_ID):
		"""
		This functions returns contest information
		"""
		if len(contest_ID)!=6:
			error='Error (104)!! Bad parameter size. The size of contest ID, which used in get_Contest_Information function, is not equal to 8 characters!'
			self.add_log(error)
			return 0,error

		Event_ID=contest_ID[0:2]
		Election_ID=contest_ID[2:4]
		Contest_ID=contest_ID[4:6]
		#
		Ballot_Exist=False
		Election_Exist=False
		Contest_Exist=False
		if (self.Ballot.ns1_Ballots.ns1_EventIdentifier.IdNumber!=Event_ID):
			error='Error (109)!! The Event ID specified in load_ballot function does not match the event in the Ballot.xml file, machine must exit !'
			self.add_log(error)
			return 0, error
		#
		for Balt in self.Ballot.ns1_Ballots.ns1_Ballot:
			if (Balt.ns1_BallotIdentifier.IdNumber==Ballot_ID):
				Ballot_Exist=True
				for Election in Balt.ns1_Election:
					if (Election.ns1_ElectionIdentifier.IdNumber==Election_ID):
						Election_Exist=True
						for Cont in Election.ns1_Contest:
							if Cont.ns1_ContestIdentifier.IdNumber==Contest_ID:
								Contest_Exist=True
								Election_Name=Election.ns1_ElectionIdentifier.ns1_ElectionName.PCDATA
								Contest_Name=Cont.ns1_ContestIdentifier.ns1_ContestName.PCDATA
								ElectionType=Cont.ns1_ElectionType.PCDATA
								MaxVotes=Cont.ns1_MaxVotes.PCDATA
								MinVotes=Cont.ns1_MinVotes.PCDATA
								MaxWriteIn=Cont.ns1_MaxWriteIn.PCDATA
								return Election_Name, Contest_Name, ElectionType, MaxVotes, MinVotes, MaxWriteIn
			#if ballot ID does not exist
			if (Ballot_Exist==False): 
				error='Error (110)!! The Ballot ID specified in get_Contest_Information function does not match any ballot identifier in the Ballot.xml file, machine must exit !'
				self.add_log(error)
				return 0, error
			elif (Election_Exist==False or Contest_Exist==False):
				error='Error (120)!! The Contest ID ('+str(contest_ID)+') does not match any contest identifier in the Ballot.xml file!'
				self.add_log(error)
				return 0, error


	def toggle_Poll(self,VMSetting_ID,status):
		"""
		This function either to connect or close the connection with DRE machine
		In both cases, it extract a set of information that related to the VM setting identifier
		and return them (Event_Name, Election_Name, Election_Start_Date, Election_End_Date, Polling_Place_Name, Event_Id, Polling_Station_ID, Ballot_ID)
		also, it modifies the self.level_flag instance to indicate that the connection is established or not.
		"""
		#check the VMSetting_ID, and retrieve related information if it is exist
		info = self.get_VMSetting_Information(VMSetting_ID)
		if info[0] == 0:
			return info
		else:
			Event_Id = info[0] #set event identifier
			Polling_Place_ID = info[1] # set polling place identifier
			Polling_Station_ID = info[2]  #set polling station identifier
			Ballot_ID = info [3] #set ballot identifier
			#check event information that related to the polling place
			Event = self.get_Event_Information(Event_Id, Polling_Place_ID) #from Event_Id and Polling_Place_ID get other information
			if Event[0] == 0:
				return Event
			else: # set event information
				Event_Name = Event[0] #set event name
				Election_Name = Event[1] #set election name
				Election_Start_Date = Event[2] #set start date
				Election_End_Date = Event[3] #set end date
				Polling_Place_Name = Event[4] #set polling place name
				if status=='connect':
					#set class instances
					self.Ballot_ID=Ballot_ID
					self.Event_ID=Event_Id
					self.Polling_Place_ID=Polling_Place_ID
					self.Polling_Station_ID=Polling_Station_ID
					self.Event_Name=Event_Name
					self.Election_Name=Election_Name
					self.Election_Start_Date=Election_Start_Date
					self.Election_End_Date=Election_End_Date
					self.Polling_Place_Name=Polling_Place_Name
					self.VMSetting_ID=VMSetting_ID
					# set level to be connected
					self.level_flag='10'
					return Event_Name, Election_Name, Election_Start_Date, Election_End_Date, Polling_Place_Name, Event_Id, Polling_Station_ID, Ballot_ID
				elif status=='close':
					if VMSetting_ID!=self.VMSetting_ID:
						error='Error (107)!! Bad VMSettingID. The VMSettingID used to open the poll is not similar to the one used to close it!'
						self.add_log(error)
						return 0,error
					#clear class instances
					self.Ballot_ID=''
					self.Event_ID=''
					self.Polling_Place_ID=''
					self.Polling_Station_ID=''
					self.Event_Name=''
					self.Election_Name=''
					self.Election_Start_Date=''
					self.Election_End_Date=''
					self.Polling_Place_Name=''
					# set level to be connected
					self.level_flag='00'
					return Event_Name, Election_Name, Election_Start_Date, Election_End_Date, Polling_Place_Name, Event_Id, Polling_Station_ID, Ballot_ID
				else:
					error='Error (120)!! General Error. Bad status for the toggle_Poll command!'
					self.add_log(error)
					return 0,error

	def add_selected_option(self,option_ID,writein=None):
		"""
		This functions adds option ID to a temp buffer (vote_options list), if writein is provided then the writein will be added to
		a temp buffer also (vote_options_writein list)
		"""
		if len(option_ID)!=8:
			error='Error (104)!! Bad parameter size. The size of option ID, which used in add_selection_option function, is not equal to 8 characters!'
			self.add_log(error)
			return 0,error
		count=0
		for vote in self.vote_options: #check if the selected option already exists in the previously selected options
			count=count+vote.count(str(option_ID))
		if(count>=1):
			error='Error (120)!! Unexpected behavious!! Selected option ID '+str(option_ID)+' is already in the vote_options list!'
			self.add_log(error)
			return 0,error
		else:
			Contest_ID=option_ID[0:6]
			Contest_Exist=False
			for contest in self.contests:
				if contest==Contest_ID:
					Contest_Exist=True
					if (option_ID[6:8]!='00'): #if the option_ID is not writein, then add option_ID to buffer and get back option information
						info=self.get_Option_Information(self.Ballot_ID,option_ID)
						if (info[0]==0):
							return info
						index=self.contests.index(contest)
						self.vote_options[index].append(option_ID) #append option_ID to the buffer
						Option_Name=info[2]
						Writein_Text=None
					#
					if(option_ID[6:8]=='00'):#if the option_ID is a writein, then add the option_ID to buffer and return contest information
						info=self.get_Contest_Information(self.Ballot_ID,option_ID[0:6])
						if (info[0]==0):
							return info
						index=self.contests.index(contest)
						self.vote_options[index].append(option_ID)#append option_ID to the buffer
						self.vote_options_writein[index]=writein#append writein to the buffer
						Option_Name='Writein'
						Writein_Text=writein
					Election_Name=info[0]
					Contest_Name=info[1]
			#
			if Contest_Exist==False:
				error='Error (120)!! The option_ID ('+str(option_ID)+') does not match any option identifier in the Ballot.xml file!'
				self.add_log(error)
				return 0, error
			else:
				return Election_Name, Contest_Name, Option_Name, Writein_Text



	def remove_selected_option(self,option_ID):
		if len(option_ID)!=8:
			error='Error (104)!! Bad parameter size. The size of option ID, which used in add_selection_option function, is not equal to 8 characters!'
			self.add_log(error)
			return 0,error
		count=0
		for vote in self.vote_options: #check if the selected option already exists in the previously selected options
			count=count+vote.count(str(option_ID))
		if(count==0):
			error='Error (120)!! Unexpected behavious!! Canceled option ID '+str(option_ID)+' is not selected before!'
			self.add_log(error)
			return 0,error
		else:
			Contest_ID=option_ID[0:6]
                        Contest_Exist=False
			for contest in self.contests:
				if contest==Contest_ID:
					Contest_Exist=True
					index=self.contests.index(contest)
					index_option=self.vote_options[index].index(option_ID)
					self.vote_options[index].pop(index_option) # remove the option ID from selected option ID's list
					if option_ID[6:8]=='00': # it is writein ID, remove the writein from the selected writeins list
						info=self.get_Contest_Information(self.Ballot_ID,Contest_ID)
						if info[0]==0:
							return info
						else:
							Writein_Text=self.vote_options_writein[index]
							Option_Name='Writein'
							self.vote_options_writein[index]='' #remove the writein from the related index
					else: #if it is not writein
						info=self.get_Option_Information(self.Ballot_ID,option_ID)
						if info[0]==0:
							return info
						else:
							Option_Name=str(info[2])
							Writein_Text=None
					#
					Election_Name=str(info[0])
					Contest_Name=str(info[1])
			if Contest_Exist==False:
				error='Error (120)!! The option ID ('+str(option_ID)+') does not match any option identifier in the Ballot.xml file!'
				self.add_log(error)
				return 0, error
			else:
				return Election_Name, Contest_Name, Option_Name, Writein_Text

	def reset_contest(self,Contest_ID):
		if len(Contest_ID)!=6:
			error='Error (104)!! Bad parameter size. The size of contest ID, which used in reset_contest function, is not equal to 6 characters!'
			self.add_log(error)
			return 0,error
		info=self.get_Contest_Information(self.Ballot_ID,Contest_ID)
		if (info[0]==0):
			return info
		Contest_Exist=False
		Election_Name=str(info[0])
		Contest_Name=str(info[1])
		for contest in self.contests:
			if contest==Contest_ID:
				Contest_Exist=True
				index=self.contests.index(contest)
				self.vote_options[index]=[] #reset contest slections in temp buffer
				self.vote_options_writein[index]='' #reset contest writein in temp buffer
				#
		if Contest_Exist==False:
			error='Error (120)!! The Contest_ID ('+str(Contest_ID)+') does not match any contest identifier in the Ballot.xml file!'
			self.add_log(error)
			return 0, error
		else:
			return Election_Name, Contest_Name


	def review(self):
		Vote_Exists=False
		Election=''
		Contest=''
		vote_summary='Your vote details: \n'
		for contest in self.contests:
			index_contest=self.contests.index(contest)
			if len(self.vote_options[index_contest]) !=0:
				contest_info=self.get_Contest_Information(self.Ballot_ID, contest)
				if (contest_info!=0):
					if Election!=contest_info[0] and Contest!=contest_info[1]:
					    vote_summary+='Election: ' +contest_info[0]+ ' Contest: '+contest_info[1] + '\n'
					if Election==contest_info[0] and Contest!=contest_info[1]:
					    vote_summary+=str('').ljust(len('Election: ')) +str('').ljust(len(contest_info[0]))+ ' Contest : '+contest_info[1] + '\n'
					for vote in self.vote_options[index_contest]:
						Vote_Exists=True
						#index_vote=self.vote_options[index_contest].index(vote)
						if vote[6:8]=='00': # if vote option ID for writein
							vote_summary+=str('').ljust(len('Election: ')) +str('').ljust(len(contest_info[0]))+str('').ljust(len(' Contest: '))+'You have selected the write in : ' + self.vote_options_writein[index_contest] + '\n'
						else: # if it is not writein
							option_info= self.get_Option_Information(self.Ballot_ID,vote)
							if option_info[0]!=0:
								vote_summary+=str('').ljust(len('Election: ')) +str('').ljust(len(contest_info[0]))+str('').ljust(len(' Contest: '))+'You have selected : ' + option_info[2] +  '\n'
							else:
								vote_summary+=str('').ljust(len('Election: ')) +str('').ljust(len(contest_info[0]))+str('').ljust(len(' Contest: ')) +option_info[1]
					Election=contest_info[0]
					Contest=contest_info[1]

		if Vote_Exists==False:
			vote_summary+=	'	    You did not have any selection! \n'
		return vote_summary


	def cast(self,vote_ID,actor,reason=None):
		vote_ID=str(vote_ID)
		vote_ID=vote_ID.zfill(8)
		#this block solve if there was conflict between the opening and closing cast session vote identifier
		#only one exception, if the vote_ID='00000000' and the actor is 'officer', this means that the cast forced
		#by the officer, and the cast vote will takes the vote_ID used to open this session
		#
		if vote_ID!=self._Vote_ID:
			if actor=='voter' or (actor=='officer' and vote_ID!='00000000'):
				self.contests=[]
				self.vote_options=[]
				self.vote_options_writein=[]
				error='Error (110)!! The vote ID used to cast this session ('+str(vote_ID)+') is different than the vote ID used in session opening ('+str(self._Vote_ID)+')! This may means that no one of them are saved.'
				self.add_log(error)
				self.level_flag='10'
				return 0, error
			if actor=='officer' and vote_ID=='00000000':
				vote_ID==self._Vote_ID
				self.add_log('Error (110)!! Cast vote ID ('+str(self._Vote_ID)+') considered as the same one that used in opening the vote cast session as the cast done by officer with vote_ID=00000000 \n')
		#
		xml= self.emlBallot()
		xmlfile = str(vote_ID) + '.xml'
		file = open('vm_cast_votes/'+xmlfile, 'w')
		file.write(xml[1])
		file.close()
		self.contests=[]
		self.vote_options=[]
		self.vote_options_writein=[]
		self._Vote_ID=0
		message= 'message: the Vote ('+ vote_ID +') cast by the '+ actor +' successfuly.'
		if reason!= None:
			reason_text= self.get_Reason(reason)
			message +=reason_text[1] +'\n'
			self.add_log('Error (111)!! Vote cast by the officer. The reason is: '+reason_text[1]+' \n')
		else:
			message +='\n'
		self.level_flag='10'
		return 1, message


	def cancel_vote_officer(self,vote_ID,reason=None):
		message=""
		if vote_ID!= self._Vote_ID and vote_ID!='00000000':
			message+='Error (112)!! The wrong vote Canceled! The canceled vote identifier ('+vote_ID+') is not similar with the vote identifier that used to open the vote cast session('+self._Vote_ID+').\n'
		if vote_ID!= self._Vote_ID and vote_ID=='00000000':
			message+='Error (110)!! Conflict vote identifiers! The vote has been forced to be canceled by the officer \n'

		self.contests=[]
		self.vote_options=[]
		self.vote_options_writein=[]
		self._Vote_ID=0
		message+= 'Message: the Vote ('+ vote_ID +') canceled by the officer successfuly.'
		if reason!= None:
			reason_text= self.get_Reason(reason)
			message +='The reason is '+ reason_text[1] +'\n'
		else:
			message +='No reason available \n'
		self.add_log('Error (111)!!'+ message)
		self.level_flag='10'
		return 1, message

	
	def emlBallot(self):
		
		now = datetime.datetime.now()
		month=str(now.month)
		month=month.zfill(2)
		day=str(now.day)
		day=day.zfill(2)
		xml = ""
		xml += '<?xml version="1.0" encoding="UTF-8"?>\n'
		xml += '<ns1:EML Id="440" SchemaVersion="7.0" xmlns:ns1="urn:oasis:names:tc:evs:schema:eml">\n'
		xml += '	<ns1:EMLHeader>\n'
		xml += '		<ns1:TransactionId>0</ns1:TransactionId>\n'
		xml += '		<ns1:OfficialStatusDetail>\n'
		xml += '			<ns1:OfficialStatus>apporved</ns1:OfficialStatus>\n'
		xml += '			<ns1:StatusDate>'+str(now.year)+'-'+month+'-'+day+'</ns1:StatusDate>\n'
		xml += '		</ns1:OfficialStatusDetail>\n'
		xml += '	</ns1:EMLHeader>\n'
		xml += '	<ns1:CastVote>\n'
		xml += '		<ns1:EventIdentifier IdNumber="'+ self.Event_ID+'"/>\n'
		for cont in self.contests:
			if (cont[0:2]!=self.Event_ID):
				continue
			index_contest=self.contests.index(cont)
			for vote in self.vote_options[index_contest]:
				#index_vote=self.vote_options[index_contest].index(vote)
				writein= self.vote_options_writein[index_contest]
				xml += '		<ns1:Election>\n'
				xml += '			<ns1:ElectionIdentifier IdNumber="'+cont[2:4]+'"/>\n'
				xml += '			<ns1:Contest>\n'
				xml += '				<ns1:ContestIdentifier IdNumber="'+cont[4:6]+'"/>\n'
				if vote[6:8]=='00':
					xml += '				<ns1:Selection>\n'
					xml += '					<ns1:WriteinCandidateName>'+writein+'</ns1:WriteinCandidateName>\n'
					xml += '				</ns1:Selection>\n'
				else:
					option = self.get_Option_Information(self.Ballot_ID,vote)
					if option[3]=='CandidateIdentifier':
						xml += '				<ns1:Selection>\n'
						xml += '					<ns1:CandidateIdentifier IdNumber="'+vote[6:8]+'"/>\n'
						xml += '				</ns1:Selection>\n'
					if option[3]=='AffiliationIdentifier':
						xml += '				<ns1:Selection>\n'
						xml += '					<ns1:AffiliationIdentifier IdNumber="'+vote[6:8]+'">\n'
						xml += '						<ns1:RegisteredName/>\n'
						xml += '					</ns1:AffiliationIdentifier>\n'
						xml += '				</ns1:Selection>\n'
					if option[3]=='ReferendumOptionIdentifier':
						xml += '				<ns1:Selection>\n'
						xml += '					<ns1:ReferendumOptionIdentifier IdNumber="'+vote[6:8]+'"/>\n'
						xml += '				</ns1:Selection>\n'
				xml += '			</ns1:Contest>\n'
				xml += '		</ns1:Election>\n'
		#
		xml += '		<ns1:BallotIdentifier IdNumber="'+self.Ballot_ID+'"/>\n'
		xml += '		<ns1:AuditInformation>\n'
		xml += '			<ns1:ProcessingUnits>\n'
		xml += '				<ns1:OriginatingDevice Role="">\n'
		xml += '					<ns1:Name>DRE</ns1:Name>\n'
		xml += '					<ns1:IdValue>'+self.Polling_Place_ID+self.Polling_Station_ID+'</ns1:IdValue>\n'
		xml += '				</ns1:OriginatingDevice>\n'
		xml += '				<ns1:Other Type="VM" Role="">\n'
		xml += '					<ns1:Name>OVVM Verification Module</ns1:Name>\n'
		xml += '					<ns1:IdValue>'+self.Vm_ID+'</ns1:IdValue>\n'
		xml += '				</ns1:Other>\n'
		xml += '			</ns1:ProcessingUnits>\n'
		xml += '		</ns1:AuditInformation>\n'
		xml += '	</ns1:CastVote>\n'
		xml += '</ns1:EML>\n'
		return 1,xml


	def load_ballot(self,Ballot_ID,Event_ID):
		"""
		"""
		Ballot_Exist=False
		#check Event Id in the ballot
		if (self.Ballot.ns1_Ballots.ns1_EventIdentifier.IdNumber!=Event_ID):
			error='Error (109)!! The Event ID specified in load_ballot function does not match the event in the Ballot.xml file, machine must exit !'
			self.add_log(error)
			return 0, error
		#
		#check Ballot Id in the ballot
		for Balt in self.Ballot.ns1_Ballots.ns1_Ballot:
			if (Balt.ns1_BallotIdentifier.IdNumber==Ballot_ID): #ballot ID exist
				Ballot_Exist=True
				for Election in Balt.ns1_Election:
					Election_ID = str(Election.ns1_ElectionIdentifier.IdNumber)
					for Cont in Election.ns1_Contest:
						Contest_ID = str(Cont.ns1_ContestIdentifier.IdNumber)
						Contest_ID= Event_ID + Election_ID + Contest_ID
						self.contests.append(Contest_ID) #append contest identifire to the contests list
						self.vote_options.append([]) #append empty array corresonting to the contest votes to the vote_options list
						self.vote_options_writein.append('')#append empty string corresonting to the contest writein to the vote_options_writein list

		if (Ballot_Exist==False): #if ballot ID does not exist
			error='Error (110)!! The Ballot ID specified in load_ballot function does not match any ballot identifier in the Ballot.xml file, machine must exit !'
			self.add_log(error)
			return 0, error
		else:
			self.Ballot_ID=Ballot_ID #set ballot ID tp a class instant
			return 1, 'message: Ballot loaded successfuly.'


	def activate_vote(self,vote_ID):
		vote_ID=str(vote_ID)#convert vote id to string if it is not
		self._Vote_ID=vote_ID.zfill(8)
		for file in os.listdir('vm_cast_votes'):
			file=str(file)
			if file[:8]==self._Vote_ID:
				error='Error (108)!! Bad vote ID. The Vote ID ('+vote_ID+') is used before!!'
				self.add_log(error)
				return 0, error
		load_ballot=self.load_ballot(self.Ballot_ID,self.Event_ID) #to load ballot contest and prepare empty vote_options and vote_options_writein lists
		if load_ballot[0]==0:
			return load_ballot
		else:
			self.level_flag='11'
			return 1,'Message: Cast vote session activated successfuly.'

	def votes_summary(self,VMSetting_ID):
		ordered_writein={}
		info = self.get_VMSetting_Information(VMSetting_ID)
		if info[0] == 0:
			return info
		Event_Id = info[0] #set event identifier
		Polling_Place_ID = info[1] # set polling place identifier
		Polling_Station_ID = info[2]  #set polling station identifier
		Ballot_ID = info [3] #set ballot identifier
		Event = self.get_Event_Information(Event_Id, Polling_Place_ID) #from Event_Id and Polling_Place_ID get other information
		if Event[0] == 0:
			return Event
		Event_Name = Event[0] #set event name
		Election_Name = Event[1] #set election name
		#Election_Start_Date = Event[2] #set start date
		#Election_End_Date = Event[3] #set end date
		Polling_Place_Name = Event[4] #set polling place name
		#
		xml_votes_list=[]
		load_ballot=self.load_ballot(Ballot_ID,Event_Id)
		if load_ballot[0]==0:
			return load_ballot
		# initialize empty count lists based on abailable contests in the ballot
		for cont in self.contests:
			index=self.contests.index(cont)
			self.vote_options_writein[index]={}
		#
		for list in self.vote_options:# generates empty votes dictionary
			list_index=self.vote_options.index(list)
			self.vote_options[list_index]={}
		#
		# generalte a list that contains all xml votes
		for file in os.listdir('vm_cast_votes'):
			if file.endswith('.xml'):
				xml_votes_list.append(file)
		# read vote files
		for castvote in xml_votes_list:
			vote_instance =XML_Objectify('vm_cast_votes/'+str(castvote)).make_instance()
			#check if the vote have the same ballot identifier
			if vote_instance.ns1_CastVote.ns1_BallotIdentifier.IdNumber!=Ballot_ID:
				print 'an xml file with not appropriate ballot identifier, will not considered'
				continue
			if vote_instance.ns1_CastVote.ns1_EventIdentifier.IdNumber!=Event_Id:
				print 'an xml file with not appropriate event identifier, will not considered'
				continue
			if vote_instance.ns1_CastVote.ns1_AuditInformation.ns1_ProcessingUnits.ns1_OriginatingDevice.ns1_IdValue.PCDATA !=str(Polling_Place_ID)+str(Polling_Station_ID):
				print vote_instance.ns1_CastVote.ns1_AuditInformation.ns1_ProcessingUnits.ns1_OriginatingDevice.ns1_IdValue.PCDATA,str(Polling_Place_ID)+str(Polling_Station_ID)
				print 'an xml file with not polling place or polling station identifiers, will not considered'
				continue

			else:
				#for Election in vote_instance.ns1_CastVote.ns1_Election:
				for Cont in self.contests:
					votes_order=[]#only used if cont is ordered
					contest_info=self.get_Contest_Information(Ballot_ID, Cont)
					if contest_info[0]==0:
						print 'error in contest'
						continue
					ElectionType=contest_info[2]
					#
					index=self.contests.index(Cont)
					#
                                        #checks if the cast vote has election record or not
                                        Election_record_exist=0
					for Elect in children(vote_instance.ns1_CastVote):
                                            if 'ns1_Election' in str(Elect):
                                                Election_record_exist=1
                                                break
                                        if Election_record_exist==1:
                                            # non ordered
                                            if ElectionType!='ordered': #the type of Cont is not ordered
                                                    for Election in vote_instance.ns1_CastVote.ns1_Election: # check the occurence of cont in the xml
                                                            Contest_ID= str(vote_instance.ns1_CastVote.ns1_EventIdentifier.IdNumber)+str(Election.ns1_ElectionIdentifier.IdNumber)+str(Election.ns1_Contest.ns1_ContestIdentifier.IdNumber)
                                                            if Contest_ID == Cont:
                                                                            for Option in children(Election.ns1_Contest.ns1_Selection):
                                                                                    if 'WriteinCandidateName' in str(Option):
                                                                                            option_id=Contest_ID+'00'
                                                                                    if 'CandidateIdentifier' in str(Option):
                                                                                            option_id=Contest_ID+str(Option.IdNumber)
                                                                                    if 'Affiliation' in str(Option):
                                                                                            option_id=Contest_ID+str(Option.IdNumber)
                                                                                    if 'ReferendumOptionIdentifier' in str(Option):
                                                                                            option_id=Contest_ID+str(Option.IdNumber)
                                                                            #
                                                                            if option_id in self.vote_options[index].keys():
                                                                                    value = int(self.vote_options[index][option_id])+1
                                                                                    self.vote_options[index][option_id]=value
                                                                            else:
                                                                                    self.vote_options[index].update({option_id:1})
                                                                            if option_id[6:8]=='00':
                                                                                    writein= Election.ns1_Contest.ns1_Selection.ns1_WriteinCandidateName.PCDATA
                                                                                    if writein in self.vote_options_writein[index].keys():
                                                                                            value= int(self.vote_options_writein[index][writein])+1
                                                                                            self.vote_options_writein[index][writein]=value
                                                                                    else:
                                                                                            self.vote_options_writein[index].update({writein:1})
                                                    continue # continue and read another Cont from  self.contests
                                            # ordered
                                            if ElectionType=='ordered': #the type of Cont is ordered
                                                    #
                                                    for Election in vote_instance.ns1_CastVote.ns1_Election:# check the occurence of cont in the xml
                                                            Contest_ID= str(vote_instance.ns1_CastVote.ns1_EventIdentifier.IdNumber)+str(Election.ns1_ElectionIdentifier.IdNumber)+str(Election.ns1_Contest.ns1_ContestIdentifier.IdNumber)
							    if Contest_ID == Cont:
                                                                    for Option in children(Election.ns1_Contest.ns1_Selection):
                                                                            if 'WriteinCandidateName' in str(Option):
                                                                                    option_id=Contest_ID+'00'
                                                                                    writein=Election.ns1_Contest.ns1_Selection.ns1_WriteinCandidateName.PCDATA
                                                                            if 'CandidateIdentifier' in str(Option):
                                                                                    option_id=Contest_ID+str(Option.IdNumber)
                                                                            if 'Affiliation' in str(Option):
                                                                                    option_id=Contest_ID+str(Option.IdNumber)
                                                                            if 'ReferendumOptionIdentifier' in str(Option):
                                                                                    option_id=Contest_ID+str(Option.IdNumber)
                                                                            votes_order.append(option_id) #add option to the vote order temp array since it is an ordered contest
                                                    #
						    for option_id in votes_order:
                                                            option_index=votes_order.index(option_id)
                                                            if option_id in self.vote_options[index].keys():
                                                                    if option_id[6:8]!='00':
                                                                            if int(option_index) in self.vote_options[index][option_id].keys():
                                                                                    value = int(self.vote_options[index][option_id][option_index])+1
                                                                                    self.vote_options[index][option_id][option_index]=value
                                                                            else:
                                                                                    self.vote_options[index][option_id].update({option_index:'1'})
                                                                    if option_id[6:8]=='00':
                                                                            if Cont in ordered_writein.keys():
                                                                                    if writein in ordered_writein[Cont].keys():
                                                                                            if int(option_index) in ordered_writein[Cont][writein].keys():
                                                                                                    value = int(ordered_writein[Cont][writein][option_index])+1
                                                                                                    ordered_writein[Cont][writein][option_index]=str(value)
                                                                                            else:
                                                                                                    ordered_writein[Cont][writein].update({option_index:1})
                                                                                    else:
                                                                                            ordered_writein[Cont].update({writein:{option_index:1}})
                                                                            else:
										    ordered_writein.update({Cont:{writein:{option_index:1}}})

                                                            else:
                                                                    if option_id[6:8]!='00':
                                                                            self.vote_options[index].update({option_id:{option_index:1}})
                                                                    if option_id[6:8]=='00':
                                                                            self.vote_options[index].update({option_id:{option_index:1}})
                                                                            ordered_writein.update({Cont:{writein:{option_index:1}}})
		#
		#
		summary='------------------------------- \n'
		summary+='Event:'+str(Event_Name)+', Election Name:'+ str(Election_Name) +'\n'
		summary+='Polling Place:'+str(Polling_Place_Name)+', Machine ID:'+str(Polling_Station_ID)+', VM ID: '+str(self.Vm_ID)+', Ballot ID: '+str(Ballot_ID)+'\n'
		summary+='Date & Time:'+ str(datetime.datetime.now())+'\n'
		summary+='------------------------------- \n'
		summary_header_length=len(summary)
		for Cont in self.contests:
			contest_info=self.get_Contest_Information(Ballot_ID, Cont)
			if contest_info[0]==0:
				print 'error in contest'
				continue
			ElectionName=contest_info[0]
			ContestName=contest_info[1]
			ElectionType=contest_info[2]
			MaxVotes=contest_info[3]
			#
			index=self.contests.index(Cont)
			#
			# non ordered
			if ElectionType!='ordered': #the type of Cont is not ordered
				if len(self.vote_options[index])!=0:
					writein=False
					writein_index=False
					summary+='\n'
                                        summary+='___________________________________\n'
                                        summary+=ElectionName+', '+ContestName+' :\n'
					for voteID in self.vote_options[index]:
						count=self.vote_options[index][voteID]
						option_info=self.get_Option_Information(Ballot_ID, voteID)
						if option_info[2]=='Writein':
							writein=True
							writein_index=index
							continue
						else:
							summary+= '		'+option_info[2]+' got ('+str(count)+') votes. \n'
					if writein:
						summary+='		Writein: \n'
						for writein_text in self.vote_options_writein[writein_index]:
							wr_count=self.vote_options_writein[writein_index][writein_text]
							summary+='			'+writein_text+' got ('+str(wr_count)+') votes. \n'
			#
			# ordered
			if ElectionType=='ordered': #the type of Cont is ordered
				if len(self.vote_options[index])!=0:
					writein=False
					writein_index=False
					summary+=ElectionName+', '+ContestName+' :\n'
					for voteID in self.vote_options[index]:
						option_info=self.get_Option_Information(Ballot_ID, voteID)
						if option_info[2]=='Writein':
							writein=True
							writein_index=index
							continue
						else:
							summary+='		'+option_info[2]+' got:\n'
							for rank in self.vote_options[index][voteID]:
								summary+= '			order '+str(int(rank)+1)+ ' for ('+str(self.vote_options[index][voteID][rank])+') times,\n '
							#summary+='\n'
					if writein:
						summary+='		Writein: \n'
						for wr_cont_ID in ordered_writein:
							if wr_cont_ID == Cont:
								for writein_text in ordered_writein[Cont]:
									summary+='			'+writein_text+' got:\n'
									for wr_rank in ordered_writein[Cont][writein_text]:
										summary+='				order '+str(int(wr_rank)+1)+ ' for ('+str(ordered_writein[Cont][writein_text][wr_rank])+') times,\n '

		summary_total_length=len(summary)
		if summary_header_length==summary_total_length:
			summary+='There are no cast votes for this machine.'
		self.contests=[]
		self.vote_options=[]
		self.vote_options_writein=[]
		ordered_writein={}


		return 1,summary,'report generated successfuly'#,ordered_writein


















































