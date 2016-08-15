# -*- coding: utf-8 -*-
"""Functions for dealing with CAS Registry Numbers (CASRN)."""

from __future__ import unicode_literals
from builtins import str

import re
import numpy as np


def validate(casrn, boolean=False):
    """
    Check the validity of a CASRN using the check digit.

    This function checks whether the input is a valid CAS registry number,
    based on the CAS documentation:
    https://www.cas.org/content/chemical-substances/checkdig

    Args:
        casrn (str or unicode or int): The CASRN to validate.
            Non-numeric characters are ignored.
        boolean (bool): Whether to return bool rather than string.

    Returns:
        The CASRN as string (unicode in Python 2), with uniform CAS-style
        hypenation and no leading/trailing spaces; or ``None`` if the
        CASRN is invalid. If ``boolean=True``, returns ``True`` or ``False``
        depending on validity.

    Examples:
        >>> validate('50--00--0 ')  # No data cleaning needed
        '50-00-0'
        >>> validate('50-00-5', boolean=True)
        False
    """
    casrn = str(casrn)
    nums_regex = re.compile(r'\d+')
    nums = ''.join(nums_regex.findall(casrn))

    if len(nums) < 5:
        valid = False
    else:
        digits = np.array([int(i) for i in nums])
        check_digit = sum(digits[:-1] * np.arange(1, len(nums))[::-1]) % 10
        valid = (check_digit == digits[-1])

    if boolean:
        return valid
    else:
        return '-'.join([nums[:-3], nums[-3:-1], nums[-1:]]) if valid else None


def find_valid(string):
    """
    Find all valid CASRNs in a string.

    Args:
        string (str or unicode): The string to search.

    Returns:
        A list of all valid CASRNs found, each as a hyphenated string.

    Example:
        >>> find_valid('Formaldehyde (50-00-0), copolymer with urea (57-13-6)')
        ['50-00-0', '57-13-6']
    """
    casrn_regex = re.compile(r'(\d{2,7})[-–—](\d{2})[-–—]\d')
    found = [validate(i.group()) for i in casrn_regex.finditer(string)]
    return [x for x in found if x is not None]
