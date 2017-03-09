# coding: utf-8

"""
Chemical database initialization
"""

from os.path import join as pjoin
import subprocess
from subprocess import run

import pandas as pd
from rdkit import Chem
from sqlalchemy import create_engine, types
from sqlalchemy.sql import text

# TODO: Configure from file or ask user for these.
conn = create_engine('postgresql://akokai@localhost/chmdata')
EPA_DATA_PATH = '/opt/akokai/data/EPA/'
DTX_STRUCT = pjoin(EPA_DATA_PATH, 'dsstox_20160701.tsv')
DTX_CASRNS = pjoin(EPA_DATA_PATH, 'Dsstox_CAS_number_name.xlsx')
DTX_CIDS = pjoin(EPA_DATA_PATH, 'PubChem_DTXSID_mapping_file.txt')

dtypes = {'dtxsid': types.Text,
          'inchi': types.Text,
          'inchikey': types.Text,
          'bin': types.Binary}

created = 0
errors = 0
chunk = 10000

dtx = pd.read_table(DTX_STRUCT, names=['dtxsid', 'inchi', 'inchikey'],
                    chunksize=chunk, low_memory=True)

for df in dtx:
    df['mol'] = df.inchi.apply(Chem.MolFromInchi)
    df.dropna(inplace=True)
    n = len(df)
    created += n
    errors += chunk - n
    print('{0} molecules created, {1} errors'.format(n, chunk - n))
    df['bin'] = df.mol.apply(lambda m: m.ToBinary())
    df.drop('mol', axis=1, inplace=True)
    df.to_sql('dtx', conn, if_exists='append', index=False, chunksize=65536, dtype=dtypes)

print('Total: {0} molecules created, {1} errors'.format(created, errors))

# ### Generate `mol`-type column
# Create a new table with columns `(dtxsid, inchi, inchikey, molecule)` where the last column contains RDKit `mol`-type structures.

cmd = text(
    '''create table chem
       as select dtxsid, inchi, inchikey, mol_from_pkl(bin) molecule from dtx;''')
res = conn.execute(cmd)
print(res.rowcount, 'rows created')

try:
    assert res.rowcount == ncreated
except AssertionError:
    pass  # TODO

# ## Import external ID mappings: DTXSID to CASRN, CID

# ### Load DTXSID:CASRN mappings
# Note that these are all 1:1 mappings.
# Using pandas here as an easy way to read in the Excel file.

dtx_cas = pd.read_excel(DTX_CASRNS)
cas_cols = ['casrn', 'dtxsid', 'name']
dtx_cas.columns = cas_cols
print(len(dtx_cas), 'DTXSID:CASRN mappings')

dtypes_cas = dict(zip(cas_cols, 3*[types.Text]))
dtx_cas.to_sql('dtx_cas', conn, if_exists='replace', index=False, chunksize=65536, dtype=dtypes_cas)

# ### Load DTXSID:CID mappings

# Each DTXSID is mapped onto one CID but non-uniquely (some share the same CID).
# Joining tables by DTXSID should ensure that the proper mapping is maintained.

# TODO: Change the file path in the SQL `copy` statement ...

cmd = text('''
    create table dtx_pubchem (sid text, cid text, dtxsid text);
    copy dtx_pubchem from '/opt/akokai/data/EPA/PubChem_DTXSID_mapping_file.txt'
    with (format csv, delimiter '\t', header);''')
res = conn.execute(cmd)
print(res.rowcount)


# In[14]:

# Check that the table contains expected data...
cmd = text('select * from dtx_pubchem limit 5;')
conn.execute(cmd).fetchall()


# ### Merge external IDs with table of molecular structures (join by DTXSID)

# In[9]:

cmd = text('''
    create table cpds
    as select chem.dtxsid, dtx_pubchem.cid, dtx_cas.casrn, dtx_cas.name,
           chem.inchikey, chem.inchi, chem.molecule
    from chem
    left outer join dtx_pubchem on dtx_pubchem.dtxsid = chem.dtxsid
    left outer join dtx_cas on dtx_cas.dtxsid = chem.dtxsid;''')
res = conn.execute(cmd)
print(res.rowcount)


# In[10]:

# Check that the table contains expected data...
cmd = text('select * from cpds limit 5;')
conn.execute(cmd).fetchall()


# ## Create the index
#
# Index the table on the structures using the GiST-powered RDKit extension. (This is what enables substructure searching in SQL.)
#
# **Make sure you are creating the index on the right table.**
#
# It takes a while...

# In[11]:

cmd = text('create index molidx on cpds using gist(molecule);')
res = conn.execute(cmd)

