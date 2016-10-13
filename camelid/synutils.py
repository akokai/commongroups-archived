# -*- coding: utf-8 -*-

import re

DESELECT_RX = [
    r'^\d{2,}',                         # starts with 2+ digits
    r'\d{3,}',                          # 3+ digits in a row anywhere
    r'^\d+$',
    r'^[A-Z0-9]{10}$',                  # Some kind of identifier
    r'^InChI',
    r'[A-Z]{14}-[A-Z]{10}-[A-Z]',       # InChIKey
    r'^AC1',
    r'^WLN:',
    r'^ACMC-',
    r'^C\d+H\d+'                        # organic molecular formula
    ]

DESELECT = [re.compile(pattern) for pattern in DESELECT_RX]

# Regex patterns for synonyms that we want to keep (e.g. database IDs),
# even if they match the deselect patterns.
SELECT_RX = {
    # 'database ID type': r'regex for ID string',  # etc.
    'UNII': r'^UNII-',
    'CHEMBL': r'^CHEMBL'
    }

SELECT = {k: re.compile(v) for k, v in SELECT_RX.items()}


def select_name(synonym):
    """
    Determine a synonym is likely to be a human-readable name.

    Parameters:
        synonym (str): The synonym to check.

    Returns:
        ``True`` if the synonym is probably a name, else ``False``.
    """
    deselecting = [patt.search(synonym) for patt in DESELECT]
    deselected = any(deselecting)
    return not deselected


def select_synonym(synonym):
    """
    Determine whether to include or exclude a synonym.

    Criteria: *Exclude* if ``synonym`` matches only patterns specified in
    ``DESELECT``. *Include* if it matches no patterns at all, or if it matches
    any pattern specified in``SELECT`` (even if it also matches in
    ``DESELECT``).

    Parameters:
        synonym (str): The synonym to check.

    Returns:
        ``True`` if the synonym is OK to include, else ``False``.

    Examples:
    >>> select_synonym('UNII-12345')
    True
    >>> select_synonym('InChI=FOOBAR')
    False
    >>> select_synonym('aziridine')
    True
    """
    deselecting = [patt.search(synonym) for patt in DESELECT]
    deselected = any(deselecting)

    selecting = {name: patt.search(synonym) for name, patt in SELECT.items()}
    selected = any(selecting.values())

    return selected or not deselected

# Now you can do:
# syns = [some list of synonyms]
# ok_synonyms = [syn for syn in syns if select_synonym(syn)]

# TODO: %timeit on an actual synonym set from PubChem.
# TODO: Add to unit tests.


def identify_synonym(synonym):
    """
    Identify synonyms conforming to certain database IDs.

    Parameters:
        synonym (str): The synonym to check.

    Returns:
        Database ID source and ID (``synonym``), if found, as a :class:`dict`.

    Examples:
    >>> identify_synonym('UNII-5000')
    {'UNII': 'UNII-5000'}
    """
    selecting = {name: patt.search(synonym) for name, patt in SELECT.items()}
    identified = {key: synonym for key, val in selecting.items()
                  if val is not None}
    return identified
