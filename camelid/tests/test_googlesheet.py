# coding: utf-8

"""Unit tests for Google Spreadsheet access."""

from itertools import islice
import json
from os.path import join as pjoin

from camelid import googlesheet as gs
from camelid.env import CamelidEnv

env = CamelidEnv('test')
config = env.read_config('test.json')

sheet = gs.SheetManager(config['title'],
                        config['worksheet'],
                        config['key_file'])

def test_get_spreadsheet():
    doc = sheet.get_spreadsheet()
    assert doc.sheet1.title == 'all CMGs'


def test_get_params():
    params_list = list(islice(sheet.get_params(), None))
    assert isinstance(params_list[0]['last_updated'], str)
    assert params_list[3]['searchstring'] == '[O-][Cr](=O)(=O)[O-].[Zn+2]'


def test_get_cmgs():
    cmgs = list(islice(sheet.get_cmgs(env), None))
    assert len(cmgs) == 4
    assert len(cmgs[0].materialid) == 5


def test_params_to_json():
    sheet.params_to_json(pjoin(env.results_path, 'params.json'))
