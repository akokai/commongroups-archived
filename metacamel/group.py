# -*- coding: utf-8 -*-
'''Chemical and material group class definition.'''

from __future__ import unicode_literals

import os
import logging
from copy import deepcopy
from itertools import islice
from time import asctime, sleep

import logging_conf
import pubchemutils as pc

logger = logging.getLogger('metacamel.group')

_CUR_PATH = os.path.dirname(os.path.abspath(__file__))
_PARENT_PATH = os.path.dirname(_CUR_PATH)
DATA_PATH = os.path.join(_PARENT_PATH, 'data')
mkdir_p(DATA_PATH)


class CMGroup:
    '''Chemical and material group class.'''

    def __init__(self, params):
        '''
        Initialize from a dict containing all parameters of a compound group.

        The dict should contain ``materialid``, ``name``,` `searchtype``,
        ``method``, ``searchstring``, and ``last_updated``. This may change.
        '''
        if 'materialid' in params:
            self._materialid = params['materialid']
        else:
            logger.warning('Initializing CMGroup with no given materialid.')
            self._materialid = asctime().replace(' ', '_').replace(':', '')
        self._params = params
        self._compounds = []
        self._listkey = None

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
    def last_updated(self):
        '''
        When the group was last updated in the chemical & material library.

        Should be some standard date format, TBD!
        No date checking functionality implemented yet!
        '''
        if 'last_updated' in self._params:
            return self._params['last_updated']

    @property
    def listkey(self):
        return self._listkey

    @listkey.setter
    def listkey(self, new_listkey):
        self._listkey = new_listkey

    @listkey.deleter
    def listkey(self):
        self._listkey = None

    def __len__(self):
        '''Return the length of the internal list of compounds.'''
        return len(self._compounds)

    def __contains__(self, compound):
        '''
        Check if a compound is already in the group list of compounds.
        '''
        return compound in self._compounds

    def __repr__(self):
        return 'CMGroup({0})'.format(self.materialid)

    @property
    def compounds_list(self):
        '''Return a deep copy of the list of compounds (a list of dicts).'''
        return deepcopy(self._compounds)

    def to_excel(self):
        '''
        Output the list of compounds & parameters to an Excel spreadsheet.
        '''
        # PLACEHOLDER!
        raise NotImplementedError

    def init_pubchem_search(self):
        '''
        Initiate an async PubChem structure-based search and save the ListKey.
        '''
        try:
            if self._params['method'] == 'substructure':
                logger.debug('Initiating PubChem substructure search for %s.'
                             % self.materialid)
                key = pc.init_substruct_search(self._params['searchstring'],
                                               method=self._params['method'])
                logger.debug('Setting ListKey for %s: %s.', key,
                             self.materialid)
                self.listkey = key
            else:
                logger.warning('Sorry, can only do substructure searches in PubChem at this time.')
                raise NotImplementedError
        except KeyError as exception:
            logger.error('Missing parameters: %s', exception)
            raise

    def retrieve_pubchem_compounds(self):
        '''
        Retrieve results from a previously-initiated async PubChem search.
        '''
        # TO DO: Compare date updated against CID creation date.
        # Add a kwarg to control this.
        if not self._listkey:
            logger.error('No existing ListKey to retrieve search results.')
            return None     # Raise an exception instead?
        logger.debug('Retrieving PubChem search results for %s'
                     % self.materialid)
        cids = pc.retrieve_search_results(self._listkey)
        logger.debug('Looking up details for %i CIDs.' % len(cids))
        new_compounds = list(islice(pc.details_from_cids(cids)))
        logger.info('Adding %i compounds from PubChem search to group %s.',
                     len(new_compounds), self.materialid)
        self._compounds.append(new_compounds)
        logger.debug('Clearing ListKey for %s' % self.materialid)
        del self.listkey

    def pubchem_update(self, wait=10):
        '''
        Perform a PubChem search to update a compound group.
        '''
        # TO DO: Consider last_updated...
        self.init_pubchem_search()
        logger.debug('Waiting %i s before retrieving search results.' % wait)
        sleep(wait)
        self.retrieve_pubchem_compounds()

    def screen(self, compound):
        '''Screen a new compound for membership in the group.'''
        if compound in self:
            return True
        else:
            # Placeholder!
            raise NotImplementedError


def batch_substruct_search(groups, batch_wait=120):
    '''
    Perform substructure searches for many groups all at once.
    '''
    for group in groups:
        group.init_pubchem_search()

    sleep(batch_wait)

    for group in groups:
        group.retrieve_pubchem_compounds()
