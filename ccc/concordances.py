#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
from random import sample
from collections import defaultdict
# part of module
from .utils import node2cooc
from .utils import get_holes, apply_corrections
from .utils import concordance_lines2df
# requirements
from pandas import DataFrame
import logging
logger = logging.getLogger(__name__)


class Concordance:
    """ concordancing """

    def __init__(self, corpus, df_dump, max_matches):
        """Executes query, gets DataFrame of corpus positions (dump of CWB).
        df_dump is indexed by (match, matchend).  Optional columns for
        each anchor.

        :param str query: valid CQP query (without 'within' clause)
        :param str s_query: s-attribute used for initial query
        :param list anchors: anchors to search for
        :param str match_strategy: CQP matching strategy

        :return: df_dump
        :rtype: DataFrame

        """

        if len(df_dump) == 0:
            logger.warning('no concordance lines to show')
            return

        # stuff we need
        self.corpus = corpus
        self.df_dump = df_dump
        self.size = len(df_dump)

        # meta data
        anchors = [i for i in range(10) if i in df_dump.columns]
        anchors += ['match', 'matchend', 'context', 'contextend']
        meta = df_dump.drop(anchors, axis=1, errors='ignore')
        meta.index = meta.index.droplevel('matchend')
        self.meta = meta

        # frequency breakdown
        if max_matches is not None and self.size > max_matches:
            logger.warning(
                'found %d matches (more than %d)' % (self.size, max_matches)
            )
            self.breakdown = DataFrame(
                index=['NODE'],
                data=[self.size],
                columns=['freq']
            )
            self.breakdown.index.name = 'word'

        else:
            logger.info('creating frequency breakdown')
            self.breakdown = self.corpus.count_dump(
                df_dump=df_dump, start='match', end='matchend', p_atts=['word']
            )
            # self.breakdown = self.corpus.count_matches(
            #     name=cache_name
            # )
            self.breakdown.sort_values(by='freq', inplace=True, ascending=False)

    def line(self, row, p_show, anchors):

        # gather values
        match, matchend = row[0]
        row = dict(row[1])
        row['match'] = match
        row['matchend'] = matchend

        # create cotext
        df = DataFrame(node2cooc(row))
        df.columns = ['match', 'cpos', 'offset']
        df = df.drop('match', axis=1)

        # lexicalize positions
        df[p_show] = DataFrame(
            df.cpos.apply(lambda x: self.corpus.cpos2patts(x, p_show)).tolist(),
            columns=p_show
        )
        df = df.set_index('cpos')

        # anchors
        anchor_column = defaultdict(list)
        for a in anchors:
            anchor_column[row[a]].append(a)
        df['anchors'] = DataFrame(
            index=anchor_column.values(),
            data=anchor_column.keys(),
            columns=['cpos']
        ).reset_index().set_index('cpos')

        return df

    def lines(self, matches=None, p_show=['word'], order='first',
              cut_off=100, form='dictionary'):
        """ creates concordance lines from self.df_node """

        # take appropriate sub-set of matches
        topic_matches = set(self.df_dump.index.droplevel('matchend'))

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
            df_dump = self.df_dump.loc[topic_matches_cut, :]

        else:
            df_dump = self.df_dump.loc[matches, :]

        # anchor points to show
        anchors = [i for i in range(10) if i in df_dump.columns]
        anchors += ['match', 'matchend', 'context', 'contextend']

        # fill concordance dictionary
        concordance = dict()
        for row in df_dump.iterrows():
            line = self.line(row, p_show, anchors)
            concordance[row[0]] = line

        if form == 'dictionary':
            return concordance

        if form == 'simple-kwic':
            kwic = True
        elif form == 'simple':
            kwic = False
        else:
            raise NotImplementedError("format type (%s) not implemented" % form)

        # TODO take care of meta data
        # if self.corpus.s_meta is None:
        concordance = concordance_lines2df(
            concordance, kwic=kwic
        )
        # else:
        #     concordance = concordance_lines2df(
        #         concordance, self.meta, kwic=kwic
        #     )

        return concordance

    def show_argmin(self, anchors, regions, p_show=['lemma'],
                    order='first', cut_off=None):

        # apply corrections
        self.df_node = apply_corrections(self.df_node, anchors)

        # get concordance
        lines = self.lines(p_show=p_show, order='first', cut_off=None)

        # initialize output
        result = dict()
        result['nr_matches'] = self.size
        result['matches'] = list()
        result['holes'] = defaultdict(list)
        result['meta'] = self.meta.to_dict()

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
                        context=None, s_break='s',
                        match_strategy='longest'):

    with open(query_path, "rt") as f:
        try:
            query = json.loads(f.read())
        except json.JSONDecodeError:
            logger.error("not a valid json file")
            return

    # add query
    query['query_path'] = query_path

    # run the query
    try:
        result, info = corpus.query(query['query'], s_break=s_break,
                                    context=context,
                                    match_strategy=match_strategy,
                                    info=True)
        query['info'] = info
        concordance = corpus.concordance(result)
        query['result'] = concordance.show_argmin(
            query['anchors'],
            query['regions'],
            p_show
        )
    except TypeError:
        logger.warning("no results for path %s" % query_path)

    return query
