# -*- coding: utf-8 -*-
"""Automatically populate and update chemical & material groups."""

from __future__ import unicode_literals

import os
import logging
import argparse
from os.path import join as pjoin
from datetime import datetime
from glob import iglob
from itertools import islice

from boltons.fileutils import mkdir_p

from . import logconf
from . import cmgroup as cmg
from . import googlesheet as gs

logger = logging.getLogger('camelid')


class CamelidEnv(object):
    """
    Run environment for :mod:`camelid`. Prefers desert or alpine habitats.

    Parameters:
        env_path (str): Path to root camelid home. If not specified,
            looks for environment variable ``CAMELID_HOME`` or defaults to
            ``~/camelid_data``.
        project (str): Project name. If unspecified, defaults to
            ``'default'``.
        worksheet (str): Title of the *worksheet* to look for CMG parameters
            within the Google Sheet. Optional; if unspecified, filled in by
            :class:`camelid.googlesheet.SheetManager`.
        key_file (str): Path to Google service account credentials
            JSON file. If unspecified here, attempts to locate it are made by
            :class:`camelid.googlesheet.SheetManager`.
    """
    def __init__(self,
                 env_path=None,
                 project=None,
                 worksheet=None,
                 key_file=None):
        # Establish path to camelid home.
        if env_path:
            self._env_path = os.path.abspath(env_path)
        elif os.getenv('CAMELID_HOME'):
            self._env_path = os.path.abspath(os.getenv('CAMELID_HOME'))
        else:
            self._env_path = pjoin(os.path.expanduser('~'), 'camelid_data')

        # Establish project location.
        project = project or 'default'
        self._project_path = pjoin(self._env_path, project)
        mkdir_p(self._project_path)

        # Set up per-project logging to file.
        self._log_path = pjoin(self._project_path, 'log')
        mkdir_p(self._log_path)
        log_file = datetime.now().strftime('%Y%m%dT%H%M%S') + '.log'
        self._log_file = pjoin(self._log_path, log_file)
        self.add_project_handler()
        logger.info('Project path: %s', self._project_path)

        # Set up data and results directories.
        self._data_path = pjoin(self._project_path, 'data')
        mkdir_p(self._data_path)
        self._results_path = pjoin(self._project_path, 'results')
        mkdir_p(self._results_path)

        # Store path to Google API credentials file.
        self._key_file = key_file

        # Set worksheet to look for parameters in Google Sheet.
        self.worksheet = worksheet

    @property
    def project_path(self):
        """Path to project directory."""
        return self._project_path

    @property
    def log_path(self):
        """Path to project log directory."""
        return self._log_path

    @property
    def log_file(self):
        """Path to the currently active log file."""
        return self._log_file

    @property
    def data_path(self):
        """
        Path to the project data directory.
        """
        return self._data_path

    @property
    def results_path(self):
        """Path to project results directory."""
        return self._results_path

    def add_project_handler(self):
        """
        Add a project-specific :class:`FileHandler` for all logging output.

        This enables logging to a file that's kept within the project
        directory.
        """
        loggers = list(logconf.CONFIG['loggers'].keys())
        proj_handler = logging.FileHandler(self._log_file, mode='w')
        fmt = logging.getLogger(loggers[0]).handlers[0].formatter
        proj_handler.setFormatter(fmt)

        for item in loggers:
            lgr = logging.getLogger(item)
            lgr.addHandler(proj_handler)

    def clear_logs(self):
        """Delete all log files belonging to the project."""
        for item in iglob(pjoin(self.log_path, '*.log')):
            os.remove(item)

    def run(self, args):
        """
        Perform operations specified by the arguments.

        See :ref:`Running camelid <running>` for possible operations.

        Parameters:
            args (dict): Parsed command-line arguments.

        Notes:
            The "resume update" option is handled by
            :func:`camelid.cmgroup.batch_cmg_search`.
        """
        if args.json_file:
            logger.info('Generating compound groups from JSON file')
            cmg_gen = cmg.cmgs_from_json(args.json_file, self)
        else:
            logger.info('Generating compound groups from Google Sheet')
            sheet = gs.SheetManager(self._key_file, self.worksheet)
            cmg_gen = sheet.get_cmgs(self)

        groups = list(islice(cmg_gen, None))

        if args.clean_start:
            logger.debug('Clearing data and logs')
            for group in groups:
                group.clear_data()
            self.clear_logs()

        logger.info('Starting batch CMG update process')
        try:
            cmg.batch_cmg_search(groups, args.resume_update)
        except:
            logger.exception('Process failed')


def create_parser():
    """Create command-line argument parser."""
    desc = 'Automatically populate and update chemical & material groups.'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-r', '--resume_update', action='store_true',
                        help='resume previous update',
                        default=False)
    parser.add_argument('-c', '--clean_start', action='store_true',
                        help='do not resume previous searches, and '
                             'delete existing data before starting',
                        default=False)
    parser.add_argument('-p', '--project', action='store', type=str,
                        help='project name')
    parser.add_argument('-e', '--env_path', action='store', type=str,
                        help='path to camelid home')
    parser.add_argument('-w', '--worksheet', action='store', type=str,
                        help='worksheet to get parameters from')
    parser.add_argument('-k', '--key_file', action='store', type=str,
                        help='path to Google API key file')
    parser.add_argument('-j', '--json_file', action='store', type=str,
                        help='read parameters from a JSON file',
                        default=False)
    parser.add_argument('-v', '--level', action='count',
                        help='lower console logging level (see more output)')
    return parser


def set_console_loglevel(level):
    console = logger.handlers[0]
    if level > 0:
        console.setLevel('DEBUG')


def main():
    parser = create_parser()
    args = parser.parse_args()
    set_console_loglevel(args.level)

    env = CamelidEnv(args.env_path, args.project,
                     args.worksheet, args.key_file)
    env.run(args)


if __name__ == '__main__':
    main()
