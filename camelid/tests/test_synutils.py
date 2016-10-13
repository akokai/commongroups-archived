# -*- coding: utf-8 -*-
"""Unit tests for synonym processing."""

from .. import synutils as syn


def test_select_synonyms():
    assert syn.select_synonym('UNII-12345') is True
    assert syn.select_synonym('InChI=FOOBAR') is False
    assert syn.select_synonym('aziridine') is True
    assert syn.select_synonym('C28H18N4O6S4.2Na') is False
    # probably want some more here


def test_identify_synonym():
    assert syn.identify_synonym('UNII-5000') == {'UNII': 'UNII-5000'}
    assert syn.identify_synonym('CHEMBL369252') == {'CHEMBL': 'CHEMBL369252'}
    assert syn.identify_synonym('12345') == {}
