# -*- coding: utf-8 -*-
"""
Unit tests for Google Spreadsheet access.

For these tests to work, follow the setup instructions in `googlesheet.py`.
"""

from os.path import join as pjoin
from itertools import islice

from .. import googlesheet as gs
from ..run import CamelidEnv

sheet = gs.SheetManager(worksheet='test')
env = CamelidEnv(project='test')


def test_get_spreadsheet():
    doc = sheet.get_spreadsheet()
    assert doc.sheet1.title == 'new CMGs'


def test_get_params():
    params_list = list(islice(sheet.get_params(), None))
    assert isinstance(params_list[0]['last_updated'], str)
    assert params_list[3]['searchstring'] == '[O-][Cr](=O)(=O)[O-].[Zn+2]'


def test_get_cmgs():
    cmgs = list(islice(sheet.get_cmgs(env), None))
    assert len(cmgs) == 4
    assert len(cmgs[0].materialid) == 5


def test_params_to_json():
    sheet.params_to_json(pjoin(env.project_path, 'params.json'))
