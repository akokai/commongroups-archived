#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Automatically update chemical & material groups.'''

from __future__ import unicode_literals

import os
import argparse
import logging
from itertools import islice

import metacamel.logconf
import metacamel.cmgroup as cmg
import metacamel.googlesheet as gs
import metacamel.pubchemutils as pc

logger = logging.getLogger('metacamel')

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
                        help='JSON file to read group parameters from '
                             'instead of Google spreadsheet')
    parser.add_argument('-w', '--worksheet', action='store', type=str,
                        help='worksheet to get parameters from',
                        default='new CMGs')
    parser.add_argument('-r', '--resume', action='store_true',
                        help='resume previous update (from CID lists)',
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

    logger.debug('Executing batch CMG search.')
    cmg.batch_cmg_search(groups)


if __name__ == '__main__':
    main()
