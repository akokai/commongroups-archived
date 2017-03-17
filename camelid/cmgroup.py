# coding: utf-8

"""Chemical and material group class definition."""

import os
from os.path import join as pjoin
import logging
import json
from itertools import islice
from datetime import date

from pandas import DataFrame, ExcelWriter
from boltons.jsonutils import JSONLIterator

from camelid import logconf  # pylint: disable=unused-import
from camelid import pubchemutils as pc
from camelid.errors import WebServiceError

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

BASE_PARAMS = {
    'cmg_id': None,
    'name': 'no name',
    'method': None,
    'structure_type': None,
    'structure': None,
    'function': None,
    'notes': ''
}


class CMGroup(object):  # TODO: Add better description in docstring
    """
    Compound group class.

    Data, logs, and common parameters for each :class:`CMGroup` are managed by
    an associated :class:`camelid.env.CamelidEnv` project environment.

    Parameters:
        params (dict): A dictionary containing the parameters of the compound
            group. See :doc:`params`.
        env (:class:`camelid.env.CamelidEnv`): The project environment to use.
    """
    def __init__(self, params, env):
        try:
            self._cmg_id = params['cmg_id']
        except KeyError:
            logger.critical('Cannot initialize CMGroup without cmg_id')
            raise

        logger.info('Creating %s', self)

        self._params = BASE_PARAMS
        self._params.update(params)
        self._data_path = env.data_path         # Needed?
        self._results_path = env.results_path

    # TODO: Update properties. This should be based on what attributes are
    # actually accessed in the rest of the code.
    @property
    def cmg_id(self):
        """Unique identifier of the compound group."""
        return self._cmg_id

    @property
    def name(self):
        """Name of the compound group."""
        return self._params['name']

    @property
    def method(self):
        """Method used to identify compound group members."""
        return self._params['method']

    @property
    def structure_type(self):
        """Type of structure notation for query: SMILES or SMARTS."""
        return self._params['structure_type']

    @property
    def structure(self):
        """String representation of molecular structure."""
        return self._params['structure']

    @property
    def notes(self):
        """Optional text describing the compound group."""
        return self._params['notes']

    def __repr__(self):
        return 'CMGroup({0})'.format(self.cmg_id)

    def to_html_by_cid(self, out_path=None):
        # TODO
        # see hypertext.cids_to_html
        pass

    def to_excel(self, out_path=None):  # TODO: Will need update.
        """
        Output the compounds list & group parameters to an Excel spreadsheet.
        """
        params_frame = DataFrame(self._params,
                                 columns=self._params.keys(),
                                 index=[0]).set_index('cmg_id')
        params_frame.set_index('cmg_id', inplace=True)

        compounds_frame = DataFrame(self.get_compounds())   # TODO
                                    # columns=BASE_PARAMS.keys())  # not this
        compounds_frame.CMG_ID = self.cmg_id
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
                             '{0}.xlsx'.format(self.cmg_id))

        logger.info('Writing Excel output to: %s', out_path)

        with ExcelWriter(out_path) as writer:
            params_frame.to_excel(writer, sheet_name='CMG Parameters')
            compounds_frame.to_excel(writer, sheet_name='Compounds')

    def init_pubchem_search(self):
        """
        Initiate an async PubChem structure-based search and save the ListKey.
        """
        try:
            if self.method == 'substructure':
                logger.info('Initiating PubChem substructure search for %s',
                            self)
                key = pc.init_substruct_search(self.searchstring,
                                               method=self.structure_type)
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
    Load a list of :class:`CMGroup` parameters from a JSON file.

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
        env (:class:`camelid.env.CamelidEnv`): The project environment. This
            determines the environment used for the :class:`CMGroup` objects.

    Yields:
        :class:`CMGroup`: Chemical/material group objects.
    """
    logger.debug('Reading group parameters from %s', json_file)
    for params in params_from_json(json_file):
        yield CMGroup(params, env)
