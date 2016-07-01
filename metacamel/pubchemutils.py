# -*- coding: utf-8 -*-
'''Functions to get specific information from PubChem.'''

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

logger = logging.getLogger('metacamel.pubchemutils')

PUG_BASE = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug'
PUG_VIEW_BASE = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug_view'


def get_creation_date(cid):
    '''Get the date of creation of the CID.'''
    uri = PUG_BASE + '/compound/cid/{0}/dates/JSON'.format(cid)
    logger.debug('Getting creation date of CID %s. Request URI: %s', cid, uri)
    req = requests.get(uri)

    try:
        data = req.json()['InformationList']['Information'][0]['CreationDate']
        date_args = [int(data[k]) for k in ('Year', 'Month', 'Day')]
        created = date(*date_args)
    except (KeyError, TypeError, ValueError):
        logger.warning('Could not retrieve creation date for CID %s.', cid)
        created = None

    return created


def get_known_casrns(cid):
    '''
    Get PubChem-designated CASRNs for a given CID and return an IndexedSet.

    This method may need to change as PubChem improves access to CASRNs.
    '''
    uri = PUG_VIEW_BASE + '/data/compound/{0}/JSON?heading=CAS'.format(cid)
    logger.debug('Getting known CASRNs for CID %s. Request URI: %s', cid, uri)
    req = requests.get(uri)
    data = req.json()
    casrns = IndexedSet()

    def visit(path, key, value):
        if value['Name'] == 'CAS':
            if validate(value['StringValue'], boolean=True):
                casrns.add(value['StringValue'])
            else:
                logger.debug('Found invalid CASRN [%s] for CID %s.',
                             value['StringValue'], cid)
        return False

    try:
        remap(data, visit=visit, reraise_visit=False)
    except LookupError:
        logger.error('Failed to retrieve known CASRNs for CID %s.', cid)

    logger.info('Found %i known CASRNs for CID %s.', len(casrns), cid)
    return casrns


def get_compound_info(cids, newer_than=None):
    '''
    Generate dicts of information retrieved from PubChem for a list of CIDs.

    Uses the PubChem API. CIDs can be an iterable of ints or strings.

    Passing `newer_than` will only retrieve information on the CID if it has
    a creation date newer than what you specify (as a `datetime.date`).

    Retrieves CASRNs, IUPAC names, and date created in PubChem.
    CASRNs are returned as a space-separated string with the 'best' one first.
    '''
    for cid in cids:
        created = get_creation_date(cid)
        # TODO: Check against `newer_than` date.
        creation_date = created.isoformat() if created else ''
        sleep(0.2)  # Try to limit to about 5 REST API requests per second.

        casrns = get_known_casrns(cid)  # Instantiates an IndexedSet.
        sleep(0.2)

        cpd = pcp.Compound.from_cid(cid)
        sleep(0.2)

        try:
            # This seems to involve another API request:
            cas_synonyms = find_valid(' '.join(cpd.synonyms))
            logger.info('Found %i CASRNs in synonyms for CID %s.',
                        len(cas_synonyms), cid)
            casrns.update(cas_synonyms)
        except IndexError:
            logger.info('No CASRNs found in synonyms for CID %s.', cid)

        # Convert the IndexedSet into a string: if any 'known' CASRNs were
        # found, those will come first.
        casrns_string = ' '.join(casrns)

        results = {'CID': cid,
                   'created': created,              # datetime.date object
                   'creation_date': creation_date,  # string
                   'CASRN_list': casrns_string,
                   'IUPAC_name': cpd.iupac_name}    # Requires a request.
        sleep(0.2)
        yield results


def filter_listkey_args(**kwargs):
    '''Return only keyword arguments relating to ListKey pagination.'''
    listkey_options = ['listkey_count', 'listkey_start']
    listkey_args = {k: kwargs[k] for k in kwargs if k in listkey_options}
    return listkey_args


def init_substruct_search(struct, method='smiles'):
    '''
    Initiate an asynchronous substructure search using the PubChem API.

    Returns the ListKey given by the server response.
    '''
    search_path = '/compound/substructure/{0}/{1}/JSON'.format(method,
                                                               quote(struct))
    search_uri = PUG_BASE + search_path
    logger.debug('Substructure search request URI: %s', search_uri)
    search_req = requests.get(search_uri)

    if search_req.status_code != 202:
        logger.error('Unexpected request status: %s', search_req.status_code)
        logger.error('Stopping attempted substructure search.')
        return None     # There may be something more useful to do here.

    listkey = str(search_req.json()['Waiting']['ListKey'])
    logger.debug('Search request status: %s; ListKey: %s',
                 search_req.status_code, listkey)
    return listkey


def retrieve_search_results(listkey, **kwargs):
    '''
    Retrieve search results from the PubChem API using the given ListKey.
    '''
    key_uri = PUG_BASE + '/compound/listkey/{0}/cids/JSON'.format(listkey)
    listkey_args = filter_listkey_args(**kwargs) if kwargs else None
    if listkey_args:
        key_uri = key_uri + '?' + urlencode(kwargs)
    logger.debug('ListKey retrieval request URI: %s', key_uri)
    key_req = requests.get(key_uri)
    logger.debug('ListKey retrieval request status: %s',
                 key_req.status_code)

    while key_req.status_code == 202:
        logger.debug('Server not ready. Waiting additional 10 s.')
        sleep(10)
        key_req = requests.get(key_uri)

    try:
        cids = key_req.json()['IdentifierList']['CID']
        logger.info('PubChem search returned %i results.', len(cids))
        return cids
    except IndexError:
        logger.error('No CIDs found in substructure search results.')
        return None


def substruct_search(struct, method='smiles', wait=10, **kwargs):
    '''
    Find compounds in PubChem matching a substructure.
    '''
    listkey = init_substruct_search(struct, method)
    logger.debug('Waiting %i s before retrieving search results.', wait)
    sleep(wait)
    cids = retrieve_search_results(listkey, **kwargs)
    return cids
