# -*- coding: utf-8 -*-
"""Scripts for processing identifier correspondences."""

from __future__ import unicode_literals

import os
from os.path import join as pjoin
import pandas as pd
from pandas import DataFrame
from boltons.fileutils import mkdir_p

from . import logconf
from .run import CamelidEnv

logger = logging.getLogger(__name__)

def cas_to_cid(ids_file, env):
    """
    CASRN to PubChem CID alignment automation script.
    
    Take the output from PubChem Identifier Exchange conversion of CASRNs into CIDs, and determine whether each CASRN:CID association appears valid within the context of the dataset. Best used on very large datasets (e.g. conversion of IDs in entire chemical library), to maximize the chance of catching identifier collisions or ambiguity.
    """

    RESULTS_PATH = env.results_path
    # ...