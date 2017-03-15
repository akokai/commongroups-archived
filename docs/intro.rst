Introduction
============

|A group of camelids|

.. |A group of camelids| image:: _static/alpacas.jpg

``camelid`` is a tool for identifying chemical substances that belong to
structurally defined groups.

Goals
-----

Certain *groups* or *classes* of chemical substances are of interest because of
their environmental or toxicological hazard characteristics. Many chemical
groups are referenced in hazard screening methods and named in regulatory
lists.  However, determining the set of specific chemicals that might belong to
each group is usually left up to someone else.

The goal of this project is to provide methods to identify arbitrary sets of
chemicals belonging to classes that are *defined by structure.* We aim to apply
basic cheminformatics techniques to:

-  Find all molecular structures within a larger set (i.e., database) that
   belong to a given class.

-  Screen individual molecular structures for membership in a given group.

-  Do each of these things automatically for a large number of groups all at
   once.

We imagine the possible uses of the project to include answering questions
like: *What dithiocarbamates are in this list of compounds?* or *Does this new
compound belong to any chemical groups associated with endocrine disruption?*


Frequently asked questions
--------------------------

**Does this tool use structural similarity searching?** No, it uses highly
specific substructure searching, mostly using `SMARTS`_. The idea is that the
classes of chemicals we want to identify are already precisely defined, rather
than inferred by similarity. We see this approach as complementary to more
"fuzzy" similarity searching methods.

**Does this tool identify toxicophores?** No. Toxicophore identification is
part of the rational basis for identifying groups of substances by structure,
and is therefore a background condition of our project, rather than its goal.

**Isn't this limited by the current state of knowledge linking individual
groups of chemicals to individual hazard endpoints?** Yes. The purpose of this
project is not to create new knowledge, but to identify potentially new
*associations* between specific compounds and hazards, based on existing
knowledge.

**Why is it called ``camelid``?** This project has to do with classifying
things and organizing them into groups. Camelids are a category of animal
that travel in herds.

.. _SMARTS: http://www.daylight.com/dayhtml/doc/theory/theory.smarts.html
