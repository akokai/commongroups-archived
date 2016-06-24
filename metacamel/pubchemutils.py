# -*- coding: utf-8 -*-
'''Functions to get specific information from PubChem.'''

from __future__ import unicode_literals

import os
import logging
from time import sleep
from urllib.parse import quote

import requests
import pubchempy as pcp
import logging_conf
from casrnutils import find_valid
from boltons.fileutils import mkdir_p
from builtins import str

_CUR_PATH = os.path.dirname(os.path.abspath(__file__))
_PARENT_PATH = os.path.dirname(_CUR_PATH)
DATA_PATH = os.path.join(_PARENT_PATH, 'data')
mkdir_p(DATA_PATH)
TMP_LISTKEY_PATH = os.path.join(DATA_PATH, 'listkeys.txt')

logger = logging.getLogger('metacamel.pubchemutils')

PUG_BASE = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/'


def casrn_iupac_from_cids(cids):
    '''
    Generate dicts of corresponding CASRNs and IUPAC names for a list of CIDs.

    Uses PubChem API. CIDs can be an iterable of ints or strings.
    '''
    for cid in cids:
        cpd = pcp.Compound.from_cid(cid)
        sleep(0.5)  # Sleep to prevent overloading API.
        # There might be a more robust way to find a list of CASRNs
        # and to process it in a more sophisticated way, e.g. find the
        # most commonly used one. For example, see:
        # https://{pubchem}/rest/pug_view/data/compound/2244/JSON?heading=CAS
        # For now, join up all the synonyms in to one long string
        # and use regex to find valid CASRNs. Use the first one found.
        try:
            casrn = find_valid(' '.join(cpd.synonyms))[0]
        except IndexError:
            # If there are no synonyms, or there are no CASRNs found:
            logger.info('No CASRNs found for CID %s' % cid)
            casrn = None
        results = {'CID': cid, 'CASRN': casrn, 'IUPAC_name': cpd.iupac_name}
        yield results


def init_substructure_search(struct, method='smiles'):
    '''
    Initiate an asynchronous substructure search using the PubChem API.

    Returns the listkey given by the server response.
    '''
    search_path = 'compound/substructure/{0}/{1}/JSON'.format(method,
                                                              quote(struct))
    search_uri = PUG_BASE + search_path
    logger.info('Substructure search request URI: %s' % search_uri)
    search_req = requests.get(search_uri)
    if search_req.status_code != 202:
        logger.error('Unexpected request status: %s' % search_req.status_code)
        logger.error('Stopping attempted substructure search.')
        return None
        # There may be something more useful to do here.
    logger.debug('Search request status: %s' % search_req.status_code)
    listkey = str(search_req.json()['Waiting']['ListKey'])
    return listkey


def retrieve_search_results(listkey):
    '''
    Retrieve search results from the PubChem API using the given ListKey.
    '''
    key_uri = PUG_BASE + 'compound/listkey/{0}/cids/JSON'.format(listkey)
    logger.info('Listkey retrieval request URI: %s' % key_uri)
    key_req = requests.get(key_uri)
    logger.debug('Listkey retrieval request status: %s' %
                 key_req.status_code)
    try:
        cids = key_req.json()['IdentifierList']['CID']
        logger.info('Substructure search returned %i results' % len(cids))
        return cids
    except IndexError:
        logger.error('No CIDs found in substructure search results.')
        return None


def substructure_search(struct, method='smiles', wait=180):
    '''
    Find compounds in PubChem matching a substructure.
    '''
    listkey = init_substructure_search(struct, method)
    logger.info('Waiting %i s before retrieving search results.' % wait)
    sleep(wait)
    cids = retrieve_search_results(listkey)
    return cids
