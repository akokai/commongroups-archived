# coding: utf-8

"""
Chemical database initialization
"""

from os.path import join as pjoin
import pandas as pd
from rdkit import Chem
from sqlalchemy import create_engine, types
from sqlalchemy.sql import text

# **Change any of the following lines as appropriate for your system.**

conn = create_engine('postgresql://akokai@localhost/chmdata')

EPA_DATA_PATH = '/opt/akokai/data/EPA/'

DTX_STRUCT = pjoin(EPA_DATA_PATH, 'dsstox_20160701.tsv')
DTX_CASRNS = pjoin(EPA_DATA_PATH, 'Dsstox_CAS_number_name.xlsx')
DTX_CIDS = pjoin(EPA_DATA_PATH, 'PubChem_DTXSID_mapping_file.txt')


# ## Generate database table of structural representations
#
# - Taking the list of EPA InChI(Key)s and DSSTox substance IDs, convert each InChI into a RDKit `Mol` object. Then convert each `Mol` into its binary representation.
# - Create a big table in PostgreSQL that adds a binary molecule-object column to the original EPA dataset. In other words, a table with columns `(dtxsid, inchi, inchikey, bin)`.
#   - This is a necessary intermediate step because there is no `mol_from_inchi` method in the PGSQL RDKit extension, but there is a `mol_from_pkl` that builds molecules out of binary representations. Otherwise we could go straight from InChI to molecules in the SQL table.
#   - The 720K rows seems to be too much to process in memory all at once, so I am going through the file lazily in chunks.
#
# ### Notes
# - Use all-lowercase column names to avoid SQL mix-ups.
# - RDKit will fail to create many of the molecules from InChI because of very specific errors. The number of molecules we have in the end will probably be less than 700K.

# In[3]:

# To be able to re-run this code from scratch, first drop the table if it already exists:
# !psql chmdata -c 'drop table dtx;'


# This will take a while and use lots of CPU and memory...

dtypes = {'dtxsid': types.Text,
          'inchi': types.Text,
          'inchikey': types.Text,
          'bin': types.Binary}

ninput = 719996
ncreated = 0
chunk = 10000

dtx = pd.read_table(DTX_STRUCT, names=['dtxsid', 'inchi', 'inchikey'],
                    chunksize=chunk, low_memory=True)

for df in dtx:
    df['mol'] = df.inchi.apply(Chem.MolFromInchi)
    df.dropna(inplace=True)
    n = len(df)
    ncreated += n
    print('{0} molecules created, {1} errors'.format(n, chunk - n))
    df['bin'] = df.mol.apply(lambda m: m.ToBinary())
    df.drop('mol', axis=1, inplace=True)
    df.to_sql('dtx', conn, if_exists='append', index=False, chunksize=65536, dtype=dtypes)

print('Total: {0} molecules created, {1} errors'.format(ncreated, ninput - ncreated))


# ### Generate `mol`-type column
#
# Create a new table with columns `(dtxsid, inchi, inchikey, molecule)` where the last column contains RDKit `mol`-type structures.

# In[3]:

# To be able to re-run the code below, first drop the table:
# !psql chmdata1 -c 'drop table chem;'


# In[4]:

cmd = text(
    '''create table chem
       as select dtxsid, inchi, inchikey, mol_from_pkl(bin) molecule from dtx;''')
res = conn.execute(cmd)
print(res.rowcount, 'rows created')


# ### Check results

# In[10]:

assert res.rowcount == ncreated


# In[5]:

# Check that the table contains expected data...
cmd = text('select * from chem limit 5;')
conn.execute(cmd).fetchall()


# ## Import external ID mappings: DTXSID to CASRN, CID
#
# ### Load DTXSID:CASRN mappings
#
# Note that these are all 1:1 mappings. Using pandas here as an easy way to read in the Excel file.

# In[12]:

dtx_cas = pd.read_excel(DTX_CASRNS)
cas_cols = ['casrn', 'dtxsid', 'name']
dtx_cas.columns = cas_cols
print(len(dtx_cas), 'DTXSID:CASRN mappings')


# In[13]:

dtypes_cas = dict(zip(cas_cols, 3*[types.Text]))
dtx_cas.to_sql('dtx_cas', conn, if_exists='replace', index=False, chunksize=65536, dtype=dtypes_cas)


# In[14]:

# Check that the table contains expected data...
cmd = text('select * from dtx_cas limit 5;')
conn.execute(cmd).fetchall()


# ### Load DTXSID:CID mappings
#
# Each DTXSID is mapped onto one CID but non-uniquely (some share the same CID). Joining tables by DTXSID should ensure that the proper mapping is maintained (see: `ID mapping inspection.ipynb`).
#
# **Change the file path in the SQL `copy...` statement below to the appropriate path for your system.**

# In[ ]:

# To be able to re-run the code below, first drop the table:
# !psql chmdata1 -c 'drop table dtx_pubchem;'


# In[13]:

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

