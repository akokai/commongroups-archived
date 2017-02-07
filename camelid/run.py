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
from .env import CamelidEnv
from . import cmgroup as cmg
from . import googlesheet as gs

logger = logging.getLogger('camelid')


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
