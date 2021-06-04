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

        # init anchor points
        anchors = [i for i in range(10) if i in df_dump.columns]
        self.anchors = anchors

    def simple(self, df, p_show=['word'], start='context', end='contextend'):
        """Retrieve concordance lines of provided df in 'simple'
        formatting, i.e. one column for each $p in p_show.

        """
        for p_att in p_show:
            df = self.corpus.dump2patt(
                df, p_att=p_att, start=start, end=end
            )

        return df[p_show]

    def kwic(self, df, p_show=['word']):
        """Retrieve concordance lines of provided df in 'kwic' formatting. The
        resulting dataframe has 3 times len(p_show) columns, namely
        for each $p in p_show:
        - left_$p: context .. match - 1
        - node_$p: match .. matchend
        - right_$p: matchend + 1 .. contextend

        """

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
        """Retrieve concordance lines of provided df in 'slot' formatting.
        Slots are singletons or pairs of self.anchors.  If no slots
        are provided, all anchors and match and matchend are slots.

        If slots is a list (of singletons and / or pairs), it will be
        translated into a dictionary with keys of the form
        "$slot[0]..$slot[1]".

        For each single slot $s and each p-attribute $p in p_show,
        $slot_$p is retrieved.  For pairs, $slot[0]..$slot[1]_$p is
        retrieved.

        If $slot[0] or $slot[1] is not defined in a row (hence the
        entry is -1), the pair is treated as a singleton.  If both
        positions are not defined, an empty string is returned.

        """

        # init output with simple view
        df_lines = self.simple(df, p_show)

        # get slots
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

        # add slots
        for key in slots.keys():
            # allow definition of slots as singletons
            if isinstance(slots[key], (int, str)):
                start = end = slots[key]
            # allow definition via lists of length 1
            elif isinstance(slots[key], list) and len(slots[key]) == 1:
                start = end = slots[key][0]
            # proper definition as pair / list of two
            else:
                start, end = slots[key]

            # retrieve concordance lines
            df_lines[[str(key) + "_" + p for p in p_show]] = self.simple(
                df, p_show=p_show, start=start, end=end
            )[p_show]

        return df_lines

    def _export(self, index, row, p_show, form='dict'):
        """Translates one row of a df_dump into a dictionary or a DataFrame.

        :return: [cpos, offset, anchors] + p_show
        :rtype: dict or DataFrame

        """

        # pack all values into a dictionary
        row = dict(row)
        match, matchend = index
        row['match'] = match
        row['matchend'] = matchend

        # create cotext
        cotext = node2cooc(row)

        # lexicalize positions
        attribute_lists = zip(
            *list(map(lambda x: self.corpus.cpos2patts(x, p_show), cotext['cpos_list']))
        )

        # init output dictionary
        d = {
            'cpos': cotext['cpos_list'],
            'offset': cotext['offset_list']
        }
        # add attributes
        for p, a in zip(p_show, attribute_lists):
            d[p] = list(a)

        if form == 'dict':
            # add match as identifier
            d['match'] = match
            # process anchors
            d['anchors'] = dict()
            for a in self.anchors:
                d['anchors'][a] = row[a]
            return d

        elif form == 'dataframe':
            # convert to dataframe and sort columns
            df = DataFrame.from_records(d).set_index('cpos')
            df = df[['offset'] + p_show]
            # process anchors
            for a in self.anchors:
                df[a] = False
                if row[a] in df.index:
                    df.at[row[a], a] = True
            return df

    def dict(self, df, p_show=['word']):
        """Retrieve concordance lines of provided df in 'dict' formatting.
        Primary export format.

        Each entry in column 'dict' has the following keys:
        # identifier
        - match <int>: single integer as ID
        # aligned token-lists
        - cpos <list>: corpus position
        - offset <list>: offset to match..matchend
        - $p for $p in p_show <list>: surface of p-attribute, each a <list>
        # roles
        - anchors <dict>: {anchor: cpos}

        """

        df['dict'] = df.apply(
            lambda row: self._export(row.name, row, p_show, form='dict'),
            axis=1
        )

        return df

    def dataframe(self, df, p_show=['word']):
        """Retrieve concordance lines of provided df_dict in 'dataframe'
        formatting.  df_dict must contain column 'dict' (return value
        of self.dict()).

        Each concordance line is a DataFrame with the cpos of each
        token as index:

        == (cpos), offset, p_show[0], p_show[1], ... ==

        """

        df['dataframe'] = df.apply(
            lambda row: self._export(row.name, row, p_show, form='dataframe'),
            axis=1
        )

        return df

    def lines(self, form='simple', p_show=['word'], s_show=[],
              order='first', cut_off=100, matches=None, slots=None):
        """Retrieve concordance lines from self.df_dump.  Central entry point
        for all methods.  Functionality includes:

        1. simple / kwic / dict / slots / dataframe format
        2. selection of p-attributes and s-attributes
        3. selection of matches using cut-off and order or a
           pre-defined list of matches
        4. definition of slots via anchor points (only for form='slot')

        Return value of all formats is a DataFrame indexed by (match,
        matchend) and requested s-attributes of the match:

        == (match, matchend), s_show[0], ... ==

        Further columns depend on output format, see the respective
        format implementations.

        :param str form: simple / kwic / dict / slots / dataframe
        :param list p_show: p-attributes to retrieve
        :param list s_show: s-attributes (at match position)
        :param str order: first / last / random
        :param int cut_off: how many lines to retrieve
        :param list matches: specific matches to retrieve
        :param dict slots: definition of slots via anchor points

        :return: concordance lines
        :rtype: DataFrame

        """

        # check parameters
        if len(self.df_dump) == 0:
            logger.error("no concordance lines to show")
            return DataFrame()
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

        # retrieve p-attributes in respective formatting
        if len(p_show) > 0:
            if form == 'simple':
                df = self.simple(df, p_show)
            elif form == 'kwic':
                df = self.kwic(df, p_show)
            elif form == 'slots':
                df = self.slots(df, p_show, slots)
            elif form == 'dict':
                df = self.dict(df, p_show)
            elif form == 'dataframe':
                df = self.dataframe(df, p_show)

        # s-attributes
        for s_att in s_show:
            tmp = self.corpus.dump2satt(df, s_att)
            if s_att in tmp.columns:  # annotation
                df[s_att] = tmp[s_att]
            else:               # ID if no annotation
                df[s_att] = tmp[s_att + "_cwbid"]

        return df
