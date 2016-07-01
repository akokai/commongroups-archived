# -*- coding: utf-8 -*-
'''Unit tests for Google Spreadsheet access.'''

from itertools import islice

from .. import googlesheet as gs

# This is global so that we avoid re-authenticating
# and retrieving the spreadsheet again for each test.
doc = gs.get_spreadsheet()


def test_get_spreadsheet():
    assert doc.sheet1.title == 'new CMGs'


def test_get_params():
    params = list(islice(gs.get_params(doc, 'test'), None))
    assert isinstance(params[0]['last_updated'], str)
    assert params[3]['searchstring'] == '[O-][Cr](=O)(=O)[O-].[Zn+2]'


def test_get_cmgs():
    cmgs = list(islice(gs.get_cmgs(doc, 'test'), None))
    assert len(cmgs) == 4
    assert len(cmgs[0].materialid) == 7


def test_params_to_json():
    gs.params_to_json(doc, 'test', 'test_group_params.json')
