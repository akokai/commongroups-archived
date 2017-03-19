# coding: utf-8

"""
Functions for generating HTML output.
"""
import os
from os.path import join as pjoin
from urllib.parse import urlencode
from ashes import AshesEnv

TEMPLATES_DIR = pjoin(os.path.dirname(os.path.abspath(__file__)), 'templates')


def pc_img(cid, size=500):
    """
    Generate HTML code for a PubChem molecular structure graphic and link.
    """
    cid_url = 'https://pubchem.ncbi.nlm.nih.gov/compound/{}'.format(cid)
    imgbase = 'https://pubchem.ncbi.nlm.nih.gov/image/imagefly.cgi?'
    params = {'cid': cid, 'width': size, 'height': size}
    img_url = imgbase + urlencode(params)
    return '<a href="{0}"><img src="{1}"></a>'.format(cid_url, img_url)


def cids_to_html(cids, path, title='PubChem images', info=None, size=500):
    """
    Generate HTML file displaying PubChem structures and CMGroup info.
    """
    info = info or dict()
    # The reverse sort is a hack to make SQL text appear first.
    # TODO: Something more sensible.
    info_list = [{'key': k, 'value': v} for k, v
                 in sorted(info.items(), reverse=True) if v is not None]
    context = {'size': size,
               'title': title,
               'info': info_list,
               'items': [{'cid': cid, 'image': pc_img(cid, size=size)}
                         for cid in cids]}
    templater = AshesEnv([TEMPLATES_DIR])
    html = templater.render('display_cids.html', context)
    with open(path, 'w') as file:
        file.write(html)


def results_to_html(cmg):
    """
    Generate an HTML document showing results of processing a CMGroup.
    """
    # TODO
    pass


def describe_cmg(cmg):
    """
    Generate an HTML snippet describing the parameters of a CMGroup.
    """
    # TODO
    html = ''
    return html


def directory(cmgs, env, title='Compound group processing results'):
    """
    Generate HTML directory of multiple CMGroups and write to file.
    """
    context = {
        'title': title,
        'items': [{'cmg_id': cmg.cmg_id,
                   'name': cmg.name,
                   'description': cmg.info['description']} for cmg in cmgs]}
    path = pjoin(env.results_path, 'index.html')
    templater = AshesEnv([TEMPLATES_DIR])
    html = templater.render('directory.html', context)
    with open(path, 'w') as file:
        file.write(html)
