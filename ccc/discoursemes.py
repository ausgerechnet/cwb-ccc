#! /usr/bin/env python
# -*- coding: utf-8 -*-

# from anycache import anycache
# part of module
from .collocates import df_node_to_cooc, add_ams
from .concordances import Concordance
from .utils import format_cqp_query
from . import Corpus
# requirements
from pandas import NA, MultiIndex
# logging
import logging
logger = logging.getLogger(__name__)


# TODO how to make this path configurable?
# ANYCACHE_PATH = '/tmp/ccc-anycache/'


# @anycache(ANYCACHE_PATH)
def constellation_merge(df1, df2, name, drop=True):

    # merge dumps via contextid ###
    df1 = df1.reset_index()
    df2 = df2.reset_index()[['contextid', 'match', 'matchend']].astype("Int64")
    m = df1.merge(df2, on='contextid', how='left')

    # calculate offset ###
    m['offset_y'] = 0       # init as overlap
    # y .. x
    m.at[m['match_x'] > m['matchend_y'], 'offset_y'] = m['matchend_y'] - m['match_x']
    # x .. y
    m.at[m['matchend_x'] < m['match_y'], 'offset_y'] = m['match_y'] - m['matchend_x']
    # missing y
    m.at[m['match_y'].isna(), 'offset_y'] = NA

    # restrict to complete constellation ###
    if drop:
        m = m.dropna()
        # also remove co-occurrences which are too far away
        m = m.loc[
            (m['matchend_y'] >= m['context']) & (m['match_y'] < m['contextend'])
        ]

    # rename columns ###
    m = m.rename(columns={
        'match_x': 'match',
        'matchend_x': 'matchend',
        'match_y': 'match_' + name,
        'matchend_y': 'matchend_' + name,
        'offset_y': 'offset_' + name
    })

    # set index ###
    m = m.set_index(['match', 'matchend']).astype("Int64")

    return m


def role_formatter(row, names, s_show, window):
    """Take a row of a dataframe indexed by match, matchend of the node,
    columns for each discourseme with sets of tuples indicating discourseme positions,
    columns for each s in s_show,
    and a column 'dict' containing the pre-formatted concordance line.

    creates a list (aligned with other lists) of lists of roles; roles are:
    - 'node' (if cpos in index)
    - 'out_of_window' (if offset of cpos from node > window)
    - discourseme names

    :return: concordance line for MMDA frontend
    :rtype: dict

    """
    d = row['dict']
    roles = list()
    # node role
    role = ['out_of_window' if abs(t) > window else None for t in d['offset']]
    for i in range(d['cpos'].index(row.name[0]), d['cpos'].index(row.name[1]) + 1):
        role[i] = 'node'
    roles.append(role)
    # discourseme roles
    for name in names:
        role = [None] * len(d['offset'])
        for t in row[name]:
            for i in range(d['cpos'].index(t[1]), d['cpos'].index(t[2]) + 1):
                role[i] = name
        roles.append(role)
    # combine individual roles into one list of lists
    roles = [[a for a in set(r) if a is not None] for r in list(zip(*roles))]
    # append to concordance line and line to output
    d['role'] = roles
    # append s-attributes
    for s in s_show:
        d[s] = row[s]
    return d


class Constellation:

    def __init__(self, dump, name='topic'):
        """
        param Dump dump: dump with dump.corpus, dump.df: == (m, me) ci, c, ce ==
        param str name: name of the node
        """

        self.df = dump.df[['contextid', 'context', 'contextend']].astype("Int64")
        self.discoursemes = {}
        self.add_discourseme(dump, name=name)
        self.corpus = dump.corpus

    def add_discourseme(self, dump, name='discourseme', drop=True):
        """
        :param Dump dump: dump.df: == (m, me) ci ==
        :param str name: name of the discourseme
        :param bool drop: remove matches without all discoursemes in node context
        """

        # register discourseme
        if name in self.discoursemes.keys():
            logger.error('name "%s" already taken; cannot register discourseme' % name)
            return
        self.discoursemes[name] = dump

        m = constellation_merge(self.df, dump.df, name, drop)

        self.df = m

    def group_lines(self):
        """
        convert dataframe:
        === (m, me) ci c ce m0 m0e o0 m1 me1 o1 m2 me2 o2 ===
        with duplicate indices to
        === (m, me) ci c ce m0 m1 m2 ===
        without duplicate indices
        where
        m0 = {(o0, m0, m0e), (o0, m0, m0e), ...}
        m1 = {(o1, m1, m1e), ...}

        """

        df = self.df.copy()
        df_reduced = df[~df.index.duplicated(keep='first')][
            ['contextid', 'context', 'contextend']
        ]
        for name in self.discoursemes.keys():
            columns = [m + "_" + name for m in ['offset', 'match', 'matchend']]
            df[name] = df[columns].values.tolist()
            df[name] = df[name].apply(tuple)
            df = df.drop(columns, axis=1)
            df_reduced[name] = df.groupby(level=['match', 'matchend'])[name].apply(set)
        return df_reduced

    def concordance(self, window=5,
                    p_show=['word', 'lemma'], s_show=[],
                    order='random', cut_off=100):
        """Retrieve concordance lines for constellation.

        :param int window: cpos further away from node will be marked 'out_of_window'

        :return: concordance lines
        :rtype: list
        """

        # convert dataframe
        df_grouped = self.group_lines()
        # retrieve concordance lines
        conc = Concordance(self.corpus.copy(), df_grouped)
        lines = conc.lines(form='dict', p_show=p_show, s_show=s_show,
                           order=order, cut_off=cut_off)
        # map roles
        output = list(lines.apply(
            lambda row: role_formatter(
                row, self.discoursemes.keys(), s_show, window
            ), axis=1
        ))
        # return
        return output

    def collocates(self, windows=[3, 5, 7],
                   p_show=['lemma'], flags=None,
                   ams=None, frequencies=True,
                   min_freq=2, order='log_likelihood', cut_off=None):
        """Retrieve collocates
        :param int window: window around node for pre-selected matches

        :return: collocates
        :rtype: list of DataFrames
        """

        # get relevant contexts
        df = self.df.drop_duplicates(subset=['context', 'contextend'])
        df_cooc, f1_set = df_node_to_cooc(df)

        logging.info('get cpos that are consumed by discoursemes')
        for idx in self.discoursemes.keys():
            f1_set.update(self.discoursemes[idx].matches())

        # correct df_cooc
        df_cooc = df_cooc.loc[~df_cooc['cpos'].isin(f1_set)]

        # count once
        N = self.corpus.corpus_size - len(f1_set)
        node_freq = self.corpus.counts.cpos(f1_set, p_show)
        node_freq.columns = ['in_nodes']

        # count for each window
        output = dict()
        for window in windows:
            output[window] = calculate_collocates(
                self.corpus, df_cooc, node_freq, window, p_show,
                N, min_freq, order, cut_off, flags, ams, frequencies
            )

        return output


# @anycache(ANYCACHE_PATH)
def calculate_collocates(corpus, df_cooc, node_freq, window, p_show,
                         N, min_freq, order, cut_off, flags, ams, frequencies):

    # move to requested window
    relevant = df_cooc.loc[abs(df_cooc['offset']) <= window]

    # number of possible occurrence positions within window
    f1_inflated = len(relevant)

    # get frequency counts
    f = corpus.counts.cpos(relevant['cpos'], p_show)
    f.columns = ['f']

    # get marginals
    if len(p_show) == 1:
        # coerce to multiindex (what was I thinking?)
        f2 = corpus.marginals(
            f.index.get_level_values(p_show[0]), p_show[0]
        )
        f2.index = MultiIndex.from_tuples(
            f2.index.map(lambda x: (x, )), names=p_show
        )
    else:
        f2 = corpus.marginals_complex(f.index, p_show)
    f2.columns = ['marginal']

    # deduct node frequencies from marginals
    f2 = f2.join(node_freq)
    f2 = f2.fillna(0, downcast='infer')
    f2['f2'] = f2['marginal'] - f2['in_nodes']

    # get sub-corpus size
    f1 = f1_inflated

    # score
    collocates = add_ams(
        f, f1, f2, N,
        min_freq, order, cut_off, flags, ams, frequencies
    )

    # throw away anti-collocates by default
    collocates = collocates.loc[collocates['O11'] >= collocates['E11']]

    # deal with index
    if len(p_show) == 1:
        collocates.index = collocates.index.map(lambda x: x[0])
        collocates.index.name = p_show[0]

    return collocates


def create_constellation(corpus_name,
                         topic_name, topic_items,
                         p_query, s_query, flags, escape,
                         s_context, context,
                         additional_discoursemes,
                         lib_path, cqp_bin, registry_path, data_path,
                         match_strategy='longest'):
    """
    simple constellation creator, cached
    """

    # init corpus
    corpus = Corpus(corpus_name, lib_path, cqp_bin, registry_path, data_path)

    # init discourseme constellation
    topic_query = format_cqp_query(topic_items,
                                   p_query=p_query, s_query=s_query,
                                   flags=flags, escape=escape)
    topic_dump = corpus.query(topic_query, context=context, context_break=s_context,
                              match_strategy=match_strategy)
    const = Constellation(topic_dump, topic_name)

    # add further discoursemes
    for disc_name in additional_discoursemes.keys():
        disc_items = additional_discoursemes[disc_name]
        disc_query = format_cqp_query(disc_items,
                                      p_query=p_query, s_query=s_query,
                                      flags=flags, escape=escape)
        disc_dump = corpus.query(disc_query, context=None, context_break=s_context,
                                 match_strategy=match_strategy)
        const.add_discourseme(disc_dump, disc_name)

    # put into cache
    # cache.set(identifier, const)

    return const


# @anycache(ANYCACHE_PATH)
# TODO take care of caching for random order
def get_concordance(corpus_name,
                    topic_name, topic_items,
                    p_query='lemma', s_query=None, flags_query="%cd", escape_query=True,
                    s_context='s', context=20,
                    additional_discoursemes={},
                    p_show=['word', 'lemma'], s_show=[], window=None,
                    order='random', cut_off=100,
                    lib_path=None, cqp_bin='cqp',
                    registry_path='/usr/local/share/cwb/registry/',
                    data_path='/tmp/ccc-data/'):
    """
    :param str corpus_name: name corpus in CWB registry

    :param str topic_name: name of the topic ("node") discourseme
    :param list topic_items: list of lexical items
    :param str p_query: p-att layer to query
    :param str s_query: s-att to use for delimiting queries
    :param str flags_query: flags to use for querying
    :param bool escape_query: whether to cqp-escape the query items

    :param str s_context: s-att to use for delimiting contexts
    :param int context: context around the nodes used to identify relevant matches

    :param dict additional_discoursemes: {name: items}

    :param list p_show: p-attributes to show
    :param list s_show: s-attributes to show
    :param int window: mark tokens further away as 'out_of_window'
    :param str order: concordance order (first / last / random)
    :param int cut_off: number of lines to retrieve

    :param str lib_path:
    :param str cqp_bin:
    :param str registry_path:
    :param str data_path:

    :return: dict of concordance lines (each one a dict, keys=1:N)
    :rtype: dict

    """

    # preprocess parameters
    s_query = s_context if s_query is None else s_query
    window = context if window is None else window

    # create constellation
    const = create_constellation(corpus_name,
                                 topic_name, topic_items,
                                 p_query, s_query, flags_query, escape_query,
                                 s_context, context,
                                 additional_discoursemes,
                                 lib_path, cqp_bin, registry_path, data_path)

    # retrieve lines
    lines = const.concordance(window=window,
                              p_show=p_show, s_show=s_show,
                              order=order, cut_off=cut_off)

    # convert to dictionary
    output = dict()
    c = 0
    for line in lines:
        c += 1
        output[c] = line

    return output


# @anycache(ANYCACHE_PATH)
def get_collocates(corpus_name,
                   topic_items,
                   p_query='lemma', s_query=None, flags_query="%cd", escape_items=True,
                   s_context='s', context=20,
                   additional_discoursemes={},
                   windows=[3, 5, 7], p_show=['word', 'lemma'], flags_show="",
                   min_freq=2,
                   order='random', cut_off=100,
                   lib_path=None, cqp_bin='cqp',
                   registry_path='/usr/local/share/cwb/registry/',
                   data_path='/tmp/ccc-data/'):
    """
    :param str corpus_name: name corpus in CWB registry

    :param list topic_items: list of lexical items
    :param str p_query: p-att layer to query
    :param str s_query: s-att to use for delimiting queries
    :param str flags_query: flags to use for querying
    :param bool escape_items: whether to cqp-escape the query items

    :param str s_context: s-att to use for delimiting contexts
    :param int context: context around the nodes used to identify relevant matches

    :param dict additional_discoursemes: {name: items}

    :param list windows: windows (int) to use for collocation analyses around nodes
    :param list p_show: p-atts to use for collocation analysis
    :param str flags_show: post-hoc folding ("%cd") with cwb-ccc-algorithm
    :param int min_freq: rare item treshold
    :param str order: collocation order (columns in scored table)
    :param int cut_off: number of collocates to retrieve

    :param str lib_path:
    :param str cqp_bin:
    :param str registry_path:
    :param str data_path:

    :return: dict of collocation tables (key=window)
    :rtype: dict

    """

    # preprocess parameters
    s_query = s_context if s_query is None else s_query
    topic_name = 'topic'
    frequencies = True
    ams = None

    # create constellation
    const = create_constellation(corpus_name,
                                 topic_name, topic_items,
                                 p_query, s_query, flags_query, escape_items,
                                 s_context, context,
                                 additional_discoursemes,
                                 lib_path, cqp_bin, registry_path, data_path)

    collocates = const.collocates(windows=windows,
                                  p_show=p_show, flags=flags_show,
                                  ams=ams, frequencies=frequencies, min_freq=min_freq,
                                  order=order, cut_off=cut_off)

    for window in collocates.keys():
        coll_window = collocates[window]
        # drop superfluous columns and sort
        coll_window = coll_window[[
            'log_likelihood',
            'log_ratio',
            'f',
            'f2',
            'mutual_information',
            'z_score',
            't_score'
        ]]

        # rename AMs
        am_dict = {
            'log_likelihood': 'log likelihood',
            'f': 'co-occurrence freq.',
            'mutual_information': 'mutual information',
            'log_ratio': 'log-ratio',
            'f2': 'marginal freq.',
            't_score': 't-score',
            'z_score': 'z-score'
        }
        collocates[window] = coll_window.rename(am_dict, axis=1)

    return collocates
