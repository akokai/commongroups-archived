# -*- coding: utf-8 -*-
'''Chemical and material group class definition.'''

from __future__ import unicode_literals

import os
import logging
import json
from copy import deepcopy
from itertools import islice
from time import asctime, sleep
from datetime import date

from pandas import DataFrame, ExcelWriter
from boltons.fileutils import mkdir_p
from boltons.jsonutils import JSONLIterator

from . import logconf
from . import pubchemutils as pc

logger = logging.getLogger('metacamel.cmgroup')

_CUR_PATH = os.path.dirname(os.path.abspath(__file__))
_PARENT_PATH = os.path.dirname(_CUR_PATH)
DATA_PATH = os.path.join(_PARENT_PATH, 'data')
mkdir_p(DATA_PATH)
RESULTS_PATH = os.path.join(_PARENT_PATH, 'results')
mkdir_p(RESULTS_PATH)

# These are the expected headings of spreadsheet columns.
# They're also the column headings used for Excel exports of group parameters.
PARAMS_KEYS = ['materialid', 'name', 'searchtype',
               'structtype', 'searchstring', 'last_updated']
# These are the column headings used for Excel exports of compound lists.
COMPOUNDS_KEYS = ['CID', 'CASRN_list', 'IUPAC_name', 'creation_date']


class CMGroup:
    '''Chemical and material group class.'''

    def __init__(self, params):
        '''
        Initialize from a dict containing all parameters of a compound group.

        The dict should contain `materialid`, `name`,` `searchtype`,
        `structtype`, `searchstring`, and `last_updated`. (For now...)
        '''
        if 'materialid' in params:
            self._materialid = params['materialid']
        else:
            logger.warning('Initializing CMGroup with no given materialid.')
            self._materialid = asctime().replace(' ', '_').replace(':', '')

        logger.debug('Created %s', self)
        self._params = params
        self._returned_cids = []
        self._cids_file = os.path.join(DATA_PATH,
                                       self.materialid + '_cids.json')
        if os.path.exists(self._cids_file):
            self.load_returned_cids()
        self._compounds_file = os.path.join(DATA_PATH,
                                            self.materialid + '_cpds.jsonl')
        self._compounds = []
        self._listkey = None

        if self._params['last_updated'] == '':
            self._last_updated = None
        else:
            try:
                date_args = [int(x) for x in
                             self._params['last_updated'].split('-')]
                self._last_updated = date(*date_args)
            except (KeyError, TypeError, ValueError):
                logger.warning('Invalid date format: %s. '
                               'Updating by date is disabled for %s.',
                               self._params['last_updated'], self)
                self._last_updated = None

    @property
    def materialid(self):
        '''The numeric ID of the chemical/material group.'''
        return self._materialid

    @property
    def name(self):
        '''The name of the chemical/material group.'''
        if 'name' in self._params:
            return self._params['name']

    @property
    def searchtype(self):
        '''
        The type of structure-based search used to define this group.

        Currently only `substructure` is of any use.
        '''
        if 'searchtype' in self._params:
            return self._params['searchtype']

    @property
    def structtype(self):
        '''
        The form of structure notation used for searching, e.g. `smiles`.

        Currently only works with `smiles`.
        '''
        if 'structtype' in self._params:
            return self._params['structtype']

    @property
    def searchstring(self):
        '''
        Query for structure-based searches, e.g. a string in SMILES notation.
        '''
        if 'searchstring' in self._params:
            return self._params['searchstring']

    @property
    def last_updated(self):
        '''
        When the group was last updated, according to the supplied parameters.

        This property is either a python `datetime.date` object, or `None`.
        Note that `datetime.date` can't be serialized to JSON or Excel
        without first converting to string.
        '''
        return self._last_updated

    @property
    def compounds_list(self):
        '''Return a deep copy of the list of compounds (a list of dicts).'''
        return deepcopy(self._compounds)

    @property
    def listkey(self):
        '''Temporary ListKey for asynchronous PubChem searches.'''
        return self._listkey

    @listkey.setter
    def listkey(self, new_listkey):
        self._listkey = new_listkey

    @listkey.deleter
    def listkey(self):
        self._listkey = None

    @property
    def returned_cids(self):
        '''Raw list of CIDs returned by the last PubChem search.'''
        return self._returned_cids

    @returned_cids.setter
    def returned_cids(self, cids):
        self._returned_cids = cids

    def load_returned_cids(self):
        '''
        Load the list of CIDs returned by the last PubChem search from file.
        '''
        try:
            with open(self._cids_file, 'r') as json_file:
                cids = json.load(json_file)
                logger.info('Loaded existing CIDs list for %s.', self)
                self.returned_cids = cids
        except FileNotFoundError:
            logger.info('Could not open CIDs file.')

    def save_returned_cids(self, cids):
        '''
        Save the list of CIDs returned by the last PubChem search to file.
        '''
        self.returned_cids = cids
        logger.debug('Writing list of returned CIDs to file: %s',
                     self._cids_file)
        with open(self._cids_file, 'w') as json_file:
            json.dump(cids, json_file)

    def __len__(self):
        '''Return the length of the group's internal list of compounds.'''
        return len(self._compounds)

    def __contains__(self, compound):
        '''
        Check if a compound is already in the group's internal list.
        '''
        # TO DO: make this match identifiers only, instead of dicts...
        return compound in self._compounds

    def __repr__(self):
        '''Return a string identifying the object.'''
        return 'CMGroup({0})'.format(self.materialid)

    def to_excel(self, file_path=None):
        '''
        Output the list of compounds & parameters to an Excel spreadsheet.
        '''
        params_frame = DataFrame(self._params,
                                 columns=PARAMS_KEYS, index=[0])
        params_frame.set_index('materialid', inplace=True)
        compounds_frame = DataFrame(self._compounds,
                                    columns=COMPOUNDS_KEYS)
        if not file_path:
            file_path = os.path.join(RESULTS_PATH,
                                     '{0}.xlsx'.format(self.materialid))
        logger.info('Writing Excel output to: %s', file_path)
        with ExcelWriter(file_path) as writer:
            params_frame.to_excel(writer, sheet_name=self.materialid)
            compounds_frame.to_excel(writer, sheet_name='Compounds')

    def init_pubchem_search(self):
        '''
        Initiate an async PubChem structure-based search and save the ListKey.
        '''
        try:
            if self.searchtype == 'substructure':
                logger.debug('Initiating PubChem substructure search for %s.',
                             self.materialid)
                key = pc.init_substruct_search(self.searchstring,
                                               method=self.structtype)
                logger.debug('Setting ListKey for %s: %s.', key,
                             self.materialid)
                self.listkey = key
            else:
                logger.error('Sorry, can only do substructure searches '
                             'in PubChem at this time.')
                raise NotImplementedError
        except KeyError:
            logger.exception('Missing parameters.')
            raise

    def retrieve_pubchem_search(self, **kwargs):
        '''
        Retrieve results from a previously-initiated async PubChem search.
        '''
        if not self.listkey:
            logger.error('No existing ListKey to retrieve search results.')
            return None     # Raise an exception instead?

        logger.debug('Retrieving PubChem search results for %s.',
                     self.materialid)

        listkey_args = pc.filter_listkey_args(**kwargs) if kwargs else None

        if listkey_args:
            cids = pc.retrieve_search_results(self.listkey, **listkey_args)
        else:
            cids = pc.retrieve_search_results(self.listkey)

        # This sets `self.returned_cids` and also saves the list to JSON.
        self.save_returned_cids(cids)

        logger.debug('Clearing ListKey for %s.', self.materialid)
        del self.listkey

    def update_with_cids(self):
        '''
        Retrieve information on a list of CIDs and add new ones to the CMG.
        '''
        if self.returned_cids == []:
            logger.warning('No CIDs to update %s.', self)
            return None
        else:
            logger.info('Updating %s from list of returned CIDS.', self)

        cids = self.returned_cids
        
        if os.path.exists(self._compounds_file):
            # TODO: Test this... 
            # - It should be able to add on to a compound list that has no
            #   overlap with `cids` list. (index not found).
            # - It should not freak out over an empty JSONL file.
            try:
                with open(self._compounds_file, 'r') as cpds_file:
                    lines = JSONLIterator(cpds_file, reverse=True)
                    last_item = lines.next()
                last_cid = last_item['CID']
                new_index = self.returned_cids.index(last_cid) + 1
                cids = self.returned_cids[new_index:]
                logger.info('Resuming update. Last CID added: %s.', last_cid)
            except (ValueError, StopIteration):
                pass

        logger.info('Looking up details for %i CIDs.', len(cids))
        new = pc.gen_compounds(cids, self.last_updated)

        with open(self._compounds_file, 'a') as cpds_file:
            while True:
                new_compounds = list(islice(new, 5))
                if new_compounds == []:
                    break
                for cpd in new_compounds:
                    cpds_file.write(json.dumps(cpd) + '\n')
                sleep(1)

        logger.info('Completed PubChem update for %s.', self)

        # TODO: decide if the following (here to end of function) is necessary
        with open(self._compounds_file, 'r') as cpds_file:
            lines = JSONLIterator(cpds_file)
            new_compounds = list(islice(lines, None))

        logger.info('Adding %i compounds from PubChem search to group %s.',
                    len(new_compounds), self.materialid)
        self._compounds.extend(new_compounds)
        # TODO: remove cids JSON file.

    def pubchem_update(self, wait=10, **kwargs):
        '''
        Perform a PubChem search to update a compound group.
        '''
        self.init_pubchem_search()
        logger.debug('Waiting %i s before retrieving search results.', wait)
        sleep(wait)
        self.retrieve_pubchem_search(**kwargs)
        self.update_with_cids()
        self.to_excel()

    def screen(self, compound):
        '''Screen a new compound for membership in the group.'''
        if compound in self:
            return True
        else:
            # Placeholder!
            raise NotImplementedError


def batch_cmg_search(groups, wait=120, **kwargs):
    '''
    Perform PubChem searches for many CMGs and output to Excel files.
    '''
    for group in groups:
        group.init_pubchem_search()

    sleep(wait)

    for group in groups:
        group.retrieve_pubchem_search(**kwargs)
        logger.info('Completed ')

    for group in groups:
        group.update_with_cids()
        group.to_excel()
        logger.info('Completed update for %s', group)


def params_from_json(params_file):
    '''Load a list of group parameters from a JSON file.'''
    with open(params_file, 'r') as json_file:
        params_list = json.load(json_file)
    return params_list


def cmgs_from_json(params_file):
    '''Generate `CMGroup` objects from a JSON file.'''
    for params in params_from_json(params_file):
        yield CMGroup(params)
