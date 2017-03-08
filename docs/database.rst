Instantiating a structure-searchable database
=============================================

A prerequisite for using ``camelid`` is a database of compounds searchable by chemical structure. There are no requirements for or limitations on what compounds and data sources are incorporated in the database. To 


Goal
~~~~

Bootstrap a chemical database with ~700,000 structures from the US EPA
CompTox Dashboard's public dataset.

Set up the database so that it can be used for substructure searching
via the `RDKit PostgreSQL database
cartridge <http://www.rdkit.org/docs/Cartridge.html>`_. Also include
CASRNs and PubChem CIDs as much as possible.

Data sources
~~~~~~~~~~~~

``dsstox_20160701.tsv``
-  Downloaded from:
https://comptox.epa.gov/dashboard/downloads (zip filename:
DSSTox\_Mapping\_20160701.zip)
-  Date: 2016-07-01 (file generated);
2016-12-14 (posted on EPA website)
-  Accessed: 2017-01-05
 
-  "The DSSTOX
mapping file contains mappings between the DSSTox substance identifier
(DTXSID) and the associated InChI String and InChI Key."

``Dsstox_CAS_number_name.xlsx``
-  Downloaded from:
https://comptox.epa.gov/dashboard/downloads
-  Date: 2016-11-14 -
Accessed: 2017-01-05
-  "The DSSTox Identifiers file is in Excel format
and includes the CAS Number, DSSTox substance identifier (DTXSID) and
the Preferred Name."

``PubChem_DTXSID_mapping_file.txt``
-  Downloaded from:
https://comptox.epa.gov/dashboard/downloads
-  Date: 2016-11-14 -
Accessed: 2017-01-05
-  "The DSSTox to PubChem Identifiers mapping file
is in TXT format and includes the PubChem SID, PubChem CID and DSSTox
substance identifier (DTXSID)."

Notes on software dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Requires:
-  a running instance of PostgreSQL with the RDKit cartridge
installed
(`instructions <https://github.com/rdkit/rdkit/blob/master/Docs/Book/Install.md>`_);
- Python packages and dependencies: rdkit, sqlalchemy, psycopg2, pandas.


Generate database table of structural representations
-----------------------------------------------------

-  Taking the list of EPA InChI(Key)s and DSSTox substance IDs, convert
   each InChI into a RDKit ``Mol`` object. Then convert each ``Mol``
   into its binary representation.
-  Create a big table in PostgreSQL that adds a binary molecule-object
   column to the original EPA dataset. In other words, a table with
   columns ``(dtxsid, inchi, inchikey, bin)``.
-  This is a necessary intermediate step because there is no
   ``mol_from_inchi`` method in the PGSQL RDKit extension, but there is
   a ``mol_from_pkl`` that builds molecules out of binary
   representations. Otherwise we could go straight from InChI to
   molecules in the SQL table.
-  The 720K rows seems to be too much to process in memory all at once,
   so I am going through the file lazily in chunks.

Notes
~~~~~

-  Use all-lowercase column names to avoid SQL mix-ups.
-  RDKit will fail to create many of the molecules from InChI because of
   very specific errors. The number of molecules we have in the end will
   probably be less than 700K.

.. code:: ipython3

    # To be able to re-run this code from scratch, first drop the table if it already exists:
    # !psql chmdata -c 'drop table dtx;'

This will take a while and use lots of CPU and memory...

.. code:: ipython3

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


.. parsed-literal::

    9996 molecules created, 4 errors
    9985 molecules created, 15 errors
    9994 molecules created, 6 errors
    9995 molecules created, 5 errors
    9995 molecules created, 5 errors
    9993 molecules created, 7 errors
    9997 molecules created, 3 errors
    9989 molecules created, 11 errors
    9996 molecules created, 4 errors
    9993 molecules created, 7 errors
    9989 molecules created, 11 errors
    9993 molecules created, 7 errors
    9992 molecules created, 8 errors
    9988 molecules created, 12 errors
    10000 molecules created, 0 errors
    10000 molecules created, 0 errors
    9998 molecules created, 2 errors
    9996 molecules created, 4 errors
    9994 molecules created, 6 errors
    9993 molecules created, 7 errors
    9998 molecules created, 2 errors
    10000 molecules created, 0 errors
    10000 molecules created, 0 errors
    10000 molecules created, 0 errors
    10000 molecules created, 0 errors
    9999 molecules created, 1 errors
    9998 molecules created, 2 errors
    9996 molecules created, 4 errors
    9990 molecules created, 10 errors
    9998 molecules created, 2 errors
    9998 molecules created, 2 errors
    9992 molecules created, 8 errors
    9996 molecules created, 4 errors
    9995 molecules created, 5 errors
    9992 molecules created, 8 errors
    9998 molecules created, 2 errors
    9998 molecules created, 2 errors
    9997 molecules created, 3 errors
    9994 molecules created, 6 errors
    10000 molecules created, 0 errors
    9995 molecules created, 5 errors
    9996 molecules created, 4 errors
    10000 molecules created, 0 errors
    9993 molecules created, 7 errors
    9995 molecules created, 5 errors
    9998 molecules created, 2 errors
    9999 molecules created, 1 errors
    9997 molecules created, 3 errors
    9998 molecules created, 2 errors
    9986 molecules created, 14 errors
    9999 molecules created, 1 errors
    9999 molecules created, 1 errors
    9996 molecules created, 4 errors
    10000 molecules created, 0 errors
    10000 molecules created, 0 errors
    9995 molecules created, 5 errors
    9993 molecules created, 7 errors
    9998 molecules created, 2 errors
    9991 molecules created, 9 errors
    10000 molecules created, 0 errors
    9991 molecules created, 9 errors
    9994 molecules created, 6 errors
    9989 molecules created, 11 errors
    9987 molecules created, 13 errors
    9987 molecules created, 13 errors
    9995 molecules created, 5 errors
    9992 molecules created, 8 errors
    9990 molecules created, 10 errors
    9991 molecules created, 9 errors
    9992 molecules created, 8 errors
    9991 molecules created, 9 errors
    9989 molecules created, 11 errors
    Total: 719631 molecules created, 365 errors


Generate ``mol``-type column
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a new table with columns ``(dtxsid, inchi, inchikey, molecule)``
where the last column contains RDKit ``mol``-type structures.

.. code:: ipython3

    # To be able to re-run the code below, first drop the table:
    # !psql chmdata1 -c 'drop table chem;'


.. parsed-literal::

    DROP TABLE


.. code:: ipython3

    cmd = text(
        '''create table chem
           as select dtxsid, inchi, inchikey, mol_from_pkl(bin) molecule from dtx;''')
    res = conn.execute(cmd)
    print(res.rowcount, 'rows created')


.. parsed-literal::

    719631 rows created


Check results
~~~~~~~~~~~~~

.. code:: ipython3

    assert res.rowcount == ncreated

.. code:: ipython3

    # Check that the table contains expected data... 
    cmd = text('select * from chem limit 5;')
    conn.execute(cmd).fetchall()




.. parsed-literal::

    [('DTXSID7020001', 'InChI=1S/C11H9N3/c12-10-6-5-8-7-3-1-2-4-9(7)13-11(8)14-10/h1-6H,(H3,12,13,14)', 'FJTNLJLPLJDTRM-UHFFFAOYSA-N', 'N=c1ccc2c([nH]1)[nH]c1ccccc12'),
     ('DTXSID5039224', 'InChI=1S/C2H4O/c1-2-3/h2H,1H3', 'IKHGUXGNUITLKF-UHFFFAOYSA-N', 'CC=O'),
     ('DTXSID50872971', 'InChI=1S/C4H8N2O/c1-3-5-6(2)4-7/h3-4H,1-2H3/b5-3+', 'IMAGWKUTFZRWSB-HWKANZROSA-N', 'C/C=N/N(C)C=O'),
     ('DTXSID2020004', 'InChI=1S/C2H5NO/c1-2-3-4/h2,4H,1H3/b3-2+', 'FZENGILVLUJGJX-NSCUHMNNSA-N', 'C/C=N/O'),
     ('DTXSID7020005', 'InChI=1S/C2H5NO/c1-2(3)4/h1H3,(H2,3,4)', 'DLFVBJFMPXGRIB-UHFFFAOYSA-N', 'CC(=N)O')]



Import external ID mappings: DTXSID to CASRN, CID
-------------------------------------------------

Load DTXSID:CASRN mappings
~~~~~~~~~~~~~~~~~~~~~~~~~~

Note that these are all 1:1 mappings. Using pandas here as an easy way
to read in the Excel file.

.. code:: ipython3

    dtx_cas = pd.read_excel(DTX_CASRNS)
    cas_cols = ['casrn', 'dtxsid', 'name']
    dtx_cas.columns = cas_cols
    print(len(dtx_cas), 'DTXSID:CASRN mappings')


.. parsed-literal::

    753398 DTXSID:CASRN mappings


.. code:: ipython3

    dtypes_cas = dict(zip(cas_cols, 3*[types.Text]))
    dtx_cas.to_sql('dtx_cas', conn, if_exists='replace', index=False, chunksize=65536, dtype=dtypes_cas)

.. code:: ipython3

    # Check that the table contains expected data... 
    cmd = text('select * from dtx_cas limit 5;')
    conn.execute(cmd).fetchall()




.. parsed-literal::

    [('26148-68-5', 'DTXSID7020001', 'A-alpha-C'),
     ('107-29-9', 'DTXSID2020004', 'Acetaldehyde oxime'),
     ('60-35-5', 'DTXSID7020005', 'Acetamide'),
     ('103-90-2', 'DTXSID2020006', 'Acetaminophen'),
     ('968-81-0', 'DTXSID7020007', 'Acetohexamide')]



Load DTXSID:CID mappings
~~~~~~~~~~~~~~~~~~~~~~~~

Each DTXSID is mapped onto one CID but non-uniquely (some share the same
CID). Joining tables by DTXSID should ensure that the proper mapping is
maintained (see: ``ID mapping inspection.ipynb``).

**Change the file path in the SQL ``copy...`` statement below to the
appropriate path for your system.**

.. code:: ipython3

    # To be able to re-run the code below, first drop the table:
    # !psql chmdata1 -c 'drop table dtx_pubchem;'

.. code:: ipython3

    cmd = text('''
        create table dtx_pubchem (sid text, cid text, dtxsid text);
        copy dtx_pubchem from '/opt/akokai/data/EPA/PubChem_DTXSID_mapping_file.txt'
        with (format csv, delimiter '\t', header);''')
    res = conn.execute(cmd)
    print(res.rowcount)


.. parsed-literal::

    735563


.. code:: ipython3

    # Check that the table contains expected data... 
    cmd = text('select * from dtx_pubchem limit 5;')
    conn.execute(cmd).fetchall()




.. parsed-literal::

    [('316388891', '20404', 'DTXSID30873143'),
     ('316388890', '10142816', 'DTXSID70873142'),
     ('316388889', '50742127', 'DTXSID40873139'),
     ('316388888', '19073841', 'DTXSID20873137'),
     ('316388887', '11505215', 'DTXSID00873135')]



Merge external IDs with table of molecular structures (join by DTXSID)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: ipython3

    cmd = text('''
        create table cpds
        as select chem.dtxsid, dtx_pubchem.cid, dtx_cas.casrn, dtx_cas.name,
               chem.inchikey, chem.inchi, chem.molecule
        from chem
        left outer join dtx_pubchem on dtx_pubchem.dtxsid = chem.dtxsid
        left outer join dtx_cas on dtx_cas.dtxsid = chem.dtxsid;''')
    res = conn.execute(cmd)
    print(res.rowcount)


.. parsed-literal::

    719631


.. code:: ipython3

    # Check that the table contains expected data... 
    cmd = text('select * from cpds limit 5;')
    conn.execute(cmd).fetchall()




.. parsed-literal::

    [('DTXSID7020001', '62805', '26148-68-5', 'A-alpha-C', 'FJTNLJLPLJDTRM-UHFFFAOYSA-N', 'InChI=1S/C11H9N3/c12-10-6-5-8-7-3-1-2-4-9(7)13-11(8)14-10/h1-6H,(H3,12,13,14)', 'N=c1ccc2c([nH]1)[nH]c1ccccc12'),
     ('DTXSID5039224', '177', '75-07-0', 'Acetaldehyde', 'IKHGUXGNUITLKF-UHFFFAOYSA-N', 'InChI=1S/C2H4O/c1-2-3/h2H,1H3', 'CC=O'),
     ('DTXSID50872971', '9548611', '61748-21-8', "N'-[(1E)-Ethylidene]-N-methylformohydrazide", 'IMAGWKUTFZRWSB-HWKANZROSA-N', 'InChI=1S/C4H8N2O/c1-3-5-6(2)4-7/h3-4H,1-2H3/b5-3+', 'C/C=N/N(C)C=O'),
     ('DTXSID2020004', '5324279', '107-29-9', 'Acetaldehyde oxime', 'FZENGILVLUJGJX-NSCUHMNNSA-N', 'InChI=1S/C2H5NO/c1-2-3-4/h2,4H,1H3/b3-2+', 'C/C=N/O'),
     ('DTXSID7020005', '178', '60-35-5', 'Acetamide', 'DLFVBJFMPXGRIB-UHFFFAOYSA-N', 'InChI=1S/C2H5NO/c1-2(3)4/h1H3,(H2,3,4)', 'CC(=N)O')]



Create the index
----------------

Index the table on the structures using the GiST-powered RDKit
extension. (This is what enables substructure searching in SQL.)

**Make sure you are creating the index on the right table.**

It takes a while...

.. code:: ipython3

    cmd = text('create index molidx on cpds using gist(molecule);')
    res = conn.execute(cmd)
