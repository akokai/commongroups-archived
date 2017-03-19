# coding: utf-8

"""
Automatically populate chemical & material groups.

This module runs the whole collection of operations available in camelid:

-  Read compound group definitions either from the web (Google Sheets) or
   from a JSON file.
-  Compile and perform database queries based on group definitions.
-  Output results and summaries.
"""

from __future__ import unicode_literals

import logging
import argparse

from camelid import logconf
from camelid.env import CamelidEnv

logger = logging.getLogger('camelid')


def create_parser():
    """Create command-line argument parser."""
    desc = 'Automatically populate chemical & material groups.'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-e', '--env_path', help='path to camelid home')
    parser.add_argument('-p', '--project', help='project name')
    parser.add_argument('-d', '--database', help='database URL')
    parser.add_argument('-g', '--googlesheet',
                        help='title of group definitions Google Sheet')
    parser.add_argument('-w', '--worksheet',
                        help='worksheet containing group definitions')
    parser.add_argument('-k', '--key_file', help='Google API key file')
    parser.add_argument('-j', '--json_file',
                        help='read group definitions from a JSON file',
                        default=False)
    parser.add_argument('-c', '--clean_start', action='store_true',
                        help='delete existing data before starting',
                        default=False)
    parser.add_argument('-v', '--level', action='count',
                        help='show more logging output in console')
    # parser.add_argument('-r', '--resume_update', action='store_true',
    #                     help='resume previous update',
    #                     default=False)  # Irrelevant
    return parser


def set_console_loglevel(level):
    console = logger.handlers[0]
    if level > 0:
        console.setLevel('DEBUG')


def main():
    parser = create_parser()
    args = parser.parse_args()
    set_console_loglevel(args.level)

    env = CamelidEnv(args.env_path, args.project, args.database)
    env.run(args)


if __name__ == '__main__':
    main()
