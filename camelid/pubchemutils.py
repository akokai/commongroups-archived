# -*- coding: utf-8 -*-
"""
Functions to get compound information from PubChem using web services.

This module makes use of :mod:`PubChemPy`. See the `PubChemPy docs`_
for a full description of how that works. Also see the
`PubChem REST API`_ specification for documentation of the web services.

.. _PubChemPy docs: http://pubchempy.readthedocs.io/
.. _PubChem REST API: https://pubchem.ncbi.nlm.nih.gov/pug_rest/PUG_REST.html
"""

from __future__ import unicode_literals

import logging
from time import sleep
from datetime import date
from urllib.parse import quote, urlencode

from boltons.setutils import IndexedSet
from boltons.iterutils import remap
import requests
import pubchempy as pcp

from . import logconf
from .casrnutils import validate, find_valid

logger = logging.getLogger(__name__)

PUG_BASE = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug'
PUG_VIEW_BASE = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug_view'


def get_creation_date(cid):
    """
    Get the date of creation of a PubChem Compound.

    Parameters:
        cid (str or int): PubChem Compound ID.

    Returns:
        :class:`datetime.date`: Creation date.

        ``None`` if not found.
    """
    url = PUG_BASE + '/compound/cid/{0}/dates/JSON'.format(cid)
    logger.debug('Getting creation date of %s: request URL: %s', cid, url)
    req = requests.get(url)

    try:
        data = req.json()['InformationList']['Information'][0]['CreationDate']
        date_args = [int(data[k]) for k in ('Year', 'Month', 'Day')]
        created = date(*date_args)
    except (KeyError, TypeError, ValueError):
        logger.warning('Could not retrieve creation date for CID %s', cid)
        created = None

    return created


def get_known_casrns(cid):
    """
    Get PubChem's specifically designated CASRNs for a given CID.

    The PubChem API can return a special section of data dedicated to CASRNs.
    This is not (yet) documented in the offical API specification.
    This method may need to change as PubChem improves access to CASRNs.

    We compile CASRNs in a container object that preserves their order when
    more are added, as in :func:`get_compound_info`.

    Parameters:
        cid (str or int): PubChem Compound ID.

    Returns:
        :class:`boltons.setutils.IndexedSet`: "Known" CASRNs.
    """
    url = PUG_VIEW_BASE + '/data/compound/{0}/JSON?heading=CAS'.format(cid)
    logger.debug('Getting known CASRNs for CID %s. Request URL: %s', cid, url)
    req = requests.get(url)
    data = req.json()
    casrns = IndexedSet()

    def visit(path, key, value):
        if value['Name'] == 'CAS':
            if validate(value['StringValue'], boolean=True):
                casrns.add(value['StringValue'])
            else:
                logger.debug('Found invalid CASRN [%s] for CID %s',
                             value['StringValue'], cid)
        return False

    try:
        remap(data, visit=visit, reraise_visit=False)
    except LookupError:
        logger.error('Failed to retrieve known CASRNs for CID %s', cid)

    logger.debug('Found %i known CASRNs for CID %s', len(casrns), cid)
    return casrns


def get_compound_info(cid):
    """
    Get CASRNs and IUPAC name for a CID and return a :class:`dict`.

    CASRNs are returned as a space-separated string with the 'best' one first.
    Tries to keep API request rate below 5 per second.

    Parameters:
        cid (str or int): PubChem Compound ID.

    Returns:
        dict: Containing ``CID``, ``CASRN_list`` [space-separated string],
        and ``IUPAC_name``.
    """
    casrns = get_known_casrns(cid)  # Instantiates an IndexedSet.
    sleep(0.2)

    cpd = pcp.Compound.from_cid(cid)
    sleep(0.2)

    try:
        # This involves another API request for `cpd.synoynms`:
        cas_synonyms = find_valid(' '.join(cpd.synonyms))
        sleep(0.2)
        logger.debug('Found %i CASRNs in synonyms for CID %s',
                     len(cas_synonyms), cid)
        casrns.update(cas_synonyms)
    except IndexError:
        logger.debug('No CASRNs found in synonyms for CID %s', cid)

    # Convert the IndexedSet into a string: if any 'known' CASRNs were
    # found, those will come first.
    casrns_string = ' '.join(casrns)

    results = {'CID': cid,
               'CASRN_list': casrns_string,
               'IUPAC_name': cpd.iupac_name}    # Another API request.
    sleep(0.2)
    return results


def gen_compounds(cids, last_updated=None):
    """
    Generate dicts of information retrieved from PubChem for a list of CIDs.

    Compound information is retrieved using :func:`get_compound_info`.
    Since this is a `generator`_, it can be made to start and stop anywhere
    while iterating through the input list of CIDs.

    Parameters:
        cids (list): PubChem Compound IDs.
        last_updated (:class:`datetime.date`): If specified, only return
            information for those PubChem Compounds with a creation date
            *newer* than ``last_updated``.

    Yields:
        dict: Compound information including ``creation_date``.

    .. _generator: https://docs.python.org/3/tutorial/classes.html#generators
    """
    for cid in cids:
        created = get_creation_date(cid)
        sleep(0.2)

        if isinstance(last_updated, date):
            delta = created - last_updated
            # This will skip CIDs created before the day of `last_updated`,
            # but will include those created on exactly the same day.
            if delta.days < 0:
                logger.info('Skipping CID %s: predates last update', cid)
                continue

        creation_date = created.isoformat() if created else ''

        results = get_compound_info(cid)
        results.update({'creation_date': creation_date})

        yield results


def filter_listkey_args(**kwargs):
    """
    Filter pagination-related keyword arguments.

    Parameters:
        **kwargs: Arbitrary keyword arguments.

    Returns:
        dict: Keyword arguments relating to ``ListKey`` pagination.
    """
    listkey_options = ['listkey_count', 'listkey_start']
    listkey_args = {k: kwargs[k] for k in kwargs if k in listkey_options}
    return listkey_args


def init_substruct_search(struct, method='smiles'):
    """
    Initiate an asynchronous substructure search using the PubChem API.

    Parameters:
        struct (str): The molecular structure search query.
        method (str): Structure input method. We mostly use `smiles`.

    Returns:
        str: The asynchronous ``ListKey`` given in the server response.
    """
    search_path = '/compound/substructure/{0}/{1}/JSON'.format(method,
                                                               quote(struct))
    search_url = PUG_BASE + search_path
    logger.debug('Substructure search request URL: %s', search_url)
    search_req = requests.get(search_url)

    if search_req.status_code != 202:
        logger.error('Unexpected request status: %s', search_req.status_code)
        logger.error('Stopping attempted substructure search')
        return None     # There may be something more useful to do here.

    listkey = str(search_req.json()['Waiting']['ListKey'])
    logger.debug('Search request status: %s; ListKey: %s',
                 search_req.status_code, listkey)
    return listkey


def retrieve_search_results(listkey, **kwargs):
    """
    Retrieve search results from the PubChem API using the given ``ListKey``.

    Parameters:
        listkey (str): The ``ListKey`` for retrieving the search results.
        **kwargs: Arbitrary keyword arguments. For example, arguments relating
            to pagination of search results: ``listkey_count`` and
            ``listkey_start``. See the `PubChem API`_ documentation.

    .. _PubChem API: https://pubchem.ncbi.nlm.nih.gov/pug_rest/PUG_REST.html

    Returns:
        list: CIDs returned by the search.
    """
    key_url = PUG_BASE + '/compound/listkey/{0}/cids/JSON'.format(listkey)
    listkey_args = filter_listkey_args(**kwargs) if kwargs else None
    if listkey_args:
        key_url = key_url + '?' + urlencode(kwargs)
    logger.debug('ListKey retrieval request URL: %s', key_url)
    key_req = requests.get(key_url)
    logger.debug('ListKey retrieval request status: %s',
                 key_req.status_code)

    while key_req.status_code == 202:
        logger.debug('Server not ready. Waiting additional 10 s')
        sleep(10)
        key_req = requests.get(key_url)

    try:
        cids = key_req.json()['IdentifierList']['CID']
        logger.info('PubChem search returned %i results', len(cids))
        return cids
    except IndexError:
        logger.error('No CIDs found in substructure search results')
        return []


def substruct_search(struct, method='smiles', wait=10, **kwargs):
    """
    Find compounds in PubChem matching a substructure.

    Parameters:
        struct (str): The molecular structure search query.
        method (str): Structure input method. We mostly use `smiles`.
        wait (int): Delay (seconds) before retrieving async search results.
        **kwargs: Arbitrary keyword arguments, such as for pagination
            (see :func:`retrieve_search_results`).

    Returns:
        list: CIDs returned by the search.
    """
    listkey = init_substruct_search(struct, method)
    logger.debug('Waiting %i s before retrieving search results', wait)
    sleep(wait)
    cids = retrieve_search_results(listkey, **kwargs)
    return cids
