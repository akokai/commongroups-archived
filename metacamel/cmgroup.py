# -*- coding: utf-8 -*-
'''Chemical and material group class definition.'''

from __future__ import unicode_literals

import os
import logging
from copy import deepcopy
from itertools import islice
from time import asctime, sleep

from pandas import DataFrame, ExcelWriter
from boltons.fileutils import mkdir_p

from . import logconf
from . import pubchemutils as pc

logger = logging.getLogger('metacamel.cmgroup')

_CUR_PATH = os.path.dirname(os.path.abspath(__file__))
_PARENT_PATH = os.path.dirname(_CUR_PATH)
DATA_PATH = os.path.join(_PARENT_PATH, 'data')
mkdir_p(DATA_PATH)
RESULTS_PATH = os.path.join(_PARENT_PATH, 'results')
mkdir_p(RESULTS_PATH)

# These are used for Excel export.
params_keys = ['materialid', 'name', 'searchtype',
               'structtype', 'searchstring', 'last_updated']
compounds_keys = ['CID', 'CASRN_list', 'IUPAC_name']


class CMGroup:
    '''Chemical and material group class.'''

    def __init__(self, params):
        '''
        Initialize from a dict containing all parameters of a compound group.

        The dict should contain ``materialid``, ``name``,` `searchtype``,
        ``structtype``, ``searchstring``, and ``last_updated``. For now...
        '''
        if 'materialid' in params:
            self._materialid = params['materialid']
        else:
            logger.warning('Initializing CMGroup with no given materialid.')
            self._materialid = asctime().replace(' ', '_').replace(':', '')
        self._params = params
        self._compounds = []
        self._listkey = None
        logger.debug('Created %s' % self)

    @property
    def materialid(self):
        '''The alphanumeric ID of the chemical/material group.'''
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

        Currently only ``substructure`` is of any use.
        '''
        if 'searchtype' in self._params:
            return self._params['searchtype']

    @property
    def structtype(self):
        '''
        The form of structure notation used for searching, e.g. ``smiles``.

        Currently only works with ``smiles``.
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
        When the group was last updated in the chemical & material library.

        Should be some standard date format. TBD! Not implemented yet!
        '''
        if 'last_updated' in self._params:
            return self._params['last_updated']

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

    @property
    def compounds_list(self):
        '''Return a deep copy of the list of compounds (a list of dicts).'''
        return deepcopy(self._compounds)

    def to_excel(self, file_path=None):
        '''
        Output the list of compounds & parameters to an Excel spreadsheet.
        '''
        params_frame = DataFrame(self._params,
                                 columns=params_keys, index=[0])
        params_frame.set_index('materialid', inplace=True)
        compounds_frame = DataFrame(self._compounds,
                                    columns=compounds_keys)
        if not file_path:
            file_path = os.path.join(RESULTS_PATH,
                                     '{0}.xlsx'.format(self.materialid))
        logger.info('Writing Excel output to: %s' % file_path)
        with ExcelWriter(file_path) as writer:
            params_frame.to_excel(writer, sheet_name=self.materialid)
            compounds_frame.to_excel(writer, sheet_name='Compounds')

    def init_pubchem_search(self):
        '''
        Initiate an async PubChem structure-based search and save the ListKey.
        '''
        try:
            if self.searchtype == 'substructure':
                logger.debug('Initiating PubChem substructure search for %s.'
                             % self.materialid)
                key = pc.init_substruct_search(self.searchstring,
                                               method=self.structtype)
                logger.debug('Setting ListKey for %s: %s.', key,
                             self.materialid)
                self.listkey = key
            else:
                logger.warning('Sorry, can only do substructure searches in PubChem at this time.')
                raise NotImplementedError
        except KeyError as exception:
            logger.error('Missing parameters: %s', exception)
            raise

    def retrieve_pubchem_compounds(self, **kwargs):
        '''
        Retrieve results from a previously-initiated async PubChem search.
        '''
        # TO DO: Compare date updated against CID creation date.
        # Add a kwarg to control this.
        if not self.listkey:
            logger.error('No existing ListKey to retrieve search results.')
            return None     # Raise an exception instead?

        logger.debug('Retrieving PubChem search results for %s.'
                     % self.materialid)
        listkey_args = pc.filter_listkey_args(**kwargs) if kwargs else None
        cids = pc.retrieve_search_results(self.listkey, **listkey_args)

        logger.debug('Looking up details for %i CIDs.' % len(cids))
        new_compounds = list(islice(pc.get_compound_info(cids), None))

        logger.info('Adding %i compounds from PubChem search to group %s.',
                     len(new_compounds), self.materialid)
        self._compounds.extend(new_compounds)

        logger.debug('Clearing ListKey for %s.' % self.materialid)
        del self.listkey

    def pubchem_update(self, wait=10, **kwargs):
        '''
        Perform a PubChem search to update a compound group.
        '''
        # TO DO: Consider last_updated...
        self.init_pubchem_search()
        logger.debug('Waiting %i s before retrieving search results.' % wait)
        sleep(wait)
        self.retrieve_pubchem_compounds(**kwargs)

    def screen(self, compound):
        '''Screen a new compound for membership in the group.'''
        if compound in self:
            return True
        else:
            # Placeholder!
            raise NotImplementedError


def batch_group_search(groups, wait=60, **kwargs):
    '''
    Perform substructure searches for many groups all at once.
    '''
    for group in groups:
        group.init_pubchem_search()

    sleep(wait)

    for group in groups:
        group.retrieve_pubchem_compounds(**kwargs)
