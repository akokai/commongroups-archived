# -*- coding: utf-8 -*-
'''Functions for dealing with CAS Registry Numbers (CASRN).'''

from __future__ import unicode_literals
from builtins import str
import re
import numpy as np


def validate(casrn, boolean=False):
    '''
    Check the validity of a CASRN using the check digit.

    Returns cleaned CASRN as `unicode` (`str`), or `None` if invalid.
    If passed `boolean=True`, returns `True` for valid CASRNS or `False` for
    invalid ones.
    Input can be `str`, `unicode`, or `int`. Non-numeric characters
    are ignored. Based on CAS documentation:
    https://www.cas.org/content/chemical-substances/checkdig
    '''
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
    '''Find all valid CASRNs in a string.'''
    casrn_regex = re.compile(r'(\d{2,7})[-–—](\d{2})[-–—]\d')
    found = [validate(i.group()) for i in casrn_regex.finditer(string)]
    return [x for x in found if x is not None]
