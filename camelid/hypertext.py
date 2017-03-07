# coding: utf-8

"""
Functions for generating HTML output.
"""

from urllib.parse import urlencode


def pc_img(cid, size=500):
    """
    Generate HTML code for a PubChem molecular structure graphic and link.
    """
    cid_uri = 'https://pubchem.ncbi.nlm.nih.gov/compound/{}'.format(cid)
    imgbase = 'https://pubchem.ncbi.nlm.nih.gov/image/imagefly.cgi?'
    params = {'cid': cid, 'width': size, 'height': size}
    img_uri = imgbase + urlencode(params)
    return '<a href="{0}"><img src="{1}"></a>'.format(cid_uri, img_uri)


def cids_to_html(cids, html_file, title='PubChem graphics', size=500):
    """
    Generate HTML file displaying PubChem structures for an iterable of CIDs.
    """

    css = """
    body {font-family: monospace;}
    h1 {position: fixed; top: 8px; left: 8px;}
    table {width: 100%;}
    td {text-align: center; padding: 8px;}
    """

    top = """<!doctype html>
    <html>
    <head><title>{0}</title>
    <style>
    {1}
    </style>
    </head>
    <body>
    <h1>{0}</h1>
    <table>""".format(title, css)

    rows = ['<tr><td>{}</td></tr>'.format(pc_img(cid, size)) for cid in cids]
    end = '</table></body></html>'

    with open(html_file, 'w') as file:
        file.writelines([top] + rows + [end])
