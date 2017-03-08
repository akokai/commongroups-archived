# coding: utf-8

"""
Get CMG parameters from a Google Sheet.

See :ref:`Google Sheets access <googlesetup>` for general information on
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
from .errors import NoCredentialsError

logger = logging.getLogger(__name__)

SCOPE = ['https://spreadsheets.google.com/feeds']

TITLE = 'CMG parameters'        # TODO: Make user-specified; assume private.
DEFAULT_WORKSHEET = 'new CMGs'  # TODO: These details are specific to org.
PARAMS_COLS = ['materialid', 'name', 'searchtype',
               'structtype', 'searchstring', 'last_updated']


class SheetManager(object):
    """
    Object to manage Google Sheets access.

    Parameters:
        key_file (str): Path to Google service account credentials
            JSON file. If unspecified, attempts to read the
            environment variable ``CAMELID_KEYFILE`` for the path.
        worksheet (str): Title of the *worksheet* to look for CMG parameters
            within the Google Sheet. If unspecified, uses a default value.
        title (str): *Title* of the Google Sheet to open. If unspecified, uses
            a default value.

    Raises:
        :class:`camelid.errors.NoCredentialsError`: If the API
            credentials are missing or cannot be parsed from JSON.

    Notes:
        Yes, we open Google Sheets *by title.*  It would be nice to open them
        by key or by URL, but that functionality in :mod:`gspread` is broken
        because of the "New Sheets".
    """
    def __init__(self, title=TITLE, worksheet=None, key_file=None):
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
        self._google = gspread.authorize(creds)
        self._title = title
        self._spreadsheet = None
        self._worksheet = worksheet or DEFAULT_WORKSHEET

    def get_spreadsheet(self):
        """
        Open the spreadsheet containing CMG parameters.

        Returns:
            :mod:`gspread.Spreadsheet`: The Google Sheet object.
        """
        if not self._spreadsheet:
            logger.debug('Opening Google Sheet by title: %s', self._title)
            self._spreadsheet = self._google.open(self._title)
        return self._spreadsheet

    def get_params(self):
        """
        Generate dicts of parameters from spreadsheet rows.

        Yields:
            dict: Parameters of each CMG; one per spreadsheet row.
        """
        doc = self.get_spreadsheet()
        logger.debug('Getting worksheet by title: %s', self._worksheet)
        wks = doc.worksheet(self._worksheet)

        for i in range(2, wks.row_count + 1):
            if wks.cell(i, 1).value in [None, '']:
                raise StopIteration
            params = {k: v for (k, v) in zip(PARAMS_COLS, wks.row_values(i))}
            yield params

    def get_cmgs(self, env):
        """
        Generate :class:`CMGroup` objects from parameters in spreadsheet rows.

        Parameters:
            env (:class:`camelid.env.CamelidEnv`): The project environment
                that the returned objects will use to store data, etc.

        Yields:
            :class:`camelid.cmgroup.CMGroup`: Based on parameters in each row.

        """
        logger.debug('Generating CMGs from worksheet: %s', self._worksheet)

        for params in self.get_params():
            yield CMGroup(params, env)

    def params_to_json(self, file=None):
        """
        Get group parameters from the worksheet and output to a JSON file.

        This could be useful for documentation purposes, but is not needed for
        keeping records of search parameters. Each CMG automatically saves its
        parameters to a JSON file in the ``data`` directory of the project.

        Parameters:
            file (str): Path to output file.

        Raises:
            TypeError: If the output file path is not specified.
        """
        if file is None:
            raise TypeError('No output file specified')

        group_params = list(islice(self.get_params(), None))

        file_path = os.path.abspath(file)
        logger.debug('Writing parameters to file: %s', file_path)
        with open(file_path, 'w') as params_file:
            json.dump(group_params, params_file, indent=2, sort_keys=True)
