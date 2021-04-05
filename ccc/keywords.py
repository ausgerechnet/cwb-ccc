#! /usr/bin/env python
# -*- coding: utf-8 -*-

# part of module
from .collocates import add_ams
# requirements
from pandas import DataFrame, MultiIndex
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
        counts = corpus.counts.dump(
            df_dump, start='match', end='matchend', p_atts=self.p_query, split=True
        )
        counts.columns = ['f']

        self.counts = counts

    def show(self, order='f', cut_off=100, ams=None,
             min_freq=2, frequencies=True, flags=None,
             marginals='corpus'):

        # consistency check
        if self.counts.empty:
            logger.warning("nothing to show")
            return DataFrame()

        # get frequencies
        f = self.counts.loc[self.counts['f'] >= min_freq]

        # determine reference frequency
        if isinstance(marginals, str):
            N = self.corpus.corpus_size
            # get marginals
            if marginals == 'corpus':
                if len(self.p_query) == 1:
                    # coerce to multiindex (what was I thinking?)
                    f2 = self.corpus.marginals(
                        f.index.get_level_values(self.p_query[0]), self.p_query[0]
                    )
                    f2.index = MultiIndex.from_tuples(
                        f2.index.map(lambda x: (x, )), names=self.p_query
                    )
                else:
                    f2 = self.corpus.marginals_complex(f.index, self.p_query)
                f2.columns = ['f2']
            else:
                raise NotImplementedError

        elif isinstance(marginals, DataFrame):
            f2 = marginals
            f2.columns = ['f2']
            N = f2['f2'].sum()

        else:
            raise NotImplementedError

        # get sub-corpus size
        f1 = self.counts['f'].sum()

        keywords = add_ams(
            f, f1, f2, N,
            min_freq, order, cut_off, flags, ams, frequencies
        )

        # deal with index
        if len(self.p_query) == 1:
            keywords.index = keywords.index.map(lambda x: x[0])
            keywords.index.name = self.p_query[0]

        return keywords
