# coding: utf-8

from os.path import join as pjoin
from camelid.env import CamelidEnv
from camelid.cmgroup import CMGroup as CMG
from camelid.cmgroup import BASE_PARAMS
from camelid import hypertext as ht

env = CamelidEnv('test')

# Test directory
par1 = {'cmg_id': 1, 'name': 'foo_group'}
par2 = {'cmg_id': 2, 'name': 'bar_group'}
desc = 'Bland description'
cmgs = [CMG(p, env, desc) for p in (par1, par2)]

ht.directory(cmgs, env)

# Test cids_to_html
cids = [4, 5, 6, 26030, 446142, 82525, 151909, 53338760]
text = """Lorem ipsum dolor sit amet, consectetur adipiscing
          elit. Duis venenatis risus erat, interdum pretium
          massa accumsan in. """
info = {'description': 6*text, 'additional notes': 'Ashes to ashes, Dust to dust.'}

ht.cids_to_html(cids,
                pjoin(env.results_path, '1.html'),
                title='Test PubChem results summary',
                info=info)
