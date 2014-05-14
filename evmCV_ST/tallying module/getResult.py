import os
from gnosis.xml.objectify import *
from collections import *
import datetime

class getResult():
	def __init__(self):
		self.contests = []
		self.selected_options=[]
		self.writein=[]
		self.coords = XML_Objectify('configuration_files/coords.xml').make_instance()
		self.Ballot =XML_Objectify('EML_files/Ballots410.xml').make_instance()
		self.Election_Event =XML_Objectify('EML_files/ElectionEvent110.xml').make_instance()
		#self.Options_List =XML_Objectify('EML_files/OptionsList630.xml').make_instance()

	def add_log(self,text):
		"""
		This function add the text parameter to the log file (vm_log/vm_log.txt).
		"""
		log = open (os.path.join('result_log','result_log.txt'),'a+')
		time = datetime.datetime.now()
		log.write(str(time)+' : '+text+' \n')
		log.close()
		return True

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
								Event_Name=str(Event.ns1_ElectionControl.ns1_EventIdentifier.ns1_EventName.PCDATA)
								Election_Name=str(Event.ns1_ElectionControl.ns1_ElectionIdentifier.ns1_ElectionName.PCDATA)
								Election_Start_Date=str(Event.ns1_EventDate.ns1_Start.PCDATA)
								Election_End_Date=str(Event.ns1_EventDate.ns1_End.PCDATA)
								Polling_Place_Name=str(PollingPlace.ns1_PhysicalLocation.ns1_PlaceName.PCDATA)
								return Event_Name, Election_Name, Election_Start_Date, Election_End_Date, Polling_Place_Name
		#
		if (Event_Exist==False):
			return 0, 'Error!! The Event ID does not match any event in ElectionEvent.xml file, machine exit !'
		elif (Poll_Exist==False):
			return 0, 'Error!! The Polling Place ID does not match any poll in ElectionEvent.xml file, machine exit !'


	def get_Option_Information(self,Ballot_Identifier,Option_Identifier,writein=False):
		if len(Option_Identifier)!=8:
			error='Error !! Bad parameter size. The size of option ID, which used in aget_Option_Information, is not equal to 8 characters!'
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
			error='Error !! The Event ID specified in load_ballot function does not match the event in the Ballot.xml file, machine must exit !'
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
								Election_Name=str(Election.ns1_ElectionIdentifier.ns1_ElectionName.PCDATA)
								Contest_Name=str(Cont.ns1_ContestIdentifier.ns1_ContestName.PCDATA)
								if (writein):
									Option_Name='Writein'
									Option_Type='WriteinCandidateName'
									return Election_Name, Contest_Name, Option_Name, Option_Type
								for Option in children(Cont.ns1_BallotChoices):
									if 'Candidate' in str(Option):
										if (Option.ns1_CandidateIdentifier.IdNumber==Option_ID):
											Option_Exist=True
											Option_Type='CandidateIdentifier'
											Option_Name=str(Option.ns1_CandidateIdentifier.ns1_CandidateName.PCDATA)
									if 'Affiliation' in str(Option):
										if (Option.ns1_AffiliationIdentifier.IdNumber==Option_ID):
											Option_Exist=True
											Option_Type='AffiliationIdentifier'
											Option_Name=str(Option.ns1_AffiliationIdentifier.ns1_RegisteredName.PCDATA)
									if 'ReferendumOptionIdentifier' in str(Option):
										if (Option.IdNumber==Option_ID):
											Option_Exist=True
											Option_Type='ReferendumOptionIdentifier'
											Option_Name=str(Option.PCDATA)
									if Option_Exist==True:
										return Election_Name, Contest_Name, Option_Name, Option_Type

		# if ballot ID does not exist
		if (Ballot_Exist==False):
			error='Error (110)!! The Ballot ID specified in load_ballot function does not match any ballot identifier in the Ballot.xml file, machine must exit !'
			return 0, error
		elif (Election_Exist==False or Contest_Exist==False or Option_Exist==False):
			error='Error (120)!! The Option ID ('+str(Option_Identifier)+') does not match any Option in the Ballot.xml file!'
			return 0, error

	def get_Contest_Information(self,Ballot_ID,option_ID):
		"""
		This functions returns contest information
		"""
		if len(option_ID)!=8:
			error='Error !! Bad parameter size. The size of contest ID, which used in get_Contest_Information function, is not equal to 8 characters!'
			return 0,error

		Event_ID=option_ID[0:2]
		Election_ID=option_ID[2:4]
		Contest_ID=option_ID[4:6]
		#
		Ballot_Exist=False
		Election_Exist=False
		Contest_Exist=False
		if (self.Ballot.ns1_Ballots.ns1_EventIdentifier.IdNumber!=Event_ID):
			error='Error !! The Event ID specified in load_ballot function does not match the event in the Ballot.xml file, machine must exit !'
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
								Election_Name=str(Election.ns1_ElectionIdentifier.ns1_ElectionName.PCDATA)
								Contest_Name=str(Cont.ns1_ContestIdentifier.ns1_ContestName.PCDATA)
								ElectionType=str(Cont.ns1_ElectionType.PCDATA)
								MaxVotes=str(Cont.ns1_MaxVotes.PCDATA)
								MinVotes=str(Cont.ns1_MinVotes.PCDATA)
								MaxWriteIn=str(Cont.ns1_MaxWriteIn.PCDATA)
								return Election_Name, Contest_Name, ElectionType, MaxVotes, MinVotes, MaxWriteIn
			#if ballot ID does not exist
			if (Ballot_Exist==False):
				error='Error (110)!! The Ballot ID specified in get_Contest_Information function does not match any ballot identifier in the Ballot.xml file, machine must exit !'
				return 0, error
			elif (Election_Exist==False or Contest_Exist==False):
				error='Error (120)!! The option ID ('+str(option_ID)+') does not match any contest identifier in the Ballot.xml file!'
				return 0, error

	def load_ballot_info(self):
		contest = {}

		for cnt in self.coords.Contest:
			if int(cnt.WriteIn.MaxWriteIn.PCDATA)>0:
				contest.update({'WriteIn':'t'})
			else:
				contest.update({'WriteIn':'f'})
			if str(cnt.Ordered.PCDATA)=='t':
				contest.update({'Ordered':'t'})
			else:
				contest.update({'Ordered':'f'})
			self.contests.append(contest)
			contest={}
		#print self.contests


	def votes_summary(self, EventID=None,PollingPlaceID=None,PollingMachineID=None, BallotID=None):

		#load contest info into the self.contests (with writein ? and ordered or not ?)
		self.load_ballot_info()

		#initialize empty votes
		for cnt in self.contests:
			self.selected_options.append({})
			self.writein.append({})

		# generalte a list that contains all xml votes
		xml_votes_list=[]
		for file in os.listdir('../gui/cast_votes'):
			if file.endswith('.xml'):
				xml_votes_list.append(file)
		#print xml_votes_list
		for castvote in xml_votes_list:
				vote_instance =XML_Objectify('../gui/cast_votes/'+str(castvote)).make_instance()
				#check if the vote have the same ballot identifier
				if (vote_instance.ElectionID!=EventID
				or vote_instance.PollingPlaceID!=PollingPlaceID
				or vote_instance.PollingMachineID!=PollingMachineID
				or vote_instance.BallotID!=BallotID):
					print 'an xml file with not appropriate identifier, will not considered'
					continue
				else:
					#check if contest element exist
					Contest_element_exist=0
					for Conts in children(vote_instance.Contests):
						if 'Contest' in str(Conts):
							Contest_element_exist=1
							break
					if Contest_element_exist==1:
						for Cont in vote_instance.Contests.Contest:
							cont_index=int(Cont.ContestID)-1
							if self.contests[cont_index]['Ordered']=='f': #not ordered contest
								for vote_code in Cont.Option:
									vote_code=vote_code.PCDATA
									if vote_code in self.selected_options[cont_index].keys(): #if the code is alrady counted at least one time before
										value = int(self.selected_options[cont_index][vote_code])+1
										self.selected_options[cont_index][vote_code]=value
									else:									  #if the code is first time count
										self.selected_options[cont_index].update({vote_code:1})
									if vote_code[6:8]=='00':                  #if the code is for writein
										writein= Cont.Writein.PCDATA
										if writein in self.writein[cont_index].keys(): #if the wrtiein is alrady counted at least one time before
											value= int(self.writein[cont_index][writein])+1
											self.writein[cont_index][writein]=value
										else:								   #if the wrtiein is first time count
											self.writein[cont_index].update({writein:1})

							if self.contests[cont_index]['Ordered']=='t':
								options=[]
								for vote_code in Cont.Option:
									options.append(vote_code.PCDATA)
								for vote_code in options:
									option_index=options.index(vote_code)+1
									if vote_code in self.selected_options[cont_index].keys(): #if the code is alrady counted at least one time before
										if int(option_index) in self.selected_options[cont_index][vote_code].keys():
											value = int(self.selected_options[cont_index][vote_code][option_index])+1
											self.selected_options[cont_index][vote_code][option_index]=value
										else:
											self.selected_options[cont_index][vote_code].update({option_index:'1'})
									else:
										self.selected_options[cont_index].update({vote_code:{option_index:1}})
									if vote_code[6:8]=='00':
										writein= Cont.Writein.PCDATA
										if writein in self.writein[cont_index].keys():
											if int(option_index) in self.writein[cont_index][writein].keys():
												value = int(self.writein[cont_index][writein][option_index])+1
												self.writein[cont_index][writein][option_index]=str(value)
											else:
												self.writein[cont_index][writein].update({option_index:1})
										else:
											self.writein[cont_index].update({writein:{option_index:1}})
		#print self.selected_options
		#print self.writein
		
		#
		info = self.get_Event_Information(EventID, PollingPlaceID)
		if info[0]==0:
			print info[1]
			self.add_log(info[1])
			sys.exit(info[1])
		#
		Event_Name=info[0]
		Election_Name=info[1]
		Polling_Place_Name=info[4]
		#
		summary='\n'
		summary+='------------------------------- \n'
		summary+='Event:'+str(Event_Name)+', Election Name:'+ str(Election_Name) +'\n'
		summary+='Polling Place:'+str(Polling_Place_Name)+', Machine ID:'+str(PollingMachineID)+', Ballot ID: '+str(BallotID)+'\n'
		summary+='Date & Time:'+ str(datetime.datetime.now())+'\n'
		summary+='------------------------------- \n'
		summary_header_length=len(summary)
		#
		for cont_votes in self.selected_options:
			if not cont_votes:
				continue
			# this bloack is to get contest information
			for vote in cont_votes:
				contest_info=self.get_Contest_Information(BallotID, vote)
				if contest_info[0]==0:
					self.add_log(info[1])
					continue
				else:
					break
			ElectionName=contest_info[0]
			ContestName=contest_info[1]
			ElectionType=contest_info[2]
			#######

			#?
			contest_index=self.selected_options.index(cont_votes)
			#
			# non ordered contest
			if not ElectionType=='ordered': #the type of Cont is not ordered
				summary+='\n'
				summary+='__________________________________________\n'
				summary+=ElectionName+', '+ContestName+' :\n'
				summary+='.....\n'
				writein=False
				writein_index=False
				for voteID in cont_votes:
					option_info=self.get_Option_Information(BallotID, voteID)
					if option_info[2]=='Writein':
						writein=True
						writein_index=contest_index
						continue
					else:
						summary+= '		'+option_info[2]+' got ('+str(cont_votes[voteID])+') votes. \n'
				if writein==True: # if there was a writein in the selected options in the non ordered contest
					summary+='		Writein: \n'
					for writein_text in self.writein[writein_index]:
						summary+='		        '+writein_text+' got ('+str(self.writein[writein_index][writein_text])+') votes. \n'
			#
			# ordered
			if ElectionType=='ordered': #the type of Cont is ordered
				summary+=ElectionName+', '+ContestName+' :\n'
				writein=False
				writein_index=False
				for voteID in cont_votes:
					option_info=self.get_Option_Information(BallotID, voteID)
					if option_info[2]=='Writein':
						writein=True
						writein_index=contest_index
						continue
					else:
						summary+='		'+option_info[2]+' got:\n'
						for rank in cont_votes[voteID]:
							summary+= '			order '+str(int(rank))+ ' for ('+str(cont_votes[voteID][rank])+') times,\n '
						#summary+='\n'
				if writein: # if there was a writein in the selected options in the non ordered contest
					summary+='		Writein: \n'
					for writein_text in self.writein[writein_index]:
						summary+='		'+ str(writein_text)+' got:\n'
						for wr_rank in self.writein[writein_index][writein_text]:
							summary+='			order '+str(int(wr_rank))+ ' for ('+str(self.writein[writein_index][writein_text][wr_rank])+') times,\n '
						#summary+='\n'
			#


		self.selected_options=[]
		self.writein=[]

		summary_total_length=len(summary)
		if summary_header_length==summary_total_length:
			summary+='There are no cast votes for this machine.'

		print summary
		return 1,summary,'report generated successfuly'#,ordered_writein


if __name__=='__main__':

	GR=getResult()
	GR.votes_summary('01','0001','01','0001')
	

