#! /usr/bin/env python
# -*- coding: utf-8 -*-

# part of module
from ccc.utils import formulate_cqp_query
from ccc.utils import merge_intervals
from ccc.utils import concordance_line2df
from ccc.collocates import df_node_to_cooc, add_ams
# requirements
from pandas import merge, DataFrame
# logging
import logging
logger = logging.getLogger(__name__)


class Disc:

    def __init__(self, corpus, items, p_query, s_query, s_context,
                 context=20, flags="%cd", escape=False, name=None):

        # TODO: start independent CQP process?
        self.corpus = corpus

        self.parameters = {
            'items': items,
            'p_query': p_query,
            's_query': s_query,
            's_context': s_context,
            'context': context,
            'flags': flags,
            'escape': escape
        }

        # run query
        query = formulate_cqp_query(items, p_query, s_query, flags, escape)
        self.dump, self.idx = corpus.query(
            query, context, s_context=s_context, return_name=True
        )

        # give the child a name
        self.name = name
        if self.name is None:
            self.name = self.idx

        self._context = None
        self._matches = None

    def matches(self):

        if self._matches is None:
            f1 = set()
            for match, matchend in self.dump.index:
                f1.update(range(match, matchend + 1))
            self._matches = f1

        return self._matches

    def context(self):

        if self._context is None:
            self._context = DataFrame.from_records(merge_intervals(
                self.dump[['context', 'contextend']].values.tolist()
            ), columns=['context', 'contextend'])

        return self._context

    def show_concordance(self, context=20, matches=None, p_show=['word'],
                         s_show=[], p_text=None, p_slots=None, regions=[],
                         order='first', cut_off=100, form='kwic'):

        if context > self.parameters['context']:
            logger.warning(
                "out of context; falling back to context=%d" %
                self.parameters['context']
            )
            context = self.parameters['context']
            df = self.dump
        elif context < self.parameters['context']:
            df = self.dump.reset_index()
            df['context_new'] = df['match'] - context
            df['contextend_new'] = df['matchend'] + context
            df['context'] = df[['context', 'context_new']].max(axis=1)
            df['contextend'] = df[['contextend', 'contextend_new']].min(axis=1)
            df = df.drop(['context_new', 'contextend_new'], axis=1)
            df = df.set_index(['match', 'matchend'])
        else:
            df = self.dump

        conc = self.corpus.concordance(df)
        return conc.lines(
            matches=matches, p_show=p_show, s_show=s_show,
            p_text=p_text, p_slots=p_slots, regions=regions, order=order,
            cut_off=cut_off, form=form
        )

    def show_collocates(self, window=5, order='f', cut_off=100,
                        p_query="lemma", ams=None, min_freq=2,
                        frequencies=True, flags=None):

        coll = self.corpus.collocates(self.dump, p_query)
        return coll.show(
            window=window, order=order, cut_off=cut_off, ams=ams,
            min_freq=min_freq, frequencies=frequencies, flags=flags
        )


class DiscPos:

    def __init__(self, topic, corpus, discoursemes):

        self.topic = topic
        self.discoursemes = discoursemes
        self.df_nodes = DataFrame()
        self.corpus = corpus

    def add_disc(self, disc):
        self.discoursemes.append(disc)

    def slice_discs(self, context=None):
        """ intersects all discoursemes
        :return: df_nodes with topic match, matchend,
        context_id, context, contextend, match_disc_1, matchend_disc_1, ...
        """
        if context is None:
            context = self.topic.parameters['context']

        df_nodes = self.topic.dump.reset_index()
        for disc in self.discoursemes:
            # get dump
            df = disc.dump.reset_index()
            df = df.drop(['context', 'contextend'], axis=1)
            # merge nodes; NB: this adds duplicates where necessary
            df_nodes = merge(df_nodes, df, on='context_id')
            # remove lines where items are too far away
            df_nodes['offset'] = df_nodes.apply(calculate_offset, axis=1)
            df_nodes = df_nodes[
                abs(df_nodes['offset']) <= context
            ]
            df_nodes = df_nodes.rename(columns={
                    'match_x': 'match',
                    'matchend_x': 'matchend',
                    'match_y': 'match_' + disc.name,
                    'matchend_y': 'matchend_' + disc.name,
                    'offset': 'offset_' + disc.name
            })

        self.df_nodes = df_nodes
        return df_nodes

    def show_concordance(self, context=20, matches=None,
                         p_show=['word'], order='random', cut_off=100):

        """ self.df_nodes has duplicate entries
        (1) convert to (match matchend) disc_1_set disc_2_set ...
        (2) convert each line to dataframe
        """

        self.slice_discs(context)  # make sure we're having the right context

        logger.info("converting discourse nodes to regular dump")
        matches = set(self.df_nodes['match'])
        rows = list()
        for match in matches:
            row = dict()
            df_loc = self.df_nodes.loc[self.df_nodes.match == match]
            disc_names = [
                c.split("offset_")[1] for c in df_loc.columns if c.startswith("offset_")
            ]
            row['match'] = match
            row['matchend'] = df_loc.iloc[0]['matchend']
            row['context_id'] = df_loc.iloc[0]['context_id']
            row['context'] = df_loc.iloc[0]['context']
            row['contextend'] = df_loc.iloc[0]['contextend']
            for disc in disc_names:
                disc_f1 = set()
                for a, b in zip(df_loc['match_' + disc], df_loc['matchend_' + disc]):
                    disc_f1.update(range(a, b + 1))
                row[disc] = disc_f1
            rows.append(row)
        df = DataFrame(rows)
        df = df.set_index(["match", "matchend"])

        logger.info("converting each line to dataframe")
        conc = self.corpus.concordance(df)
        lines = conc.lines(matches=matches, p_show=p_show, order=order,
                           cut_off=cut_off, form='dataframes')

        logger.info("inserting discourseme info")
        dfs = list()
        for line in lines.iterrows():
            df = line[1]['df']
            # indicate topic matches
            match, matchend = line[0]
            df[self.topic.name] = df.index.isin(set(range(match, matchend + 1)))
            # indicate discourseme matches
            for disc in disc_names:
                df[disc] = df.index.isin(line[1][disc])
            df = df.drop(['match', 'matchend', 'context', 'contextend'], axis=1)
            dfs.append(df)
        lines['df'] = dfs

        return lines

    def show_collocates(self, window=5, order='f', cut_off=100,
                        p_query="lemma", ams=None, min_freq=2,
                        frequencies=True, flags=None):

        self.slice_discs(window)  # make sure we're having the right context

        # get and correct df_cooc, f1_set
        df_cooc, f1_set = df_node_to_cooc(self.df_nodes)
        for disc in self.discoursemes:
            logger.info('excluding discourseme "%s" from context' % disc.name)
            matches = disc.matches()
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
        f2 = self.corpus.counts.marginals(
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


def calculate_offset(row):
    """ calculates offset of y to x """

    # necessary values
    match_x = row['match_x']
    match_y = row['match_y']

    # init matchends if necessary
    if 'matchend_x' in row.keys():
        matchend_x = row['matchend_x']
    else:
        matchend_x = match_x
    if 'matchend_y' in row.keys():
        matchend_y = row['matchend_y']
    else:
        matchend_y = match_y

    # y ... x
    if match_x > matchend_y:
        offset = matchend_y - match_x
    # x ... y
    elif matchend_x < match_y:
        offset = matchend_x - match_y
    # overlap
    else:
        offset = 0

    return offset
