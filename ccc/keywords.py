#! /usr/bin/env python
# -*- coding: utf-8 -*-

from .collocates import add_ams
from pandas import DataFrame
import logging
logger = logging.getLogger(__name__)


class Keywords:
    """ calculating collocates """

    def __init__(self, corpus, df_node, p_query):

        if len(df_node) == 0:
            logger.warning('cannot calculate keywords on 0 regions')
            return

        self.corpus = corpus
        self.df_node = df_node
        self.size = len(df_node)
        if p_query not in self.corpus.attributes_available['value'].values:
            logger.warning(
                'p_att "%s" not available, falling back to primary layer' % p_query
            )
            p_query = 'word'
        self.p_query = p_query

        logger.info('collecting token counts of subcorpus')
        counts = corpus.regions2counts(df_node, p_att=p_query)
        counts.columns = ['O11']

        self.counts = counts

    def show(self, order='O11', cut_off=100, ams=None,
             drop_hapaxes=True):

        if ams is None:
            ams = [
                'z_score', 't_score', 'dice',
                'log_likelihood', 'mutual_information'
            ]

        if self.counts.empty:
            return DataFrame()

        f1 = self.counts['O11'].sum()

        # drop hapax legomena for improved performance
        if drop_hapaxes:
            counts = self.counts.loc[~(self.counts['O11'] <= 1)]

        # get marginals
        f2 = self.corpus.marginals(
            counts.index, self.p_query
        )
        f2.columns = ['f2']
        contingencies = counts.join(f2)

        # add constant columns
        contingencies['N'] = self.corpus.corpus_size
        contingencies['f1'] = f1

        # add measures
        keywords = add_ams(contingencies, ams)

        # sort dataframe
        keywords.sort_values(
            by=[order, 'item'],
            ascending=False, inplace=True
        )

        if cut_off is not None:
            keywords = keywords.head(cut_off)

        return keywords
