#! /usr/bin/env python
# -*- coding: utf-8 -*-

from random import sample
from collections import defaultdict
import json
# part of module
from .utils import node2cooc
from .utils import get_holes, apply_corrections
# requirements
from pandas import DataFrame
import logging
logger = logging.getLogger(__name__)


MAX_MATCHES = 100000            # maximum number of matches to still calculate frequency breakdown


class Concordance:
    """ concordancing """

    def __init__(self, corpus, df_node, breakdown=True):

        if len(df_node) == 0:
            logger.warning('0 query hits')
            return

        matches = df_node.index.droplevel('matchend')
        self.meta = DataFrame(index=matches,
                              data=df_node['s_id'].values,
                              columns=['s_id'])

        self.corpus = corpus
        self.df_node = df_node
        self.size = len(df_node)

        # frequency breakdown of matches
        if self.size > MAX_MATCHES:
            logger.warning('found %d matches (more than %d)' % (self.size, MAX_MATCHES))
            logger.warning('skipping frequency breakdown')
            breakdown = False
        if breakdown:
            self.breakdown = self.corpus.count_matches(df_node)
            self.breakdown.index.name = 'type'
            self.breakdown.sort_values(by='freq', inplace=True, ascending=False)

    def lines(self, matches=None, p_show=[], order='first', cut_off=100):
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
                    lambda x: self.corpus.cpos2token(x, p_att)
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

    def show_argmin(self, anchors, regions, p_show=['lemma'],
                    order='first', cut_off=None):

        # apply corrections
        self.df_node = apply_corrections(self.df_node, anchors)

        # get concordance
        lines = self.lines(p_show=p_show, order='first', cut_off=None)

        # initialize output
        result = dict()
        result['settings'] = self.settings
        result['nr_matches'] = self.size
        result['matches'] = list()
        result['holes'] = defaultdict(list)
        result['meta'] = self.df_meta.to_dict()

        # loop through concordances
        for key in lines.keys():

            line = lines[key]

            # fill concordance line
            entry = dict()
            entry['df'] = line.to_dict()
            entry['position'] = key
            entry['full'] = " ".join(entry['df']['word'].values())

            # hole structure
            holes = get_holes(line, anchors, regions)
            if 'lemmas' in holes.keys():
                entry['holes'] = holes['lemmas']
            else:
                entry['holes'] = holes['words']

            result['matches'].append(entry)

            # append to global holes list
            for idx in entry['holes'].keys():
                result['holes'][idx].append(entry['holes'][idx])

        return result


def process_argmin_file(corpus, query_path, p_show=['lemma'],
                        context=None, s_break='tweet', match_strategy='longest'):

    with open(query_path, "rt") as f:
        try:
            query = json.loads(f.read())
        except json.JSONDecodeError:
            logger.error("not a valid json file")
            return

    # add query
    query['query_path'] = query_path

    # run the query
    concordance = Concordance(corpus, query['query'], context,
                              s_break, match_strategy)
    query['result'] = concordance.show_argmin(
        query['anchors'],
        query['regions'],
        p_show
    )

    return query
