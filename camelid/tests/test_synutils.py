# -*- coding: utf-8 -*-
"""Unit tests for synonym processing."""

from .. import synutils as syn


def test_select_synonyms():
    assert syn.select_synonym('UNII-12345') is True
    assert syn.select_synonym('InChI=FOOBAR') is False
    assert syn.select_synonym('aziridine') is True
    # probably want some more here


def test_identify_synonym():
    assert syn.identify_synonym('UNII-5000') == {'UNII': 'UNII-5000'}
    assert syn.identify_synonym('12345') == {}
