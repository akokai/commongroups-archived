# -*- coding: utf-8 -*-
'''Chemical and material group class definition.'''

from __future__ import unicode_literals

import os
import logging
import json
from itertools import islice
from time import asctime, sleep
from datetime import date

from pandas import DataFrame, ExcelWriter
from boltons.jsonutils import JSONLIterator

import logconf
import pubchemutils as pc
from run_camelid import CamelidEnv

logger = logging.getLogger(__name__)

# The column headings used for Excel exports of group parameters:
PARAMS_COLS = ['materialid', 'name', 'searchtype', 'structtype',
               'searchstring', 'last_updated', 'current_update']
               # 'cpds_count', 'casrn_count']
               # TODO: add those to export

# The column headings used for Excel exports of compound lists.
# Most correspond to keys that will be present in compound data dicts
# returned from PubChem searches. Some are generated upon export.
EXPORT_COLS = ['CASRN',         # Generated from CASRN_list upon export
               'IUPAC_name',
               'CMG_ID',        # Generated from CMGroup attributes
               'Action',
               'CASRN_list',
               'CID',
               'creation_date']


class CMGroup:
    '''Chemical and material group class.'''

    def __init__(self, params, env=None):
        '''
        Initialize from a dict containing all parameters of a compound group.

        The dict should contain `materialid`, `name`,` `searchtype`,
        `structtype`, `searchstring`, and `last_updated`. (For now...)
        The `env` argument is a `CamelidEnv` object representing the current
        project. If unspecified, a new 'default' project will be created.
        '''
        try:
            self._materialid = params['materialid']
        except KeyError:
            logger.critical('Cannot initialize CMGroup without materialid.')
            raise

        env = env or CamelidEnv()
        self._data_path = env.data_path
        self._results_path = env.results_path

        logger.debug('Created %s', self)

        self._params = params
        self._listkey = None

        # Compounds list is stored in this JSONL file, one dict per line.
        self._compounds_file = os.path.join(self._data_path,
                                            self.materialid + '_cpds.jsonl')

        # List of CIDs returned from last PubChem search would be stored here.
        self._cids_file = os.path.join(self._data_path,
                                       self.materialid + '_cids.json')

        # Determine whether we are checking for new additions to the group.
        try:
            date_args = [int(x) for x in
                         self._params['last_updated'].split('-')]
            self._last_updated = date(*date_args)
        except (KeyError, TypeError, ValueError):
            logger.info('No date or invalid date format for %s. '
                        'Updates will retrieve all search results.', self)
            self._last_updated = None

        # Track date of current update for this session.
        # Could potentially result in missed CIDs, if the update process lasts
        # > 1 day and some new compounds are added to PubChem in the meantime.
        self._params.update({'current_update': date.today().isoformat()})

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

    def get_compounds(self):
        '''
        Read compounds (list of dicts) from file and store as an attribute.
        '''
        try:
            with open(self._compounds_file, 'r') as cpds_file:
                lines = JSONLIterator(cpds_file)
                new_compounds = list(islice(lines, None))
                logger.debug('Loading %i compounds from JSON for %s.',
                             len(new_compounds), self)
                return new_compounds
        except (FileNotFoundError, ValueError, StopIteration):
            logger.debug('No compounds in %s.', self)
            return []

    def get_returned_cids(self):
        '''
        Load the list of CIDs returned by the last PubChem search from file.
        '''
        try:
            with open(self._cids_file, 'r') as json_file:
                cids = json.load(json_file)
                logger.debug('Loading search results: %i CIDs for %s.',
                             len(cids), self)
                return cids
        except (FileNotFoundError, json.JSONDecodeError):
            logger.debug('No existing CIDs found for %s.', self)
            return []

    def save_returned_cids(self, cids):
        '''
        Save the list of CIDs returned by the last PubChem search to file.
        '''
        logger.debug('Saving search results for %s containing %i CIDs.',
                     self, len(cids))
        with open(self._cids_file, 'w') as json_file:
            json.dump(cids, json_file)

    def clean_data(self):
        '''Delete JSON files generated from previous operations.'''
        logger.debug('Removing data for %s.', self)
        try:
            os.remove(self._cids_file)
            os.remove(self._compounds_file)
        except OSError:
            logger.exception('Failed to delete all files.')

    def __repr__(self):
        '''Return a string identifying the object.'''
        return 'CMGroup({0})'.format(self.materialid)

    def to_excel(self, file_path=None):
        '''
        Output the list of compounds & parameters to an Excel spreadsheet.
        '''
        # TODO: add to export: total number of cpds, number with CASRN
        params_frame = DataFrame(self._params,
                                 columns=PARAMS_COLS, index=[0])
        params_frame.set_index('materialid', inplace=True)

        compounds_frame = DataFrame(self.get_compounds(),
                                    columns=EXPORT_COLS)
        compounds_frame.CMG_ID = self.materialid
        compounds_frame.Action = 'add'

        def first_casrn(casrns):
            if casrns:
                return casrns.split()[0]
            else:
                return ''

        compounds_frame.CASRN = compounds_frame.CASRN_list.apply(first_casrn)

        if file_path:
            file_path = os.path.abspath(file_path)
        else:
            file_path = os.path.join(self._results_path,
                                     '{0}.xlsx'.format(self.materialid))

        logger.info('Writing Excel output to: %s', file_path)

        with ExcelWriter(file_path) as writer:
            params_frame.to_excel(writer, sheet_name='CMG Parameters')
            compounds_frame.to_excel(writer, sheet_name='Compounds')

    def init_pubchem_search(self):
        '''
        Initiate an async PubChem structure-based search and save the ListKey.
        '''
        try:
            if self.searchtype == 'substructure':
                logger.info('Initiating PubChem substructure search for %s.',
                            self)
                key = pc.init_substruct_search(self.searchstring,
                                               method=self.structtype)
                logger.debug('Setting ListKey for %s: %s.', self, key)
                self.listkey = key
            else:
                raise NotImplementedError('Sorry, can only do substructure '
                                          'searches in PubChem at this time.')
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

        logger.info('Retrieving PubChem search results for %s.', self)

        listkey_args = pc.filter_listkey_args(**kwargs) if kwargs else None

        if listkey_args:
            cids = pc.retrieve_search_results(self.listkey, **listkey_args)
        else:
            cids = pc.retrieve_search_results(self.listkey)

        # This sets `self.returned_cids` and also saves the list to JSON.
        self.save_returned_cids(cids)

        logger.debug('Clearing ListKey for %s.', self)
        self.listkey = None

    def update_from_cids(self):
        '''
        Retrieve information on a list of CIDs and add new ones to the CMG.
        '''
        returned_cids = self.get_returned_cids()

        if not returned_cids:
            logger.warning('No CIDs to update %s.', self)
            return None

        try:
            with open(self._compounds_file, 'r') as cpds_file:
                lines = JSONLIterator(cpds_file, reverse=True)
                last_item = lines.next()
            last_cid = last_item['CID']
            new_index = returned_cids.index(last_cid) + 1
            cids = returned_cids[new_index:]
            logger.info('Resuming update of %s; last CID added: %s.',
                        self, last_cid)
        except (FileNotFoundError, ValueError, StopIteration):
            cids = returned_cids
            logger.info('Starting update of %s from search results.', self)

        logger.info('Looking up information for %i CIDs.', len(cids))
        new = pc.gen_compounds(cids, self.last_updated)

        while True:
            new_compounds = list(islice(new, 5))
            if new_compounds == []:
                break
            with open(self._compounds_file, 'a') as cpds_file:
                for cpd in new_compounds:
                    cpds_file.write(json.dumps(cpd) + '\n')
            sleep(1)

        logger.info('Completed PubChem update for %s.', self)

    def pubchem_update(self, wait=10, **kwargs):
        '''
        Perform a PubChem search to update a compound group.
        '''
        self.init_pubchem_search()
        logger.info('Waiting %i s before retrieving search results.', wait)
        sleep(wait)
        self.retrieve_pubchem_search(**kwargs)
        self.update_from_cids()
        self.to_excel()

    def screen(self, compound):
        '''Screen a new compound for membership in the group.'''
        # TODO: Placeholder!
        if compound in self.get_compounds():
            return True
        else:
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
        group.update_from_cids()
        group.to_excel()

    logger.info('Completed all group updates!')


def params_from_json(params_file):
    '''Load a list of group parameters from a JSON file.'''
    with open(params_file, 'r') as json_file:
        params_list = json.load(json_file)
    return params_list


def cmgs_from_json(params_file, env):
    '''
    Generate `CMGroup` objects from a JSON file, with a given `CamelidEnv`.
    '''
    for params in params_from_json(params_file):
        yield CMGroup(params, env)
