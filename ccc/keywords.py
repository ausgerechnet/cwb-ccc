#! /usr/bin/env python
# -*- coding: utf-8 -*-

# part of module
from .utils import fold_df
# requirements
from pandas import DataFrame
from association_measures.measures import calculate_measures
import association_measures.frequencies as fq
# logging
import logging
logger = logging.getLogger(__name__)


class Keywords:
    """ calculating keywords """

    def __init__(self, corpus, name, df_node, p_query):

        self.corpus = corpus

        if df_node is not None:
            self.df_node = df_node
            self.size = len(df_node)
        elif name is not None:
            self.name = name
            self.df_node = corpus.cqp.Dump(name)
            self.size = int(corpus.cqp.Exec("size %s" % name))

        if self.size == 0:
            logger.warning('cannot calculate keywords on 0 regions')
            return

        if p_query not in corpus.attributes_available['value'].values:
            logger.warning(
                'p_att "%s" not available, falling back to primary layer' % p_query
            )
            p_query = 'word'
        self.p_query = p_query

        logger.info('collecting token counts of subcorpus')
        counts = corpus.count_matches(df=self.df_node, p_att=p_query, split=True)
        counts.columns = ['f']

        self.counts = counts

    def show(self, order='f', cut_off=100, ams=None,
             min_freq=2, frequencies=True, flags=None):

        if self.counts.empty:
            return DataFrame()

        f1 = self.counts['f'].sum()

        # drop items that occur less than min-freq
        counts = self.counts.loc[~(self.counts['f'] < min_freq)]

        # get marginals
        f2 = self.corpus.marginals(
            counts.index, self.p_query
        )
        f2.columns = ['f2']

        # join to contingency table
        contingencies = counts.join(f2)

        # post-processing: fold items
        contingencies = fold_df(contingencies, flags)

        # add constant columns
        contingencies['N'] = self.corpus.corpus_size
        contingencies['f1'] = f1
        # NB: frequency signature notation (Evert 2004: 36)

        # add measures
        if frequencies:
            keywords = contingencies.join(fq.observed_frequencies(contingencies))
            keywords = keywords.join(fq.expected_frequencies(keywords))
            keywords = keywords.join(calculate_measures(contingencies, ams))
        else:
            keywords = contingencies.join(calculate_measures(contingencies, ams))
        keywords.index.name = 'item'

        # sort dataframe
        keywords.sort_values(
            by=[order, 'item'],
            ascending=False, inplace=True
        )

        if cut_off is not None:
            keywords = keywords.head(cut_off)

        return keywords
