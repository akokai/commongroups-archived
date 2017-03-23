Instantiating a structure-searchable database
=============================================

A prerequisite for using ``commongroups`` is a database of compounds searchable
by chemical structure. This is separate from the required software dependencies.
We do not distribute a pre-built database, and there are no requirements for or
limits on what compounds and data sources might be included in the database.

Nevertheless, we developed and tested ``commongroups`` using a database compiled
from public data available in the `US EPA CompTox Dashboard`_, containing
approximately 700K structures. We believe is a good starting point for most
users.

What follows is a general description of how such a database can be created
and prepared for use with ``commongroups``. In a future release, there will also be
an installation script to automatically build a database along these lines.

Suggested data sources
----------------------

From the `US EPA CompTox Dashboard`_:

-  ``dsstox_20160701.tsv``

   -  Downloaded from: https://comptox.epa.gov/dashboard/downloads
      as ``DSSTox\_Mapping\_20160701.zip``

   -  Date: 2016-07-01 (file generated); 2016-12-14 (posted on EPA website)

   -  Accessed: 2017-01-05

   -  Contains mappings between the DSSTox substance identifier (DTXSID)
      and the associated InChI/InChIKey.

-  ``Dsstox_CAS_number_name.xlsx``

   -  Downloaded from: https://comptox.epa.gov/dashboard/downloads

   -  Date: 2016-11-14

   -  Accessed: 2017-01-05

   -  Contains the CASRN, DTXSID, and the "preferred name" used by US EPA.

-  ``PubChem_DTXSID_mapping_file.txt``

   -  Downloaded from: https://comptox.epa.gov/dashboard/downloads

   -  Date: 2016-11-14

   -  Accessed: 2017-01-05

   -  Contains the PubChem SID, PubChem CID and DTXSID.


Generating a table of structural representations
------------------------------------------------

We use RDKit in Python, with ``pandas`` and ``sqlalchemy``, to generate a
database table that contains molecular structure representations in the RDKit
``mol`` data type. Note that this process can take a while to complete, and is
quite resource-intensive.

-  Take the list of InChI(Key)s and DSSTox substance IDs and convert
   each InChI into a RDKit ``Mol`` object; then convert each molecule object
   into its binary representation.

   -  *Note:* This is a necessary intermediate step because there is no
      ``mol_from_inchi`` method in the PostgreSQL RDKit extension, but there is
      a ``mol_from_pkl`` method that builds molecules out of binary
      representations. If we started with a SMILES-based data set instead of
      InChI, this procedure would be unnecessary.

   -  RDKit fails to create many of the molecules from InChI because of
      very specific errors. The number of molecules in the actual table will
      be somewhat less than 700K.

-  Create a table in PostgreSQL that includes this column of binary objects.

-  Create a new column using the ``mol_from_pkl`` method to generate
   ``mol``- type data, i.e., structures that are understandable by the RDKit
   database extension.

We then integrated the US EPA's mappings from DSSTox substance identifier
(DTXSID) to CASRN, PubChem CID/SID, and chemical names, available in the data
sources listed above.

Creating the index
------------------

To enable fast SQL queries on the molecular structures, we index the table on
the column containing ``mol``-type structures, using the RDKit extension.
This is also a fairly resource-intensive process.

.. _US EPA CompTox Dashboard: https://comptox.epa.gov/dashboard
