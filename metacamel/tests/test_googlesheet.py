# -*- coding: utf-8 -*-
'''Unit tests for Google Spreadsheet access.'''

from itertools import islice

from .. import googlesheet as gs


def test_get_spreadsheet():
    sheet = gs.get_spreadsheet()
    assert sheet.sheet1.title == 'new CMGs'

def test_get_CMGs():
    cmgs = list(islice(gs.get_CMGs('new CMGs'), 2))
    assert len(cmgs[0].materialid) == 7