# coding: utf-8

import logging

import pandas as pd
from pandas import DataFrame

import rdkit
from rdkit import Chem, rdBase
from rdkit.Chem import AllChem, Draw, rdqueries, rdMolDescriptors

import sqlalchemy
from sqlalchemy.sql import select, and_, or_, not_, text

from camelid import logconf  # pylint: disable=unused-import

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def substructure_query(pattern, mol, fields):
    """
    Construct a substructure query based on a SMARTS query molecule.

    Parameters:
        pattern: Substructure query molecule as SMARTS string.
        mol: SQLAlchemy object representing a column of searchable molecules.
        fields (iterable): SQLAlchemy selctable objects to select from.
    """
    where_clause = mol.op('@>')(text(':q ::qmol').bindparams(q=str(pattern)))
    que = select(fields).where(where_clause)
    return que


def substruct_exclude_query(pattern, exclude_pattern, mol, fields):
    """
    Construct a query matching one substructure and excluding another.

    Parameters:
        pattern (str): Substructure to match, as SMARTS string.
        exclude_pattern (str): Substructure to exclude, as SMARTS string.
        mol: SQLAlchemy object representing a column of searchable molecules.
        fields (iterable): SQLAlchemy selctable objects to select from.
    """
    sub_clause = mol.op('@>')(text(':p ::qmol').bindparams(p=pattern))
    not_clause = mol.op('@>')(text(':x ::qmol').bindparams(x=exclude_pattern))
    que = select(fields).where(and_(sub_clause,
                                    not_(not_clause)))
    return que


def get_query_results(que, con):
    res = con.execute(que)
    logger.info('%i results', res.rowcount)
    ret = DataFrame(res.fetchall(), columns=res.keys())
    return ret
