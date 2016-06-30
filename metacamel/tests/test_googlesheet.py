# -*- coding: utf-8 -*-
'''Unit tests for Google Spreadsheet access.'''

from itertools import islice

from .. import googlesheet as gs

doc = gs.get_spreadsheet()


def test_get_spreadsheet():
    assert doc.sheet1.title == 'new CMGs'


def test_get_cmgs():
    cmgs = list(islice(gs.get_cmgs(doc, 'new CMGs'), 2))
    assert len(cmgs[0].materialid) == 7


def test_params_to_json():
    gs.params_to_json(doc, 'new CMGs', 'test_download.json')
