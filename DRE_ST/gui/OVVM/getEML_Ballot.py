import sys
import datetime
from OVVM_VM import *



#if sys.platform != 'win32':
#    sys.path.append('../..')
#else:
#    sys.path.append('..\\..')
# This function generates the output XML file (Cast Vote)
def emlBallot(EventID,PollingPlaceID,PollingMachineID, VmID, BallotID, contests, votes, writeins):
	VM = VM()
	now = datetime.datetime.now()
	xml = ""
	
	xml += '<?xml version="1.0" encoding="UTF-8"?>'
	xml += '<ns1:EML Id="440" SchemaVersion="7.0" xmlns:ns1="urn:oasis:names:tc:evs:schema:eml">'
	xml += '	<ns1:EMLHeader>'
	xml += '		<ns1:TransactionId>0</ns1:TransactionId>'
	xml += '		<ns1:OfficialStatusDetail>'
	xml += '			<ns1:OfficialStatus>apporved</ns1:OfficialStatus>'
	xml += '			<ns1:StatusDate>'+str(now.year)+'-'+str(now.month)+'-'+str(now.day)+'</ns1:StatusDate>'
	xml += '		</ns1:OfficialStatusDetail>'
	xml += '	</ns1:EMLHeader>'
	xml += '	<ns1:CastVote>'
	xml += '		<ns1:EventIdentifier IdNumber="'+EventID+'"/>'
	for cont in contests:
		if (cont[0:2]!=EventID):
			continue
		xml += '		<ns1:Election>'
		xml += '			<ns1:ElectionIdentifier IdNumber="'+cont[2:4]+'"/>'
		xml += '			<ns1:Contest>'
		xml += '				<ns1:ContestIdentifier IdNumber="'+cont[3:6]+'"/>'
		index_contest=contests.index(cont)
		for vote in votes[index_contest]:
			index_vote=votes[index_contest].index(vote)
			writein= writeins[index_contest][index_vote]
			if len(writein)!=0:
				xml += '				<ns1:Selection>'
				xml += '					<ns1:WriteinCandidateName>'+writein+'</ns1:WriteinCandidateName>'
				xml += '				</ns1:Selection>'
			else:
				option = VM.get_Option_Information(BallotID,vote)
				if option[3]=='CandidateIdentifier':
					xml += '				<ns1:Selection>'
					xml += '					<ns1:CandidateIdentifier IdNumber="'+vote[6:8]+'"/>'
					xml += '				</ns1:Selection>'
				if option[3]=='AffiliationIdentifier':
					xml += '				<ns1:Selection>'
					xml += '					<ns1:AffiliationIdentifier IdNumber="'+vote[6:8]+'">'
					xml += '						<ns1:RegisteredName/>'
					xml += '					</ns1:AffiliationIdentifier>'
					xml += '				</ns1:Selection>'
				if option[3]=='AffiliationIdentifier':
					xml += '				<ns1:Selection>'
					xml += '					<ns1:ReferendumOptionIdentifier IdNumber="'+vote[6:8]+'"/>'
					xml += '				</ns1:Selection>'
		xml += '			</ns1:Contest>'
		xml += '		</ns1:Election>'
	#
	xml += '		<ns1:BallotIdentifier IdNumber="'+BallotID+'"/>'
	xml += '		<ns1:AuditInformation>'
	xml += '			<ns1:ProcessingUnits>'
	xml += '				<ns1:OriginatingDevice Role="'+PollingPlaceID+PollingMachineID+'">'
	xml += '					<ns1:Name>DRE</ns1:Name>'
	xml += '					<ns1:IdValue/>'
	xml += '				</ns1:OriginatingDevice>'
	xml += '				<ns1:Other Type="VM" Role="">'
	xml += '					<ns1:Name>OVVM Verification Module</ns1:Name>'
	xml += '					<ns1:IdValue>'+VmID+'</ns1:IdValue>'
	xml += '				</ns1:Other>'
	xml += '			</ns1:ProcessingUnits>'
	xml += '		</ns1:AuditInformation>'
	xml += '	</ns1:CastVote>'
	xml += '</ns1:EML>'
	return xml