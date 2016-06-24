# -*- coding: utf-8 -*-
'''Unit tests for PubChem API usage.'''

import sys
from itertools import islice
sys.path.append('metacamel')

from metacamel import pubchemutils as pc


def test_find_pubchem_casrns():
    cids = [22230, 311, 2244]
    results = list(islice(pc.casrn_iupac_from_cids(cids), None))
    for result in results:
        assert result['CASRN'] is not None
