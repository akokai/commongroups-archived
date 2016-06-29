# -*- coding: utf-8 -*-
'''Test for import errors.'''


def test_imports():
    import metacamel
    from metacamel import pubchemutils as pc
    from metacamel.casrnutils import validate


def main():
    test_imports()


if __name__ == '__main__':
    main()
