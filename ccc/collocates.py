#! /usr/bin/env python
# -*- coding: utf-8 -*-

from itertools import chain
# part of module
from .utils import node2cotext
from .counts import score_counts_signature
# requirements
from pandas import DataFrame
# logging
import logging
logger = logging.getLogger(__name__)


class Collocates:
    """ collocation analysis """

    def __init__(self, corpus, df_dump, p_query=['lemma'], mws=10):

        # consistency check
        if len(df_dump) == 0:
            self.f1_set = set()
            logger.warning('empty dump')
            return

        # init corpus
        self.corpus = corpus.copy()

        # what's in the dump?
        self.df_dump = df_dump
        self.size = len(df_dump)

        # maximum window size (= context)
        self.mws = mws

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

        # collect cpos of matches and context
        logger.info('collecting cpos of matches and context')
        self.deflated, self.f1_set = df_node_to_cooc(self.df_dump, self.mws)
        logger.info('collected %d corpus positions' % len(self.deflated))

    def count(self, window):

        # check window
        mws = window if self.mws is None else self.mws
        if window > mws:
            logger.warning('requested window outside maximum window size')
            window = mws

        # slice window
        logger.info('slicing window %d' % mws)
        relevant = self.deflated.loc[abs(self.deflated['offset']) <= window]

        # number of possible occurrence positions within window
        f1 = len(relevant)

        # frequency counts
        f = self.corpus.counts.cpos(relevant['cpos'], self.p_query)

        return f, f1

    def show(self, window=5, order='O11', cut_off=100, ams=None,
             min_freq=2, frequencies=True, flags=None,
             marginals='corpus'):

        # consistency check
        if len(self.f1_set) == 0:
            logger.error("nothing to show")
            return DataFrame()

        # get context frequencies
        f, f1 = self.count(window)

        # get node frequencies
        node_freq = self.corpus.counts.cpos(self.f1_set, self.p_query)

        # determine corpus size
        if isinstance(marginals, str):
            if marginals == 'corpus':
                N = self.corpus.corpus_size - len(self.f1_set)
            else:
                raise NotImplementedError
        elif isinstance(marginals, DataFrame):
            # DataFrame must contain a column 'freq'
            N = marginals['freq'].sum()
        else:
            raise NotImplementedError

        collocates = calculate_collocates(
            self.corpus, self.deflated, node_freq, window, self.p_query,
            N, min_freq, order, cut_off, flags, ams, frequencies
        )

        return collocates


def df_node_to_cooc(df_dump, context=None):
    """ converts df_dump to df_cooc + f1_set

    strategy:
    (1a) create overlapping contexts with nodes
    (1b) concatenate local contexts
    (2a) sort by abs(offset)
    (2b) deduplicate by cpos, keep first occurrences (=smallest offset)
    (3a) f1_set = (cpos where offset == 0)
    (3b) remove rows where cpos in f1_set

    NB: equivalent to UCS when switching steps 3a and 3b

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
    df = DataFrame.from_records(df.apply(node2cotext, axis=1).values)

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


def calculate_collocates(corpus, df_cooc, node_freq, window, p_show,
                         N, min_freq, order, cut_off, flags,
                         ams=None, frequencies=True):

    # move to requested window
    relevant = df_cooc.loc[abs(df_cooc['offset']) <= window]

    # number of possible occurrence positions within window
    f1 = len(relevant)

    # get frequency counts
    f = corpus.counts.cpos(relevant['cpos'], p_show)

    # get marginals
    if len(p_show) == 1:
        marginals = corpus.marginals(f[p_show[0]], p_show[0])
    else:
        marginals = corpus.marginals_complex(f.index, p_show)

    # f2 = marginals - node frequencies
    f2 = marginals[['freq']].rename(columns={'freq': 'marginal'}).join(
        node_freq[['freq']].rename(columns={'freq': 'in_nodes'})
    )
    f2 = f2.fillna(0, downcast='infer')
    f2['f2'] = f2['marginal'] - f2['in_nodes']

    # score
    collocates = score_counts_signature(
        f[['freq']], f1, f2[['f2']], N,
        min_freq, order, cut_off, flags, ams, frequencies
    )

    # for backwards compatiblity
    if frequencies:
        # throw away anti-collocates by default
        collocates = collocates.loc[collocates['O11'] >= collocates['E11']]
        collocates = collocates.join(f2[['in_nodes', 'marginal']], how='left')

    return collocates
