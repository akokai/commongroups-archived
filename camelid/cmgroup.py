# -*- coding: utf-8 -*-
"""Chemical and material group class definition."""

from __future__ import unicode_literals

import os
import logging
import json
from itertools import islice
from time import asctime, sleep
from datetime import date

from pandas import DataFrame, ExcelWriter
from boltons.jsonutils import JSONLIterator

from . import logconf
from . import pubchemutils as pc

logger = logging.getLogger(__name__)

# The column headings used for Excel exports of group information:
PARAMS_COLS = ['materialid', 'name', 'searchtype', 'structtype',
               'searchstring', 'last_updated', 'current_update',
               'num_compounds', 'num_casrn']

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


class CMGroup(object):
    """
    Chemical and material group class.

    Data are stored as filed in the project environment associated with the
    :class:`CMGroup`.

    Parameters:
        params (dict): A dictionary containing the parameters of the compound
            group. It should contain: ``materialid``, ``name``,
            ``searchtype``, ``structtype``, ``searchstring``, and
            ``last_updated``. (For now...)
        env (:class:`camelid.run.CamelidEnv`): The project environment to use.
    """
    def __init__(self, params, env):
        try:
            self._materialid = params['materialid']
        except KeyError:
            logger.critical('Cannot initialize CMGroup without materialid')
            raise

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
            logger.info('No date or invalid date format for %s: '
                        'updates will retrieve all search results', self)
            self._last_updated = None

        self._params['current_update'] = None

    @property
    def materialid(self):
        """The numeric ID of the chemical/material group."""
        return self._materialid

    @property
    def name(self):
        """The name of the chemical/material group."""
        if 'name' in self._params:
            return self._params['name']

    @property
    def searchtype(self):
        """
        The type of structure-based search used to define this group.

        Currently only `substructure` is supported.
        """
        if 'searchtype' in self._params:
            return self._params['searchtype']

    @property
    def structtype(self):
        """
        The form of structure notation used for searching, e.g. `smiles`.

        Currently only works with `smiles`.
        """
        if 'structtype' in self._params:
            return self._params['structtype']

    @property
    def searchstring(self):
        """
        Query for structure-based searches, e.g. a string in SMILES notation.
        """
        if 'searchstring' in self._params:
            return self._params['searchstring']

    @property
    def last_updated(self):
        """
        When the group was last updated, according to the supplied parameters.

        This property is either a python `datetime.date` object, or `None`.
        Note that `datetime.date` can't be serialized to JSON or Excel
        without first converting to string.
        """
        return self._last_updated

    @property
    def listkey(self):
        """Temporary ListKey for asynchronous PubChem searches."""
        return self._listkey

    @listkey.setter
    def listkey(self, new_listkey):
        self._listkey = new_listkey

    def get_compounds(self):
        """
        Read compounds (list of dicts) from file and store as an attribute.
        """
        try:
            with open(self._compounds_file, 'r') as cpds_file:
                lines = JSONLIterator(cpds_file)
                new_compounds = list(islice(lines, None))
                logger.debug('Loading %i compounds from JSON for %s',
                             len(new_compounds), self)
                return new_compounds
        except (FileNotFoundError, ValueError, StopIteration):
            logger.debug('No compounds in %s', self)
            return []

    def get_returned_cids(self):
        """
        Load the list of CIDs returned by the last PubChem search from file.
        """
        try:
            with open(self._cids_file, 'r') as json_file:
                cids = json.load(json_file)
                logger.debug('Loading search results: %i CIDs for %s',
                             len(cids), self)
                return cids
        except (FileNotFoundError, json.JSONDecodeError):
            logger.debug('No existing CIDs found for %s', self)
            return []

    def save_returned_cids(self, cids):
        """
        Save the list of CIDs returned by the last PubChem search to file.
        """
        logger.debug('Saving search results for %s containing %i CIDs',
                     self, len(cids))
        with open(self._cids_file, 'w') as json_file:
            json.dump(cids, json_file)

    def clear_data(self):
        """Delete JSON files generated from previous operations."""
        logger.debug('Removing data for %s', self)
        try:
            os.remove(self._cids_file)
            os.remove(self._compounds_file)
        except OSError:
            logger.exception('Failed to delete all files')

    def __repr__(self):
        """Return a string identifying the object."""
        return 'CMGroup({0})'.format(self.materialid)

    def to_excel(self, file_path=None):
        """
        Output the list of compounds & parameters to an Excel spreadsheet.
        """
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
                return None

        compounds_frame.CASRN = compounds_frame.CASRN_list.apply(first_casrn)

        # Count the number of compounds and the number with CASRN.
        params_frame.num_compounds = len(compounds_frame)
        params_frame.num_casrn = compounds_frame.CASRN.count()

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
        """
        Initiate an async PubChem structure-based search and save the ListKey.
        """
        try:
            if self.searchtype == 'substructure':
                logger.info('Initiating PubChem substructure search for %s',
                            self)
                key = pc.init_substruct_search(self.searchstring,
                                               method=self.structtype)
                logger.debug('Setting ListKey for %s: %s', self, key)
                self.listkey = key
                # Track date of current update:
                self._params.update(
                    {'current_update': date.today().isoformat()})
            else:
                raise NotImplementedError('Sorry, can only do substructure '
                                          'searches in PubChem at this time')
        except KeyError:
            logger.exception('Missing parameters')
            raise

    def retrieve_pubchem_search(self, **kwargs):
        """
        Retrieve results from a previously-initiated async PubChem search.
        """
        if not self.listkey:
            logger.error('No existing ListKey to retrieve search results')
            return None     # Raise an exception instead?

        logger.info('Retrieving PubChem search results for %s', self)

        listkey_args = pc.filter_listkey_args(**kwargs) if kwargs else None

        if listkey_args:
            cids = pc.retrieve_search_results(self.listkey, **listkey_args)
        else:
            cids = pc.retrieve_search_results(self.listkey)

        # This sets `self.returned_cids` and also saves the list to JSON.
        self.save_returned_cids(cids)

        logger.debug('Clearing ListKey for %s', self)
        self.listkey = None

    def update_from_cids(self):
        """
        Retrieve information on a list of CIDs and add new ones to the CMG.
        """
        returned_cids = self.get_returned_cids()

        if not returned_cids:
            logger.warning('No CIDs to update %s', self)
            return None

        try:
            with open(self._compounds_file, 'r') as cpds_file:
                lines = JSONLIterator(cpds_file, reverse=True)
                last_item = lines.next()
            last_cid = last_item['CID']
            new_index = returned_cids.index(last_cid) + 1
            cids = returned_cids[new_index:]
            logger.info('Resuming update of %s; last CID added: %s',
                        self, last_cid)
        except (FileNotFoundError, ValueError, StopIteration):
            cids = returned_cids
            logger.info('Starting update of %s from search results', self)

        logger.info('Looking up information for %i CIDs', len(cids))
        new = pc.gen_compounds(cids, self.last_updated)

        while True:
            new_compounds = list(islice(new, 5))
            if new_compounds == []:
                break
            with open(self._compounds_file, 'a') as cpds_file:
                for cpd in new_compounds:
                    cpds_file.write(json.dumps(cpd) + '\n')
            sleep(1)

        logger.info('Completed PubChem update for %s', self)

    def pubchem_update(self, wait=10, **kwargs):
        """
        Perform a PubChem search to update the CMG, and output to Excel.

        Parameters:
            wait (int): Delay (seconds) before retrieving async search results.
            **kwargs: Arbitrary keyword arguments.
        """
        self.init_pubchem_search()
        logger.info('Waiting %i s before retrieving search results', wait)
        sleep(wait)
        self.retrieve_pubchem_search(**kwargs)
        self.update_from_cids()
        self.to_excel()

    def screen(self, compound):
        # TODO: Placeholder!
        # """Screen a new compound for membership in the group."""
        if compound in self.get_compounds():
            return True
        else:
            raise NotImplementedError


def batch_cmg_search(groups, resume_update=False, wait=120, **kwargs):
    """
    Perform PubChem searches for many CMGs and output all to Excel files.

    Parameters:
        groups (iterable): The CMGs to be updated.
        resume_update (bool): If `True`, does not perform a search, but looks
            for previous search results saved in the project environment
            and continues the update process for those search results.
        wait (int): Delay (seconds) before retrieving async search results.
        **kwargs: Arbitrary keyword arguments, such as for pagination of
            search results.
    """
    if not resume_update:
        for group in groups:
            group.init_pubchem_search()

        logger.info('Waiting %i s before retrieving search results', wait)
        sleep(wait)

        for group in groups:
            group.retrieve_pubchem_search(**kwargs)

        logger.info('Completed retrieving all group search results')

    for group in groups:
        group.update_from_cids()
        group.to_excel()

    logger.info('Completed all group updates!')


def params_from_json(params_file):
    """
    Load a list of group parameters from a JSON file.

    Parameters:
        params_file (str): Path to a JSON file containing CMG parameters.

    Returns:
        A container, usually a list of dicts.
    """
    with open(params_file, 'r') as json_file:
        params_list = json.load(json_file)
    return params_list


def cmgs_from_json(env):
    """
    Generate :class:`camelid.cmgroup.CMGroup` objects from a JSON file.

    Parameters:
        env (:class:`camelid.run.CamelidEnv`): The project environment. This
            determines the path to the JSON file and the environment used for
            the :class:`CMGroup` objects that are created.

    Yields:
        :class:`CMGroup`: Chemical/material group objects.
    """
    logger.debug('Reading group parameters from %s', env.params_json)
    for params in params_from_json(env.params_json):
        yield CMGroup(params, env)
