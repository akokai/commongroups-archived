# coding: utf-8

"""
Functions for generating HTML output.
"""
import os
from os.path import join as pjoin
from urllib.parse import urlencode
from ashes import AshesEnv

templates_dir = pjoin(os.path.dirname(os.path.abspath(__file__)), 'templates')


def pc_img(cid, size=500):
    """
    Generate HTML code for a PubChem molecular structure graphic and link.
    """
    cid_url = 'https://pubchem.ncbi.nlm.nih.gov/compound/{}'.format(cid)
    imgbase = 'https://pubchem.ncbi.nlm.nih.gov/image/imagefly.cgi?'
    params = {'cid': cid, 'width': size, 'height': size}
    img_url = imgbase + urlencode(params)
    return '<a href="{0}"><img src="{1}"></a>'.format(cid_url, img_url)


def cids_to_html(cids, html_file, title='PubChem graphics', notes='', size=500):
    """
    Generate HTML file displaying PubChem structures for an iterable of CIDs.
    """
    context = {'title': title,
               'notes': notes,
               'items': [pc_img(cid, size=size) for cid in cids]}
    templater = AshesEnv([templates_dir])
    html = templater.render('query_cids.html', context)
    with open(html_file, 'w') as file:
        file.write(html)


def results_to_html(cmg, env):
    """
    Generate an HTML document showing results of processing a ``CMGroup``.
    """
    # TODO
    pass


def describe_cmg(cmg, env):
    """
    Generate an HTML snippet describing the parameters of a ``CMGroup``.
    """
    # TODO
    html = ''
    return html


def directory(cmgs, env, title='CMG Processing results'):
    """
    Generate HTML directory of results for multiple ``CMGroup``s.
    """
    context = {'title': title,
               'items': [{'materialid': cmg.materialid,
                          'name': cmg.name,
                          'notes': cmg.notes} for cmg in cmgs]}
    html_file = pjoin(env.results_path, 'index.html')
    templater = AshesEnv(['templates'])
    html = templater.render('directory.html', context)
    with open(html_file, 'w') as file:
        file.write(html)
