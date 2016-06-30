# -*- coding: utf-8 -*-
'''
Google Spreadsheet access.

See the ``gspread`` docs for instructions on getting OAuth2 credentials for
Google Drive API access: http://gspread.readthedocs.io/en/latest/index.html
Make a copy of the service account credentials JSON file in
``../private/google-credentials.json``.

Notes:
- Opening by key or by URL in ``gspread`` is broken by the "New Sheets",
but opening by title seems to work.
- Don't forget to share the relevant Google Spreadsheet with your Google
service account client e-mail.
'''

import os
import logging

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from . import logconf
from .cmgroup import CMGroup, params_keys

logger = logging.getLogger('metacamel.googlesheet')

_CUR_PATH = os.path.dirname(os.path.abspath(__file__))
_PARENT_PATH = os.path.dirname(_CUR_PATH)
PRIVATE_PATH = os.path.join(_PARENT_PATH, 'private')
API_JSON = os.path.join(PRIVATE_PATH, 'google-credentials.json')

title = 'CMG parameters'

scope = ['https://spreadsheets.google.com/feeds']

credentials = ServiceAccountCredentials.from_json_keyfile_name(API_JSON, scope)


def get_spreadsheet():
    '''Open the group parameters spreadsheet as a ``gspread.Spreadsheet``.'''
    logger.debug('Authorizing Google Service Account credentials.')
    gc = gspread.authorize(credentials)
    logger.debug('Opening Google Spreadsheet by title: %s' % title)
    cmg_spreadsheet = gc.open(title)
    return cmg_spreadsheet


def get_CMGs(sheet_name='new CMGs'):
    '''.'''
    logger.debug('Getting new CMGs worksheet.')
    wks = get_spreadsheet().worksheet(sheet_name)

    for i in range(2, wks.row_count + 1):
        if wks.cell(i, 1).value is None:
            break
        params = {k: v for (k, v) in zip(params_keys, wks.row_values(i))}
        yield CMGroup(params)
