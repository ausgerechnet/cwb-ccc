#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from itertools import chain

# requirements
from pandas import DataFrame

# part of module
from .counts import score_counts
from .utils import node2cotext

logger = logging.getLogger(__name__)


class Collocates:
    """ collocation analysis """

    def __init__(self, corpus, df_dump, p_query=['lemma'], mws=10,
                 df_cooc=None, f1_set=None, node_freq=None):

        # consistency check
        if df_dump is not None and len(df_dump) == 0:
            self.f1_set = set()
            logger.warning('empty dump')
            return

        # init corpus
        self.corpus = corpus.copy()

        # # what's in the dump?
        # self.df_dump = df_dump
        # self.size = len(df_dump)

        # maximum window size (= context)
        self.mws = mws

        # determine layer to work on
        self.p_query = [p_query] if isinstance(p_query, str) else p_query
        available_attributes = self.corpus.attributes_available['attribute'].values
        if not set(self.p_query).issubset(set(available_attributes)):
            logger.warning('specfied p-attribute(s) ("%s") not available' % " ".join(self.p_query))
            logger.warning('falling back to primary layer')
            self.p_query = ['word']

        # collect cpos of matches and context
        if df_dump is not None:
            logger.info('collecting cpos of matches and context')
            self.df_cooc, self.f1_set = dump2cooc(df_dump, self.mws)
            self.node_freq = self.corpus.counts.cpos(self.f1_set, self.p_query)
            logger.info('collected %d corpus positions' % len(self.df_cooc))
        else:
            if df_cooc is None or f1_set is None or node_freq is None:
                logger.error('if no dump is given, you have to provide all frequencies')
                return
            self.df_cooc = df_cooc
            self.f1_set = f1_set
            self.node_freq = node_freq

    def count(self, window):

        # check window
        mws = window if self.mws is None else self.mws
        if window > mws:
            logger.warning('requested window outside maximum window size')
            window = mws

        # slice window
        logger.info('slicing window %d' % window)
        relevant = self.df_cooc.loc[abs(self.df_cooc['offset']) <= window]

        # frequency counts
        f = self.corpus.counts.cpos(relevant['cpos'], self.p_query)

        return f

    def show(self, window=5, order='log_likelihood', cut_off=100, ams=None,
             min_freq=2, frequencies=True, flags=None,
             marginals='corpus', show_negative=False):

        # consistency check
        if len(self.f1_set) == 0:
            logger.error("nothing to show")
            return DataFrame()

        # get window counts and apply min freq
        f = self.count(window).rename(columns={'freq': 'f'})
        f1 = f['f'].sum()
        f = f.loc[f['f'] >= min_freq]

        # get reference frequencies
        if isinstance(marginals, str):
            if marginals == 'corpus':
                N = self.corpus.corpus_size - len(self.f1_set)
                marginals = self.corpus.marginals(f.index, self.p_query)
            else:
                raise NotImplementedError
        elif isinstance(marginals, DataFrame):
            # DataFrame must contain a column 'freq'
            N = marginals['freq'].sum()
        else:
            raise NotImplementedError

        # f2 = marginals - node frequencies
        f2 = marginals[['freq']].rename(columns={'freq': 'marginal'}).join(
            self.node_freq[['freq']].rename(columns={'freq': 'in_nodes'})
        )
        f2 = f2.fillna(0, downcast='infer')
        f2['f2'] = f2['marginal'] - f2['in_nodes']

        # create dataframe
        df = f2.join(f)
        df = df.fillna(0)
        df['f1'] = f1
        df['N'] = N

        # score
        collocates = score_counts(df, order, cut_off, flags, ams)

        if frequencies:
            # throw away anti-collocates by default
            if not show_negative:
                collocates = collocates.loc[collocates['O11'] >= collocates['E11']]
            # add node and marginal frequencies
            collocates = collocates.join(f2[['in_nodes', 'marginal']], how='left')

        return collocates


def dump2cooc(df_dump, context=None):
    """ converts df_dump to df_cooc + f1_set

    strategy:
    (1a) create overlapping contexts with nodes
    (1b) concatenate local contexts
    (2a) sort by abs(offset)
    (2b) deduplicate by cpos, keep first occurrences (=smallest offset)
    (3a) f1_set = (cpos where offset == 0)
    (3b) remove rows where cpos in f1_set

    :param DataFrame df_dump: [match, matchend] + [context_id, context, contextend]
    :param int context: confine context?

    :return: deduplicated df_cooc [match, cpos, offset] + f1_set (cpos of nodes)
    :rtype: tuple(DataFrame, set)
    """

    if context == 0:
        logger.warning("can't work on 0 context")
        return DataFrame(), set()

    # reset the index to be able to work with it
    df = df_dump.reset_index()

    if context is None:
        if (
            df['match'].values == df['context'].values
        ).all() and (
            df['matchend'].values == df['contextend'].values
        ).all():
            return DataFrame(), set()
        else:
            df['start'] = df['context']
            df['end'] = df['contextend']

    else:
        logger.info("re-confine regions by given context")
        df['start'] = df['match'] - context
        df['start'] = df[['start', 'context']].max(axis=1)
        df['end'] = df['matchend'] + context
        df['end'] = df[['end', 'contextend']].min(axis=1)

    logger.info("(1a) create local contexts")
    df = DataFrame.from_records(
        node2cotext(df['match'], df['matchend'], df['context'], df['contextend'])
    )

    logger.info("(1b) concatenate local contexts")
    df_infl = DataFrame({
        'match': list(chain.from_iterable(df['match_list'].values)),
        'cpos': list(chain.from_iterable(df['cpos_list'].values)),
        'offset': list(chain.from_iterable(df['offset_list'].values))
    })

    logger.info("(2a) sort by absolute offset")
    df_infl['abs_offset'] = df_infl.offset.abs()
    df_infl = df_infl.sort_values(by=['abs_offset', 'cpos'])
    df_infl = df_infl.drop(["abs_offset"], axis=1)

    logger.info("(2b) drop duplicates")
    df_defl = df_infl.drop_duplicates(subset='cpos')

    logger.info("(3a) identify nodes ...")
    f1_set = set(df_defl.loc[df_defl['offset'] == 0]['cpos'])

    logger.info("(3b) ... and remove them")
    df_defl = df_defl[df_defl['offset'] != 0]

    return df_defl, f1_set
