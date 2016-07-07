# -*- coding: utf-8 -*-
'''Unit tests for CMGroup class.'''

import os
import shutil
from time import sleep
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
        assert len(group) == 0


def test_resume_update():
    materialid = PARAMS_LIST[3]['materialid']
    shutil.copy(os.path.join(_CUR_PATH, 'cids.json'),
                os.path.join(DATA_PATH, materialid + '_cids.json'))
    shutil.copy(os.path.join(_CUR_PATH, 'cpds.jsonl'),
                os.path.join(DATA_PATH, materialid + '_cpds.jsonl'))
    group = cmg.CMGroup(PARAMS_LIST[3])
    group.load_returned_cids()
    group.update_with_cids()


def test_pubchem_update():
    group = cmg.CMGroup(PARAMS_LIST[0])
    # To save time, only retrieve the first 5 CIDs.
    # TODO: Ideally we should also test without any `listkey_count`,
    # i.e. with a search that returns very few results.
    group.pubchem_update(listkey_count=5)
    assert len(group) > 0


def test_batch_cmg_search():
    groups = list(islice(cmg.cmgs_from_json(PARAMS_JSON), None))

    # To save time, only retrieve the first 3 CIDs.
    cmg.batch_cmg_search(groups, wait=30, listkey_count=3)

    for group in groups:
        assert len(group) > 0
        assert group.compounds_list[0]['IUPAC_name'] is not None
