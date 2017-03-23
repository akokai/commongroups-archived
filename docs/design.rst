Design
======

General concepts
----------------

We understand **compound groups** to be sets of substances defined by their
shared molecular features, and which are useful to consider as a group because
they share other properties of interest.

The premise for grouping chemicals together is that many substances share
substantial similarities in toxicological characteristics. The notion that
these similarities are related to underlying similarities in molecular
structure is supported by toxicological research (Kazius et al., 2005; Singh et
al., 2016). Environmental fate and exposure potential are also known to be
related to molecular structure, making compound groups an important unit of
analysis in chemical hazard assessment and in the environmental health sciences
more broadly (Krowech et al., 2016).

Compounds groups of toxicological interest can be identified by a number of
research strategies, including computational and predictive toxicology
approaches (Faulkner et al., 2017).

Our focus, however, is on enumerating compounds that belong to groups *already
identified* through established methods. Over several decades of toxicological,
epidemiological, and regulatory science worldwide, several hundred compound
groups have been recognized and associated with known health hazards. For
example, `IARC <http://monographs.iarc.fr/>`_ classifies "Nickel compounds" and
several other compound groups according to their carcinogenicity.

See below for :ref:`references <toxrefs>`.


Methods for associating compounds with groups
---------------------------------------------

Computational tools exist for analyzing and searching molecular structures. Given a broad enough **set of relevant molecular structures**, and a set of **defined structural patterns** corresponding to compound groups of interest, it should be possible to apply computational methods to identify which compounds belong to which group(s). That is the goal of Common Groups.

A first priority is to define commonly accepted hazard-based groups in terms of molecular structures. Our target set of compound groups consists of all the groups named within the collection of authoritative hazard identification lists used in the `GreenScreen for Safer Chemicals`_.

Defining groups
^^^^^^^^^^^^^^^

In this project we define groups by specifying one or more patterns in molecular structure. We express these patterns in `SMARTS`_ notation. For some groups, we may need to specify multiple patterns linked by logical conditions ("and", "or", "not", etc.).

For example, [**TODO**, insert example].

The ``commongroups`` program accepts group definitions in the form of specific `parameters <params>`_ described below.

We believe that the technical definitions of compound groups should be
openly discussed and peer-reviewed to ensure their accuracy and robustness.


Design of this program
----------------------

The ``commongroups`` software package manages the process of going from a compound group definition to a list of compounds that match that definition. Group definitions can be retrieved from a Google Spreadsheet.

For each compound group, ``commongroups`` formulates a database query that expresses the specified logic and the structural patterns in `SQL`_. It then runs this query on a database of chemical structures, and retrieves the resulting set of compounds that match the group definition.

The actual compounds identified will depend on what compounds that are represented in the database that is used. For information about how we construct a database for this purpose, see :doc:`Database <database>`. For detailed technical documentation about how the program works, see :doc:`Usage <usage>` and the :doc:`Developer reference <developer>`.

.. _params:

Parameters for defining a compound group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following parameters are necessary to define a compound group.
**This is subject to change.**

-  ``method``: The search method for identifying compounds in the group.
   Currently this can be either 'substructure' for simple substructure matching
   or 'function' for more complex SQL queries involving comparison against
   multiple substructures.

-  ``structure``: The structure used as input to the search method.

-  ``structure_type``: How the structure is notated, e.g., SMILES or SMARTS.

-  ``function``: The specific function used as the search method (if it is not
   a simple substructure search).

-  ``cmg_id``: A unique identifier for the group.

-  ``name``: The name of the group, e.g., "Pthalates".

In addition to these parameters, compound groups can be further described by additional information, such as notes, descriptions, or search statistics. This information is not used for computational purposes, but exists for interpretation and communication of results.


.. _toxrefs:

References
----------

-  Kazius, J., McGuire, R., & Bursi, R. (2005). Derivation and validation of
   toxicophores for mutagenicity prediction. *Journal of Medicinal Chemistry*, 48(1), 312–320. https://doi.org/10.1021/jm040835a

-  Singh, P. K., Negi, A., Gupta, P. K., Chauhan, M., & Kumar, R. (2016).
   Toxicophore exploration as a screening technology for drug design and
   discovery: Techniques, scope and limitations. *Archives of Toxicology*,
   90(8), 1785–1802. https://doi.org/10.1007/s00204-015-1587-5

-  Krowech, G., Hoover, S., Plummer, L., Sandy, M., Zeise, L., & Solomon, G.
   (2016). Identifying chemical groups for biomonitoring. *Environmental Health
   Perspectives,* 124(12), A219–A226. https://doi.org/10.1289/EHP537

-  Faulkner, D., Rubin Shen, L. K., et al. (2017). Tools for green molecular
   design to reduce toxicological risk. In R. J. Richardson & D. E. Johnson
   (Eds.), *Computational systems pharmacology and toxicology* (pp. 36–59).
   Cambridge: Royal Society of Chemistry.
   https://doi.org/10.1039/9781782623731-00036

.. _GreenScreen for Safer Chemicals: http://www.greenscreenchemicals.org/

.. _SMARTS: http://www.daylight.com/dayhtml/doc/theory/theory.smarts.html

.. _SQL: https://en.wikipedia.org/wiki/SQL
