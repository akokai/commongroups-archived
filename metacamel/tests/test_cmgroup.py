# -*- coding: utf-8 -*-
'''Unit tests for CMGroup class.'''

import os
import shutil
from itertools import islice

from .. import cmgroup as cmg

_CUR_PATH = os.path.dirname(os.path.abspath(__file__))
_PARENT_PATH = os.path.dirname(_CUR_PATH)
DATA_PATH = os.path.join(os.path.dirname(_PARENT_PATH), 'data')
PARAMS_JSON = os.path.join(_CUR_PATH, 'group_params.json')

PARAMS_LIST = cmg.params_from_json(PARAMS_JSON)


def test_cmgroup():
    for params in PARAMS_LIST:
        group = cmg.CMGroup(params)
        assert group.materialid == params['materialid']
        assert group.name == params['name']


def test_clean_data():
    group = cmg.CMGroup(PARAMS_LIST[3])
    shutil.copy(os.path.join(_CUR_PATH, 'cids.json'), group._CIDS_FILE)
    shutil.copy(os.path.join(_CUR_PATH, 'cpds.jsonl'), group._COMPOUNDS_FILE)
    assert len(group.get_compounds()) == 3
    assert len(group.get_returned_cids()) == 5
    group.clean_data()
    assert group.get_compounds() == []
    assert group.get_returned_cids() == []
    group.clean_data()


def test_resume_update():
    group = cmg.CMGroup(PARAMS_LIST[3])
    shutil.copy(os.path.join(_CUR_PATH, 'cids.json'), group._CIDS_FILE)
    shutil.copy(os.path.join(_CUR_PATH, 'cpds.jsonl'), group._COMPOUNDS_FILE)
    group.update_from_cids()
    assert len(group.get_compounds()) == 5

    # Test what happens when _COMPOUNDS_FILE contains CIDS that are
    # not listed in the _CIDS_FILE. It should append compounds.
    shutil.copy(os.path.join(_CUR_PATH, 'cpds_other.jsonl'),
                group._COMPOUNDS_FILE)
    group.update_from_cids()
    assert len(group.get_compounds()) == 8

    # Test what happens when _COMPOUNDS_FILE is absent. In this case
    # It should end up containing all the CIDs in _CIDS_FILE.
    group.clean_data()
    shutil.copy(os.path.join(_CUR_PATH, 'cids.json'), group._CIDS_FILE)
    group.update_from_cids()
    assert len(group.get_compounds()) == 5


def test_pubchem_update():
    group = cmg.CMGroup(PARAMS_LIST[0])
    # To save time, only retrieve the first 5 CIDs.
    # TODO: Ideally we should also test without any `listkey_count`,
    # i.e. with a search that returns very few results.
    group.pubchem_update(listkey_count=5)
    assert len(group.get_compounds()) > 0


def test_batch_cmg_search():
    groups = list(islice(cmg.cmgs_from_json(PARAMS_JSON), None))

    # To save time, only retrieve the first 3 CIDs.
    cmg.batch_cmg_search(groups, wait=30, listkey_count=3)

    for group in groups:
        assert len(group.get_compounds()) > 0
        assert group.get_compounds()[0]['IUPAC_name'] is not None
