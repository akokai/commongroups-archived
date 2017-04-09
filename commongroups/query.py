# coding: utf-8

import logging

import pandas as pd
from pandas import DataFrame

import rdkit
from rdkit import Chem, rdBase
# from rdkit.Chem import AllChem, Draw, rdqueries, rdMolDescriptors

import sqlalchemy
from sqlalchemy import MetaData, Table
from sqlalchemy.sql import literal_column, select, and_, or_, not_, text

from commongroups import logconf  # pylint: disable=unused-import

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def get_query_results(que, con):
    """
    Execute a database query using SQLAlchemy.

    Parameters:
        que: SQLAlchemy :class:`Select` object.
        con: SQLAlchemy database :class:`Connection` object.

    Returns:
        A pandas :class:`DataFrame` containing all rows of results.
    """
    res = con.execute(que)
    logger.info('%i results', res.rowcount)
    ret = DataFrame(res.fetchall(), columns=res.keys())
    return ret


class QueryMethod(object):
    """
    Query method for a compound group.
    """
    def __init__(self, db_table, db_mol, *args, **kwargs):
        self.db_table = db_table
        self.db_mol = db_mol  # TODO: bindparams to where_clause for db_mol?
        self.query = None

    def create_query_where(self, where_clause):
        que = select([self.db_table]).where(where_clause)
        return que

    def get_results(self, con):
        if not self.query:
            return
        return get_query_results(self.query, con)


# def substructure_query(pattern, mol, fields):
#     """
#     Construct a substructure query based on a SMARTS query molecule.

#     Parameters:
#         pattern: Substructure query molecule as SMARTS string.
#         mol: SQLAlchemy object representing a column of searchable molecules.
#         fields (iterable): SQLAlchemy selctable objects to select from.

#     Returns:
#         SQLAlchemy :class:`Select` object.
#     """
#     where_clause = mol.op('@>')(text(':q ::qmol').bindparams(q=str(pattern)))
#     que = select(fields).where(where_clause)
#     return que


# def substruct_exclude(pattern, excludes, mol, fields):
#     """
#     Construct a query matching one substructure and excluding others.

#     Parameters:
#         pattern (str): Substructure to match, as a SMARTS string.
#         excludes (iterable): Substructures to exclude, as SMARTS strings.
#         mol: SQLAlchemy object representing a column of searchable molecules.
#         fields (iterable): SQLAlchemy selctable objects to select from.

#     Returns:
#         SQLAlchemy :class:`Select` object.
#     """
#     sub_clause = mol.op('@>')(text(':p ::qmol').bindparams(p=pattern))
#     not_clauses = []
#     for pat in excludes:
#         match = mol.op('@>')(text(':x ::qmol').bindparams(x=pat))
#         not_clauses.append(not_(match))
#     que = select(fields).where(and_(sub_clause, *not_clauses))
#     return que


# def get_element_inorganic(elem_smarts, mol, fields):
#     """
#     Match all compounds containing an element but exclude any compounds
#     containing C-H or C-C bonds. Works OK most of the time.
#     """
#     organic_smarts = ['[C,c]~[C,c]', '[C!H0,c!H0]']
#     return substruct_exclude(elem_smarts, organic_smarts, mol, fields)
