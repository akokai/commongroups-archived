# -*- coding: utf-8 -*-
'''Unit tests for PubChem API usage.'''

from itertools import islice

from .. import pubchemutils as pc

CIDS_WITH_CAS = [22230, 311, 2244]
CIDS_WITHOUT_CAS = [13628823]


def test_get_known_casrns():
    for cid in CIDS_WITH_CAS:
        casrns = pc.get_known_casrns(cid)
        print('CID: {0}\nKnown CASRNs: {1}'.format(cid, ' '.join(casrns)))
        assert len(casrns) > 0

    for cid in CIDS_WITHOUT_CAS:
        casrns = pc.get_known_casrns(cid)
        assert len(casrns) == 0


def test_get_compound_info_casrns():
    results = list(islice(pc.get_compound_info(CIDS_WITH_CAS), None))
    for result in results:
        assert result['CASRN_list'] != ''


def test_get_compound_info():
    cids = [241, 2912, 13628823, 24290]
    results = list(islice(pc.get_compound_info(cids), None))
    for result in results:
        print('CID: {0}\nAll CASRNs: {1}'.format(result['CID'],
                                                 result['CASRN_list']))
        assert result['CASRN_list'] is not None
        assert result['IUPAC_name'] is not None
        # assert result['creation_date'] is not None # ...or something


def test_filter_listkey_args():
    args = {'listkey_start': 1, 'listkey_count': 1}
    assert pc.filter_listkey_args(**args) == args


def test_substruct_search():
    # To save time, only retrieve the first 5 CIDs.
    results = pc.substruct_search('[CH3][Hg]', wait=1, listkey_count=5)
    assert len(results) > 0
