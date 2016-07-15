# -*- coding: utf-8 -*-
'''Logging configuration'''

from __future__ import unicode_literals

import os
import sys
import logging
import logging.config

from boltons.fileutils import mkdir_p

_CUR_PATH = os.path.dirname(os.path.abspath(__file__))
_PARENT_PATH = os.path.dirname(_CUR_PATH)
LOG_PATH = os.path.join(_PARENT_PATH, 'log')
mkdir_p(LOG_PATH)
LOG_FILE_PATH = os.path.join(LOG_PATH, 'camelid.log')

CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
            'style': '%'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'formatter': 'default',
            'filename': LOG_FILE_PATH,
            'mode': 'w'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': sys.stdout
        }
    },
    'loggers': {
        'camelid': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'camelid.googlesheet': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'camelid.cmgroup': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'camelid.pubchemutils': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'pubchempy': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': []
    }
}

logging.config.dictConfig(CONFIG)
