#! /usr/bin/env python
# -*- coding: utf-8 -*-

from itertools import chain
# part of module
from .utils import node2cooc, fold_df
# requirements
from pandas import DataFrame
from association_measures.measures import calculate_measures
import association_measures.frequencies as fq
# logging
import logging
logger = logging.getLogger(__name__)


class Collocates:
    """ collocation analysis """

    def __init__(self, corpus, df_dump, p_query, context=None, mws=10):

        # consistency check
        if len(df_dump) == 0:
            logger.warning('cannot calculate collocates of 0 contexts')
            return

        # TODO: start independent CQP process
        self.corpus = corpus

        # what's in the dump?
        self.df_dump = df_dump
        self.size = len(df_dump)

        # determine maximum window size
        if context is not None:
            if mws > context:
                logger.warning(
                    "maximum window size outside context, using mws=%d" % context
                )
                mws = context
        self.mws = mws

        # determine layer to work on
        if p_query not in self.corpus.attributes_available['name'].values:
            logger.warning(
                'p_att "%s" not available, falling back to primary layer' % p_query
            )
            p_query = 'word'
        self.p_query = p_query

        # collect context and save result
        logger.info('collecting contexts')
        deflated, f1_set = df_node_to_cooc(self.df_dump)
        logger.info('collected %d token positions' % len(deflated))
        self.deflated = deflated
        self.f1_set = f1_set

    def count(self, window):

        mws = self.mws
        if window > mws:
            logger.warning(
                'requested window outside maximum window size,'
                ' falling back to %d' % mws
            )
            window = mws

        # slice relevant window
        relevant = self.deflated.loc[abs(self.deflated['offset']) <= window]

        # number of possible occurrence positions within window
        f1_inflated = len(relevant)

        # get frequency counts
        counts = self.corpus.counts.cpos(
            relevant['cpos'], [self.p_query]
        )
        counts.columns = ['f']

        return counts, f1_inflated

    def show(self, window=5, order='f', cut_off=100, ams=None,
             min_freq=2, frequencies=True, flags=None):

        # consistency check
        if len(self.f1_set) == 0:
            logger.error("nothing to show")
            return DataFrame()

        # count
        counts, f1_inflated = self.count(window)
        if counts.empty:
            logger.error("nothing to show")
            return DataFrame()

        # drop items that occur less than min-freq
        counts = counts.loc[~(counts['f'] < min_freq)]

        # re-format index
        counts.index = counts.index.get_level_values(self.p_query)

        # get marginals
        f2 = self.corpus.counts.marginals(
            counts.index, self.p_query, flags=0
        )
        f2.columns = ['marginal']

        # deduct node frequencies from marginals
        node_freq = self.corpus.counts.cpos(self.f1_set, [self.p_query])
        node_freq.index = node_freq.index.get_level_values(self.p_query)
        node_freq.columns = ['in_nodes']
        f2 = f2.join(node_freq)
        f2.fillna(0, inplace=True)
        f2['in_nodes'] = f2['in_nodes'].astype(int)
        f2['f2'] = f2['marginal'] - f2['in_nodes']

        # join to contingency table
        contingencies = counts.join(f2)

        # post-processing: fold items
        contingencies = fold_df(contingencies, flags)

        # add constant columns
        contingencies['N'] = self.corpus.corpus_size - len(self.f1_set)
        contingencies['f1'] = f1_inflated
        # NB: frequency signature notation (Evert 2004: 36)

        # add measures
        if frequencies:
            collocates = contingencies.join(fq.observed_frequencies(contingencies))
            collocates = collocates.join(fq.expected_frequencies(collocates))
            collocates = collocates.join(calculate_measures(contingencies, ams))
        else:
            collocates = contingencies.join(calculate_measures(contingencies, ams))
        collocates.index.name = 'item'

        # sort dataframe
        collocates.sort_values(
            by=[order, 'item'],
            ascending=False, inplace=True
        )

        if cut_off is not None:
            collocates = collocates.head(cut_off)

        return collocates


# utilities ####################################################################
def df_node_to_cooc(df_dump, context=None):
    """ converts df_dump to df_cooc

    df_node: [match, matchend] + [context_id, context, contextend]
    df_cooc: [match, cpos, offset] (dedpulicated)
    f1_set: cpos of nodes

    deduplication strategy:
    (1) create overlapping contexts with nodes
    (2) sort by abs(offset)
    (3) deduplicate by cpos, keep first occurrences (=smallest offset)
    (4) f1_set = (cpos where offset == 0)
    (5) remove rows where cpos in f1_set

    NB: equivalent to UCS when switching steps 3 and 4
    """

    # can't work on 0 context
    if context == 0:
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
    df = DataFrame.from_records(df.apply(node2cooc, axis=1).values)

    logger.info("(1b) concatenate local contexts")
    df_infl = DataFrame({
        'match': list(chain.from_iterable(df['match_list'].values)),
        'cpos': list(chain.from_iterable(df['cpos_list'].values)),
        'offset': list(chain.from_iterable(df['offset_list'].values))
    })

    logger.info("(2) sort by absolut offset")
    df_infl['abs_offset'] = df_infl.offset.abs()
    df_infl.sort_values(by=['abs_offset', 'cpos'], inplace=True)
    df_infl.drop(["abs_offset"], axis=1)

    logger.info("(3) drop duplicates")
    df_defl = df_infl.drop_duplicates(subset='cpos')

    logger.info("(4) identify matches")
    f1_set = set(df_defl.loc[df_defl['offset'] == 0]['cpos'])

    logger.info("(5) remove matches")
    df_defl = df_defl[df_defl['offset'] != 0]

    return df_defl, f1_set
