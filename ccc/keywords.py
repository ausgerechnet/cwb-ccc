#! /usr/bin/env python
# -*- coding: utf-8 -*-

# logging
import logging

# requirements
from pandas import DataFrame

# part of module
from .counts import score_counts

logger = logging.getLogger(__name__)


class Keywords:
    """ keyword analysis """

    def __init__(self, corpus, df_dump, p_query=['lemma']):

        self.corpus = corpus

        # activate dump
        self.size = len(df_dump)

        # consistency check
        if self.size == 0:
            logger.warning('cannot calculate keywords on 0 regions')
            return

        # determine layer to work on
        self.p_query = [p_query] if isinstance(p_query, str) else p_query
        available_attributes = self.corpus.attributes_available['attribute'].values
        if not set(self.p_query).issubset(set(available_attributes)):
            logger.warning(
                'specfied p-attribute(s) ("%s") not available\n' % " ".join(self.p_query) +
                'falling back to primary layer'
            )
            self.p_query = ['word']

        # collect context and save result
        logger.info('collecting token counts of subcorpus')
        self.counts = corpus.counts.dump(
            df_dump, start='match', end='matchend', p_atts=self.p_query, split=True
        )

    def show(self, order='f', cut_off=100, ams=None,
             min_freq=2, frequencies=True, flags=None,
             marginals='corpus'):

        # consistency check
        if self.counts.empty:
            logger.warning("nothing to show")
            return DataFrame()

        # get subcorpus frequencies und apply min freq
        f = self.counts.rename(columns={'freq': 'f'})
        f1 = f['f'].sum()
        f = f.loc[f['f'] >= min_freq]

        # get reference frequency
        if isinstance(marginals, str):
            if marginals == 'corpus':
                N = self.corpus.corpus_size
                marginals = self.corpus.marginals(f.index, self.p_query)
            else:
                raise NotImplementedError
        elif isinstance(marginals, DataFrame):
            # DataFrame must contain a column 'freq'
            N = marginals['freq'].sum()
        else:
            raise NotImplementedError

        # create dataframe
        f2 = marginals[['freq']].rename(columns={'freq': 'f2'})
        df = f2.join(f)
        df['f1'] = f1
        df['N'] = N

        # score
        keywords = score_counts(df, order, cut_off, flags, ams)

        return keywords
