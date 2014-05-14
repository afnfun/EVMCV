import sys
#if sys.platform != 'win32':
#    sys.path.append('../..')
#else:
#    sys.path.append('..\\..')
# This function generates the output XML file (Cast Vote)
def ballotxml(ElectionID,PollingPlaceID,PollingMachineID, BallotID, VoteNumber, codes, writein):
	xml = ""
	xml += '<CastVote ElectionID="' + str(ElectionID)+'" PollingPlaceID="' + str(PollingPlaceID) + '" PollingMachineID="' + str(PollingMachineID) + '" BallotID="' + str(BallotID) + '" VoteNumber="' + str(VoteNumber) + '" >\n'
	xml += '	<Contests>\n'
	for i , code in enumerate(codes):
		if code == 0: continue
		if type(code) is list and len(code) !=0 and code.count(0) < len(code):
			xml += '		<Contest ContestID="'+str(i+1)+'">\n'
			for x in code:
				if x == 0: continue
				xml += '			<Option>'+x+'</Option>\n'
			if len(writein[i])>0:
				xml += '			<Writein>'+writein[i]+'</Writein>\n'
			xml += '		</Contest>\n'
		if type(code) is not list:
			xml += '		<Contest ContestID="'+str(i+1)+'">\n'
			xml += '			<Option>'+code+'</Option>\n'
			if len(writein[i])>0:
				xml += '			<Writein>'+writein[i]+'</Writein>\n'
			xml += '		</Contest>\n'
	xml += '	</Contests>\n'
	xml += '</CastVote>'
	return xml