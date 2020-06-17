#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
from random import sample
from collections import defaultdict
# part of module
from .utils import node2cooc
from .utils import apply_corrections
from .utils import format_concordance_lines
# requirements
from pandas import DataFrame
# logging
import logging
logger = logging.getLogger(__name__)


class Concordance:
    """ concordancing """

    def __init__(self, corpus, df_dump, name=None, max_matches=None):

        if len(df_dump) == 0:
            logger.warning('no concordance lines to show')
            return

        # TODO: start independent CQP process
        self.corpus = corpus

        # what's in the dump?
        self.df_dump = df_dump
        self.size = len(df_dump)
        anchors = [i for i in range(10) if i in df_dump.columns]
        anchors += ['match', 'matchend', 'context', 'contextend']
        self.anchors = anchors

        # frequency breakdown
        if max_matches is not None and self.size > max_matches:
            logger.warning(
                'no frequency breakdown (found %d matches)' % (self.size, max_matches)
            )
            self.breakdown = DataFrame(
                index=['NODE'],
                data=[self.size],
                columns=['freq']
            )
            self.breakdown.index.name = 'word'
        else:
            logger.info('creating frequency breakdown')
            self.breakdown = self.corpus.counts.dump(
                df_dump=df_dump,
                start='match', end='matchend',
                p_atts=['word']
            )

    def text_line(self, index, columns, p_show=['word']):
        """Translates one row of self.df_dump into a concordance_line.

        :return: dictionary of [match, cpos, offset, anchors] + p_show
        :rtype: dict

        """

        # pack values
        match, matchend = index
        row = dict(columns)
        row['match'] = match
        row['matchend'] = matchend

        # create cotext
        _ = node2cooc(row)
        cpos = _['cpos_list']

        # init output dictionary
        out = {
            'cpos': cpos,
            'offset': _['offset_list'],
            'match': match
        }
        assert(match == _['match_list'][0])

        # lexicalize positions
        attribute_lists = zip(
            *list(map(lambda x: self.corpus.cpos2patts(x, p_show), cpos))
        )
        for a, p in zip(p_show, attribute_lists):
            out[a] = list(p)

        # process anchors
        out['anchors'] = dict()
        for a in self.anchors:
            out['anchors'][a] = row[a]

        return out

    def lines(self, matches=None, p_show=['word'], order='first',
              s_show=[], regions=[], p_text=None, p_slots='lemma',
              cut_off=100, form='raw'):
        """ creates concordance lines from self.df_dump

        :param str form: raw / simple / kwic / dataframes

        """

        # select appropriate subset of matches
        logger.info('lines: selecting matches')
        all_matches = set(self.df_dump.index.droplevel('matchend'))

        # cut_off
        if matches is None:
            if not cut_off or len(all_matches) < cut_off:
                cut_off = len(all_matches)

        # order
        if order == 'random':
            matches = sample(all_matches, cut_off)
        elif order == 'first':
            matches = sorted(list(all_matches))[:cut_off]
        elif order == 'last':
            matches = sorted(list(all_matches))[-cut_off:]
        else:
            raise NotImplementedError('concordance order not implemented')

        logger.info("lines: retrieving %d concordance line(s)" % len(matches))
        df = self.df_dump.loc[matches, :]

        # texts
        if len(p_show) > 0:

            df_lines = df.apply(
                lambda row: self.text_line(row.name, row, p_show),
                axis=1
            )

            # format text
            if form == 'raw':
                concordance = df_lines
            else:
                concordance = format_concordance_lines(
                    df_lines, p_show, regions, p_text, form=form
                )
                df = df.join(DataFrame(concordance))

        # meta data
        if len(s_show) > 0:
            meta = self.corpus.get_s_annotations(df, s_show)
            df = df.join(meta)

        return df


def process_argmin_file(corpus, query_path, p_show=['lemma'],
                        context=None, s_break='s',
                        match_strategy='longest'):

    # try to parse file
    with open(query_path, "rt") as f:
        try:
            query = json.loads(f.read())
        except json.JSONDecodeError:
            logger.error("not a valid json file")
            return

    # add query path to query info
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
