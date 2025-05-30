#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""keywords.py

Keywords class and keywords() method

"""
# logging
import logging

# requirements
from pandas import DataFrame

# part of module
from .cache import generate_idx
from .counts import score_counts

logger = logging.getLogger(__name__)


class Keywords:
    """ keyword analysis """

    def __init__(self, corpus, df_dump, p_query=['lemma'],
                 counts=None):

        # consistency check
        if df_dump is not None and len(df_dump) == 0:
            logger.warning('empty dump')
            return

        # init corpus
        self.corpus = corpus

        # determine layer to work on
        self.p_query = [p_query] if isinstance(p_query, str) else p_query
        available_attributes = self.corpus.available_attributes()['attribute'].values
        if not set(self.p_query).issubset(set(available_attributes)):
            logger.warning('specfied p-attribute(s) ("%s") not available' % " ".join(self.p_query))
            logger.warning('falling back to primary layer')
            self.p_query = ['word']

        # collect context and save result
        if df_dump is not None:

            # get from cache if possible
            identifier = generate_idx([df_dump.reset_index()[['match', 'matchend']], p_query])
            counts = self.corpus.cache.get(identifier + "-matchcounts")

            # create and cache otherwise
            if not isinstance(counts, DataFrame):
                logger.info('collecting token counts of subcorpus')
                counts = corpus.counts.dump(
                    df_dump, start='match', end='matchend', p_atts=self.p_query, split=True
                )
                self.corpus.cache.set(identifier + "-matchcounts", counts)

        else:
            if counts is None:
                logger.error('if no dump is given, you have to provide all counts')
                return

        self.counts = counts

    def show(self, order='log_likelihood', cut_off=100, ams=None,
             min_freq=2, flags=None, marginals='corpus',
             show_negative=False):

        # consistency check
        if self.counts.empty:
            logger.warning("nothing to show")
            return DataFrame()

        # get subcorpus frequencies und apply min freq
        f = self.counts.rename(columns={'freq': 'f'})
        vocab = len(f)
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
        df = f.join(f2, how='left')
        df = df.fillna(0)
        df['f1'] = f1
        df['N'] = N

        # score
        keywords = score_counts(df, order=order, cut_off=cut_off,
                                flags=flags, ams=ams, vocab=vocab)

        # throw away anti-keywords by default
        if not show_negative:
            keywords = keywords.loc[keywords['O11'] >= keywords['E11']]

        return keywords


def keywords(corpus, corpus_reference, p=['lemma'],
             p_reference=['lemma'], order='O11', cut_off=100,
             ams=None, min_freq=2, flags=None):
    """directly extract keywords by comparing two (sub-)corpora

    :param ccc.Corpus corpus: target corpus
    :param ccc.Corpus corpus_reference: reference corpus
    :param list p: p-att (str possible)
    :param list p_reference: p-att (str possible)
    :param str order: AM to order
    :param list ams: list of AMs
    :param int min_freq: minimum number of occurrences in target corpus
    :param list flags: '%cd'

    """

    # get from cache if possible
    identifier = generate_idx([corpus.__str__(), corpus_reference.__str__(),
                               p, p_reference, order, cut_off, ams, min_freq, flags], prefix='kw-')
    keywords = corpus.cache.get(identifier)

    if keywords is None:
        # get and merge both dataframes of counts
        logger.info('starting keyword analysis')
        target = corpus.marginals(p_atts=p)[['freq']].rename(columns={'freq': 'f1'})
        reference = corpus_reference.marginals(p_atts=p_reference)[['freq']].rename(columns={'freq': 'f2'})

        logger.info('-- combining frequency lists')
        df = target.join(reference, how='outer')
        df['N1'] = target['f1'].sum()
        df['N2'] = reference['f2'].sum()
        df = df.fillna(0)  # , downcast='infer')

        logger.info('-- cut-off')
        vocab = len(df)
        df = df.loc[df['f1'] >= min_freq]

        # score counts
        keywords = score_counts(df, order=order, cut_off=cut_off,
                                flags=flags, ams=ams, digits=4, vocab=vocab)
        logger.info('-- done with keyword analysis')
        corpus.cache.set(identifier, keywords)

    return keywords
