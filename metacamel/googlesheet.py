# -*- coding: utf-8 -*-
'''
Google Spreadsheet access.

See the `gspread` docs for instructions on getting OAuth2 credentials for
Google Drive API access: http://gspread.readthedocs.io/en/latest/index.html
Make a copy of the service account credentials JSON file in
`../private/google-credentials.json`.

Notes:
- Opening by key or by URL in `gspread` is broken by the "New Sheets",
but opening by title seems to work.
- Don't forget to share the relevant Google Spreadsheet with your Google
service account client e-mail.
'''

from __future__ import unicode_literals

import os
import logging
import json
from itertools import islice

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from boltons.fileutils import mkdir_p

from . import logconf
from .cmgroup import CMGroup

logger = logging.getLogger('metacamel.googlesheet')

_CUR_PATH = os.path.dirname(os.path.abspath(__file__))
_PARENT_PATH = os.path.dirname(_CUR_PATH)
PRIVATE_PATH = os.path.join(_PARENT_PATH, 'private')
API_JSON = os.path.join(PRIVATE_PATH, 'google-credentials.json')
DATA_PATH = os.path.join(_PARENT_PATH, 'data')
mkdir_p(DATA_PATH)

SCOPE = ['https://spreadsheets.google.com/feeds']

TITLE = 'CMG parameters'
PARAMS_COLS = ['materialid', 'name', 'searchtype',
               'structtype', 'searchstring', 'last_updated']


def get_spreadsheet():
    '''Open the group parameters spreadsheet as a `gspread.Spreadsheet`.'''
    creds = ServiceAccountCredentials.from_json_keyfile_name(API_JSON, SCOPE)
    logger.debug('Authorizing Google Service Account credentials.')
    google = gspread.authorize(creds)
    logger.debug('Opening Google Spreadsheet by title: %s', TITLE)
    cmg_spreadsheet = google.open(TITLE)
    return cmg_spreadsheet


def get_params(worksheet):
    '''Generate dicts of parameters from spreadsheet rows.'''
    doc = get_spreadsheet()
    logger.debug('Getting worksheet by title: %s', worksheet)
    wks = doc.worksheet(worksheet)

    for i in range(2, wks.row_count + 1):
        if wks.cell(i, 1).value in [None, '']:
            raise StopIteration
        params = {k: v for (k, v) in zip(PARAMS_COLS, wks.row_values(i))}
        yield params


def get_cmgs(worksheet):
    '''Generate `CMGroup` objects from parameters in spreadsheet rows.'''
    for params in get_params(worksheet):
        yield CMGroup(params)


def params_to_json(worksheet, file_name=None):
    '''
    Get group parameters from given worksheet and output to a JSON file.

    A JSON file with the given name will be created in the `data` directory.
    '''
    if file_name is None:
        logger.error('No output file name specified.')
        raise TypeError

    group_params = list(islice(get_params(worksheet), None))

    with open(file_name, 'w') as params_file:
        json.dump(group_params, params_file, indent=2, sort_keys=True)
