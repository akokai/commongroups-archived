# -*- coding: utf-8 -*-
'''Functions to get specific information from PubChem.'''

from __future__ import unicode_literals
from time import sleep
import pubchempy as pcp
from metacamel.casrnutils import find_valid


def casrn_iupac_from_cids(cids):
    '''
    Generate dicts of corresponding CASRNs and IUPAC names for a list of CIDs.

    Uses PubChem API. CIDs can be an iterable of ints or strings.
    '''
    for cid in cids:
        iupac_name = pcp.Compound.from_cid(cid).iupac_name
        sleep(0.5)  # Sleep to prevent overloading API.
        # There might be a more robust way to find a list of CASRNs
        # and to process it in a more sophisticated way, e.g. find the
        # most commonly used one. For example, see:
        # https://{pubchem}/rest/pug_view/data/compound/2244/JSON?heading=CAS
        # For now, join up all the synonyms in to one long string:
        try:
            synonyms = ' '.join(pcp.get_synonyms(cid)[0]['Synonym'])
        except IndexError:  # If there are no synonyms in PubChem...
            synonyms = ''
        sleep(0.5)  # Not sure how much sleep we actually need.
        # Leave the regexing to another function, which is very thorough
        # and also makes sure the CASRNs are numerically valid:
        casrns = find_valid(synonyms)
        if casrns:
            casrn = casrns[0]
        else:
            casrn = None
        results = {'CID': cid, 'CASRN': casrn, 'IUPAC_name': iupac_name}
        yield results
