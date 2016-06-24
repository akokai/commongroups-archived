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
        cpd = pcp.Compound.from_cid(cid)
        sleep(0.5)  # Sleep to prevent overloading API.
        # There might be a more robust way to find a list of CASRNs
        # and to process it in a more sophisticated way, e.g. find the
        # most commonly used one. For example, see:
        # https://{pubchem}/rest/pug_view/data/compound/2244/JSON?heading=CAS
        # For now, join up all the synonyms in to one long string
        # and use regex to find valid CASRNs. Use the first one found.
        try:
            casrn = find_valid(' '.join(cpd.synonyms))[0]
        except IndexError:
            # If there are no synonyms, or there are no CASRNs found:
            casrn = None
        results = {'CID': cid, 'CASRN': casrn, 'IUPAC_name': cpd.iupac_name}
        yield results
