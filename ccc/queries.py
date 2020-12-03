#! /usr/bin/env python
# -*- coding: utf-8 -*-

""" queries.py: read-write support for CQPY query files

- a CQPY file contains a YAML header and the actual CQP input
- YAML header *can* be commented
- query formatting (whitespace incl. linebreaks) is preserved

"""

import re
import yaml
import json
# logging
import logging
logger = logging.getLogger(__name__)


def load_query_json(query_path):
    """ support for query.json files pre 2020-08-29 """

    # read file
    with open(query_path, "rt") as f:
        query = json.loads(f.read())

    out = dict()
    # needs following keys:
    # 'meta'
    # 'corpus'
    # 'display'
    # 'anchors'
    # 'cqp'

    # we defintinely need this one
    out['cqp'] = query['query']

    # meta
    if 'name' not in query.keys():
        query['name'] = query_path.split("/")[-1].split(".")[0]
    if 'pattern' not in query.keys():
        query['pattern'] = -1
    out['meta'] = {
        'name': query['name'],
        'pattern': int(query['pattern'])
    }

    # corpus
    if 'corpus_name' not in query.keys():
        query['corpus_name'] = "BREXIT_V20190522_DEDUP"
    if 'lib_path' not in query.keys():
        query['lib_path'] = None
    out['corpus'] = {
        'corpus_name': query['corpus_name'],
        'lib_path': query['lib_path']
    }

    # display
    if 's_show' not in query.keys():
        query['s_show'] = ['tweet_id']
    if 'p_show' not in query.keys():
        query['p_show'] = ['word', 'lemma']
    if 'p_text' not in query.keys():
        query['p_text'] = 'word'
    if 'p_slots' not in query.keys():
        query['p_slots'] = 'lemma'
    out['display'] = {
        'p_show': query['p_show'],
        's_show': query['s_show'],
        'p_slots': query['p_slots'],
        'p_text': query['p_text']
    }

    # anchors
    out['anchors'] = {
        'corrections': dict(),
        'slots': dict()
    }
    if 'anchors' in query.keys():
        anchors = query.pop('anchors')
        for anchor, offset, idx, clear in anchors:
            if offset != 0:
                out['anchors']['corrections'][anchor] = offset
            if idx is not None:
                out['anchors']['slots'][idx] = anchor
    if 'regions' in query.keys():
        for start, end, idx, clear in query['regions']:
            if idx is not None:
                out['anchors']['slots'][idx] = [start, end]

    # query
    if 's_context' not in query.keys():
        query['s_context'] = 'tweet'
    if 'context' not in query.keys():
        query['context'] = None
    out['query'] = {
        'context': query['context'],
        's_context': query['s_context']
    }

    return out


def cqpy_load(path):
    """
    load cqpy query file from path, return string
    """

    doc = open(path, 'rt').read()

    try:
        # commented YAML header
        header, cqp = doc.split("# ---\n")
    except ValueError:
        # uncommented YAML header
        header, cqp = doc.split("---\n")
    except yaml.scanner.ScannerError:
        logger.error("could not parse CQPY file")
        return dict()

    # read header
    header_list = [re.sub(r"\A# ", "", h) for h in header.split("\n")]
    query = yaml.load("\n".join(header_list), Loader=yaml.FullLoader)

    # add CQP
    query['cqp'] = cqp.lstrip().rstrip()

    return query


def cqpy_dump(query, comment=True):
    """
    serialize query as cqpy-string
    """

    # get actual query
    cqp = query.pop('cqp')

    # header
    out = "--- # CQPY query file\n"
    out += yaml.dump(query, default_flow_style=False)
    out += "---"
    # comment header?
    if comment:
        out = "\n".join(["# " + line for line in out.split("\n")])
    # actual cqp query
    out += "\n\n" + cqp

    return out


def run_query(corpus, query, match_strategy='longest',
              cut_off=None, form='extended'):
    """
    query needs following sections:
    - cqp
    - query > context
    - query > s_context
    - anchors > corrections
    - anchors > slots
    - display > p_show
    - display > s_show
    - display > p_text
    - display > p_slots
    """

    dump = corpus.query(
        cqp_query=query['cqp'],
        context=query['query']['context'],
        context_break=query['query']['s_context'],
        corrections=query['anchors']['corrections'],
        match_strategy=match_strategy,
    )

    lines = dump.concordance(
        matches=None,
        p_show=query['display']['p_show'],
        s_show=query['display']['s_show'],
        p_text=query['display']['p_text'],
        p_slots=query['display']['p_slots'],
        slots=query['anchors']['slots'],
        cut_off=cut_off,
        form=form
    )

    return lines
