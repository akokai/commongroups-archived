Design
======

General concepts
----------------

Compound groups
^^^^^^^^^^^^^^^

We understand compound groups to be sets of substances that can be defined by their shared molecular features, for reasons that they share other properties of interest.

The premise for grouping chemicals together is that many substances share
substantial similarities in toxicological characteristics. The notion that
these similarities are related to underlying similarities in molecular
structure is supported by toxicological research (Kazius et al., 2005; Singh et
al., 2016). Environmental fate and exposure potential are also known to be
related to molecular structure, making compound groups an important unit of
analysis in chemical hazard assessment and in the environmental health sciences
more broadly (Krowech et al., 2016).

Compounds groups of toxicological interest can be identified by a number of
computational strategies, including predictive toxicology approaches (Faulkner
et al., 2017).

Our focus, however, is on enumerating compounds that belong to groups *already
identified* through established methods. Over several decades of toxicological,
epidemiological, and regulatory science worldwide, several hundred compound
groups have been recognized and associated with known health hazards. For
example, `IARC <http://monographs.iarc.fr/>`_ classifies "Nickel compounds" and
several other compound groups according to their carcinogenicity.

References
^^^^^^^^^^

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


.. _methods:

Methods
-------

Computational tools exist for analyzing and searching molecular structures. Given a broad enough set of **relevant molecular structures**, and a set of **defined structural patterns** corresponding to compound groups of interest, it should be possible to apply computational methods to identify which compounds belong to which group(s).


Defining groups
^^^^^^^^^^^^^^^

Coming soon

Assigning compounds to groups
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Coming soon

Design of this program
----------------------

More technical documentation about how the program works can be found under
:doc:`Usage <usage>` and the :doc:`Developer reference <developer>`.

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

In addition to these parameters, compound groups can be further described by
adding additional information (to the object's ``info`` attribute).
This information is meant for users, and is not used for computational purposes.
