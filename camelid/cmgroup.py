# coding: utf-8

"""Chemical and material group class definition."""

import os
from os.path import join as pjoin
import logging
import json
from itertools import islice
from datetime import date

from pandas import DataFrame, ExcelWriter
# from boltons.jsonutils import JSONLIterator

from camelid import logconf  # pylint: disable=unused-import
from camelid import pubchemutils as pc
from camelid.hypertext import cids_to_html
from camelid.errors import WebServiceError

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

BASE_PARAMS = {
    'cmg_id': None,
    'name': 'no name',
    'method': None,
    'structure_type': None,
    'structure': None,
    'function': None,
    'description': ''
}


class CMGroup(object):
    """
    Compound group object.

    Initialize with parameters that should be known in advance of any querying,
    and are assumed to stay unchanged. Process using the ``_TODO_`` method(s)
    and find a computed summary of results in the ``info`` attribute. Add your
    own annotations using :func:`add_info`.

    Output and logs for each :class:`CMGroup` are managed by an associated
    :class:`camelid.env.CamelidEnv` project environment.

    Parameters:
        params (dict): A dictionary containing the parameters of the compound
            group. See :doc:`params`.
        env (:class:`camelid.env.CamelidEnv`): The project environment to use.
    """
    def __init__(self, params, env):
        try:
            assert 'cmg_id' in params
        except (AssertionError, KeyError):
            logger.critical('Cannot initialize CMGroup without cmg_id')
            raise
        self._params = BASE_PARAMS
        self._params.update(params)
        self.info = {'description': self._params['description']}
        self.data_path = env.data_path         # Needed?
        self.results_path = env.results_path
        logger.info('Created %s', self)

    # These descriptor attributes are partly for convenience, and partly to
    # mark the intention of not modifying the params.
    @property
    def cmg_id(self):
        """Unique identifier of the compound group."""
        return self._params['cmg_id']

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
        """String representation of molecular structural pattern."""
        return self._params['structure']

    def add_info(self, info):
        """
        Add information to the group as key-value pairs.

        Parameters:
            data (dict): A dict containing any number of items.
        """
        self.info.update(info)

    def __repr__(self):
        return 'CMGroup({})'.format(self._params)

    def __str__(self):
        return 'CMGroup({})'.format(self.cmg_id)

    def query_update(self, que, conn, count_fields):  # TODO
        """
        Do a query and update given fields...

        Parameters:
            fields: Iterable of SQLAlchemy selctable objects to select from.
        """
        pass

    # def cids_to_html(self, out_path=None):
    #     if not out_path:
    #         out_path = pjoin(self.results_path,
    #                          '{}.html'.format(self.results_path))
    #     cids_to_html(cids, out_path, self.name, self.info['description'])
    #     pass

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

    def init_pubchem_search(self):  # TODO: Delete
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

    def retrieve_pubchem_search(self, **kwargs):  # TODO: Delete
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

    def pubchem_update(self, wait=10, **kwargs):  # TODO: Delete
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
