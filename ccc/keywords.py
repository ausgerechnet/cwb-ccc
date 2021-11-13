#! /usr/bin/env python
# -*- coding: utf-8 -*-

# part of module
from .counts import score_counts_signature
# requirements
from pandas import DataFrame
# logging
import logging
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

        # TODO: also comprises s-att -- implement convenient retrieval
        p_available = set(self.corpus.attributes_available['attribute'].values)
        if not set(self.p_query).issubset(p_available):
            logger.warning(
                'specfied p-attribute(s) (%s) not available' % " ".join(self.p_query)
            )
            logger.warning('falling back to primary layer')
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

        # get subcorpus frequencies
        f = self.counts.loc[self.counts['freq'] >= min_freq]
        f1 = self.counts['freq'].sum()

        # get reference frequency
        if isinstance(marginals, str):
            if marginals == 'corpus':
                N = self.corpus.corpus_size
                if len(self.p_query) == 1:
                    marginals = self.corpus.marginals(
                        f[self.p_query[0]], self.p_query[0]
                    )
                else:
                    marginals = self.corpus.marginals_complex(
                        f[self.p_query], self.p_query
                    )
            else:
                raise NotImplementedError
        elif isinstance(marginals, DataFrame):
            # DataFrame must contain a column 'freq'
            N = marginals['freq'].sum()
        else:
            raise NotImplementedError

        # score
        keywords = score_counts_signature(
            f[['freq']], f1, marginals[['freq']], N,
            min_freq, order, cut_off, flags, ams, frequencies
        )

        return keywords
