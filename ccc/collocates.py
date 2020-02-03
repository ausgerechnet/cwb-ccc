#! /usr/bin/env python
# -*- coding: utf-8 -*-

from itertools import chain
# part of module
from .utils import node2cooc
# requirements
from pandas import DataFrame
from association_measures import measures, frequencies


class Collocates(object):

    def __init__(self, engine, max_window_size=20, s_break='text',
                 order='O11', p_query='lemma', cut_off=100,
                 drop_hapaxes=True, ams=['z_score', 't_score', 'dice',
                                         'log_likelihood', 'mutual_information']):

        self.engine = engine

        self.settings = {
            'max_window_size': max_window_size,
            's_break': s_break,
            'p_query': p_query,
            'order': order,
            'cut_off': cut_off,
            'ams': ams,
            'drop_hapaxes': drop_hapaxes
        }

    def query(self, query, window=5):

        if window > self.settings['max_window_size']:
            print("WARNING: desired window outside maximum window size")
            return DataFrame()

        print("... collecting nodes ...", end="\r")
        df_node = self.engine.df_node_from_query(
            query, self.settings['s_break'], context=self.settings['max_window_size']
        )
        print("... collecting nodes ... collected %d nodes" % len(df_node))

        print("... collecting cotexts ...", end="\r")
        df_cooc, match_pos = df_node_to_cooc(df_node)
        print("... collecting cotexts ... collected %d positions" % len(df_cooc))

        if df_cooc.empty:
            return DataFrame()

        print("... calculating collocates ...", end="\r")
        collocates = self.calculate_collocates(
            df_cooc, len(match_pos), window
        )
        print("... scoring collocates ... scored %d types" % len(collocates))

        return collocates

    def df_cooc_to_counts(self, df_cooc, window):

        # slice relevant window
        relevant = df_cooc.loc[abs(df_cooc['offset']) <= window]
        # relevant = relevant.drop_duplicates('cpos')

        # number of possible occurrence positions within window
        f1_inflated = len(relevant)

        # get frequency counts
        counts = self.engine.cpos2counts(
            relevant['cpos'], self.settings['p_query']
        )
        counts.columns = ["O11"]

        # drop hapax legomena for improved performance
        if self.settings['drop_hapaxes']:
            counts = counts.loc[~(counts['O11'] <= 1)]

        return counts, f1_inflated

    def calculate_collocates(self, df_cooc, f1, window):

        # get counts
        counts, f1_inflated = self.df_cooc_to_counts(
            df_cooc,
            window
        )
        # get marginals
        f2 = self.engine.marginals(
            counts.index, self.settings['p_query']
        )
        f2.columns = ['f2']
        # get frequency signatures
        contingencies = counts_to_contingencies(
            counts, f1, f1_inflated, f2, self.engine.corpus_size
        )
        # add measures and sort dataframe
        collocates = add_ams(
            contingencies, self.settings['ams']
        )
        collocates.sort_values(
            by=[self.settings['order'], 'item'], ascending=False, inplace=True
        )

        return collocates


# utilities ####################################################################
def df_node_to_cooc(df_node, context=None):
    """ converts df_node to df_cooc

    df_node: [match, matchend] + [target, keyword, s_id, region_start, region_end]
    df_cooc: [match, cpos, offset] (dedpulicated)
    f1_set: cpos of nodes

    deduplication strategy:
    (1) create overlapping cotexts with nodes
    (2) sort by abs(offset)
    (3) deduplicate by offset, keep first occurrences
    (4) f1_set = (cpos where offset == 0)
    (5) remove rows where cpos in f1_set

    NB: equivalent to UCS when switching steps 3 and 4
    """

    # print("reset the index to be able to work with it")
    df_node.reset_index(inplace=True)

    if context is not None:
        # print("re-confine regions by given context")
        df_node['start'] = df_node['match'] - context
        df_node['start'] = df_node[['start', 'region_start']].max(axis=1)
        df_node['end'] = df_node['matchend'] + context
        df_node['end'] = df_node[['end', 'region_end']].min(axis=1)
    else:
        df_node['start'] = df_node['region_start']
        df_node['end'] = df_node['region_end']

    # print("(1a) create local cotexts")
    df = DataFrame.from_records(df_node.apply(node2cooc, axis=1).values)

    # print("(1b) concatenate local cotexts")
    df_infl = DataFrame({
        'match': list(chain.from_iterable(df['match_list'].values)),
        'cpos': list(chain.from_iterable(df['cpos_list'].values)),
        'offset': list(chain.from_iterable(df['offset_list'].values))
    })

    # print("(2) sort by absolut offset")
    df_infl['abs_offset'] = df_infl.offset.abs()
    df_infl.sort_values(by=['abs_offset', 'cpos'], inplace=True)
    df_infl.drop(["abs_offset"], axis=1)

    # print("(3) drop duplicates")
    df_infl.drop_duplicates(subset='cpos', inplace=True)

    # print("(4a) identify matches")
    f1_set = set(df_infl.loc[df_infl['offset'] == 0]['cpos'])
    # print("(4b) remove matches")
    df_infl = df_infl[df_infl['offset'] != 0]

    return df_infl, f1_set


def counts_to_contingencies(counts, f1, f1_inflated, f2, N):
    """ window counts + marginals to contingency table"""

    # create contingency table
    N_deflated = N - f1
    contingencies = counts
    contingencies = contingencies.join(f2)
    contingencies['N'] = N_deflated
    contingencies['f1'] = f1_inflated
    return contingencies


def add_ams(contingencies, am_names):
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

    # rename for convenience
    df = contingencies

    # create the contigency table with the observed frequencies
    df['O11'], df['O12'], df['O21'], df['O22'] = frequencies.observed_frequencies(df)
    # create the indifference table with the expected frequencies
    df['E11'], df['E12'], df['E21'], df['E22'] = frequencies.expected_frequencies(df)

    # calculate all association measures
    measures.calculate_measures(df, measures=ams)
    df.index.name = 'item'

    return df
