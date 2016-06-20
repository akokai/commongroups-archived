# -*- coding: utf-8 -*-
'''Chemical and material group class definition.'''


class CMGroup:
    '''Chemical and material group class.'''

    def __init__(self, materialid, specification):
        self.materialid = materialid
        self.specification = specification
        self.name = specification['name']
        self.compounds = []

    def screen(self, compound):
        '''Screen a new compound for membership in the group.'''
        # Placeholder!
        return None

    def contains(self, compound):
        '''Check if a compound is already in the group.'''
        # Placeholder!
        return compound in self.compounds
