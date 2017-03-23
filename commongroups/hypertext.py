# coding: utf-8

"""
Functions for generating HTML output.
"""
import os
from os.path import join as pjoin
from urllib.parse import urlencode
from ashes import AshesEnv

TEMPLATES_DIR = pjoin(os.path.dirname(os.path.abspath(__file__)), 'templates')
DIR_TITLE = 'Compound group processing results'


def pc_img(cid, size=500):
    """
    Generate HTML code for a PubChem molecular structure graphic and link.
    """
    cid_url = 'https://pubchem.ncbi.nlm.nih.gov/compound/{}'.format(cid)
    imgbase = 'https://pubchem.ncbi.nlm.nih.gov/image/imagefly.cgi?'
    params = {'cid': cid, 'width': size, 'height': size}
    img_url = imgbase + urlencode(params)
    return '<a href="{0}"><img src="{1}"></a>'.format(cid_url, img_url)


def get_notes(cmg):
    """Retrieve ``notes`` from CMGroup info, if exists."""
    if 'notes' in cmg.info:
        return cmg.info['notes']
    else:
        return ''


def info_to_context(info):
    """
    Convert a CMGroup's ``info`` into a context for HTML templating.

    Use some sensible defaults for ordering items.
    """
    top_keys = ['notes', 'method_doc', 'sql']
    more_keys = [key for key in info.keys() if key not in top_keys]
    ordered_keys = top_keys + sorted(more_keys)
    ret = []
    for item in ordered_keys:
        if item in info and info[item]:  # Value is not blank
            ret.append({'key': item, 'value': info[item]})
    return ret


def cids_to_html(cids, path, title='PubChem images', info=None, size=500):
    """
    Generate HTML file displaying PubChem structures and CMGroup info.
    """
    # TODO: Options to add links to JSON, CSV, Excel files.
    #       Something like: formats=['csv', 'json', 'excel']
    if info:
        info_list = info_to_context(info)
    else:
        info_list = []
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


def directory(cmgs, env, title=DIR_TITLE, formats=None):
    """
    Generate HTML directory of multiple CMGroups and write to file.
    """
    # TODO: doc
    items = [{'cmg_id': cmg.cmg_id,
              'name': cmg.name,
              'notes': get_notes(cmg)} for cmg in cmgs]
    formats = formats or []
    context = {'title': title, 'items': items, 'formats': formats}
    path = pjoin(env.results_path, 'index.html')
    templater = AshesEnv([TEMPLATES_DIR])
    html = templater.render('directory.html', context)
    with open(path, 'w') as file:
        file.write(html)
