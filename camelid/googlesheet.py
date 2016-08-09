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
from os.path import join as pjoin
import logging
import json
from itertools import islice

import gspread
from oauth2client.service_account import ServiceAccountCredentials as SAC

from . import logconf
from .cmgroup import CMGroup

logger = logging.getLogger(__name__)

SCOPE = ['https://spreadsheets.google.com/feeds']

TITLE = 'CMG parameters'
PARAMS_COLS = ['materialid', 'name', 'searchtype',
               'structtype', 'searchstring', 'last_updated']


class NoCredentialsError(Exception):
    '''Raised when there is no Google API credentials file.'''
    def __init__(self, path):
        self.path = path

    def __str__(self):
        msg = 'Google API credentials key file not found: {0}'
        return msg.format(self.path)


class SheetManager:
    '''Object to manage Google Sheets access.'''
    def __init__(self, key_file, worksheet, title=TITLE):
        if not os.path.exists(key_file):
            raise NoCredentialsError(key_file)

        creds = SAC.from_json_keyfile_name(key_file, SCOPE)
        logger.debug('Authorizing Google Service Account credentials.')
        self.google = gspread.authorize(creds)
        self.title = title
        self.spreadsheet = None
        self.worksheet = worksheet

    def get_spreadsheet(self):
        '''Open the group parameters spreadsheet as a `gspread.Spreadsheet`.'''
        if not self.spreadsheet:
            logger.debug('Opening Google Spreadsheet by title: %s', self.title)
            self.spreadsheet = self.google.open(self.title)
        return self.spreadsheet

    def get_params(self):
        '''Generate dicts of parameters from spreadsheet rows.'''
        doc = self.get_spreadsheet()
        logger.debug('Getting worksheet by title: %s', self.worksheet)
        wks = doc.worksheet(self.worksheet)

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
