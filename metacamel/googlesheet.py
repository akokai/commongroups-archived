# -*- coding: utf-8 -*-
'''
Google Spreadsheet access

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
logger = logging.getLogger('metacamel.googlesheet')

_CUR_PATH = os.path.dirname(os.path.abspath(__file__))
_PARENT_PATH = os.path.dirname(_CUR_PATH)
PRIVATE_PATH = os.path.join(_PARENT_PATH, 'private')
API_JSON = os.path.join(PRIVATE_PATH, 'google-credentials.json')

sheet_title = 'CMG_parameters'

scope = ['https://spreadsheets.google.com/feeds']

credentials = ServiceAccountCredentials.from_json_keyfile_name(API_JSON, scope)

gc = gspread.authorize(credentials)

logger.debug('Opening Google Spreadsheet by title: %s' % sheet_title)
cmg_spreadsheet = gc.open(sheet_title)
