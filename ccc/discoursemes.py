#! /usr/bin/env python
# -*- coding: utf-8 -*-

# part of module
from .collocates import dump2cooc
from .concordances import Concordance
from .collocates import Collocates
from .utils import format_cqp_query
from . import Corpus
# requirements
from pandas import NA, DataFrame
from association_measures.measures import calculate_measures
# logging
import logging
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

# #### 1 occurrence
# ... die [CDU]:m-me+m_t-me_t will eigentlich ...

# #### 2 occurrences
# ... die [CDU]:m-me+m_t-me_t und [CSU] gehen da ...  0
# ... die [CDU]:m-me und [CSU]:m_t-me_t gehen da ...  2
# ... die [CDU]:m_t-me_t und [CSU]:m-me gehen da ... -2
# ... die [CDU] und [CSU]:m-me+m_t-me_t gehen da ...  0

# #### 3 occurrences
# ... die [Union]:0+1, d.h. die [CDU] und [CSU] gehen da ...
# ... die [Union]:0, d.h. die [CDU]:1 und [CSU] gehen da ...
# ... die [Union]:0, d.h. die [CDU] und [CSU]:1 gehen da ...
# ... die [Union]:1, d.h. die [CDU]:0 und [CSU] gehen da ...
# ... die [Union], d.h. die [CDU]:0+1 und [CSU] gehen da ...
# ... die [Union], d.h. die [CDU]:0 und [CSU]:1 gehen da ...
# ... die [Union]:1, d.h. die [CDU] und [CSU]:0 gehen da ...
# ... die [Union], d.h. die [CDU]:1 und [CSU]:0 gehen da ...
# ... die [Union], d.h. die [CDU] und [CSU]:0+1 gehen da ...

# add_discourseme(dump, name, drop=True)
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

# #### t . d
# #### d . t
# ... die [CDU]:0+1 [will]:2 eigentlich ...

# #### t . t . d
# #### t . d . t
# #### d . t . t
# ... die [CDU]:0+1 und [CSU] [will]:2 eigentlich ...
# ... die [CDU]:0 und [CSU]:1 [will]:2 eigentlich ...
# ... die [CDU]:1 und [CSU]:0 [will]:2 eigentlich ...
# ... die [CDU] und [CSU]:0+1 [will]:2 eigentlich ...

# add_discourseme(dump, name, drop=False)

#     (m     me)     ci        c       ce     m_t    me_t      o_t    m_d    me_d    o_d
#    638    638      18      629      672     638     638        0    636     636     -2
#           638      18      629      672     640     640        2    636     636     -2
#    640    640      18      629      672     638     638       -2    636     636     -4
#           640      18      629      672     640     640        0    636     636     -4
#   1202   1202      36     1195     1218    1202    1202        0   1205    1205      3
# ...       ...     ...      ...      ...     ...     ...       ...   ...     ...    ...
# 149292 149292    7317   149286   149306  149290  149290       -2   <NA>    <NA>   <NA>
#        149292    7317   149286   149306  149292  149292        0   <NA>    <NA>   <NA>

# group_lines()
# === (m, me) ci c ce m0 m0e o0 m1 me1 o1 m2 me2 o2 ===
# with duplicate indices to
# === (m, me) ci c ce d0 d1 d2 ===
# without duplicate indices, where
# d0 = {(o0, m0, m0e), (o0, m0, m0e), ...}
# d1 = {(o1, m1, m1e), ...}
# ...

##########################################################
# (2) OUTER JOIN ON CONTEXTID: FULL TEXTUAL COOCCURRENCE #
##########################################################


def constellation_left_join(df1, df2, name, drop=True):
    """join an additional dump df2 to an existing constellation

    :param DataFrame df1: constellation dump === (m, me) ci c ce m_t* me_t* o_t* m_1* me_1* o_1* ... ==
    :param DataFrame df2: additional dump === (m, me) ci c ce ==
    :param str name: name for additional discourseme
    :param bool drop: drop all rows that do not contain all discoursemes within topic context?
    :return: constellation dump including additional dump  === (m, me) ci c ce m_t me_t o_t m_1 me_1 o_1 ... m_name me_name o_name ==
    :rtype: DataFrame
    """

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
        # only keep co-occurrences that are within context
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
    m = m.set_index(['match', 'matchend'])

    return m


def constellation_outer_join(df1, df2, name):
    """join an additional dump df2 to an existing constellation

    :param DataFrame df1: textual const.  === (ci) nr_1 nr_2 ... ==
    :param DataFrame df2: additional dump === (m, me) ci c ce ==
    :param str name: name for additional discourseme
    :return: constellation dump incl. additional dump === (ci) nr_1 nr_2 ... nr_name ==
    :rtype: DataFrame
    """

    # merge dumps via contextid ###
    table = DataFrame(df2[['contextid']].value_counts())
    table.columns = [name]
    m = df1.join(table, how='outer').astype("Int64")

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

    # init
    d = row['dict']
    roles = list()

    # 'out_of_window' | None | 'node'
    role = ['out_of_window' if abs(t) > window else None for t in d['offset']]
    for i in range(d['cpos'].index(row.name[0]), d['cpos'].index(row.name[1]) + 1):
        role[i] = 'node'
    roles.append(role)

    # discourseme names
    for name in names:
        role = [None] * len(d['offset'])
        for t in row[name]:
            for i in range(d['cpos'].index(t[1]), d['cpos'].index(t[2]) + 1):
                role[i] = name
        roles.append(role)

    # combine individual roles into one list of lists
    d['role'] = [[a for a in set(r) if a is not None] for r in list(zip(*roles))]

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

        self.corpus = dump.corpus
        # init with given dump
        self.df = dump.df[['contextid', 'context', 'contextend']].astype("Int64")
        # init added discoursemes
        self.discoursemes = {}
        # the topic is treated as common discourseme
        self.add_discourseme(dump, name=name)

    def __str__(self):
        return (
            "\n" + "a constellation with %d match indices" % len(self.df) + "\n" +
            "%d registered discourseme(s) " % len(self.discoursemes) + "\n" +
            "\n".join(["- '%s' with %d matches" % (d, len(self.discoursemes[d].df))
                       for d in self.discoursemes])
        )

    def __repr__(self):
        """Info string

        """
        return self.__str__()

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
        self.df = constellation_left_join(self.df, dump.df, name, drop=drop)

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

        return output

    def collocates(self, windows=[3, 5, 7],
                   p_show=['lemma'], flags=None,
                   ams=None, frequencies=True,
                   min_freq=2, order='log_likelihood', cut_off=None,
                   marginals='corpus'):
        """Retrieve collocates for constellation.

        :param int window: window around node for pre-selected matches

        :return: collocates
        :rtype: list of DataFrames
        """

        # get relevant contexts
        df_dump = self.df.drop_duplicates(subset=['context', 'contextend'])
        df_cooc, f1_set = dump2cooc(df_dump)

        logging.info('get cpos that are consumed by discoursemes')
        for idx in self.discoursemes.keys():
            f1_set.update(self.discoursemes[idx].matches())

        # correct df_cooc
        df_cooc = df_cooc.loc[~df_cooc['cpos'].isin(f1_set)]

        # count once
        node_freq = self.corpus.counts.cpos(f1_set, p_show)

        collocates = Collocates(
            corpus=self.corpus, df_dump=None, p_query=p_show, mws=max(windows),
            df_cooc=df_cooc, f1_set=f1_set, node_freq=node_freq
        )

        output = dict()
        for window in windows:
            output[window] = collocates.show(
                window=window, order=order, cut_off=cut_off, ams=ams,
                min_freq=min_freq, frequencies=frequencies, flags=flags,
                marginals=marginals
            )

        return output


class TextConstellation:

    def __init__(self, dump, s_context, name='topic'):
        """
        param Dump dump: dump with dump.corpus, dump.df: == (m, me) ci, c, ce ==
        param str name: name of the node
        """

        self.corpus = dump.corpus
        table = DataFrame(dump.df[['contextid']].value_counts())
        table.columns = [name]
        self.df = table
        self.s_context = s_context
        self.N = len(self.corpus.attributes.attribute(s_context, 's'))

    def add_discourseme(self, dump, name='discourseme'):

        # register discourseme
        if name in self.df.columns:
            logger.error('name "%s" already taken; cannot register discourseme' % name)
            return

        self.df = constellation_outer_join(self.df, dump.df, name)

    def associations(self, ams=None, frequencies=True,
                     min_freq=2, order='log_likelihood',
                     cut_off=None):

        tables = DataFrame()
        cooc = self.df > 0
        for name in self.df.columns:
            table = round(textual_associations(
                cooc, self.N, name
            ).reset_index(), 2)
            table['node'] = name
            tables = tables.append(table)

        tables = tables[
            ['node', 'candidate'] +
            [d for d in tables.columns if d not in ['node', 'candidate']]
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
    measures = calculate_measures(contingencies, freq=True)
    contingencies = contingencies.join(measures)

    return contingencies


def create_constellation(corpus_name,
                         topic_name, topic_items,
                         p_query, s_query, flags, escape,
                         s_context, context,
                         additional_discoursemes,
                         lib_path=None, cqp_bin='cqp',
                         registry_path='/usr/local/share/cwb/registry/',
                         data_path='/tmp/ccc-data/',
                         match_strategy='longest',
                         dataframe=False, drop=True, text=False):
    """
    simple constellation creator
    """

    # init corpus
    corpus = Corpus(corpus_name, lib_path, cqp_bin, registry_path, data_path)

    # init discourseme constellation
    topic_query = format_cqp_query(
        topic_items, p_query=p_query, s_query=s_query, flags=flags, escape=escape
    )
    topic_dump = corpus.query(
        topic_query, context=context, context_break=s_context,
        match_strategy=match_strategy
    )

    if not text:
        const = Constellation(topic_dump, topic_name)
    else:
        const = TextConstellation(topic_dump, s_context, topic_name)

    # add further discoursemes
    for disc_name in additional_discoursemes.keys():
        disc_items = additional_discoursemes[disc_name]
        disc_query = format_cqp_query(
            disc_items, p_query=p_query, s_query=s_query, flags=flags, escape=escape
        )
        disc_dump = corpus.query(
            disc_query, context=None, context_break=s_context,
            match_strategy=match_strategy
        )
        if not text:
            const.add_discourseme(disc_dump, disc_name, drop=drop)
        else:
            const.add_discourseme(disc_dump, disc_name)

    if dataframe:
        return const.df
    else:
        return const
