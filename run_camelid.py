#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Automatically update chemical & material groups.'''

from __future__ import unicode_literals

import os
import argparse
import logging
from itertools import islice

import camelid.logconf
import camelid.cmgroup as cmg
import camelid.googlesheet as gs
import camelid.pubchemutils as pc

logger = logging.getLogger('camelid')

_CUR_PATH = os.path.dirname(os.path.abspath(__file__))
_PARENT_PATH = os.path.dirname(_CUR_PATH)
DATA_PATH = os.path.join(os.path.dirname(_PARENT_PATH), 'data')

JSON_FILE = os.path.join(DATA_PATH, 'group_params.json')


def main():
    '''
    Search for new compounds belonging specified chemical & material groups.
    '''
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('-f', '--json_file', action='store', type=str,
                        help='read group parameters from a JSON file '
                             'instead of Google spreadsheet')
    parser.add_argument('-w', '--worksheet', action='store', type=str,
                        help='worksheet to get parameters from',
                        default='new CMGs')
    parser.add_argument('-r', '--resume_update', action='store_true',
                        help='resume previous update (from CID lists)',
                        default=False)
    parser.add_argument('-c', '--clean_start', action='store_true',
                        help='do not resume previous searches; '
                             'delete existing data before starting',
                        default=False)
    args = parser.parse_args()

    if args.json_file:
        logger.debug('Getting group parameters from file: %s', args.json_file)
        cmg_gen = cmg.cmgs_from_json(args.json_file)
    else:
        logger.debug('Getting group parameters from worksheet: %s',
                     args.worksheet)
        cmg_gen = gs.get_cmgs(args.worksheet)

    groups = list(islice(cmg_gen, None))

    if args.clean_start:
        for group in groups:
            group.clean_data()

    logger.debug('Starting batch CMG update process.')
    try:
        cmg.batch_cmg_search(groups, args.resume_update)
    except:
        logger.exception('Process failed.')


if __name__ == '__main__':
    main()
