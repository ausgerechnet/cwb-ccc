#! /usr/bin/env python
# -*- coding: utf-8 -*-

import re
from timeit import default_timer
from functools import wraps
# requirements
import numpy as np
from unidecode import unidecode
# logging
import logging
logger = logging.getLogger(__name__)


def time_it(func):
    """
    decorator for printing the execution time of a function call
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = default_timer()
        result = func(*args, **kwargs)
        end = default_timer()
        name = func.__name__
        logger.info("%s took %s seconds" % (name, round(end - start, 2)))
        return result
    return wrapper


###########
# ANCHORS #
###########
def chunk_anchors(lst, n, exclude={0, 1}):
    """yields n-sized chunks from lst without excluded values"""
    lst_rm = [i for i in lst if i not in exclude]
    for i in range(0, len(lst_rm), n):
        yield lst_rm[i:i + n]


def apply_correction(row, correction):
    """Applies correction to one row in column.

    :param list row: row of dump with [value, context, contextend]
    :param int correction: offset to add/subtract from position
    """
    value, lower_bound, upper_bound = row
    value += correction
    if value < lower_bound or value > upper_bound:
        value = -1
    return value


def correct_anchors(df, corrections):
    """Corrects df columns via dictionary of corrections

    :param DataFrame df: dump
    :param dict corrections: {anchor_name (0-9, column in df): offset (int)}
    """
    for correction in corrections:
        if correction in df.columns:
            logger.info('correcting anchor %d by offset %d' % (
                correction, corrections[correction]
            ))
            df[correction] = df[
                [correction, 'context', 'contextend']
            ].apply(lambda x: apply_correction(x, corrections[correction]), axis=1)
        else:
            logger.warning('anchor "%s" not in dataframe' % str(correction))
    return df


###########
# QUERIES #
###########
def cqp_escape(token):
    """ escape CQP meta-characters

    :param str token: string to escape

    :return: escaped string
    :rtype: str

    """
    return token.translate(str.maketrans({
        ".": r"\.",
        "?": r"\?",
        "*": r"\*",
        "+": r"\+",
        "|": r"\|",
        "(": r"\(",
        ")": r"\)",
        "[": r"\[",
        "]": r"\]",
        "{": r"\{",
        "}": r"\}",
        "^": r"\^",
        "$": r"\$"
    }))


def formulate_cqp_query(items, p_query='word', s_query=None,
                        flags="", escape=True):
    """ wrapper for easy queries

    :return: valid cqp query
    :rtype: str
    """

    # gather all MWUs
    mwu_queries = list()
    for item in items:

        # escape item (optional)
        if escape:
            item = cqp_escape(item)

        # split items on white-space
        tokens = item.split(" ")
        mwu_query = ""

        # convert to CQP syntax considering p-att and flags
        for token in tokens:
            mwu_query += '[{p_query}="{token}"{flags}]'.format(
                p_query=p_query, token=token, flags=flags
            )

        # add MWU item to list
        mwu_queries.append("(" + mwu_query + ")")

    # disjunctive join
    query = ' | '.join(mwu_queries)

    # add s_query (optional)
    if s_query is not None:
        query = '({query}) within {s_query};'.format(
            query=query, s_query=s_query
        )

    # return
    return query


def preprocess_query(query):
    """ parse anchors and 'within' statement from query """

    # get s_query and strip 'within' statement
    s_query = None
    query = query.rstrip(";")
    tokens = query.split(" ")
    if len(tokens) > 2:
        if tokens[-2] == "within":
            query = " ".join(tokens[:-2])
            s_query = tokens[-1]

    # get anchors
    p = re.compile(r"@\d")
    anchors = dict()
    for m in p.finditer(query):
        anchors[m.group()] = [m.start(), m.end()]
    anchors = [int(a[1]) for a in anchors.keys()]

    return query, s_query, anchors


#################################
# working on nodes and contexts #
#################################
def node2cooc(row):
    """ convert one row of df_node to info for df_cooc """

    # take values from row
    match = row['match']
    matchend = row['matchend']
    start = row['context']
    end = row['contextend']

    # get lists
    cpos_list = list(range(start, end + 1))
    match_list = [match] * len(cpos_list)

    # TODO get rid of this ridiculous loop by using map
    offset_list = list()
    for cpos in range(start, end + 1):
        if cpos < match:
            offset_list.append(cpos - match)
        elif cpos > matchend:
            offset_list.append(cpos - matchend)
        else:
            offset_list.append(0)

    # return object
    result = {
        'match_list': match_list,
        'cpos_list': cpos_list,
        'offset_list': offset_list
    }

    return result


def merge_intervals(inter, start_index=0):
    """ for merging contexts """
    for i in range(start_index, len(inter)-1):
        if inter[i][1] >= inter[i+1][0]:
            new_start = inter[i][0]
            new_end = inter[i+1][1]
            inter[i] = [new_start, new_end]
            del inter[i+1]
            return merge_intervals(inter.copy(), start_index=i)
    return inter


def calculate_offset(row):
    """ calculates offset of y to x """

    # necessary values
    match_x = row['match_x']
    match_y = row['match_y']

    # init matchends if necessary
    if 'matchend_x' in row.keys():
        matchend_x = row['matchend_x']
    else:
        matchend_x = match_x
    if 'matchend_y' in row.keys():
        matchend_y = row['matchend_y']
    else:
        matchend_y = match_y

    # y ... x
    if match_x > matchend_y:
        offset = matchend_y - match_x
    # x ... y
    elif matchend_x < match_y:
        offset = matchend_x - match_y
    # overlap
    else:
        offset = 0

    return offset


##################
# s-att handling #
##################
def merge_s_atts(s_query, s_break, s_meta):
    """ consistencize s-atts """
    # s_query < s_break < s_meta

    # case 1.1: only s_query
    if s_break is None and s_meta is None:
        s_break = s_meta = s_query

    # case 1.2: only s_break
    elif s_query is None and s_meta is None:
        s_query = s_meta = s_break

    # case 1.3: only s_meta
    elif s_query is None and s_break is None:
        s_query = s_break = s_query

    # case 2.1: s_query and s_break
    elif s_meta is None:
        s_meta = s_break

    # case 2.2: s_query and s_meta
    elif s_break is None:
        s_break = s_meta

    # useless cases
    # case 2.3: s_break and s_meta
    # case 3: all given

    if s_meta is not None and not s_meta.endswith("_id"):
        s_meta = s_meta + "_id"

    logger.info("s_query: %s - s_break: %s - s_meta: %s" % (
        str(s_query), str(s_break), str(s_meta)
    ))
    return s_query, s_break, s_meta


##################
# p-att handling #
##################
def fold_item(item, flags="%cd"):
    if flags is None:
        return item

    if "c" in flags:
        # lower-case
        item = item.lower()

    if "d" in flags:
        # TODO align with CWB
        # remove diacritica
        item = unidecode(item)

    return item


def fold_df(df, flags="%cd"):
    df.index = df.index.map(lambda x: fold_item(x, flags))
    grouped = df.groupby(df.index)
    df = grouped.aggregate(np.sum)
    return df
