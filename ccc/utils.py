#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""utils.py

various utilities for the module

"""
import logging
import pkgutil
import re
from functools import wraps
from timeit import default_timer

# requirements
import numpy as np
from pandas import NA, DataFrame
from unidecode import unidecode

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
        logger.info(f"{name} took {round(end - start, 2)} seconds")
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

    if value == -1:
        # missing value
        return value

    value += correction
    if value < lower_bound:
        value = lower_bound
    if value > upper_bound:
        value = upper_bound
    return value


def correct_anchors(df, corrections):
    """Corrects df columns via dictionary of corrections

    :param DataFrame df: dump
    :param dict corrections: {anchor_name (0-9, column in df): offset (int)}
    """
    for correction in corrections:
        if correction in df.columns:
            logger.info(f'correcting anchor {correction} by offset {corrections[correction]}')
            df[correction] = df[
                [correction, 'context', 'contextend']
            ].apply(lambda x: apply_correction(x, corrections[correction]), axis=1)
        else:
            logger.warning(f'anchor "{correction}" not in dataframe')
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
        "$": r"\$",
        '"': r"\"",
        "'": r"\'"
    }))


def format_cqp_query(items, p_query='word', s_query=None,
                     flags="", escape=True):
    """ wrapper for easy queries

    :return: valid cqp query
    :rtype: str
    """

    # gather all MWUs
    mwu_queries = list()
    single_items = list()
    for item in items:

        # escape item (optional)
        if escape:
            item = cqp_escape(item)

        # split items on white-space
        tokens = item.split(" ")
        if len(tokens) > 1:
            mwu_query = ""

            # convert to CQP syntax considering p-att and flags
            for token in tokens:
                mwu_query += f'[{p_query}="{token}"{flags}]'

            # add MWU item to list
            mwu_queries.append("(" + mwu_query + ")")
        else:
            single_items.append(tokens[0])

    singles_query = "([" + p_query + "=" + '"' + "|".join(single_items) + '"' + flags + "])"
    queries = mwu_queries + [singles_query]
    # disjunctive join
    query = ' | '.join(queries)

    # add s_query (optional)
    if s_query is not None:
        query = f'({query}) within {s_query};'

    # return
    return query


def find_all(pattern, string):
    p = re.compile(pattern)
    matches = dict()
    for m in p.finditer(string):
        matches[m.group()] = [m.start(), m.end()]
    return matches


def preprocess_query(query):
    """
    - get s_query and strip 'within' statement
    - get anchors
    - get macros
    - get wordlists

    :return: raw query, s_query, anchors, macros, wordlists
    :rtype: dict
    """

    # get s_query and strip 'within' statement
    s_query = None
    query = query.rstrip(";")
    tokens = query.split(" ")
    if len(tokens) > 2:
        if tokens[-2] == "within":
            query = " ".join(tokens[:-2])
            s_query = tokens[-1]

    # find anchors, macros, wordlists
    anchors = [int(a[1]) for a in find_all(r"@\d", query).keys()]
    macros = list(find_all(r"/[A-Za-z_]+\[\d*\]", query).keys())
    wordlists = list(find_all(r"\$[A-Za-z_]+", query).keys())

    return {
        'query': query,
        's_query': s_query,
        'anchors': anchors,
        'macros': macros,
        'wordlists': wordlists
    }


def decode(text):
    """savely decode a string catching common errors

    """
    try:
        text = text.decode('utf-8')
    except (UnicodeDecodeError, AttributeError):
        text = ""
    return text


#################################
# working on nodes and contexts #
#################################
def _node2cotext(match, matchend, context, contextend):
    """converts the four cpos-values of nodes into a dict of lists of
    cpos, match, and offset

    """
    # get lists
    cpos_list = list(range(context, contextend + 1))
    match_list = [match] * len(cpos_list)
    offset_list = [
        (cpos - match) if cpos < match else
        (cpos - matchend) if cpos > matchend else
        0 for cpos in cpos_list
    ]

    # return object
    result = {
        'match_list': match_list,
        'cpos_list': cpos_list,
        'offset_list': offset_list
    }

    return result


node2cotext = np.vectorize(_node2cotext)


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

    # if match_y is missing, offset is missing
    if match_y is NA or match_y == -1:
        return NA

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
        offset = match_y - matchend_x
    # overlap
    else:
        offset = 0

    return offset


##################
# s-att handling #
##################
def merge_s_atts(s_query, s_break, s_meta):
    """ DEPRECATED consistencize s-atts """
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

    logger.info(f"s_query: {s_query} - s_break: {s_break} - s_meta: {s_meta}")
    return s_query, s_break, s_meta


##################
# p-att handling #
##################
def fold_item(item, flags="%cd"):

    if flags is None:
        return item

    # is the item a string or a tuple?
    isstr = isinstance(item, str)
    item = (item, ) if isstr else item

    if "c" in flags:
        # lower-case
        item = [i.lower() for i in item]

    if "d" in flags:
        # TODO align with CWB
        # remove diacritica
        item = [unidecode(i) for i in item]

    item = item[0] if isstr else tuple(item)

    return item


def fold_df(df, flags="%cd"):

    if flags is None:
        return df

    df.index = df.index.map(lambda x: fold_item(x, flags))
    df = df.select_dtypes(include=np.number)
    grouped = df.groupby(df.index)
    df = grouped.aggregate(np.sum)
    return df


def filter_df(df, path):

    data = pkgutil.get_data(__name__, path)
    items = set(data.decode().split("\n"))
    return df.loc[~df.index.isin(items)]


##########################
# concordance dataframes #
##########################
def dump_left_join(df1, df2, name, drop=True, window=None):
    """join an additional dump df2 to an existing constellation

    :param DataFrame df1: constellation dump === (m, me) ci c ce m_t* me_t* o_t* m_1* me_1* o_1* ... ==
    :param DataFrame df2: additional dump === (m, me) ci c ce ==
    :param str name: name for additional discourseme
    :param bool drop: drop all rows that do not contain all discoursemes within topic context?
    :return: constellation dump including additional dump  === (m, me) ci c ce m_t me_t o_t m_1 me_1 o_1 ... m_name me_name o_name ==
    :rtype: DataFrame
    """

    # merge dumps via contextid ###
    df1 = df1.reset_index()
    df2 = df2.reset_index()[['contextid', 'match', 'matchend']].astype("Int64")
    m = df1.merge(df2, on='contextid', how='left')

    # calculate offset ###
    m['offset_y'] = 0       # init as overlap
    # y .. x
    m.loc[m['match_x'] > m['matchend_y'], 'offset_y'] = m['matchend_y'] - m['match_x']
    # x .. y
    m.loc[m['matchend_x'] < m['match_y'], 'offset_y'] = m['match_y'] - m['matchend_x']
    # missing y
    m.loc[m['match_y'].isna(), 'offset_y'] = NA

    # restrict to complete constellation ###
    if drop:
        m = m.dropna()
        # only keep co-occurrences that are within context
        m = m.loc[(m['matchend_y'] >= m['context']) & (m['match_y'] < m['contextend'])]
        if window:
            # only keep co-occurrences that are within window
            m = m.loc[abs(m['offset_y']) <= window]

    # rename columns ###
    m = m.rename(columns={'match_x': 'match',
                          'matchend_x': 'matchend',
                          'match_y': 'match_' + name,
                          'matchend_y': 'matchend_' + name,
                          'offset_y': 'offset_' + name})

    # set index ###
    m = m.set_index(['match', 'matchend'])

    return m


def group_lines(df, names):
    """
    convert dataframe:
    === (m, me) ci c ce m0 m0e o0 m1 me1 o1 m2 me2 o2 ===
    with duplicate indices to
    === (m, me) ci c ce m0 m1 m2 ===
    without duplicate indices
    where
    m0 = {(o0, m0, m0e), (o0, m0, m0e), ...}
    m1 = {(o1, m1, m1e), ...}

    """

    df = df.copy()
    # TODO: deduplication necessary?
    df_reduced = df[~df.index.duplicated(keep='first')][['contextid', 'context', 'contextend']]
    for name in names:
        columns = [m + "_" + name for m in ['offset', 'match', 'matchend']]
        df[name] = df[columns].values.tolist()
        df[name] = df[name].apply(tuple)
        df = df.drop(columns, axis=1)
        df_reduced[name] = df.groupby(level=['match', 'matchend'], group_keys=False)[name].apply(set)

    return df_reduced


def aggregate_matches(df, name, context_col='contextid',
                      match_cols=['match', 'matchend']):
    """
    convert dataframe:
    === (m, me) ci ===
    to
    === (ci) {name} COUNTS_{name} BOOL_{name} ===

    """
    # counts
    counts = DataFrame(df[context_col].value_counts()).astype("Int64")
    counts.columns = [name + '_COUNTS']

    # matches
    matches = df.reset_index()
    matches[name] = matches[match_cols].values.tolist()
    matches[name] = matches[name].apply(tuple)
    matches = matches.groupby('contextid', group_keys=True)[name].apply(set)

    # combine
    table = counts.join(matches)

    # bool
    table[name + '_BOOL'] = table[name + '_COUNTS'] > 0
    table[name + '_BOOL'] = table[name + '_BOOL'].fillna(False)

    return table


def format_roles(row, names, s_show, window, htmlify_meta=False):
    """Take a row of a dataframe indexed by match, matchend of the node,
    columns for each discourseme with sets of tuples indicating discourseme positions,
    columns for each s in s_show,
    and a column 'dict' containing the pre-formatted concordance line.

    creates a list (aligned with other lists) of lists of roles; roles are:
    - 'node' (if cpos in index)
    - 'out_of_window' (if offset of cpos from node > window)
    - discourseme names

    :return: concordance line for MMDA frontend
    :rtype: dict

    """

    # TODO directly create relevant objects, no need for frontend to take care of it
    # init
    d = row['dict']
    roles = list()

    # 'out_of_window' | None | 'node'
    role = ['out_of_window' if abs(t) > window else None for t in d['offset']]
    for i in range(d['cpos'].index(row.name[0]), d['cpos'].index(row.name[1]) + 1):
        role[i] = 'node'
    roles.append(role)

    # discourseme names
    for name in names:

        role = [None] * len(d['offset'])

        if not isinstance(row[name], float):
            for t in row[name]:

                # check match information
                if len(t) == 2:
                    # lazy definition without offset
                    start = 0
                    end = 1
                elif len(t) == 3:
                    # with offset
                    start = 1
                    end = 2
                else:
                    continue

                # skip NAs
                if not isinstance(t[start], int):
                    continue

                # skip the ones too far away
                try:
                    start = d['cpos'].index(t[start])
                    end = d['cpos'].index(t[end]) + 1
                except ValueError:
                    continue

                for i in range(start, end):
                    role[i] = name

        roles.append(role)

    # combine individual roles into one list of lists
    d['role'] = [[a for a in set(r) if a is not None] for r in list(zip(*roles))]

    # add s-attributes
    if htmlify_meta:
        meta = {key: row[key] for key in s_show if not key.endswith("_BOOL")}
        d['meta'] = DataFrame.from_dict(meta, orient='index').to_html(bold_rows=False, header=False)
        for s in s_show:
            if s.endswith("_BOOL"):
                d[s] = row[s]
    else:
        for s in s_show:
            d[s] = row[s]

    return d
