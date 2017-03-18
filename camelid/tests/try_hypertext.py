# coding: utf-8

from os.path import join as pjoin
from camelid.env import CamelidEnv
from camelid.cmgroup import CMGroup as CMG
from camelid.cmgroup import BASE_PARAMS
from camelid import hypertext as ht

env = CamelidEnv('test')
env.clear_logs()

# Test directory

par1, par2 = BASE_PARAMS.copy(), BASE_PARAMS.copy()
par1.update({'materialid': 1, 'name': 'foo_group'})
par2.update({'materialid': 2, 'name': 'bar_group'})

cmgs = [CMG(p, env) for p in (par1, par2)]

print(cmgs)

ht.directory(cmgs, env)

# Test cids_to_html

cids = [4, 5, 6, 26030, 446142, 82525, 151909, 53338760]
ht.cids_to_html(cids,
                pjoin(env.results_path, '1.html'),
                notes='Lorem ipsum dolor sit amet, consectetur adipiscing '
                      'elit. Duis venenatis risus erat, interdum pretium '
                      'massa accumsan in.')
