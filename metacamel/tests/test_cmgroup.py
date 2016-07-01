# -*- coding: utf-8 -*-
'''Unit tests for CMGroup class.'''

import os
import json

from ..cmgroup import CMGroup, batch_group_search

_CUR_PATH = os.path.dirname(os.path.abspath(__file__))
_PARENT_PATH = os.path.dirname(_CUR_PATH)
DATA_PATH = os.path.join(os.path.dirname(_PARENT_PATH), 'data')

with open(os.path.join(DATA_PATH, 'test_group_params.json'), 'r') as fp:
    PARAMS_LIST = json.load(fp)


def test_cmgroup():
    for params in PARAMS_LIST:
        group = CMGroup(params)
        assert group.materialid == params['materialid']
        assert len(group) == 0


def test_pubchem_update():
    group = CMGroup(PARAMS_LIST[0])
    # To save time, only retrieve the first 5 CIDs.
    group.pubchem_update(listkey_count=5)
    assert len(group) > 0


def test_batch_group_search():
    groups = []

    for params in PARAMS_LIST:
        groups.append(CMGroup(params))

    # To save time, only retrieve the first 3 CIDs.
    batch_group_search(groups, wait=30, listkey_count=3)

    for group in groups:
        group.to_excel()
        assert len(group) > 0
        assert group.compounds_list[0]['IUPAC_name'] is not None
