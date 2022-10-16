#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging

# requirements
from association_measures.measures import score
from pandas import NA, DataFrame, concat

# part of module
from . import Corpus
from .collocates import Collocates, dump2cooc
from .concordances import Concordance
from .dumps import Dump
from .utils import format_cqp_query

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


# TODO discourseme definition: items, queries, corpora
class Discourseme:
    def __init__(self):
        pass


def constellation_left_join(df1, df2, name, drop=True, window=None):
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
    m.loc[m['match_x'] > m['matchend_y'], 'offset_y'] = m['matchend_y'] - m['match_x']
    # x .. y
    m.loc[m['matchend_x'] < m['match_y'], 'offset_y'] = m['match_y'] - m['matchend_x']
    # missing y
    m.loc[m['match_y'].isna(), 'offset_y'] = NA

    # restrict to complete constellation ###
    if drop:
        m = m.dropna()
        if window is None:
            # only keep co-occurrences that are within context
            m = m.loc[
                (m['matchend_y'] >= m['context']) & (m['match_y'] < m['contextend'])
            ]
        else:
            m = m.loc[abs(m['offset_y']) <= window]

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


def aggregate_matches(df, name, context_col='contextid',
                      match_cols=['match', 'matchend']):

    # counts
    counts = DataFrame(df[context_col].value_counts()).astype("Int64")
    counts.columns = ['COUNTS_' + name]

    # matches
    matches = df.reset_index()
    matches['MATCHES_' + name] = matches[match_cols].values.tolist()
    matches['MATCHES_' + name] = matches['MATCHES_' + name].apply(tuple)
    matches = matches.groupby('contextid', group_keys=True)['MATCHES_' + name].apply(set)

    # combine
    table = counts.join(matches)

    return table


def format_roles(row, names, s_show, window, htmlify_meta=False):
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

    # TODO directly create relevant objects, no need for frontend to take care of it
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

        if not isinstance(row[name], float):
            for t in row[name]:

                # check match information
                if len(t) == 2:
                    # lazy definition without offset
                    start = 0
                    end = 1
                elif len(t) == 3:
                    # with offset
                    start = 1
                    end = 2
                else:
                    continue

                # skip NAs
                if not isinstance(t[start], int):
                    continue

                # skip the ones too far away
                try:
                    start = d['cpos'].index(t[start])
                    end = d['cpos'].index(t[end]) + 1
                except ValueError:
                    continue

                for i in range(start, end):
                    role[i] = name

        roles.append(role)

    # combine individual roles into one list of lists
    d['role'] = [[a for a in set(r) if a is not None] for r in list(zip(*roles))]

    # add s-attributes
    if htmlify_meta:
        meta = {key: row[key] for key in s_show if not key.startswith("BOOL")}
        d['meta'] = DataFrame.from_dict(
            meta, orient='index'
        ).to_html(bold_rows=False, header=False)
        for s in s_show:
            if s.startswith("BOOL"):
                d[s] = row[s]
    else:
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

    def add_discourseme(self, dump, name='discourseme', drop=True, window=None):
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
        self.df = constellation_left_join(self.df, dump.df, name,
                                          drop=drop, window=window)

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
                    htmlify_meta=False):
        """Retrieve concordance lines for constellation.

        :param int window: cpos further away from node will be marked 'out_of_window'

        :return: concordance lines
        :rtype: list
        """

        # convert dataframe
        df = self.group_lines()

        # cut off and sampling (done here to be able to use random_seed)
        cut_off = len(df) if cut_off is None or cut_off > len(df) else cut_off
        if order == 'random':
            df = df.sample(cut_off, random_state=random_seed)
        elif order == 'first':
            df = df.head(cut_off)
        elif order == 'last':
            df = df.head(cut_off)
        else:
            raise NotImplementedError

        # retrieve concordance lines
        conc = Concordance(self.corpus.copy(), df)
        lines = conc.lines(form='dict', p_show=p_show, s_show=s_show,
                           order=order, cut_off=cut_off)

        # map roles
        output = lines.apply(
            lambda row: format_roles(
                row, self.discoursemes.keys(), s_show, window, htmlify_meta
            ), axis=1
        )

        return list(output)

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

        logger.info('get cpos that are consumed by discoursemes')
        for idx in self.discoursemes.keys():
            f1_set.update(self.discoursemes[idx].matches())
        df_cooc = df_cooc.loc[~df_cooc['cpos'].isin(f1_set)]

        # count node freqs
        node_freq = self.corpus.counts.cpos(f1_set, p_show)

        # determine collocates
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

        if isinstance(dump, dict):
            dumps = dump.copy()
            name = list(dumps.keys())[0]
            dump = dumps.pop(name)

        elif isinstance(dump, Dump):
            dumps = {}

        else:
            raise ValueError()

        # create
        self.s_context = s_context
        self.corpus = dump.corpus
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
            logger.error('name "%s" already taken; cannot register discourseme' % name)
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

    def concordance(self, window=0,
                    p_show=['word', 'lemma'], s_show=[],
                    order='random', cut_off=100, random_seed=42,
                    htmlify_meta=False, form='list'):

        # cut off and sampling
        cut_off = len(self.df) if cut_off is None or cut_off > len(self.df) else cut_off
        if order == 'random':
            df = self.df.sample(cut_off, random_state=random_seed)
        elif order == 'first':
            df = self.df.head(cut_off)
        elif order == 'last':
            df = self.df.head(cut_off)
        else:
            raise NotImplementedError

        # join context..contextend
        contexts = self.corpus.dump_from_s_att(self.s_context, annotation=False)
        contexts.columns = ['contextid']
        contexts = contexts.reset_index().set_index('contextid')
        df = df.join(contexts).set_index(['match', 'matchend'])

        # retrieve concordance lines
        conc = Concordance(self.corpus.copy(), df)
        lines = conc.lines(form='dict', p_show=p_show, s_show=s_show,
                           order=order, cut_off=cut_off)

        # get boolean columns for each discourseme
        names_bool = list()
        for name in [c for c in df.columns if c.startswith("COUNTS_")]:
            name_bool = '_'.join(['BOOL', name.split("COUNTS_")[-1]])
            names_bool.append(name_bool)
            lines[name_bool] = (lines[name] > 0)
            lines[name_bool] = lines[name_bool].fillna(False)

        # format roles
        match_cols = [c for c in lines.columns if c.startswith("MATCHES_")]
        match_names = [c.split("MATCHES_")[-1] for c in match_cols]
        col_mapper = dict(zip(match_cols, match_names))
        lines = lines.rename(columns=col_mapper)

        if form == 'table':
            return lines
        elif form == 'list':
            output = lines.apply(
                lambda row: format_roles(
                    row, match_names, s_show=names_bool+s_show, window=window, htmlify_meta=htmlify_meta
                ), axis=1
            )
            return list(output)
        else:
            raise NotImplementedError()

    def associations(self, ams=None, frequencies=True,
                     min_freq=2, order='log_likelihood',
                     cut_off=None):

        counts = self.df[[c for c in self.df.columns if c.startswith("COUNTS_")]]
        counts.columns = [c.split("COUNTS_")[-1] for c in counts.columns]
        cooc = counts > 0

        # TODO triangular matrix
        tables = DataFrame()
        for name in counts.columns:
            table = round(textual_associations(
                cooc, self.N, name
            ).reset_index(), 2)
            table['node'] = name
            tables = concat([tables, table])

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
    measures = score(contingencies, freq=True)
    contingencies = contingencies.join(measures.drop(['N'], axis=1))

    return contingencies


########################################################
# CONSTELLATION CREATION FROM DISCOURSEMES AND QUERIES
# TODO parallelize
########################################################
def create_constellation(corpus_name,
                         # discoursemes
                         topic_discourseme,
                         filter_discoursemes,
                         additional_discoursemes,
                         # context settings
                         s_context,
                         context=20,
                         # query settings
                         p_query='word',
                         s_query=None,
                         flags='%cd',
                         escape=True,
                         match_strategy='longest',
                         # CWB settings
                         lib_path=None,
                         cqp_bin='cqp',
                         registry_path='/usr/local/share/cwb/registry/',
                         data_path='/tmp/ccc-data/',
                         window=None,
                         approximate=False):
    """simple constellation creator. returns a Constellation() if a
    topic_discourseme is given, otherwise a TextConstellation(). Note
    that for TextConstellations, there is no difference between
    additional discoursemes and filter discoursemes (instead, a
    boolean column for each discourseme is added).

    :param dict topic_discourseme: used for init
    :param dict filter_discoursemes: inner join
    :param dict additional_discourseme: left join

    """

    # pre-process parameters
    s_context = s_query if not s_context else s_context
    s_query = s_context if s_query is None else s_query

    # init corpus
    corpus = Corpus(corpus_name, lib_path, cqp_bin, registry_path, data_path)

    # topic -> Constellation()
    if len(topic_discourseme) > 0:

        if len(topic_discourseme) > 1:
            raise ValueError("only one topic discourseme can be given")

        # init with topic
        topic_name = list(topic_discourseme.keys())[0]
        topic_items = topic_discourseme[topic_name]
        topic_query = format_cqp_query(
            topic_items, p_query=p_query, s_query=s_query, flags=flags, escape=escape
        )
        topic_dump = corpus.query(
            topic_query,
            context=context,
            context_break=s_context,
            match_strategy=match_strategy
        )
        const = Constellation(topic_dump, topic_name)

        if approximate:
            sub = topic_dump.df.set_index(['context', 'contextend'])
            corpus.activate_subcorpus(nqr='TempRestriction', df_dump=sub)
        # add filter discoursemes
        for disc_name, disc_items in filter_discoursemes.items():
            disc_query = format_cqp_query(
                disc_items, p_query=p_query, s_query=s_query, flags=flags, escape=escape
            )
            disc_dump = corpus.query(
                disc_query,
                context=None,
                context_break=s_context,
                match_strategy=match_strategy
            )
            if len(disc_dump.df) > 0:
                const.add_discourseme(disc_dump, disc_name, drop=True, window=window)
            else:
                raise ValueError()

        # add additional discoursemes
        for disc_name, disc_items in additional_discoursemes.items():
            disc_query = format_cqp_query(
                disc_items, p_query=p_query, s_query=s_query, flags=flags, escape=escape
            )
            disc_dump = corpus.query(
                disc_query,
                context=None,
                context_break=s_context,
                match_strategy=match_strategy
            )
            if len(disc_dump.df) > 0:
                const.add_discourseme(disc_dump, disc_name, drop=False)
        corpus.activate_subcorpus()

    # no topic -> TextConstellation()
    else:

        # no filter implemented: all discoursemes are equal
        discoursemes = {**filter_discoursemes, **additional_discoursemes}

        # init with arbitrary topic
        topic_name = list(discoursemes.keys())[0]
        topic_items = discoursemes.pop(topic_name)
        topic_query = format_cqp_query(
            topic_items, p_query=p_query, s_query=s_query, flags=flags, escape=escape
        )
        topic_dump = corpus.query(
            topic_query,
            context=context,
            context_break=s_context,
            match_strategy=match_strategy
        )
        const = TextConstellation(topic_dump, s_context, topic_name)

        # add further discoursemes
        for disc_name, disc_items in discoursemes.items():
            disc_query = format_cqp_query(
                disc_items, p_query=p_query, s_query=s_query, flags=flags, escape=escape
            )
            disc_dump = corpus.query(
                disc_query,
                context=None,
                context_break=s_context,
                match_strategy=match_strategy
            )
            const.add_discourseme(disc_dump, disc_name)

    return const


def create_constellation_query(corpus_name,
                               # discoursemes
                               topic_discourseme,
                               filter_discoursemes,
                               additional_discoursemes,
                               # context settings
                               s_context,
                               context=20,
                               # CWB settings
                               match_strategy='longest',
                               lib_path=None,
                               cqp_bin='cqp',
                               registry_path='/usr/local/share/cwb/registry/',
                               data_path='/tmp/ccc-data/',
                               window=None):
    """same as above, but with pre-formatted CQP queries

    """

    # init corpus
    corpus = Corpus(corpus_name, lib_path, cqp_bin, registry_path, data_path)

    # topic -> Constellation()
    if len(topic_discourseme) > 0:

        if len(topic_discourseme) > 1:
            raise ValueError("only one topic discourseme can be given")

        # init with topic
        topic_name = list(topic_discourseme.keys())[0]
        topic_query = topic_discourseme[topic_name]
        topic_dump = corpus.query(
            topic_query,
            context=context,
            context_break=s_context,
            match_strategy=match_strategy
        )
        const = Constellation(topic_dump, topic_name)

        # add filter discoursemes
        for disc_name, disc_query in filter_discoursemes.items():
            disc_dump = corpus.query(
                disc_query,
                context=None,
                context_break=s_context,
                match_strategy=match_strategy
            )
            const.add_discourseme(disc_dump, disc_name, drop=True, window=window)

        # add additional discoursemes
        for disc_name, disc_query in additional_discoursemes.items():
            disc_dump = corpus.query(
                disc_query,
                context=None,
                context_break=s_context,
                match_strategy=match_strategy
            )
            const.add_discourseme(disc_dump, disc_name, drop=False)

    # no topic -> TextConstellation()
    else:

        # no filter implemented: all discoursemes are equal
        discoursemes = {**filter_discoursemes, **additional_discoursemes}

        # init with arbitrary topic
        topic_name = list(discoursemes.keys())[0]
        topic_query = discoursemes.pop(topic_name)
        topic_dump = corpus.query(
            topic_query,
            context=context,
            context_break=s_context,
            match_strategy=match_strategy
        )
        const = TextConstellation(topic_dump, s_context, topic_name)

        # add further discoursemes
        for disc_name, disc_query in discoursemes.items():
            disc_dump = corpus.query(
                disc_query,
                context=None,
                context_break=s_context,
                match_strategy=match_strategy
            )
            const.add_discourseme(disc_dump, disc_name)

    return const
