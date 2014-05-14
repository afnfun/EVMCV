from gnosis.xml.objectify import *
import datetime
import os
import sys

class OVVM_DRE():
	def __init__(self):
		self.VMS =XML_Objectify('EML_files/VmSettings710.xml').make_instance() # get the VMSetting info
		#check the status of the VmSettings710.xml
		if (self.VMS.ns1_EMLHeader.ns1_OfficialStatusDetail.ns1_OfficialStatus.PCDATA != 'approved'):
				all_log('error!! VmSettings710.xml is not approved, Contact election official')
				sys.exit("error!! VmSettings710.xml is not approved, Contact election official")
		self.Sequence=0
		self.commands={'calibrate':'0','connect':'1','close':'2','report':'3','activate':'4','votercast':'5','officercast':'6','officercancel':'7','select':'8','cancel':'9','writein':'A','reset':'B','review':'C','reason':'D'}

	#
	def add_log(self,text):
		"""
		This function add the text parameter to the log file (vm_log/vm_log.txt).
		"""
		# create log directory if it is not exists
		if not os.path.exists('OVVM_DRE_log'):
			os.makedirs('OVVM_DRE_log')
		log = open (os.path.join('OVVM_DRE_log','OVVM_DRE_log.txt'),'a+')
		time = datetime.datetime.now()
		log.write(str(time)+' : '+text+' \n')
		log.close()
		return True
	#
	def map_DRE_option_code(self, DRE_option_code):
		for VMSet in self.VMS.ns1_options.ns1_option:
			if DRE_option_code == str(VMSet.DRE_code):
				return VMSet.OVVM_code
		self.add_log('Error !! Given DRE option code does not match any OVVM option code in the VMSetting710.xml file')
		return 0, 'Error !! Given DRE option code does not match any OVVM option code in the VMSetting710.xml file'

	def get_VM_Setting_ID(self,DRE_Evend_ID, Poll_ID, Machine_ID):
		#get the VMSetting ID for this DRE from the VMSetting.xml file
		Setting_ID=None
		Event=None
		for VMSet in self.VMS.ns1_VmSettings:
			if (VMSet.ns1_EventIdentifier.DRE_ID == DRE_Evend_ID):
				Event=DRE_Evend_ID
				for Set in VMSet.ns1_Settings:
					#check if the polling place ID and Machine ID matches with VMSettings records
					if (Set.ns1_PollingPlaceID.PCDATA == Poll_ID and Set.ns1_PollingStationID.PCDATA==Machine_ID):
						Setting_ID=Set.IdNumber
						break
		#
		#check election identifiers in the VMSetting.xml file
		if (Event==None):
			self.add_log('Error!! Event identifiers for this DRE is not included in the VMSetting.xml file, machine exit !')
			sys.exit("Error!! Event identifiers for this DRE is not included in the VMSetting.xml, please contact election official. Machine exit!!")
		elif (Setting_ID==None):
			self.add_log('Error!! There is no VMSetting identifiers matches with the DRE identifiers, machine exit !')
			sys.exit("Error!! There is no VMSetting identifiers matches with the DRE identifiers, please contact election official. Machine exit!!")
		else:
			return Setting_ID
		#

	def get_verification_message(self,command,parameter,text=None):
		message=''
		if command not in self.commands:
			self.add_log('Error !! Bad command used in the get_verification_message function.')
			sys.exit('Error !! Bad command used in the get_verification_message function.')
		#convert the sequence to Hex character
		if self.Sequence !=0:
			SequenceHex=str(hex(self.Sequence).rstrip("L").lstrip("0x")).upper()#Convert the Sequence to single hex character
		else:
			SequenceHex='0'
		#
		if (command =='calibrate' 
		or command =='connect' 
		or command =='close' 
		or command =='report' 
		or command =='activate' 
		or command =='votercast' 
		or command =='officercast' 
		or command =='officercancel' 
		or command =='review' 
		or command =='reason'):
			if len(parameter) !=8:
				self.add_log('Error !! Bad parameter size (not equal to 8 characters) used in the get_verification_message function.')
				sys.exit('Error !!  Bad parameter size (not equal to 8 characters) used in the get_verification_message function.')
			#
			message= str(self.commands[command]) +str(SequenceHex)+ str(parameter)
			if (command == 'calibrate' or command=='officercancel' or command=='officercast') and text!=None  :
				message=str(self.commands[command]) + str(SequenceHex)+str(parameter) + ':' + str(text) + ','
			else:
				message=str(self.commands[command]) + str(SequenceHex)+ str(parameter) + ','

		if (command=='select'
		or command=='cancel'
		or command=='writein'
		or command=='reset'):
			parameter=self.map_DRE_option_code(parameter)
			if parameter[0]==0:
				self.add_log('Error !! Bad parameter (DRE Option identifire does not have related OVVM identifire int the VMSetting710.xml) used in the get_verification_message function.')
				sys.exit('Error !!  Bad parameter (DRE Option identifire does not have related OVVM identifire int the VMSetting710.xml) used in the get_verification_message function.')
			if (command=='writein'):
				if text == None:
					self.add_log('Error !! Missing parameter in the get_verification_message function. The writein command is not provided with text.')
					return 0, 'Error !! Missing parameter in the get_verification_message function. The writein command is not provided with text.'
				else:
					message=str(self.commands[command]) + str(SequenceHex)+str(parameter) + ':' + str(text) + ','
			else:
				message=str(self.commands[command]) + str(SequenceHex) + str(parameter) + ','

		self.Sequence=self.Sequence+1
		if self.Sequence==16: self.Sequence=0
		return message

















































