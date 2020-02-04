#! /usr/bin/env python
# -*- coding: utf-8 -*-

from random import sample
# part of module
from .utils import node2cooc, anchor_query_to_anchors
# requirements
from pandas import DataFrame


MAX_MATCHES = 100000            # maximum number of matches to still calculate frequency breakdown


class Concordance:

    def __init__(self,
                 engine,
                 context=20,
                 s_break='text',
                 match_strategy='standard'):

        self.engine = engine

        self.settings = {
            'context': context,
            's_break': s_break,
            'match_strategy': match_strategy
        }

        # these values will
        self.size = 0
        self.meta = None
        self.breakdown = None

    def query(self, query, anchored=None, breakdown=True):
        """ executes query and gets df_node, meta, and frequency breakdown """

        if anchored is None:
            anchored = (len(anchor_query_to_anchors(query)) > 0)

        if not anchored:
            df_node = self.engine.df_node_from_query(
                query,
                s_break=self.settings['s_break'],
                context=self.settings['context'],
                match_strategy=self.settings['match_strategy']
            )
        else:
            df_node = self.engine.df_anchor_from_query(
                query,
                s_break=self.settings['s_break'],
                context=self.settings['context'],
                match_strategy=self.settings['match_strategy']
            )

        self.df_node = df_node
        if len(df_node) == 0:
            print('WARNING: 0 query hits')
            return

        # get values
        self.size = len(df_node)
        matches = df_node.index.droplevel('matchend')
        self.meta = DataFrame(index=matches,
                              data=df_node['s_id'].values,
                              columns=['s_id'])

        # frequency breakdown of matches
        if self.size > MAX_MATCHES:
            print('WARNING: found more than %d matches, skipping frequency breakdown' % MAX_MATCHES)
            breakdown = False

        if breakdown:
            self.breakdown = self.engine.count_matches(df_node)

    def show(self, matches=None, p_show=[], order='first', cut_off=100):
        """ creates concordance lines from self.df_node """

        # take appropriate sub-set of matches
        topic_matches = set(self.df_node.index.droplevel('matchend'))

        if matches is None:
            if not cut_off or len(topic_matches) < cut_off:
                cut_off = len(topic_matches)
            if order == 'random':
                topic_matches_cut = sample(topic_matches, cut_off)
            elif order == 'first':
                topic_matches_cut = sorted(list(topic_matches))[:cut_off]
            elif order == 'last':
                topic_matches_cut = sorted(list(topic_matches))[-cut_off:]
            else:
                raise NotImplementedError('concordance order not implemented')
            df_node = self.df_node.loc[topic_matches_cut, :]

        else:
            df_node = self.df_node.loc[matches, :]

        # check if there's anchors
        anchor_keys = set(df_node.columns) - {'region_start', 'region_end', 's_id'}
        anchored = len(anchor_keys) > 0

        # fill concordance dictionary
        concordance = dict()
        for row_ in df_node.iterrows():

            # gather values
            match, matchend = row_[0]
            row = dict(row_[1])
            row['match'] = match
            row['matchend'] = matchend
            row['start'] = row['region_start']
            row['end'] = row['region_end']

            # create cotext
            df = DataFrame(node2cooc(row))
            df.columns = ['match', 'cpos', 'offset']
            df.drop('match', inplace=True, axis=1)

            # lexicalize positions
            for p_att in ['word'] + p_show:
                df[p_att] = df.cpos.apply(
                    lambda x: self.engine.cpos2token(x, p_att)
                )
            df.set_index('cpos', inplace=True)

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
