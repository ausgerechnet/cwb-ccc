#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
# logging
import logging
logger = logging.getLogger(__name__)


# argmin query files
def read_query_json(query_path, convert=True):

    # parse it
    with open(query_path, "rt") as f:
        try:
            query = json.loads(f.read())
        except json.JSONDecodeError:
            logger.error("not a valid json file")
            query = dict()

    # we defintinely need this one
    assert('query' in query.keys())

    # name it
    if 'name' not in query.keys():
        name = query_path.split("/")[-1].split(".")[0]
        query['name'] = name

    # converts 2020-06-18 standard
    if convert:
        if 'anchors' in query.keys():
            corrections = dict()
            anchors = query.pop('anchors')
            for anchor, offset, idx, clear in anchors:
                if offset != 0:
                    corrections[anchor] = offset
            query['corrections'] = corrections
        if 'regions' in query.keys():
            regions = list()
            for start, end, idx, clear in query['regions']:
                regions.append((start, end))
            query['regions'] = regions

    # ensure keys of the above
    if 'corrections' not in query.keys():
        query['corrections'] = dict()
    if 'regions' not in query.keys():
        query['regions'] = []

    # set standard argmin query parameters for everything else
    if 'corpus_name' not in query.keys():
        query['corpus_name'] = "BREXIT_V20190522_DEDUP"
    if 'lib_path' not in query.keys():
        query['lib_path'] = None

    if 's_show' not in query.keys():
        query['s_show'] = ['tweet_id']
    if 's_context' not in query.keys():
        query['s_context'] = 'tweet'

    # p-attributes
    if 'p_show' not in query.keys():
        query['p_show'] = ['word', 'lemma']
    if 'p_text' not in query.keys():
        query['p_text'] = 'word'
    if 'p_slots' not in query.keys():
        query['p_slots'] = 'lemma'

    # context
    if 'context' not in query.keys():
        query['context'] = None

    return query


def run_query(corpus, query, match_strategy='longest'):

    # get post-processed dump
    result = corpus.query(
        query=query['query'],
        context=query['context'],
        s_context=query['s_context'],
        corrections=query['corrections'],
        match_strategy=match_strategy,
    )

    # extended concordancing
    concordance = corpus.concordance(
        result, max_matches=0
    )
    lines = concordance.lines(
        p_show=query['p_show'],
        s_show=query['s_show'],
        p_text=query['p_text'],
        p_slots=query['p_slots'],
        regions=query['regions'],
        cut_off=None,
        form='extended'
    )

    return lines
