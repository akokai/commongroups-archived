# -*- coding: utf-8 -*-
"""
Specially defined exceptions that may be raised in the camelid package.
"""

from __future__ import unicode_literals


class CamelidError(Exception):
    """Base Exception for all camelid errors."""
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)


class NoCredentialsError(CamelidError):
    """Raised when there is no Google API credentials file."""
    def __init__(self, path, *args, **kwargs):
        self.path = path
        super().__init__(self, *args, **kwargs)

    def __str__(self):
        msg = 'Google API credentials key file not found: {0}'
        return msg.format(self.path)


class WebServiceError(CamelidError):
    """Raised when a web service returns something unexpected."""
    def __init__(self, status, text, *args, **kwargs):
        self.status = status
        self.text = text
        super().__init__(self, *args, **kwargs)

    def __str__(self):
        msg = 'Status {0}: {1}'.format(self.status, self.text)
        return msg
