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
import logging
logger = logging.getLogger(__name__)


class Disc:
    """
    realization of a discourseme given a corpus and query parameters
    """

    def __init__(self, corpus, items, p_query, s_query, s_context,
                 context=20, flags="%cd", escape=False):
        """
        .items
        .parameters
        .idx
        .dump
        """

        self.items = items

        self.parameters = {
            'p_query': p_query,
            's_query': s_query,
            's_context': s_context,
            'context': context,
            'flags': flags,
            'escape': escape
        }

        # run query
        query = formulate_cqp_query(
            items, p_query, s_query, flags, escape
        )
        dump = corpus.query(
            query, context, context_break=s_context
        )
        self.dump = dump
        self.idx = dump.name_cache

        self._context = None
        self._matches = None

    def concordance(self, context=None, matches=None,
                    p_show=['word'], s_show=[], order='random',
                    cut_off=100, form='dataframes'):

        # deal with context
        if context is None:
            context = self.parameters['context']
        if context > self.parameters['context']:
            logger.warning(
                "out of context; falling back to context=%d" %
                self.parameters['context']
            )
            context = self.parameters['context']
            df = self.dump.df
        elif context < self.parameters['context']:
            df = self.dump.df.reset_index()
            df['context_new'] = df['match'] - context
            df['contextend_new'] = df['matchend'] + context
            df['context'] = df[['context', 'context_new']].max(axis=1)
            df['contextend'] = df[['contextend', 'contextend_new']].min(axis=1)
            df = df.drop(['context_new', 'contextend_new'], axis=1)
            df = df.set_index(['match', 'matchend'])
        else:
            df = self.dump.df

        conc = Concordance(self.dump.corpus.copy(), df)
        return conc.lines(
            matches=matches, p_show=p_show, s_show=s_show,
            p_text=None, p_slots=None, slots=[], order=order,
            cut_off=cut_off, form=form
        )

    def collocates(self, window=5, order='f', cut_off=100,
                   p_query="lemma", ams=None, min_freq=2,
                   frequencies=True, flags=None):

        coll = Collocates(self.dump.corpus.copy(), self.dump.df, p_query)
        return coll.show(
            window=window, order=order, cut_off=cut_off, ams=ams,
            min_freq=min_freq, frequencies=frequencies, flags=flags
        )


class DiscCon:
    """
    realization of a discursive position given a topic and discoursemes
    discoursemes can be added after initialization
    """

    def __init__(self, topic, discoursemes=[], name='Last'):
        """
        .topic
        .corpus
        .parameters
        .name

        .discoursemes: dict of Discs with key == Disc.idx

        .df_nodes = dict of df_nodes with key == window
        """

        self.topic = topic

        # TODO: start independent CQP process
        self.corpus = topic.dump.corpus
        self.parameters = topic.parameters
        self.name = name

        self.discoursemes = dict()
        for d in discoursemes:
            self.add_disc(d)

        self.df_nodes = dict()

    def add_disc(self, disc):

        if disc.idx in self.discoursemes.keys():
            logger.warning("discourseme already associated to discursive position")
        else:
            self.discoursemes[disc.idx] = disc
            self.df_nodes = dict()  # reset df nodes

    def add_items(self, items):

        disc = Disc(
            corpus=self.corpus.copy(),
            items=items,
            **self.parameters
        )
        self.add_disc(disc)
        return disc.idx

    def slice_discs(self, window=None):
        """ intersects all discoursemes
        :return: df_nodes with topic match, matchend,
        context_id, context, contextend, match_disc1_idx, matchend_disc1_idx, ...
        """

        if window is None:
            window = self.topic.parameters['context']

        df_nodes = self.topic.dump.df.reset_index()

        for disc in self.discoursemes.values():
            # get dump
            df = disc.dump.df.reset_index()
            df = df.drop(['context', 'contextend'], axis=1)
            # merge nodes; NB: this adds duplicates where necessary
            df_nodes = merge(df_nodes, df, on='context_id')
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

    def concordance(self, window=5, matches=None,
                    p_show=['word'], s_show=[], order='random',
                    cut_off=100, form='dataframes'):

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
        # TODO SPEEEEEEED UPPPP!!!!!
        all_matches = set(df_nodes['match'])
        rows = list()
        for match in all_matches:
            row = dict()
            df_loc = df_nodes.loc[df_nodes.match == match]
            row['match'] = match
            row['matchend'] = df_loc.iloc[0]['matchend']
            row['context_id'] = df_loc.iloc[0]['context_id']
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
            p_text=None, p_slots=None, slots=[], order=order,
            cut_off=cut_off, form=form
        )

        logger.info("inserting discourseme and window/context info")
        # TODO mark out of context
        dfs = list()
        for line in lines.iterrows():
            df = line[1]['df']
            # indicate topic matches
            match, matchend = line[0]
            df[self.topic.idx] = df.index.isin(set(range(match, matchend + 1)))
            # indicate discourseme matches
            for idx in disc_ids:
                df[idx] = df.index.isin(line[1][idx])
            df = df.drop(['match', 'matchend', 'context', 'contextend'], axis=1)
            dfs.append(df)
        lines['df'] = dfs

        return lines

    def collocates(self, window=5, order='f', cut_off=100,
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
        for idx in self.discoursemes:
            logger.info('excluding discourseme "%s" from context' % idx)
            matches = self.discoursemes[idx].dump.matches()
            f1_set.update(matches)
            df_cooc = df_cooc.loc[~df_cooc['cpos'].isin(f1_set)]

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
