# -*- coding: utf-8 -*-
"""
Get CMG parameters from a Google Sheet.

See :ref:`Google Sheets access <google-setup>` for general information on
using this functionality.
"""

from __future__ import unicode_literals

import os
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
DEFAULT_WORKSHEET = 'new CMGs'
PARAMS_COLS = ['materialid', 'name', 'searchtype',
               'structtype', 'searchstring', 'last_updated']


class NoCredentialsError(Exception):
    """Raised when there is no Google API credentials file."""
    def __init__(self, path):
        super().__init__(self)
        self.path = path

    def __str__(self):
        msg = 'Google API credentials key file not found: {0}'
        return msg.format(self.path)


class SheetManager(object):
    """Object to manage Google Sheets access."""
    def __init__(self, key_file=None, worksheet=None, title=TITLE):
        if key_file:
            _key_file = os.path.abspath(key_file)
        elif os.getenv('CAMELID_KEYFILE'):
            _key_file = os.path.abspath(os.getenv('CAMELID_KEYFILE'))
        else:
            raise NoCredentialsError(key_file)

        try:
            creds = SAC.from_json_keyfile_name(_key_file, SCOPE)
        except FileNotFoundError:
            raise NoCredentialsError(_key_file)

        logger.debug('Authorizing Google Service Account credentials')
        self.google = gspread.authorize(creds)
        self.title = title
        self.spreadsheet = None
        self.worksheet = worksheet or DEFAULT_WORKSHEET

    def get_spreadsheet(self):
        """Open the group parameters spreadsheet as a `gspread.Spreadsheet`."""
        if not self.spreadsheet:
            logger.debug('Opening Google Spreadsheet by title: %s', self.title)
            self.spreadsheet = self.google.open(self.title)
        return self.spreadsheet

    def get_params(self):
        """Generate dicts of parameters from spreadsheet rows."""
        doc = self.get_spreadsheet()
        logger.debug('Getting worksheet by title: %s', self.worksheet)
        wks = doc.worksheet(self.worksheet)

        for i in range(2, wks.row_count + 1):
            if wks.cell(i, 1).value in [None, '']:
                raise StopIteration
            params = {k: v for (k, v) in zip(PARAMS_COLS, wks.row_values(i))}
            yield params

    def get_cmgs(self, env):
        """
        Generate `CMGroup` objects from parameters in spreadsheet rows.

        The resulting `CMGroup`s will be based in project environment `env`.
        """
        logger.debug('Generating CMGs from worksheet: %s', self.worksheet)

        for params in self.get_params():
            yield CMGroup(params, env)

    def params_to_json(self, file=None):
        """
        Get group parameters from the worksheet and output to a JSON file.
        """
        if file is None:
            raise TypeError('No output file specified')

        group_params = list(islice(self.get_params(), None))

        file_path = os.path.abspath(file)
        with open(file_path, 'w') as params_file:
            json.dump(group_params, params_file, indent=2, sort_keys=True)
