# -*- coding: utf-8 -*-
"""Unit tests for PubChem API usage."""

from itertools import islice
from datetime import date

from commongroups import pubchemutils as pc

CIDS_WITH_CAS = [311, 2244]
# The following might need to be changed if CASRNS are eventually added
# to these compounds records.
CIDS_WITHOUT_CAS = [13628823, 119081525]
NEW_CIDS = CIDS_WITHOUT_CAS


def test_get_creation_date():
    for cid in NEW_CIDS:
        created = pc.get_creation_date(cid)
        assert created is not None
        delta = created - date(2005, 5, 5)
        assert delta.days > 0


def test_get_known_casrns():
    for cid in CIDS_WITH_CAS:
        casrns = pc.get_known_casrns(cid)
        print('CID: {0}\nKnown CASRNs: {1}'.format(cid, ' '.join(casrns)))
        assert len(casrns) > 0

    for cid in CIDS_WITHOUT_CAS:
        casrns = pc.get_known_casrns(cid)
        assert len(casrns) == 0


def test_get_compound_info():
    cids = CIDS_WITH_CAS + CIDS_WITHOUT_CAS
    results = list(islice(pc.gen_compounds(cids), None))
    for result in results:
        assert result['CASRN_list'] is not None
        assert result['IUPAC_name'] is not None
        assert result['creation_date'] is not None

    for result in results[:len(CIDS_WITH_CAS)]:
        assert result['CASRN_list'] != ''

    for result in results[len(CIDS_WITHOUT_CAS):]:
        assert result['CASRN_list'] == ''


def test_filter_listkey_args():
    args = {'listkey_start': 1, 'listkey_count': 1}
    assert pc.filter_listkey_args(**args) == args


def test_substruct_search():
    # To save time, only retrieve the first 5 CIDs.
    results = pc.substruct_search('[CH3][Hg]', wait=1, listkey_count=5)
    assert len(results) > 0
