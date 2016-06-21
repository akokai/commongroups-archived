# Assume a big python list of CIDS. instance of gernerator will iterate over the list and produce the synonyms.

def cas_iupac_from_cid(cid):
	# Takes a cid (integer or string) and returns dictionary of casrn (empty string if None) and
	# iupac (empty string if None) synonyms.

	CASRN = ''
	synonyms = pcp.get_synonyms(cid)[0]['Synonym']
	for synonym in synonyms:
		match = re.match('(\d{2,7}-\d\d-\d)', synonym)
		if match:
			CASRN = match.group(1) # group(0)?? Don't understand what the index does...

	IUPAC = pcp.Compound.from_cid(cid).iupac_name # Can return NoneType!
	findings_dict={'casrn':CASRN, 'iupac':str(IUPAC)}
	return findings_dict


def cas_iupac_iterator(cids_list):
	# Takes a cids_list and acts as a generator of a dictionary of casrn and iupac synonyms per cid

	for cid in cids_list:
		yield cas_iupac_from_cid(cid)








