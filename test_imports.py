# -*- coding: utf-8 -*-
'''Test for import errors.'''


def test_imports():
    import camelid
    from camelid import pubchemutils as pc
    from camelid.casrnutils import validate


def main():
    test_imports()


if __name__ == '__main__':
    main()
