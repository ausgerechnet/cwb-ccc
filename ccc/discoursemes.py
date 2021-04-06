#! /usr/bin/env python
# -*- coding: utf-8 -*-

# part of module
from ccc.utils import formulate_cqp_query, calculate_offset
from ccc.collocates import df_node_to_cooc, add_ams
from ccc.concordances import Concordance
from ccc.collocates import Collocates
# requirements
from pandas import merge, DataFrame
# logging
from .utils import time_it
import logging
logger = logging.getLogger(__name__)


class Discourseme:
    """
    realization of a discourseme with context in a corpus
    """

    def __init__(self, corpus, items, p_query, s_query, flags="%cd", escape=False):
        """
        .nodes
        .idx
        .dump
        """

        self.nodes = {
            'items': items,
            'p_query': p_query,
            's_query': s_query,
            'flags': flags,
            'escape': escape,
            'corpus': corpus.corpus_name
        }
        self.query = formulate_cqp_query(items, p_query, s_query, flags, escape)
        self.idx = corpus.cache.generate_idx(self.nodes.values(), prefix='nodes_')
        self.dump = corpus.query(self.query, context=None, context_break=s_query)

    def concordance(self, context=None, context_left=None,
                    context_right=None, context_break=None,
                    p_show=['word'], s_show=[], order='random',
                    cut_off=100, matches=None, form='dataframe'):

        self.dump.set_context(context, context_break,
                              context_left, context_right)

        return self.dump.concordance(
            matches=matches, p_show=p_show, s_show=s_show,
            slots=[], order=order,
            cut_off=cut_off, form=form
        )

    def collocates(self, window_sizes=[3, 5, 7], context_break=None,
                   order='log_likelihood', cut_off=100,
                   p_query="lemma", ams=None, min_freq=2,
                   frequencies=True, flags=None):

        # determine mode and mws
        if type(window_sizes) is int:
            single = True
            mws = window_sizes
        elif type(window_sizes) is list:
            single = False
            mws = max(window_sizes)
        else:
            raise NotImplementedError("window_sizes must be int or list")

        self.dump.set_context(context=mws, context_break=context_break)

        coll = Collocates(
            corpus=self.dump.corpus.copy(),
            df_dump=self.dump.df,
            p_query=p_query,
            mws=mws
        )

        if single:
            return coll.show(
                window=mws, order=order, cut_off=cut_off, ams=ams,
                min_freq=min_freq, frequencies=frequencies, flags=flags
            )

        else:
            collocates = dict()
            for window in window_sizes:
                collocates[window] = coll.show(
                    window=window, order=order, cut_off=cut_off, ams=ams,
                    min_freq=min_freq, frequencies=frequencies, flags=flags
                )
            return collocates


class DiscoursemeConstellation:
    """
    realization of a discourseme constellation given a topic and discoursemes

    discoursemes can be added after initialization
    """

    def __init__(self, topic, discoursemes={}, name='Last'):
        """
        .topic
        .corpus
        .nodes
        .name

        .discoursemes: dict of Discs with key == Disc.idx
        .df_nodes = dict of df_nodes with key == window
        """

        self.topic = topic

        self.corpus = topic.dump.corpus
        self.nodes = topic.nodes
        self.name = name

        self.discoursemes = dict()
        for d in discoursemes:
            self.add_disc(d)

        self.df_nodes = dict()

    def add_disc(self, disc):

        if disc.idx in self.discoursemes.keys():
            logger.warning("discourseme already included in constellation")
        else:
            self.discoursemes[disc.idx] = disc
            self.df_nodes = dict()  # reset df_nodes

    def add_items(self, items):

        disc = Discourseme(
            corpus=self.corpus.copy(),
            items=items,
            **{i: self.nodes[i] for i in self.nodes if i not in ['corpus', 'items']}
        )
        self.add_disc(disc)
        return disc.idx

    @time_it
    def slice_discs(self, window=5, context_break=None):
        """ intersects all discoursemes
        :return: df_nodes indexed by topic-matches:

        == (m, m-end) c-id, c, c-end, m_d1, m-e_d1, ... ==

        with duplicates for each match, matchend where necessary
        """

        topic_dump = self.topic.dump
        topic_dump.set_context(context=window, context_break=context_break)
        df_nodes = topic_dump.df.reset_index()

        for disc in self.discoursemes.values():

            df = disc.dump.df.reset_index()
            df = df.drop(['context', 'contextend'], axis=1)
            # merge nodes; NB: this adds duplicates where necessary
            # s_break = self.topic.nodes['s_query'] + '_cwbid'
            s_break = 'contextid'
            df_nodes = merge(df_nodes, df, on=s_break)
            # remove lines where items are too far away
            df_nodes['offset'] = df_nodes.apply(calculate_offset, axis=1)
            df_nodes = df_nodes[
                abs(df_nodes['offset']) <= window
            ]
            df_nodes = df_nodes.rename(columns={
                'match_x': 'match',
                'matchend_x': 'matchend',
                'match_y': 'match_' + disc.idx,
                'matchend_y': 'matchend_' + disc.idx,
                'offset': 'offset_' + disc.idx
            })

        self.df_nodes[window] = df_nodes

        return df_nodes

    @time_it
    def concordance(self, window=5, matches=None,
                    p_show=['word'], s_show=[], order='random',
                    cut_off=100, form='dataframe'):

        """ self.df_nodes has duplicate entries
        (1) convert to (match matchend) disc_1_set disc_2_set ...
        (2) convert each line to dataframe
        """

        # make sure we're having the right context
        if window not in self.df_nodes.keys():
            df_nodes = self.slice_discs(window).copy()
        else:
            df_nodes = self.df_nodes[window]

        # get ids of all discoursemes
        disc_ids = set(self.discoursemes.keys())

        logger.info("converting discourse nodes to regular dump")
        # TODO speed up
        all_matches = set(df_nodes['match'])
        rows = list()
        for match in all_matches:
            row = dict()
            df_loc = df_nodes.loc[df_nodes.match == match]
            row['match'] = match
            row['matchend'] = df_loc.iloc[0]['matchend']
            row['context id'] = df_loc.iloc[0]['contextid']
            row['context'] = df_loc.iloc[0]['context']
            row['contextend'] = df_loc.iloc[0]['contextend']
            for idx in disc_ids:
                disc_f1 = set()
                for a, b in zip(df_loc['match_' + idx], df_loc['matchend_' + idx]):
                    disc_f1.update(range(a, b + 1))
                row[idx] = disc_f1
            rows.append(row)
        df = DataFrame(rows)
        df = df.set_index(["match", "matchend"])

        logger.info("converting each line to dataframe")
        conc = Concordance(self.corpus.copy(), df)
        lines = conc.lines(
            matches=matches, p_show=p_show, s_show=s_show,
            slots=[], order=order,
            cut_off=cut_off, form=form
        )

        logger.info("inserting discourseme and window/context info")
        # TODO mark out of context
        dfs = list()
        for line in lines.iterrows():
            df = line[1]['dataframe']
            # indicate topic matches
            match, matchend = line[0]
            df[self.topic.idx] = df.index.isin(set(range(match, matchend + 1)))
            # indicate discourseme matches
            for idx in disc_ids:
                df[idx] = df.index.isin(line[1][idx])
            # df = df.drop(['match', 'matchend', 'context', 'contextend'], axis=1)
            dfs.append(df)
        lines['dataframe'] = dfs

        return lines

    @time_it
    def collocates(self, window=5, order='log_likelihood', cut_off=100,
                   p_query="lemma", ams=None, min_freq=2,
                   frequencies=True, flags=None):

        # make sure we're having the right context
        if window not in self.df_nodes.keys():
            df_nodes = self.slice_discs(window)
        else:
            df_nodes = self.df_nodes[window]

        # get and correct df_cooc, f1_set
        df_cooc, f1_set = df_node_to_cooc(df_nodes)

        if len(f1_set) == 0:
            logger.warning("no matches")
            return DataFrame()

        # check for presence of topic in topic context
        # NB: this is necessary since we might have excluded
        # some occurrences of the topic from df_nodes
        # when selecting relevant instances in the constellation
        logger.info('searching for topic discourseme in topic context')
        f1_set = self.topic.dump.matches()

        # check for presence of discoursemes in topic context
        for idx in self.discoursemes:
            logger.info('searching for discourseme "%s" in topic context' % idx)
            matches = self.discoursemes[idx].dump.matches()
            f1_set.update(matches)

        logger.info("excluding all discourseme matches from context")
        df_cooc = df_cooc.loc[~df_cooc['cpos'].isin(f1_set)]

        # moving to requested window
        relevant = df_cooc.loc[abs(df_cooc['offset']) <= window]

        # number of possible occurrence positions within window
        f1_inflated = len(relevant)

        # get frequency counts
        f = self.corpus.counts.cpos(
            relevant['cpos'], [p_query]
        )
        f.columns = ['f']
        f.index = f.index.get_level_values(p_query)

        # get marginals
        f2 = self.corpus.marginals(
            f.index, p_query
        )
        f2.columns = ['marginal']

        # deduct node frequencies from marginals
        logger.info("deducting node frequencies")
        node_freq = self.corpus.counts.cpos(f1_set, [p_query])
        node_freq.index = node_freq.index.get_level_values(p_query)
        node_freq.columns = ['in_nodes']
        f2 = f2.join(node_freq)
        f2 = f2.fillna(0)
        f2['in_nodes'] = f2['in_nodes'].astype(int)
        f2['f2'] = f2['marginal'] - f2['in_nodes']

        # get sub-corpus size
        f1 = f1_inflated

        # get corpus size
        N = self.corpus.corpus_size - len(f1_set)

        collocates = add_ams(
            f, f1, f2, N,
            min_freq, order, cut_off, flags, ams, frequencies
        )

        return collocates

    # def collocates_range(self, windows=[3, 5, 7, 10], order='f', cut_off=100,
    #                      p_query="lemma", ams=None, min_freq=2,
    #                      frequencies=True, flags=None):

    #     # sort windows and start with largest
    #     windows = sorted(windows, reverse=True)
    #     max_window = windows[0]

    #     # make sure we're having the right context
    #     if max_window not in self.df_nodes.keys():
    #         df_nodes = self.slice_discs(max_window)
    #     else:
    #         df_nodes = self.df_nodes[max_window]

    #     # get and correct df_cooc, f1_set
    #     df_cooc, f1_set = df_node_to_cooc(df_nodes)

    #     if len(f1_set) == 0:
    #         logger.warning("no matches")
    #         return DataFrame()

    #     # check for presence of topic in topic context
    #     # NB: this is necessary since we might have excluded
    #     # some occurrences of the topic from df_nodes
    #     # when selecting relevant instances in the constellation
    #     logger.info('searching for topic discourseme in topic context')
    #     f1_set = self.topic.dump.matches()

    #     # check for discoursemes in topic context
    #     for idx in self.discoursemes:
    #         logger.info('searching for discourseme "%s" in topic context' % idx)
    #         matches = self.discoursemes[idx].dump.matches()
    #         f1_set.update(matches)
    #         df_cooc = df_cooc.loc[~df_cooc['cpos'].isin(f1_set)]

    #     logger.info("excluding all discourseme matches from context")
    #     df_cooc = df_cooc.loc[~df_cooc['cpos'].isin(f1_set)]

    #     # do it once for max_window
    #     relevant = df_cooc.loc[abs(df_cooc['offset']) <= max_window]

    #     # number of possible occurrence positions within window
    #     f1_inflated = len(relevant)

    #     # get frequency counts
    #     f = self.corpus.counts.cpos(
    #         relevant['cpos'], [p_query]
    #     )
    #     f.columns = ['f']
    #     f.index = f.index.get_level_values(p_query)

    #     # get marginals
    #     f2 = self.corpus.marginals(
    #         f.index, p_query
    #     )
    #     f2.columns = ['marginal']

    #     # deduct node frequencies from marginals
    #     logger.info("deducting node frequencies")
    #     node_freq = self.corpus.counts.cpos(f1_set, [p_query])
    #     node_freq.index = node_freq.index.get_level_values(p_query)
    #     node_freq.columns = ['in_nodes']
    #     f2 = f2.join(node_freq)
    #     f2 = f2.fillna(0)
    #     f2['in_nodes'] = f2['in_nodes'].astype(int)
    #     f2['f2'] = f2['marginal'] - f2['in_nodes']

    #     # get sub-corpus size
    #     f1 = f1_inflated

    #     # get corpus size
    #     N = self.corpus.corpus_size - len(f1_set)

    #     collocates = add_ams(
    #         f, f1, f2, N,
    #         min_freq, order, cut_off, flags, ams, frequencies
    #     )

    #     # repeat for all other window sizes
    #     for w in windows[1:]:
    #         print(w)

    #     return collocates


# class DiscoursemeConstellation:

#     def __init__(self, topic, discoursemes={}, name='Last'):
#         """
#         :param DataFrame topic.dump.df: (match, matchend) context contextend contextid
#         :param Corpus topic.corpus: corpus with subcorpus = topic
#         :
#         .discoursemes: dict of Discs with key == Disc.idx
#         .df_nodes = dict of df_nodes with key == window
#         """

#         self.topic = topic

#         self.corpus = topic.dump.corpus
#         self.nodes = topic.nodes
#         self.name = name

#         self.discoursemes = dict()
#         for d in discoursemes:
#             self.add_disc(d)

#         self.df_nodes = dict()
