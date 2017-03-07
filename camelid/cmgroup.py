# coding: utf-8

"""Chemical and material group class definition."""

from __future__ import unicode_literals

import os
from os.path import join as pjoin
import logging
import json
from itertools import islice
from time import asctime, sleep
from datetime import date

from pandas import DataFrame, ExcelWriter
from boltons.jsonutils import JSONLIterator

from . import logconf
from . import pubchemutils as pc
from .errors import WebServiceError

logger = logging.getLogger(__name__)

# TODO: Update
BASE_PARAMS = {
    'materialid': None,
    'name': '',
    'searchtype': None,
    'structtype': None,
    'searchstring': None,
    'last_updated': None,
    'current_update': None
}

# TODO: Update
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


class CMGroup(object):  # TODO: Add better description in docstring
    """
    Chemical and material group class.

    Data, logs, and common parameters for each :class:`CMGroup` are managed by
    an associated :class:`camelid.run.CamelidEnv` project environment.

    Parameters:
        params (dict): A dictionary containing the parameters of the compound
            group. Its keys should include all the keys in ``BASE_PARAMS``.
        env (:class:`camelid.env.CamelidEnv`): The project environment to use.
    """
    def __init__(self, params, env):
        try:
            self._materialid = params['materialid']
        except KeyError:
            logger.critical('Cannot initialize CMGroup without materialid')
            raise

        logger.info('Creating %s', self)

        self._data_path = env.data_path
        self._results_path = env.results_path

        # Parameters will be stored here, including updates during runtime.
        self._params_file = pjoin(self._data_path,
                                  '{}_params.json'.format(self.materialid))

        # Compounds list is stored in this JSONL file, one dict per line.
        self._compounds_file = pjoin(self._data_path,
                                     '{}_cpds.jsonl'.format(self.materialid))

        # List of CIDs returned from last PubChem search would be stored here.
        self._cids_file = pjoin(self._data_path,
                                '{}_cids.json'.format(self.materialid))

        self._params = self.get_params()
        self._params.update(params)
        self.save_params()

        # Determine whether we are checking for new additions to the group.
        try:
            date_args = [int(x) for x in
                         self.params['last_updated'].split('-')]
            self._last_updated = date(*date_args)
        except (KeyError, TypeError, ValueError):
            logger.info('No date or invalid date format for %s: '
                        'updates will retrieve all search results', self)
            self._last_updated = None

        self._listkey = None

    @property
    def materialid(self):
        """The numeric ID of the chemical/material group."""
        return self._materialid

    @property
    def params(self):
        """
        Parameters used to construct the CMG, including any runtime changes.
        """
        return self._params

    @property
    def name(self):
        """The name of the chemical/material group."""
        if 'name' in self.params:
            return self.params['name']

    @property
    def searchtype(self):
        """
        The type of structure-based search used to define this group.

        Currently only `substructure` is supported.
        """
        return self.params['searchtype']

    @property
    def structtype(self):
        """
        The form of structure notation used for searching, e.g. ``smiles``.

        Currently only works with ``smiles``.
        """
        return self.params['structtype']

    @property
    def searchstring(self):
        """
        Query for structure-based searches, e.g. a string in SMILES notation.
        """
        if 'searchstring' in self.params:
            return self.params['searchstring']

    @property
    def last_updated(self):
        """
        When the group was last updated, according to the supplied parameters.

        This property is either a :class:`datetime.date` object or ``None``.
        Note that :class:`datetime.date` can't be serialized to JSON or Excel
        without first converting to string.
        """
        return self._last_updated

    @property
    def listkey(self):
        return self._listkey

    @listkey.setter
    def listkey(self, new_listkey):
        self._listkey = new_listkey

    def save_params(self):
        """
        Write parameters to a JSON file in the project environment.

        This allows some runtime-generated data (i.e., current update date)
        to persist when resuming after a failure.
        """
        with open(self._params_file, 'w') as json_file:
            logger.debug('Saving current parameters of %s to file', self)
            json.dump(self.params, json_file)

    def get_params(self):
        """
        Return saved parameters from a previous run, or default parameters.

        Returns:
            Parameters as container object, normally :class:`dict`.
        """
        try:
            with open(self._params_file, 'r') as json_file:
                logger.debug('Loading parameters from file for %s', self)
                new_params = json.load(json_file)
                return new_params
        except (FileNotFoundError, json.JSONDecodeError):
            logger.debug('No stored parameters found for %s', self)
            return BASE_PARAMS

    def get_compounds(self):
        """
        Read the compounds list that has been written to to file.

        Returns:
            list: All the compounds that have been added to the group during
                the update process; each compound is a :class:`dict`.
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
        with open(self._cids_file, 'w') as json_file:
            logger.debug('Saving search results for %s containing %i CIDs',
                         self, len(cids))
            json.dump(cids, json_file)

    def clear_data(self):
        """Delete data files generated from previous operations."""
        logger.debug('Removing data for %s', self)
        for file in (self._params_file,
                     self._cids_file,
                     self._compounds_file):
            try:
                os.remove(file)
            except OSError:
                logger.warning('Failed to delete %s', file)

    def __repr__(self):
        return 'CMGroup({0})'.format(self.materialid)

    def to_html_by_cid(self, out_path=None):
        # TODO
        # see hypertext.cids_to_html
        pass

    def to_excel(self, out_path=None):  # TODO: Will need update.
        """
        Output the compounds list & group parameters to an Excel spreadsheet.
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

        if out_path:
            out_path = os.path.abspath(out_path)
        else:
            out_path = pjoin(self._results_path,
                              '{0}.xlsx'.format(self.materialid))

        logger.info('Writing Excel output to: %s', out_path)

        with ExcelWriter(out_path) as writer:
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
                self.save_params()
            else:
                raise NotImplementedError('Sorry, can only do substructure '
                                          'searches in PubChem at this time')
        except WebServiceError:
            logger.exception('Failed to initiate PubChem search for %s', self)
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

        try:
            if listkey_args:
                cids = pc.retrieve_search_results(self.listkey, **listkey_args)
            else:
                cids = pc.retrieve_search_results(self.listkey)

            self.save_returned_cids(cids)
            logger.debug('Clearing ListKey for %s', self)
            self.listkey = None
        except WebServiceError:
            logger.exception('Failed to retrieve search results for %s', self)

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


# TODO: This should create a browseable HTML directory of all groups.
def batch_cmg_search(groups, resume_update=False, wait=120, **kwargs):
    """
    Perform PubChem searches for many CMGs and output all to Excel files.

    Parameters:
        groups (iterable): The CMGs to be updated.
        resume_update (bool): If `True`, does not perform a new search, but
            looks for previous search results saved in the project environment
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


def cmgs_from_json(json_file, env):
    """
    Generate :class:`CMGroup` objects from a JSON file.

    Parameters:
        json_file (str): Path to a JSON file containing parameters for any
            number of CMGs.
        env (:class:`camelid.run.CamelidEnv`): The project environment. This
            determines the environment used for the :class:`CMGroup` objects.

    Yields:
        :class:`CMGroup`: Chemical/material group objects.
    """
    logger.debug('Reading group parameters from %s', json_file)
    for params in params_from_json(json_file):
        yield CMGroup(params, env)
