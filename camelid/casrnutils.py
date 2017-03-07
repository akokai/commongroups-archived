# coding: utf-8

# This module is from:
# chemex - https://github.com/akokai/chemex

"""Functions for dealing with CAS Registry Numbers (CASRN)."""

import re
import numpy as np


def validate(casrn, output='str'):
    """
    Check the validity of a CASRN using the check digit.

    This function checks whether the input is a valid CAS registry number,
    based on the CAS documentation:
    https://www.cas.org/content/chemical-substances/checkdig

    Parameters:
        casrn (str or int): The CASRN to validate.
            Non-numeric characters are ignored.
        output (str): Type of result to return; either ``'str'``
            (default) or ``'bool'``.

    Returns:
        If ``output='str'``, returns the CASRN as :class:`str`, with uniform
        CAS-style hypenation and no leading/trailing spaces; or ``None`` if
        the CASRN is invalid.

        If ``output='bool'``, returns ``True`` or ``False``
        depending on validity.

    Examples:
        >>> validate('50--00--0 ')  # No data cleaning needed
        '50-00-0'
        >>> validate('50-00-5', output='bool')
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

    if output == 'bool':
        return valid
    else:
        return '-'.join([nums[:-3], nums[-3:-1], nums[-1:]]) if valid else None


def find(string, lenient=False, valid=True):
    """
    Find all valid CASRNs in a string.

    Parameters:
        string (str or unicode): The string to search.
        lenient (bool): Try to find badly-formatted CASRNs too
            (default `False`).
        valid (bool): Find only valid CASRNs (default ``True``).

    Returns:
        A list of all valid CASRNs found, each as a hyphenated string.

    Examples:
        >>> find('Formaldehyde (50-00-0), copolymer with urea (57-13-6)')
        ['50-00-0', '57-13-6']
    """
    if lenient:
        casrn_rx = re.compile(r'(\d+)[-–—](\d+)[-–—]*\d*')
    else:
        casrn_rx = re.compile(r'(\d{2,7})[-–—](\d{2})[-–—]\d')

    found = [i.group() for i in casrn_rx.finditer(string)]

    if valid:
        found = list(filter(None, [validate(x) for x in found]))

    return found
