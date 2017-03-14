# coding: utf-8

from rdkit import Chem, rdBase
from rdkit.Chem import AllChem, Draw, rdqueries, rdMolDescriptors
from rdkit.Chem.Draw import IPythonConsole
from sqlalchemy import create_engine
from sqlalchemy.sql import select, and_, or_, not_, text

from camelid import logconf

logger = logging.getLogger(__name__)

# Not necessary to define in this module!
TABLE = 'cpds'
FIELDS = ('cid', 'inchi', 'molecule')
MOLFIELD = 'molecule'

# def _query(qmol, table, fields, molfield, smarts=True, *args, **kwargs):
#     where = "{0} @> '{1}'::qmol".format(molfield, str(qmol))
#     content = [', '.join(fields), table, where]
#     qtext = 'select {0} from {1} where {2}'.format(*content)
#     return qtext


def _smarts_query(qmol, table, fields, molfield, *args, **kwargs):
    where = "{0} @> '{1}'::qmol".format(molfield, str(qmol))
    content = [', '.join(fields), table, where]
    qtext = 'select {0} from {1} where {2}'.format(*content)
    return qtext


def construct_smarts_query(qmol, *args, **kwargs):
    return _smarts_query(qmol, TABLE, FIELDS, MOLFIELD, *args, **kwargs)


# Use SQLAlchemy???
# class QueryText(object):
#     def __init__():
#         pass


def query_results(conn, qtext):
    res = conn.execute(text(qtext))
    logger.info('%i results', res.rowcount)
    return res.fetchall()
