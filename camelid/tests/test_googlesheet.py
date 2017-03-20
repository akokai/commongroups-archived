# coding: utf-8

"""Unit tests for Google Spreadsheet access."""

from itertools import islice
import json
from os.path import join as pjoin

from camelid.cmgroup import BASE_PARAMS
from camelid.env import CamelidEnv
from camelid.googlesheet import SheetManager as GSM

env = CamelidEnv('test')
config = env.read_config('test.json')
goog = GSM(config['title'],
           config['worksheet'],
           config['key_file'])


def test_get_spreadsheet():
    doc = goog.get_spreadsheet()
    assert 'test' in [wks.title for wks in doc.worksheets()]


def test_get_params():
    tested = list(islice(goog.get_params(), None))
    for item in tested:
        assert 'params' in item.keys()
        assert all([x in item['params'].keys() for x in BASE_PARAMS])
        assert isinstance(item['params']['cmg_id'], str)
        assert 'info' in item.keys()
        assert 'notes' in item['info'].keys()
        assert isinstance(item['info']['notes'], str)
    assert tested[0]['params']['method'] == 'substructure'


def test_get_cmgs():
    cmgs = list(islice(goog.get_cmgs(env), None))
    assert len(cmgs) == 6
    assert cmgs[0].cmg_id == 'test-00'


def test_params_to_json():
    goog.params_to_json(pjoin(env.results_path, 'params.json'))
