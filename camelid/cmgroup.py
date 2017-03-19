# coding: utf-8

"""Compound group class definition."""

import os
from os.path import join as pjoin
import logging
import json
from itertools import islice
from datetime import date

import pandas as pd
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
}


class CMGroup(object):
    """
    Compound group object.

    Initialize with parameters that should be known in advance of any querying,
    and are assumed to stay unchanged. Process using the ``_TODO_`` method(s)
    and find a computed summary of results in the ``info`` attribute. Add your
    own annotations using :func:`add_info`.

    Data, output, and logs for each :class:`CMGroup` are managed using an
    associated :class:`camelid.env.CamelidEnv` project environment. See
    :doc:`design`.

    Parameters:
        params (dict): A dictionary containing the parameters of the compound
            group. See :doc:`params`.
        env (:class:`camelid.env.CamelidEnv`): The project environment to use.
        description (str): Optional textual description of the compound group.
        info (dict): Optional extra information as key-value pairs. This is
            for loading CMGroup objects from JSON.
    """
    def __init__(self, params, env, description='', info=None):
        try:
            assert 'cmg_id' in params
        except (AssertionError, KeyError):
            logger.critical('Cannot initialize CMGroup without cmg_id')
            raise
        self._params = BASE_PARAMS.copy()
        self._params.update(params)
        self.info = info or {'description': ''}
        if description:
            self.info.update({'description': description})
        self.data_path = env.data_path
        self.results_path = env.results_path
        self._compounds = None
        logger.info('Created %s', self)

    # These read-only descriptor attributes are partly for convenience,
    # and partly to mark the intention to not modify the params.
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

    # Making compounds a read-only attribute because DataFrames are easy to
    # accidentally modify. However, this makes accessing CMG.compounds more
    # expensive because we are creating a copy.
    @property
    def compounds(self):
        """:class:`DataFrame` of compounds."""
        return self._compounds.copy()

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

    def to_dict(self):
        """Return a dict of CMGroup parameters and info."""
        ret = {'params': self._params, 'info': self.info}
        return ret

    def to_json(self, json_path=None):
        """Serialize CMGroup parameters and info as JSON."""
        if not json_path:
            json_path = pjoin(self.results_path, '{}.json'.format(self.cmg_id))
        with open(json_path, 'w') as file:
            json.dump(self.to_dict(), file)

    def compounds_to_pkl(self, pkl_path=None):
        """Serialize DataFrame of compounds to a binary file."""
        if not pkl_path:
            pkl_path = pjoin(self.data_path, '{}.pkl'.format(self.cmg_id))
        self._compounds.to_pickle(pkl_path)

    def compounds_from_pkl(self, pkl_path=None):
        """Import DataFrame of compounds to the CMGroup from file."""
        if not pkl_path:
            pkl_path = pjoin(self.data_path, '{}.pkl'.format(self.cmg_id))
        frame = pd.read_pickle(pkl_path)
        self._compounds = frame

    # TODO: Needs update.
    def to_excel(self, out_path=None):
        """
        Output the compounds list & group parameters to an Excel spreadsheet.
        """
        raise NotImplementedError
    #     params_frame = DataFrame(self._params,
    #                              columns=self._params.keys(),
    #                              index=[0]).set_index('cmg_id')
    #     params_frame.set_index('cmg_id', inplace=True)

    #     compounds_frame = DataFrame(self.get_compounds())
    #                                 # columns=BASE_PARAMS.keys())  # not this
    #     compounds_frame.CMG_ID = self.cmg_id
    #     compounds_frame.Action = 'add'

    #     def first_casrn(casrns):
    #         if casrns:
    #             return casrns.split()[0]
    #         else:
    #             return None

    #     compounds_frame.CASRN = compounds_frame.CASRN_list.apply(first_casrn)

    #     # Count the number of compounds and the number with CASRN.
    #     params_frame.num_compounds = len(compounds_frame)
    #     params_frame.num_casrn = compounds_frame.CASRN.count()

    #     if out_path:
    #         out_path = os.path.abspath(out_path)
    #     else:
    #         out_path = pjoin(self._results_path,
    #                          '{0}.xlsx'.format(self.cmg_id))

    #     logger.info('Writing Excel output to: %s', out_path)

    #     with ExcelWriter(out_path) as writer:
    #         params_frame.to_excel(writer, sheet_name='CMG Parameters')
    #         compounds_frame.to_excel(writer, sheet_name='Compounds')

    # TODO
    # def screen(self, compound):
    #     """Screen a new compound for membership in the group."""
    #     if compound in self.get_compounds():
    #         return True
    #     else:
    #         raise NotImplementedError

# The following are batch operations that can be performed on iterables
# of CMGroups.

# TODO: This should create a browseable HTML directory of all groups.
# def batch_cmg_search(groups, resume_update=False, wait=120, **kwargs):
#     """
#     Perform searches for many CMGs and output all to Excel files.

#     Parameters:
#         groups (iterable): The CMGs to be updated.
#         resume_update (bool): If `True`, does not perform a new search, but
#             looks for previous search results saved in the project environment
#             and continues the update process for those search results.
#         wait (int): Delay (seconds) before retrieving async search results.
#         **kwargs: Arbitrary keyword arguments, such as for pagination of
#             search results.
#     """
#     if not resume_update:
#         for group in groups:
#             group.init_pubchem_search()

#         logger.info('Waiting %i s before retrieving search results', wait)
#         sleep(wait)

#         for group in groups:
#             group.retrieve_pubchem_search(**kwargs)

#         logger.info('Completed retrieving all group search results')

#     for group in groups:
#         group.update_from_cids()
#         group.to_excel()

#     logger.info('Completed all group updates!')


def cmgs_to_json(cmgs, json_path):
    """
    Write information about a number of :class:`CMGroup`s to JSON.

    Parameters:
        cmgs (iterable): The compound group objects to write to JSON.
        json_path (str): Path for JSON file to be written.
    """
    cmg_data = [cmg.to_dict() for cmg in cmgs]
    with open(json_path, 'w') as json_file:
        json.dump(cmg_data, json_file)


# TODO: Update for added info dict.
def params_from_json(json_path):
    """
    Load a list of :class:`CMGroup` parameters from a JSON file.

    Parameters:
        json_path (str): Path to a JSON file containing CMG parameters.

    Returns:
        A container, usually a list of dicts.
    """
    with open(json_path, 'r') as json_file:
        params_list = json.load(json_file)
    return params_list


# TODO: Update for added info dict.
def cmgs_from_json(json_path, env):
    """
    Generate :class:`CMGroup` objects from a JSON file.

    Parameters:
        json_path (str): Path to a JSON file containing parameters for any
            number of CMGs.
        env (:class:`camelid.env.CamelidEnv`): The project environment. This
            determines the environment used for the :class:`CMGroup` objects.

    Yields:
        :class:`CMGroup`: Chemical/material group objects.
    """
    logger.debug('Reading group parameters from %s', json_path)
    for params in params_from_json(json_path):
        yield CMGroup(params, env)
