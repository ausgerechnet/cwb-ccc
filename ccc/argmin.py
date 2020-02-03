#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
from collections import defaultdict
# part of module
from .concordances import df_node_to_concordance


# corrections
def apply_correction(row, correction):
    value, lower_bound, upper_bound = row
    value += correction
    if value < lower_bound or value > upper_bound:
        value = -1
    return value


def apply_corrections(df_anchor, corrections):
    for correction in corrections:
        if correction[0] in df_anchor.columns:
            df_anchor[correction[0]] = df_anchor[
                [correction[0], 'region_start', 'region_end']
            ].apply(lambda x: apply_correction(x, correction[1]), axis=1)
    return df_anchor


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


# actual query
def argmin_query(engine, query, anchors, regions=[],
                 s_break='text', context=0, p_show=['lemma'],
                 cut_off=None, order="first", match_strategy='longest'):

    print("running anchor query ...", end="\r")
    df_anchor = engine.df_anchor_from_query(
        query,
        s_break=s_break,
        context=context,
        match_strategy=match_strategy
    )
    print("running anchor query ... %d matches" % len(df_anchor))

    # initialize output
    result = dict()
    result['matches'] = list()
    result['holes'] = defaultdict(list)

    # if result is empty ...
    if df_anchor.empty:
        result['nr_matches'] = 0
        return result

    # apply corrections
    df_anchor = apply_corrections(df_anchor, anchors)

    # retrieve concordance
    concordance = df_node_to_concordance(engine,
                                         df_anchor,
                                         order=order,
                                         cut_off=cut_off,
                                         p_show=p_show,
                                         anchored=True)

    # number of matches
    result['nr_matches'] = len(concordance)

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


# read file and process query
def process_argmin_file(engine, query_path, concordance_settings):

    with open(query_path, "rt") as f:
        try:
            query = json.loads(f.read())
        except json.JSONDecodeError:
            print("WARNING: not a valid json file")
            return

    # add query parameters
    query['corpus_name'] = engine.corpus_name
    query['concordance_settings'] = concordance_settings
    query['query_path'] = query_path

    # get result
    query['result'] = argmin_query(engine,
                                   query['query'],
                                   query['anchors'],
                                   query['regions'],
                                   concordance_settings['s_break'],
                                   concordance_settings['context'],
                                   concordance_settings['p_show'])

    return query
