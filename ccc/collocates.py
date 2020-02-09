#! /usr/bin/env python
# -*- coding: utf-8 -*-

from itertools import chain
# part of module
from .utils import node2cooc
# requirements
from pandas import DataFrame
from association_measures import measures, frequencies
import logging
logger = logging.getLogger(__name__)


class Collocates:
    """ calculate and format collocates """

    def __init__(self, corpus, df_node, p_query, mws=10):

        if len(df_node) == 0:
            logger.warning('cannot calculate collocates of 0 contexts')
            return

        self.corpus = corpus
        self.df_node = df_node
        self.size = len(df_node)
        context = self.corpus.hits['parameters']['context']
        if context is not None:
            if mws > context:
                logger.warning(
                    "maximum window size outside context, using mws=%d" % context
                )
                mws = context
        self.mws = mws
        if p_query not in self.corpus.attributes_available['value'].values:
            logger.warning(
                'p_att "%s" not available, falling back to primary layer' % p_query
            )
            p_query = 'word'
        self.p_query = p_query

        logger.info('collecting contexts')
        deflated, f1_set = df_node_to_cooc(df_node)
        logger.info('collected %d token positions' % len(deflated))

        self.deflated = deflated
        self.f1_set = f1_set

    def count(self, window):

        mws = self.mws
        if window > mws:
            logger.warning('desired window outside maximum window size')
            logger.warning('will use maximum window (%d)' % mws)
            window = mws

        # slice relevant window
        relevant = self.deflated.loc[abs(self.deflated['offset']) <= window]

        # number of possible occurrence positions within window
        f1_inflated = len(relevant)

        # get frequency counts
        counts = self.corpus.cpos2counts(
            relevant['cpos'], self.p_query
        )
        counts.columns = ['O11']

        return counts, f1_inflated

    def show(self, window=5, order='O11', cut_off=100, ams=None,
             drop_hapaxes=True):

        if ams is None:
            ams = [
                'z_score', 't_score', 'dice',
                'log_likelihood', 'mutual_information'
            ]

        if len(self.f1_set) == 0:
            logger.error("there's nothing to show")
            return DataFrame()

        counts, f1_inflated = self.count(window)
        if counts.empty:
            logger.error("there's nothing to show")
            return DataFrame()

        # drop hapax legomena for improved performance
        if drop_hapaxes:
            counts = counts.loc[~(counts['O11'] <= 1)]

        # get marginals
        f2 = self.corpus.marginals(
            counts.index, self.p_query
        )
        f2.columns = ['f2']
        contingencies = counts.join(f2)

        # add constant columns
        contingencies['N'] = self.corpus.corpus_size - len(self.f1_set)
        contingencies['f1'] = f1_inflated

        # add measures
        collocates = add_ams(contingencies, ams)

        # sort dataframe
        collocates.sort_values(
            by=[order, 'item'],
            ascending=False, inplace=True
        )

        if cut_off is not None:
            collocates = collocates.head(cut_off)

        return collocates


# utilities ####################################################################
def df_node_to_cooc(df_node, context=None):
    """ converts df_node to df_cooc

    df_node: [match, matchend] + [s_id, region_start, region_end]
    df_cooc: [match, cpos, offset] (dedpulicated)
    f1_set: cpos of nodes

    deduplication strategy:
    (1) create overlapping contexts with nodes
    (2) sort by abs(offset)
    (3) deduplicate by offset, keep first occurrences
    (4) f1_set = (cpos where offset == 0)
    (5) remove rows where cpos in f1_set

    NB: equivalent to UCS when switching steps 3 and 4
    """

    # reset the index to be able to work with it
    df_node.reset_index(inplace=True)

    if context == 0:
        return DataFrame(), set()

    elif context is None:
        if (df_node['match'].values == df_node['region_start'].values).all() and (df_node['matchend'].values == df_node['region_end'].values).all():
            return DataFrame(), set()
        else:
            df_node['start'] = df_node['region_start']
            df_node['end'] = df_node['region_end']

    else:
        logger.info("re-confine regions by given context")
        df_node['start'] = df_node['match'] - context
        df_node['start'] = df_node[['start', 'region_start']].max(axis=1)
        df_node['end'] = df_node['matchend'] + context
        df_node['end'] = df_node[['end', 'region_end']].min(axis=1)

    logger.info("(1a) create local contexts")
    df = DataFrame.from_records(df_node.apply(node2cooc, axis=1).values)

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


def add_ams(df, am_names):
    """ annotates a contingency table with AMs """

    # select relevant association measures
    ams_all = {
        'z_score': measures.z_score,
        't_score': measures.t_score,
        'dice': measures.dice,
        'log_likelihood': measures.log_likelihood,
        'mutual_information': measures.mutual_information
    }
    ams = [ams_all[k] for k in am_names if k in ams_all.keys()]

    # create contigency table with observed frequencies
    df['O11'], df['O12'], df['O21'], df['O22'] = frequencies.observed_frequencies(df)
    # create indifference table with expected frequencies
    df['E11'], df['E12'], df['E21'], df['E22'] = frequencies.expected_frequencies(df)

    # calculate association measures
    df = measures.calculate_measures(df, measures=ams)
    df.index.name = 'item'

    return df
