#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""discoursemes.py

mostly support for MMDA frontend

"""
import logging

# requirements
from association_measures.measures import score
from pandas import DataFrame, concat

# part of module
from . import Corpus, SubCorpus
from .cache import generate_idx
from .collocates import Collocates, dump2cooc
from .concordances import Concordance
from .utils import (aggregate_matches, dump_left_join, format_cqp_query,
                    format_roles, group_lines)

logger = logging.getLogger(__name__)


########################################################
# (1) FOCUS ON TOPIC: DIRECTED (IE INDEXED) DATAFRAMES #
########################################################
# init(dump, name='topic')
# input : dump.df: === (m, me) ci c ce ==
# output: self.df: === (m, me) ci c ce m_topic me_topic o_topic ===
# with duplicate indices:

#   (m   me)     ci        c       ce      m_t   me_t   o_t
#  638  638      18      629      672      638    638     0
#       638      18      629      672      640    640     2
#  640  640      18      629      672      638    638    -2
#       640      18      629      672      640    640     0
# 1202 1202      36     1195     1218     1202   1202     0
# ...   ...     ...      ...      ...      ...    ...   ...

##########################################################
# add_discourseme(dump, name, drop=True)
##########################################################
# input:  === (m, me) ci c ce m_t me_t o_t ==
#         === (m_d, me_d) ci ==
# output: === (m, me) ci c ce m_t me_t o_t m_d me_d o_d ==

#   (m   me)     ci       c      ce    m_t   me_t    o_t     m_d   me_d   o_d
#  638  638      18     629     672    638    638      0     636    636    -2
#       638      18     629     672    640    640      2     636    636    -2
#  640  640      18     629     672    638    638     -2     636    636    -4
#       640      18     629     672    640    640      0     636    636    -4
# 1202 1202      36    1195    1218   1202   1202      0    1205   1205     3
#  ...  ...     ...     ...     ...    ...    ...    ...     ...    ...   ...

##########################################################
# add_discourseme(dump, name, drop=False)
##########################################################
# input:  === (m, me) ci c ce m_t me_t o_t ==
#         === (m_d, me_d) ci ==
# output: === (m, me) ci c ce m_t me_t o_t m_d me_d o_d ==

#     (m     me)     ci        c       ce     m_t    me_t      o_t    m_d    me_d    o_d
#    638    638      18      629      672     638     638        0    636     636     -2
#           638      18      629      672     640     640        2    636     636     -2
#    640    640      18      629      672     638     638       -2    636     636     -4
#           640      18      629      672     640     640        0    636     636     -4
#   1202   1202      36     1195     1218    1202    1202        0   1205    1205      3
# ...       ...     ...      ...      ...     ...     ...       ...   ...     ...    ...
# 149292 149292    7317   149286   149306  149290  149290       -2   <NA>    <NA>   <NA>
#        149292    7317   149286   149306  149292  149292        0   <NA>    <NA>   <NA>

##########################################################
# group_lines()
##########################################################
# === (m, me) ci c ce m0 m0e o0 m1 me1 o1 m2 me2 o2 ===
# with duplicate indices to
# === (m, me) ci c ce d0 d1 d2 ===
# without duplicate indices, where
# d0 = {(o0, m0, m0e), (o0, m0, m0e), ...}
# d1 = {(o1, m1, m1e), ...}
# ...

#####################################################
# (2) OUTER JOIN ON CONTEXTID: TEXTUAL COOCCURRENCE #
#####################################################

#           d_COUNTS                                                  d      d_BOOL
# context_id
# 1061             8  {(33025, 33025), (33027, 33027), (32998, 32998...        True
# 545              4  {(16933, 16933), (16935, 16935), (16919, 16919...        True
# 6815             4  {(132976, 132976), (132969, 132969), (132978, ...        True
# 6548             4  {(123407, 123407), (123394, 123394), (123409, ...        True
# 6986             4  {(139381, 139381), (139383, 139383), (139396, ...        True
# ...            ...                                                ...         ...
# 2259             1                                   {(79339, 79339)}        True
# 1158             1                                   {(36252, 36252)}        True
# 2201             1                                   {(77579, 77579)}        True
# 6636             1                                 {(126185, 126185)}        True
# 1529             1                                   {(51388, 51388)}        True


class Discourseme():

    def __init__(self, cwb_id, name, df):
        """
        :param str name: name of the discourseme
        :param DataFrame df:
        """
        pass

    def breakdown(self, p_atts):
        pass

    def concordance(self, context, p_atts, form):
        pass

    def meta(self, s_atts):
        pass

    def collocates(self, context, form):
        pass


class Constellation_:

    # sqlite database
    cwb_id = ""
    name = ""
    match = 0
    matchend = 1

    def add_discourseme(self, name, df):
        pass

    def breakdown(self, p_atts=['lemma'], flags='', form='dataframe'):
        pass

    def concordance(self, names=None, p_atts=['word'], s_atts=[],
                    s_context=None, context_left=10, context_right=10,
                    order='random', random_seed=42, number=100,
                    form='dataframe'):
        """
        filtered by names (None=all)
        kwic-focus on match, matchend of each name
        other discoursemes are highlighted
        """
        pass

    def meta(self, s_att, pos='match', form='dataframe'):
        """
        dataframe: s_att_value, frequency, ipm
        """

        # # init corpus
        # corpus = Corpus(corpus_name, lib_path, cqp_bin, registry_path, data_path)

        # # init discourseme constellation
        # topic_query = format_cqp_query(topic_items,
        #                                p_query=p_query, s_query=s_query,
        #                                flags=flags_query, escape=escape)
        # dump = corpus.query(topic_query, context=None)
        # # get meta data
        # meta = dump.concordance(
        #     s_show=s_show, form='simple', order=order, cut_off=cut_off
        # )

        # # tabulate
        # output = list()
        # for s in s_show:

        #     # tabulate number of tokens
        #     # TODO: no need to calculate for each text_x, text_y, etc.
        #     lengths = corpus.query_s_att(s)
        #     lengths = lengths.df.reset_index()
        #     lengths['nr_tokens'] = lengths['matchend'] - lengths['match'] + 1

        #     # absolute frequency in each subcorpus
        #     m = meta[s].value_counts()

        #     if len(m) < 100:
        #         m = m.to_frame()
        #         m.columns = ['frequency']
        #         ell = lengths.groupby(s)[['nr_tokens']].agg(sum)
        #         ell = ell.join(m, how='outer')
        #         ell = ell.fillna(0, downcast='infer')
        #         ell['IPM'] = round(ell['frequency'] / ell['nr_tokens'] * 10**6, 2)
        #         ell.index.name = s
        #         ell = ell.reset_index()
        #         output.append(ell.to_html(index=False, bold_rows=False))

        pass

    def collocates(self, window=5, p_atts=['lemma'], flags='',
                   ams=None, order='log_likelihood', cut_off=None, form='dataframe',
                   reference=None):
        """
        if reference is None: reference are marginals
        """
        pass

    def associations(self, reference=None):
        """
        if reference is None: reference are marginals
        """
        pass


class Constellation:

    def __init__(self, dump, name='topic'):
        """
        param Dump dump: dump with dump.corpus, dump.df: == (m, me) ci, c, ce ==
        param str name: name of the node
        """

        self.corpus = dump
        # init with given dump
        self.df = dump.df[['contextid', 'context', 'contextend']].astype("Int64")
        # init added discoursemes
        self.discoursemes = {}
        # the topic is treated as common discourseme
        self.add_discourseme(dump, name=name)

    def __str__(self):
        return (
            "\n" + f"a constellation with {len(self.df)} match indices" + "\n" +
            f"{len(self.discoursemes)} registered discourseme(s)" + "\n" +
            "\n".join([f"- '{d}' with {len(self.discoursemes[d].df)} matches" for d in self.discoursemes])
        )

    def __repr__(self):
        """Info string

        """
        return self.__str__()

    def add_discourseme(self, dump, name='discourseme', drop=True, window=None):
        """
        :param Dump dump: dump.df: == (m, me) ci ==
        :param str name: name of the discourseme
        :param bool drop: remove matches without all discoursemes in node context
        """

        # register discourseme
        if name in self.discoursemes.keys():
            logger.error(f'name "{name}" already taken; cannot register discourseme')
            return

        self.discoursemes[name] = dump
        self.df = dump_left_join(self.df, dump.df, name,
                                 drop=drop, window=window)

    def breakdown(self, p_atts=['word'], flags=""):

        breakdowns = list()
        for idx, dump in self.discoursemes.items():
            d = dump.breakdown(p_atts=p_atts, flags=flags)
            d['discourseme'] = idx
            breakdowns.append(d)
        breakdown = concat(breakdowns)

        return breakdown

    def concordance(self, window=5,
                    p_show=['word', 'lemma'], s_show=[],
                    order='random', cut_off=100, random_seed=42,
                    htmlify_meta=False, cwb_ids=True, form='dict'):
        """Retrieve concordance lines for constellation.

        :param int window: cpos further away from node will be marked 'out_of_window'

        :return: concordance lines
        :rtype: list
        """

        # convert dataframe
        hkeys = list(self.discoursemes.keys())
        df = group_lines(self.df, hkeys)
        conc = Concordance(self.corpus.copy(), df)
        lines = conc.lines(form=form, p_show=p_show, s_show=s_show, order=order, cut_off=cut_off, cwb_ids=cwb_ids)

        if form == 'dict':
            lines = list(lines.apply(lambda row: format_roles(row, hkeys, s_show, window, htmlify_meta=htmlify_meta), axis=1))

        return lines

    def collocates(self, windows=[3, 5, 7], p_show=['lemma'],
                   flags=None, ams=None, min_freq=2,
                   order='log_likelihood', cut_off=None,
                   marginals='corpus'):
        """Retrieve collocates for constellation.

        :param int window: window around node for pre-selected matches

        :return: collocates
        :rtype: list of DataFrames
        """

        # get df_cooc, f1_set, node_freq from cache if possible
        identifier = generate_idx(
            [self.df.reset_index()[['match', 'matchend', 'context', 'contextend']], p_show, min_freq, self.discoursemes.values()]
        )
        f1_set = self.corpus.cache.get(identifier + "-f1_set")
        df_cooc = self.corpus.cache.get(identifier + "-df_cooc")
        node_freq = self.corpus.cache.get(identifier + "-node_freq")

        # create and cache otherwise
        if not isinstance(df_cooc, DataFrame):

            # get relevant contexts
            logger.info('create cooc matrix')
            df_dump = self.df.drop_duplicates(subset=['context', 'contextend'])
            df_cooc, f1_set = dump2cooc(df_dump)

            logger.info('get cpos that are consumed by discoursemes')
            for idx, disc in self.discoursemes.items():
                # print(idx)
                cpos_total = disc.matches()  # cpos in whole corpus (if not approximate)
                # cpos_in = set(df_cooc['cpos']).intersection(cpos_total)  # cpos in context
                # breakdown = disc.breakdown(p_atts=p_show)  # breakdown of discourseme
                # print(len(cpos_total))
                # print(len(cpos_in))
                # print(breakdown)
                f1_set.update(cpos_total)
                # print(len(f1_set))
            df_cooc = df_cooc.loc[~df_cooc['cpos'].isin(f1_set)]

            # count node freqs
            node_freq = self.corpus.counts.cpos(f1_set, p_show)

        # determine collocates
        collocates = Collocates(
            corpus=self.corpus.copy(),
            df_dump=None,
            p_query=p_show,
            mws=max(windows),
            df_cooc=df_cooc,
            f1_set=f1_set,
            node_freq=node_freq
        )
        output = dict()
        for window in windows:
            output[window] = collocates.show(
                window=window,
                order=order,
                cut_off=cut_off,
                ams=ams,
                min_freq=min_freq,
                flags=flags,
                marginals=marginals
            )

        return output


class TextConstellation:

    def __init__(self, dump, s_context, name='topic'):
        """
        param Dump dump: dump with dump.corpus, dump.df: == (m, me) ci, c, ce ==
        param str name: name of the node
        """

        if isinstance(dump, dict):
            dumps = dump.copy()
            name = list(dumps.keys())[0]
            dump = dumps.pop(name)

        elif isinstance(dump, SubCorpus):
            dumps = {}

        else:
            raise ValueError()

        # create
        self.s_context = s_context
        self.corpus = dump
        self.N = len(self.corpus.attributes.attribute(s_context, 's'))

        # init discoursemes
        self.discoursemes = {name: dump}

        try:
            self.df = aggregate_matches(dump.df, name)
        except KeyError:        # no matches
            self.df = DataFrame()

        for name, dump in dumps.items():
            self.add_discourseme(dump, name)

    def add_discourseme(self, dump, name='discourseme'):

        # register discourseme
        if name in self.df.columns:
            logger.error(f'name "{name}" already taken; cannot register discourseme')
            return

        try:
            dump = dump.set_context(context_break=self.s_context)
            df = aggregate_matches(dump.df, name)
        except KeyError:        # no matches
            df = DataFrame()

        if df.empty:
            return
        elif self.df.empty:
            self.df = df
        else:
            df = self.df.join(df, how='outer')

        self.discoursemes[name] = dump
        self.df = df.sort_index()

    def breakdown(self, p_atts=['word'], flags=""):

        breakdowns = list()
        for idx, dump in self.discoursemes.items():
            d = dump.breakdown(p_atts=p_atts, flags=flags)
            d['discourseme'] = idx
            breakdowns.append(d)
        breakdown = concat(breakdowns)

        return breakdown

    def concordance(self, window=0, p_show=['word', 'lemma'],
                    s_show=[], order='random', cut_off=100,
                    random_seed=42, htmlify_meta=False):

        # join context..contextend
        contexts = self.corpus.dump_from_s_att(self.s_context, annotation=False)
        contexts.columns = ['contextid']
        contexts = contexts.reset_index().set_index('contextid')
        df = self.df.join(contexts)

        # index by CONTEXT MATCHES
        df = df.set_index(['match', 'matchend'])
        names = list(self.discoursemes.keys())
        names_bool = [n + '_BOOL' for n in names]
        names_count = [n + '_COUNTS' for n in names]
        for b, c in zip(names_bool, names_count):
            df[b] = df[b].fillna(False)
            df[c] = df[c].fillna(0)

        # ACTUAL CONCORDANCING
        conc = Concordance(self.corpus.copy(), df)
        lines = conc.lines(form='dict', p_show=p_show, s_show=s_show, order=order, cut_off=cut_off)
        output = lines.apply(lambda row: format_roles(
            row, names, s_show=names_bool+s_show, window=0, htmlify_meta=htmlify_meta
        ), axis=1)

        return list(output)

    def associations(self, ams=None, min_freq=2,
                     order='log_likelihood', cut_off=None):

        counts = self.df[[c for c in self.df.columns if c.endswith("_BOOL")]]

        if len(counts.columns) == 1:
            logger.error('cannot calculate associations has only one registered discourseme')
            return None

        counts.columns = [c.split("_BOOL")[0] for c in counts.columns]
        cooc = counts.fillna(False)

        # TODO triangular matrix
        tables = list()
        for name in counts.columns:
            # TODO super slow for pandas 2.0, but why?
            table = round(textual_associations(cooc, self.N, name).reset_index(), 2)
            table['node'] = name
            tables.append(table)
        tables = concat(tables)

        tables = tables[
            ['node', 'candidate'] + [d for d in tables.columns if d not in ['node', 'candidate']]
        ]

        return tables


def textual_associations(cooc, N, column):
    """Textual association.

    """
    f1 = cooc[column].sum()
    candidates = [c for c in cooc.columns if c != column]
    records = list()
    for candidate in candidates:
        f2 = cooc[candidate].sum()
        f = (cooc[[column, candidate]].sum(axis=1) == 2).sum()
        records.append({
            'candidate': candidate,
            'f1': f1,
            'f2': f2,
            'f': f,
            'N': N
        })
    contingencies = DataFrame(records).set_index('candidate')
    measures = score(contingencies, freq=True)
    contingencies = contingencies.join(measures.drop(['N'], axis=1))

    return contingencies


def create_constellation(corpus_name,
                         # discoursemes
                         topic_discourseme,
                         filter_discoursemes,
                         additional_discoursemes,
                         # context settings
                         s_context,
                         context=20,
                         window=None,
                         approximate=False,
                         # CWB settings
                         match_strategy='longest',
                         lib_dir=None,
                         cqp_bin='cqp',
                         registry_dir='/usr/local/share/cwb/registry/',
                         data_dir=None,
                         # for creating from items rather than queries
                         querify=True,
                         p_query='word',
                         s_query=None,
                         flags='%cd',
                         escape=True):
    """simple constellation creator. returns a Constellation() if a
    topic_discourseme is given, otherwise a TextConstellation(). Note
    that for TextConstellations, there is no difference between
    additional discoursemes and filter discoursemes (instead, a
    boolean column for each discourseme is added).

    :param dict topic_discourseme: used for init
    :param dict filter_discoursemes: inner join
    :param dict additional_discourseme: left join

    """

    # translate items into queries?
    if querify:

        # copy so local changes don't affect input
        topic_discourseme = topic_discourseme.copy()
        filter_discoursemes = filter_discoursemes.copy()
        additional_discoursemes = additional_discoursemes.copy()

        # pre-process parameters
        s_context = s_query if not s_context else s_context
        s_query = s_context if s_query is None else s_query

        # create queries
        for disc_name, disc_items in topic_discourseme.items():
            disc_query = format_cqp_query(
                disc_items, p_query=p_query, s_query=s_query, flags=flags, escape=escape
            )
            topic_discourseme[disc_name] = disc_query

        for disc_name, disc_items in filter_discoursemes.items():
            disc_query = format_cqp_query(
                disc_items, p_query=p_query, s_query=s_query, flags=flags, escape=escape
            )
            filter_discoursemes[disc_name] = disc_query

        for disc_name, disc_items in additional_discoursemes.items():
            disc_query = format_cqp_query(
                disc_items, p_query=p_query, s_query=s_query, flags=flags, escape=escape
            )
            additional_discoursemes[disc_name] = disc_query

    # init corpus
    corpus = Corpus(corpus_name, lib_dir, cqp_bin, registry_dir, data_dir)

    # topic -> Constellation()
    if len(topic_discourseme) > 0:

        if len(topic_discourseme) > 1:
            raise ValueError("only one topic discourseme can be given")

        # init with topic
        topic_name = list(topic_discourseme.keys())[0]
        topic_query = topic_discourseme[topic_name]
        topic_dump = corpus.query_cqp(
            topic_query,
            context=context,
            context_break=s_context,
            match_strategy=match_strategy
        )
        const = Constellation(topic_dump, topic_name)

        # only count on subcorpus of context of matches
        if approximate:
            sub = topic_dump.df.set_index(['context', 'contextend'])
            corpus = corpus.subcorpus('TempRestriction', df_dump=sub)

        # add filter discoursemes
        for disc_name, disc_query in filter_discoursemes.items():
            disc_dump = corpus.query_cqp(
                disc_query,
                context=None,
                context_break=s_context,
                match_strategy=match_strategy
            )
            if len(disc_dump.df) > 0:
                const.add_discourseme(disc_dump, disc_name, drop=True, window=window)

        # add additional discoursemes
        for disc_name, disc_query in additional_discoursemes.items():
            disc_dump = corpus.query_cqp(
                disc_query,
                context=None,
                context_break=s_context,
                match_strategy=match_strategy
            )
            if len(disc_dump.df) > 0:
                const.add_discourseme(disc_dump, disc_name, drop=False)

    # no topic -> TextConstellation()
    else:

        # no filter implemented: all discoursemes are equal
        discoursemes = {**filter_discoursemes, **additional_discoursemes}

        # init with arbitrary topic
        topic_name = list(discoursemes.keys())[0]
        topic_query = discoursemes.pop(topic_name)
        topic_dump = corpus.query_cqp(
            topic_query,
            context=context,
            context_break=s_context,
            match_strategy=match_strategy
        )
        const = TextConstellation(topic_dump, s_context, topic_name)

        # add further discoursemes
        for disc_name, disc_query in discoursemes.items():
            disc_dump = corpus.query_cqp(
                disc_query,
                context=None,
                context_break=s_context,
                match_strategy=match_strategy
            )
            if len(disc_dump.df) > 0:
                const.add_discourseme(disc_dump, disc_name)

    return const
