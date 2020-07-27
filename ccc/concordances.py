#! /usr/bin/env python
# -*- coding: utf-8 -*-

from random import sample
# part of module
from .utils import node2cooc
from .utils import format_concordance_lines
# requirements
from pandas import DataFrame
# logging
import logging
logger = logging.getLogger(__name__)


class Concordance:
    """ concordancing """

    def __init__(self, corpus, df_dump):

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
        cotext = node2cooc(row)
        cpos = cotext['cpos_list']

        # init output dictionary
        out = {
            'cpos': cpos,
            'offset': cotext['offset_list'],
            'match': match
        }
        assert(match == cotext['match_list'][0])

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

    def lines(self, matches=None, p_show=['word'], s_show=[],
              p_text=None, p_slots=None, regions=[], order='first',
              cut_off=100, form='raw'):
        """ creates concordance lines from self.df_dump

        :param str form: raw / simple / kwic / dataframes / extended

        """

        # check parameter consistency
        if p_text is not None and p_text not in p_show:
            logger.error('p_text not in p_show')
        if p_slots is not None and p_slots not in p_show:
            logger.error('p_slots not in p_show')

        # select appropriate subset of matches
        logger.info('lines: selecting matches')
        if matches is None:
            matches = set(self.df_dump.index.droplevel('matchend'))

        # pre-process cut_off if necessary
        if (cut_off is None) or (len(matches) < cut_off):
            cut_off = len(matches)

        # order
        if order == 'random':
            matches = sample(matches, cut_off)
        elif order == 'first':
            matches = sorted(list(matches))[:cut_off]
        elif order == 'last':
            matches = sorted(list(matches))[-cut_off:]
        else:
            raise NotImplementedError('concordance order not implemented')

        logger.info("lines: retrieving %d concordance line(s)" % len(matches))
        df = self.df_dump.loc[matches, :]

        # texts
        if len(p_show) > 0:

            # retrieve lines as Series
            # - index: match, matchend
            # - values: dictionaries
            df_lines = df.apply(
                lambda row: self.text_line(row.name, row, p_show),
                axis=1,
            )
            df_lines.name = 'raw'

            # format text
            if form == 'raw':
                concordance = df_lines
            else:
                concordance = format_concordance_lines(
                    df_lines, p_show, p_text,
                    p_slots, regions, form=form
                )
            df = df.join(DataFrame(concordance))

        # meta data
        if len(s_show) > 0:
            meta = self.corpus.get_s_annotations(df, s_show)
            df = df.join(meta)

        return df
