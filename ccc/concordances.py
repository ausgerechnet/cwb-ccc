#! /usr/bin/env python
# -*- coding: utf-8 -*-

from random import sample
# part of module
from .cwb import anchor_query_to_anchors
from .utils import node2cooc
# requirements
from pandas import DataFrame


class Concordance(object):

    def __init__(self,
                 engine,
                 context=20,
                 s_break='text',
                 order='random',
                 p_show=[],
                 cut_off=100):

        self.engine = engine

        self.settings = {
            'context': context,
            's_break': s_break,
            'p_show': p_show,
            'order': order,
            'cut_off': cut_off
        }

    def query(self, query, anchored=None):

        if anchored is None:
            anchored = len(anchor_query_to_anchors(query)) > 0

        if not anchored:
            df_node = self.engine.df_node_from_query(
                query,
                s_break=self.settings['s_break'],
                context=self.settings['context']
            )
        else:
            df_node = self.engine.df_anchor_from_query(
                query,
                s_break=self.settings['s_break'],
                context=self.settings['context']
            )

        if len(df_node) == 0:
            return {}

        concordance = df_node_to_concordance(
            engine=self.engine,
            df_node=df_node,
            order=self.settings['order'],
            cut_off=self.settings['cut_off'],
            p_show=self.settings['p_show'],
            anchored=anchored
        )

        return concordance


# node to concordance (needs engine) ###########################################
def df_node_to_concordance(engine,
                           df_node,
                           order='random',
                           cut_off=100,
                           p_show=[],
                           anchored=None,
                           role='match'):
    """ formats concordance lines for a df_node """

    # reset the index to be able to work with it
    df_node.reset_index(inplace=True)

    # avoid trying to get more concordance lines than there are
    topic_matches = set(df_node['match'])
    if not cut_off or len(topic_matches) < cut_off:
        cut_off = len(topic_matches)

    # take appropriate sub-set
    if order == 'random':
        topic_matches_cut = sample(topic_matches, cut_off)
    elif order == 'first':
        topic_matches_cut = sorted(list(topic_matches))[:cut_off]
    elif order == 'last':
        topic_matches_cut = sorted(list(topic_matches))[-cut_off:]
    else:
        raise NotImplementedError("concordance order not implemented")

    # check if there's anchors
    anchor_keys = set(df_node.columns) - {'region_start', 'region_end', 's_id',
                                          'matchend', 'match'}

    # automatically determine by default
    if anchored is None:
        anchored = len(anchor_keys) > 0

    df_node['start'] = df_node['region_start']
    df_node['end'] = df_node['region_end']

    # fill concordance dictionary
    concordance = dict()
    for match in topic_matches_cut:

        # take match from df_node
        row = df_node.loc[df_node['match'] == match]

        # create cotext
        df = DataFrame(row.apply(node2cooc, axis=1).values[0])
        df.columns = ['match', 'cpos', 'offset']
        df.drop('match', inplace=True, axis=1)

        # lexicalize positions
        df['word'] = df.cpos.apply(engine.cpos2token)
        for p_att in p_show:
            df[p_att] = df.cpos.apply(
                lambda x: engine.cpos2token(x, p_att)
            )
        df.set_index('cpos', inplace=True)

        # role
        df[role] = (df['offset'] == 0)

        # handle optional anchors
        if anchored:
            anchors = dict()
            for anchor in anchor_keys:
                anchors[anchor] = int(row[anchor])
            df['anchor'] = None
            for anchor in anchors.keys():
                if anchors[anchor] != -1:
                    df.at[anchors[anchor], 'anchor'] = anchor

        # save concordance line
        concordance[match] = df

    return concordance
