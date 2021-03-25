#! /usr/bin/env python
# -*- coding: utf-8 -*-

from random import sample
import itertools
# part of module
from .utils import node2cooc
# requirements
from pandas import DataFrame
# logging
import logging
logger = logging.getLogger(__name__)


class Concordance:
    """ concordancing """

    def __init__(self, corpus, df_dump):

        # bind corpus
        self.corpus = corpus

        # make sure there's context
        if 'context' not in df_dump.columns:
            df_dump['context'] = df_dump.index.get_level_values('match')
        if 'contextend' not in df_dump.columns:
            df_dump['contextend'] = df_dump.index.get_level_values('matchend')

        # bind dump and check size
        self.df_dump = df_dump
        self.size = len(df_dump)
        if self.size == 0:
            logger.warning('empty dump')

        # check anchor points
        anchors = [i for i in range(10) if i in df_dump.columns]

        self.anchors = anchors

    def simple(self, df, p_show=['word'], start='context', end='contextend'):

        for p_att in p_show:
            df = self.corpus.dump2patt(
                df, p_att=p_att, start=start, end=end
            )

        return df[p_show]

    def kwic(self, df, p_show=['word']):

        # left: context .. match - 1
        # node: match .. matchend
        # right: matchend + 1 .. contextend
        df = df.reset_index()
        df['leftend'] = df['match'] - 1
        df['rightstart'] = df['matchend'] + 1
        df = df.set_index(['match', 'matchend'])

        for p in p_show:
            df['left' + "_" + p] = self.corpus.dump2patt(
                df, p, start='context', end='leftend'
            )[p]
            df['node' + "_" + p] = self.corpus.dump2patt(
                df, p, start='match', end='matchend'
            )[p]
            df['right' + "_" + p] = self.corpus.dump2patt(
                df, p, start='rightstart', end='contextend'
            )[p]

        return df[["_".join(combo) for combo in itertools.product(
            ['left', 'node', 'right'], p_show
        )]]

    def slots(self, df, p_show=['word'], slots=None):
        """
        slots are singletons or pairs of self.anchors
        by default, all single anchors are slots

        if slots is a list, the names of the resulting columns are simply $s0..$s1_$p

        for each single slot $s and each $p in p_show, $s_$p is retrieved
        for pairs, $s0..$s1_$p is retrieved
        if $s0 or $s1 is not defined in a row, the pair is treated as a single slot
        if both are not defined, an empty string is returned
        """

        if slots is None:
            slots = self.anchors + [('match', 'matchend')]

        # translate list into dict
        if isinstance(slots, list):
            slots_dict = dict()
            for slot in slots:
                if isinstance(slot, (int, str)):
                    key = slot
                else:
                    key = "..".join([str(s) for s in slot])
                slots_dict[key] = slot
            slots = slots_dict

        # init output with simple view
        df_lines = self.simple(df, p_show)

        # add slots
        for key in slots.keys():
            # allow definition of slots as singletons
            if isinstance(slots[key], (int, str)):
                start = end = slots[key]
            else:
                start, end = slots[key]
            df_lines[[str(key) + "_" + p for p in p_show]] = self.simple(
                df, p_show=p_show, start=start, end=end
            )[p_show]

        return df_lines

    def _dict_line(self, index, row, p_show):
        """Translates one row of self.df_dump into a dictionary.

        :return: dictionary of [match, cpos, offset, anchors] + p_show
        :rtype: dict

        """

        # pack values
        match, matchend = index
        row = dict(row)
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

    def dict(self, df, p_show=['word']):

        df['dict'] = df.apply(
            lambda row: self._dict_line(row.name, row, p_show),
            axis=1
        )

        return df

    def dataframe(self, df_dict, p_show):

        return DataFrame.from_records(
            index=df_dict.index,
            data=df_dict['dict'].apply(
                lambda row: line2df(row, p_show),
            ).values,
        )

    def lines(self, form='simple', p_show=['word'], s_show=[],
              order='first', cut_off=100, matches=None, slots=None):
        """ creates concordance lines from self.df_dump

        :param str form: simple / kwic / dict / slots / dataframe

        """

        # check parameters
        if len(self.df_dump) == 0:
            logger.error("no concordance lines to show")
            return
        if form not in ['simple', 'kwic', 'dict', 'dataframe', 'slots']:
            logger.error('format not implemented, using "simple" format')
            form = 'simple'
        if isinstance(p_show, str):
            p_show = [p_show]
        if isinstance(s_show, str):
            p_show = [s_show]

        # select appropriate subset of matches
        logger.info('lines: selecting matches')
        if matches is None:
            # select all matches
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
            logger.error('order not implemented, using "random" order')
            order = 'random'
        logger.info("lines: retrieving %d concordance line(s)" % len(matches))
        df = self.df_dump.loc[matches, :]

        # p-attributes and formatting
        if len(p_show) > 0:
            if form == 'simple':
                df = self.simple(df, p_show)
            elif form == 'kwic':
                df = self.kwic(df, p_show)
            elif form == 'slots':
                df = self.slots(df, p_show, slots)
            else:
                df = self.dict(df, p_show)
                if form == 'dataframe':
                    df = self.dataframe(df, p_show)
        # s-attributes
        for s_att in s_show:
            df = self.corpus.dump2satt(df, s_att)

        return df


def line2df(line, p_show):
    """transforms one text_line to dictionary of {"df": DataFrame}. Pops
    "anchors", "match"; everything else must be aligned lists.

    :param dict line: dictionary

    :return: {'df': DataFrame}
    :rtype: dict

    """

    # pop non-lists
    anchors = []
    if 'anchors' in line.keys():
        anchors = line.pop('anchors')
    if 'match' in line:
        line.pop('match')       # not needed

    # transform to df
    df = DataFrame.from_records(line).set_index('cpos')
    df = df[['offset'] + p_show]

    # append anchors
    for a in anchors:
        df[a] = False
        if anchors[a] in df.index:
            df.at[anchors[a], a] = True

    return {
        'dataframe': df
    }
