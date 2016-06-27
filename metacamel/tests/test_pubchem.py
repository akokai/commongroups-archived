# -*- coding: utf-8 -*-
'''Unit tests for PubChem API usage.'''

import sys
from itertools import islice
sys.path.append('metacamel')

from metacamel import pubchemutils as pc

cids_with_cas = [22230, 311, 2244]
cids_without_cas = [13628823]

def test_get_known_casrns():
    for cid in cids_with_cas:
        casrns = pc.get_known_casrns(cid)
        assert len(casrns) > 0

    for cid in cids_without_cas:
        casrns = pc.get_known_casrns(cid)
        assert len(casrns) == 0


def test_find_pubchem_casrns():
    results = list(islice(pc.details_from_cids(cids_with_cas), None))
    for result in results:
        assert result['CASRN_list'] != ''
