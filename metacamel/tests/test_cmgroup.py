# -*- coding: utf-8 -*-
'''Unit tests for CMGroup class.'''

import os
import json
from itertools import islice

from ..cmgroup import CMGroup, batch_group_search

_CUR_PATH = os.path.dirname(os.path.abspath(__file__))
_PARENT_PATH = os.path.dirname(_CUR_PATH)
DATA_PATH = os.path.join(os.path.dirname(_PARENT_PATH), 'data')

with open(os.path.join(DATA_PATH, 'group_params_example.json'), 'r') as params:
    params_list = json.load(params)


def test_construct_groups():
    for params in params_list:
        group = CMGroup(params)
        assert group.materialid == params['materialid']
        assert len(group) == 0


def test_pubchem_search():
    group = CMGroup(params_list[0])
    # To save time, only retrieve the first 5 CIDs.
    group.pubchem_update(listkey_count=5)
    assert len(group) > 0


def test_batch_group_search():
    groups = []

    for params in params_list:
        groups.append(CMGroup(params))

    # To save time, only retrieve the first 3 CIDs.
    batch_group_search(groups, wait=30, listkey_count=3)

    for group in groups:
        group.to_excel()
        assert len(group) > 0
        assert group.compounds_list[0]['IUPAC_name'] is not None
