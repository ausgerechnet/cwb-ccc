#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
from collections import defaultdict
# part of module
from .concordances import Concordance
from .utils import apply_corrections


# hole structure
def get_holes(df, anchors, regions):

    anchor_holes = dict()
    for anchor in anchors:
        if anchor[2] is not None:
            anchor_holes[anchor[2]] = anchor[0]
    region_holes = dict()
    for region in regions:
        if region[2] is not None:
            region_holes[region[2]] = region[:2]

    holes = defaultdict(dict)

    for idx in anchor_holes.keys():
        anchor = anchor_holes[idx]
        row = df[df['anchor'] == anchor]

        if row.empty:
            word = None
            lemma = None
        else:
            row_nr = int(row.index.values)
            word = df.at[row_nr, 'word']
            if 'lemma' in df.columns:
                lemma = str(df.at[row_nr, 'lemma'])
            else:
                lemma = None

        holes['words'][idx] = word
        holes['lemmas'][idx] = lemma

    for idx in region_holes.keys():
        region_start = region_holes[idx][0]
        region_end = region_holes[idx][1]

        row_start = df[df['anchor'] == region_start]
        row_end = df[df['anchor'] == region_end]

        # if both of them are empty
        if row_start.empty and row_end.empty:
            words = None
            lemmas = None
        else:
            # if one of them is empty: start and end are the same
            if row_start.empty:
                row_start = row_end
            elif row_end.empty:
                row_end = row_start

            row_start = int(row_start.index.values)
            row_end = int(row_end.index.values)
            region = df.loc[row_start:row_end]
            words = " ".join(list(region['word']))
            if 'lemma' in df.columns:
                lemmas = " ".join(list(region['lemma']))
            else:
                lemmas = None

        holes['words'][idx] = words
        holes['lemmas'][idx] = lemmas

    return holes


class ArgConcordance(Concordance):
    """ just a concordancer with extra formatting """

    def __init__(self, engine, context=None, s_break='tweet',
                 match_strategy='longest'):

        super().__init__(engine, context, s_break, match_strategy)

    def argmin_query(self, query, anchors, regions, p_show=['lemma']):

        # run the query
        query, s_query, anchors_query = self.query(query)
        if self.size == 0:
            return

        # apply corrections
        self.df_node = apply_corrections(self.df_node, anchors)

        # get concordance
        concordance = self.lines(p_show=p_show, order='first', cut_off=None)

        # initialize output
        result = dict()
        result['query'] = {
            'query': query,
            's_query': s_query,
            'anchors': anchors_query
        }
        result['nr_matches'] = self.size
        result['matches'] = list()
        result['holes'] = defaultdict(list)

        # loop through concordances
        for key in concordance.keys():

            line = concordance[key]

            # fill concordance line
            entry = dict()
            entry['df'] = line.to_dict()
            entry['position'] = key
            entry['full'] = " ".join(entry['df']['word'].values())

            # hole structure
            holes = get_holes(line, anchors, regions)
            if 'lemmas' in holes.keys():
                entry['holes'] = holes['lemmas']
            else:
                entry['holes'] = holes['words']

            result['matches'].append(entry)

            # append to global holes list
            for idx in entry['holes'].keys():
                result['holes'][idx].append(entry['holes'][idx])

        return result


def process_argmin_file(engine, query_path, p_show=['lemma']):

    with open(query_path, "rt") as f:
        try:
            query = json.loads(f.read())
        except json.JSONDecodeError:
            print("WARNING: not a valid json file")
            return

    # add query parameters
    query['corpus_name'] = engine.corpus_name
    query['subcorpus'] = engine.subcorpus
    query['query_path'] = query_path

    # run the query
    concordance = ArgConcordance(engine)
    query['result'] = concordance.argmin_query(query['query'],
                                               query['anchors'],
                                               query['regions'],
                                               p_show)

    return query
