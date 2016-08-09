# -*- coding: utf-8 -*-
"""Automatically update chemical & material groups."""

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
    """Run environment for camelid. Prefers desert or alpine habitat."""
    def __init__(self,
                 env_path=None,
                 project=None,
                 worksheet=None,
                 key_file=None):
        # Establish path to camelid home.
        if env_path:
            self.env_path = os.path.abspath(env_path)
        elif os.getenv('CAMELID_HOME'):
            self.env_path = os.path.abspath(os.getenv('CAMELID_HOME'))
        else:
            self.env_path = pjoin(os.path.expanduser('~'), 'camelid_data')

        # Establish project location.
        project = project or 'default'
        self.project_path = pjoin(self.env_path, project)
        mkdir_p(self.project_path)

        # Set up per-project logging to file.
        self.log_path = pjoin(self.project_path, 'log')
        mkdir_p(self.log_path)
        log_file = datetime.now().strftime('%Y%m%dT%H%M%S') + '.log'
        self.log_file = pjoin(self.log_path, log_file)
        logconf.add_project_handler(self.log_file)
        logger.info('Project path: %s', self.project_path)

        # Set up data and results directories.
        self.data_path = pjoin(self.project_path, 'data')
        mkdir_p(self.data_path)
        self.results_path = pjoin(self.project_path, 'results')
        mkdir_p(self.results_path)

        # Set file path to look for parameters in JSON format.
        self.params_json = pjoin(self.project_path, 'params.json')

        # Store path to Google API credentials file.
        self._key_file = key_file

        # Set worksheet to look for parameters in Google Sheet.
        self.worksheet = worksheet

    def clear_logs(self):
        for item in iglob(pjoin(self.log_path, '*.log')):
            os.remove(item)

    def run(self, args):
        if args.json_file:
            logger.info('Generating compound groups from JSON file')
            cmg_gen = cmg.cmgs_from_json(self)
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
    """Parse arguments for the run script."""
    desc = 'Search for compounds belonging to specified chemical classes.'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-e', '--env_path', action='store', type=str,
                        help='path to camelid home')
    parser.add_argument('-p', '--project', action='store', type=str,
                        help='project name')
    parser.add_argument('-w', '--worksheet', action='store', type=str,
                        help='worksheet to get parameters from')
    parser.add_argument('-k', '--key_file', action='store', type=str,
                        help='path to Google API key file')
    parser.add_argument('-j', '--json_file', action='store_true',
                        help='read parameters from JSON file',
                        default=False)
    parser.add_argument('-r', '--resume_update', action='store_true',
                        help='resume previous update',
                        default=False)
    parser.add_argument('-c', '--clean_start', action='store_true',
                        help='do not resume previous searches, and '
                             'delete existing data before starting',
                        default=False)
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    env = CamelidEnv(args.env_path, args.project,
                     args.worksheet, args.key_file)
    env.run(args)


if __name__ == '__main__':
    main()
