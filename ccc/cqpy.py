#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""cqpy.py

read-write support for CQPY query files

- a CQPY file contains a YAML header and the actual CQP input
- YAML header *can* be commented
- query formatting (whitespace incl. linebreaks) is preserved

"""
import json
import logging
import re

# requirements
import yaml

logger = logging.getLogger(__name__)


def cqpy_load_json(query_path):
    """ DEPRECATED: support for query.json files pre 2020-08-29 """

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
        query['pattern'] = 9999
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
    load cqpy query file from path, return dictionary
    """

    return cqpy_loads(open(path, 'rt').read())


def cqpy_loads(doc):
    """
    load cqpy query file from string, return dictionary
    """

    try:
        # commented YAML header
        header, cqp = doc.split("# ---\n")
    except ValueError:
        # uncommented YAML header
        header, cqp = doc.split("---\n")
    except yaml.scanner.ScannerError:
        logger.error("not a valid CQPY file")
        return dict()

    # read header
    header_list = [re.sub(r"\A# ", "", h) for h in header.split("\n")]
    query = yaml.load("\n".join(header_list), Loader=yaml.FullLoader)

    # add CQP
    query['cqp'] = cqp.lstrip().rstrip()

    # post-process anchors
    query = check_anchors(query)

    return query


def check_anchors(query):
    """
    make sure integer anchors are indeed integers
    """
    if 'anchors' in query:
        if 'corrections' in query['anchors']:
            corrections_int = dict()
            for k, c in query['anchors']['corrections'].items():
                try:
                    corrections_int[int(k)] = c
                except ValueError:  # for 'match', 'matchend', etc.
                    pass
            query['anchors']['corrections'] = corrections_int
    return query


def cqpy_dump(query, path, comment=True, mode='wt'):
    """
    write query in CQPY format to path
    """

    open(path, mode=mode).write(cqpy_dumps(query, comment))


def cqpy_dumps(query, comment=True):
    """
    serialize query as CQPY string
    """

    # get actual query
    query = query.copy()
    cqp = query.pop('cqp')

    # header
    out = "--- # CQPY query file\n"
    out += yaml.dump(query, default_flow_style=False)
    out += "---"
    # comment header?
    if comment:
        out = "\n".join(["# " + line for line in out.split("\n")])
    # actual cqp query
    out += "\n\n" + cqp + "\n"

    return out


def run_query(corpus, query,
              context=None, context_break=None, match_strategy='longest',
              corrections={}, slots={},
              p_show=['word', 'lemma'], s_show=[], cut_off=None, form='slots'):
    """Execute a query in a corpus. Return concordance lines as dataframe
    in 'slots' format. Parameters that are not set in the query-dict
    will be overwritten by method arguments.

    :param Corpus corpus: ccc.Corpus
    :param dict query: query with the following parts:
                       - cqp
                       - query > context        None
                       - query > context_break  None
                       - query > match_strategy "longest"
                       - anchors > corrections  {}
                       - anchors > slots        {}
                       - display > p_show       ['word', 'lemma']
                       - display > s_show       []
                       - display > cut_off      None
                       - display > form         'slots'

    :return: concordances lines
    :rtype: DataFrame

    """

    # the actual CQP query
    cqp = query['cqp']

    # determine query parameters
    if 'query' in query:

        # backwards compatability
        if 's_context' in query['query']:
            logger.warning("use of 's_context' is deprecated")
            query['query']['context_break'] = query['query'].pop('s_context')

        context = query['query'].get('context', context)
        context_break = query['query'].get('context_break', context_break)
        match_strategy = query['query'].get('match_strategy', match_strategy)

    # determine anchor parameters
    if 'anchors' in query:
        query = check_anchors(query)
        corrections = query['anchors'].get('corrections', corrections)
        slots = query['anchors'].get('slots', slots)

    # determine display parameters
    if 'display' in query:

        p_show = query['display'].get('p_show', p_show)
        s_show = query['display'].get('s_show', s_show)
        cut_off = query['display'].get('cut_off', cut_off)
        form = query['display'].get('form', form)

        # backwards compatability
        for p in ['p_slots', 'p_text']:
            if p in query['display']:
                # logger.warning(f"use of '{p}' is deprecated")
                if query['display'][p] not in p_show:
                    p_show += [query['display'][p]]

    # query the corpus
    dump = corpus.query_cqp(
        cqp_query=cqp,
        context=context,
        context_break=context_break,
        corrections=corrections,
        match_strategy=match_strategy,
    )

    # retrieve concordance lines
    lines = dump.concordance(
        p_show=p_show,
        s_show=s_show,
        slots=slots,
        cut_off=cut_off,
        form=form
    )

    # post-process: only return relevant columns
    if 'display' in query:
        if 'p_text' in query['display']:
            drop = [p for p in p_show if p != query['display']['p_text']]
            lines = lines.drop(drop, axis=1)
        if 'p_slots' in query['display']:
            drop = list()
            for slot in slots.keys():
                drop = ["_".join([slot, p]) for p in p_show
                        if p != query['display']['p_slots']]
                lines = lines.drop(drop, axis=1)

    return lines
