# -*- coding: utf-8 -*-

from itertools import islice

import pubchemutils as pc


def try_casrn_from_cids():
    cids = [241, 2912, 13628823, 24290]
    results = list(islice(pc.casrn_iupac_from_cids(cids), None))
    print(results)


def try_substruct_search():
    results = pc.substruct_search('[CH3][Hg]', wait=1)
    print(results)


def main():
    # try_casrn_from_cids()
    try_substruct_search()


if __name__ == '__main__':
    main()
