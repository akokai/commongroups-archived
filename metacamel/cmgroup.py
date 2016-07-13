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
        self._listkey = None

        self._compounds = []
        self._COMPOUNDS_FILE = os.path.join(DATA_PATH,
                                            self.materialid + '_cpds.jsonl')
        if os.path.exists(self._COMPOUNDS_FILE):
            self.load_compounds()

        self._returned_cids = []
        self._CIDS_FILE = os.path.join(DATA_PATH,
                                       self.materialid + '_cids.json')
        if os.path.exists(self._CIDS_FILE):
            self.load_returned_cids()

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
    def compounds(self):
        '''The internal list of compounds (a list of dicts).'''
        return self._compounds

    @compounds.setter
    def compounds(self, new_compounds):
        self._compounds = new_compounds

    def add_compounds(self, new_compounds):
        self.compounds = self.compounds + new_compounds

    def load_compounds(self):
        '''
        Read compounds (list of dicts) from file to replace internal list.
        '''
        try:
            with open(self._COMPOUNDS_FILE, 'r') as cpds_file:
                lines = JSONLIterator(cpds_file)
                new_compounds = list(islice(lines, None))
                logger.info('Loading %i compounds from JSON for %s.',
                            len(new_compounds), self)
                self.compounds = new_compounds
        except (ValueError, StopIteration):
            logger.info('No compounds to be added to %s.', self)
            self.compounds = []

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
            with open(self._CIDS_FILE, 'r') as json_file:
                cids = json.load(json_file)
                logger.info('Loaded existing CIDs list for %s.', self)
                self.returned_cids = cids
        except (FileNotFoundError, json.JSONDecodeError):
            logger.debug('No existing CIDs found for %s.', self)
            self.returned_cids = []

    def save_returned_cids(self, cids):
        '''
        Save the list of CIDs returned by the last PubChem search to file.
        '''
        logger.debug('Saving search results for %s, containing %i CIDs.',
                     self, len(cids))
        self.returned_cids = cids
        with open(self._CIDS_FILE, 'w') as json_file:
            json.dump(cids, json_file)

    def clean_json(self):
        '''Clean up JSON files generated from PubChem search.'''
        logger.debug('Removing JSON files for %s.', self)
        try:
            os.remove(self._CIDS_FILE)
            os.remove(self._COMPOUNDS_FILE)
        except OSError:
            logger.exception('Failed to delete all JSON files.')

        logger.debug('Resetting group %s.', self)
        self.compounds = []
        self.returned_cids = []

    def __len__(self):
        '''Return the length of the group's internal list of compounds.'''
        return len(self.compounds)

    def __contains__(self, compound):
        '''
        Check if a compound is already in the group's internal list.
        '''
        # TO DO: make this match identifiers only, instead of dicts...
        return compound in self.compounds

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
        compounds_frame = DataFrame(self.compounds,
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
                             self)
                key = pc.init_substruct_search(self.searchstring,
                                               method=self.structtype)
                logger.debug('Setting ListKey for %s: %s.', self, key)
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

        logger.debug('Retrieving PubChem search results for %s.', self)

        listkey_args = pc.filter_listkey_args(**kwargs) if kwargs else None

        if listkey_args:
            cids = pc.retrieve_search_results(self.listkey, **listkey_args)
        else:
            cids = pc.retrieve_search_results(self.listkey)

        # This sets `self.returned_cids` and also saves the list to JSON.
        self.save_returned_cids(cids)

        logger.debug('Clearing ListKey for %s.', self)
        del self.listkey

    def update_with_cids(self):
        '''
        Retrieve information on a list of CIDs and add new ones to the CMG.
        '''
        if not self.returned_cids:
            logger.warning('No CIDs to update %s.', self)
            return None
        else:
            logger.info('Updating %s from list of returned CIDS.', self)

        try:
            last_cid = self.compounds[-1]['CID']
            new_index = self.returned_cids.index(last_cid) + 1
            cids = self.returned_cids[new_index:]
            logger.info('Resuming update of %s; last CID added: %s.',
                        self, last_cid)
        except (IndexError, ValueError):
            cids = self.returned_cids
            logger.info('Starting new update of %s '
                        'based on PubChem search results.', self)

        logger.info('Looking up details for %i CIDs.', len(cids))
        new = pc.gen_compounds(cids, self.last_updated)

        with open(self._COMPOUNDS_FILE, 'a') as cpds_file:
            while True:
                new_compounds = list(islice(new, 5))
                if new_compounds == []:
                    break
                for cpd in new_compounds:
                    cpds_file.write(json.dumps(cpd) + '\n')
                sleep(1)

        logger.info('Completed PubChem update for %s.', self)

        # Add new compounds to the internal list associated with the CMGroup.
        # NOTE: right now, this just reads the entire JSONL file into a list
        # of dicts and overwrites the value of self._compounds.
        logger.info('Adding %i compounds in total from PubChem search to %s.',
                    len(new_compounds), self)
        self.load_compounds()

    def pubchem_update(self, wait=10, **kwargs):
        '''
        Perform a PubChem search to update a compound group.
        '''
        self.init_pubchem_search()
        logger.info('Waiting %i s before retrieving search results.', wait)
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


def batch_cmg_search(groups, resume_update=False, wait=120, **kwargs):
    '''
    Perform PubChem searches for many CMGs and output to Excel files.
    '''
    if not resume_update:
        for group in groups:
            group.init_pubchem_search()

        logger.info('Waiting %i s before retrieving search results.', wait)
        sleep(wait)

        for group in groups:
            group.retrieve_pubchem_search(**kwargs)

        logger.info('Completed retrieving all group search results.')

    for group in groups:
        group.update_with_cids()
        group.to_excel()

    logger.info('Completed all group updates!')


def params_from_json(params_file):
    '''Load a list of group parameters from a JSON file.'''
    with open(params_file, 'r') as json_file:
        params_list = json.load(json_file)
    return params_list


def cmgs_from_json(params_file):
    '''Generate `CMGroup` objects from a JSON file.'''
    for params in params_from_json(params_file):
        yield CMGroup(params)
