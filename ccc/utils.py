import shelve
import re
import numpy as np
from unidecode import unidecode
from pandas import DataFrame
from hashlib import sha256
from timeit import default_timer
from functools import wraps
from collections import defaultdict
import logging
logger = logging.getLogger(__name__)


class Cache:

    def __init__(self, corpus_name, path=None):
        self.path = path
        self.corpus = corpus_name

    def generate_idx(self, identifiers):
        string = ''.join([str(idx) for idx in identifiers])
        string += self.corpus
        h = sha256(str(string).encode()).hexdigest()
        return 'CACHE_' + h[:10]

    def get(self, identifiers):
        key = self.generate_idx(identifiers)
        if self.path is not None:
            with shelve.open(self.path) as db:
                try:
                    return db[key]
                except KeyError:
                    return None
        else:
            return None

    def set(self, identifiers, value):
        if self.path is not None:
            key = self.generate_idx(identifiers)
            with shelve.open(self.path) as db:
                db[key] = value


# split list in tuples (for anchor queris)
def chunk_anchors(lst, n, exclude={0, 1}):
    """yields n-sized chunks from lst without excluded values"""
    lst_rm = [i for i in lst if i not in exclude]
    for i in range(0, len(lst_rm), n):
        yield lst_rm[i:i + n]


# anchor corrections
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


# query processing
def cqp_escape(token):
    """ escape CQP meta-characters """

    escaped = token.translate(str.maketrans({".": r"\.", "?": r"\?",
                                             "*": r"\*", "+": r"\+",
                                             "|": r"\|", "(": r"\(",
                                             ")": r"\)", "[": r"\[",
                                             "]": r"\]", "{": r"\{",
                                             "}": r"\}", "^": r"\^",
                                             "$": r"\$"}))
    return escaped


def formulate_cqp_query(items, p_query='word', s_query=None,
                        flags="", escape=True):
    """ wrapper for easy queries """

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
    """ parse anchors and within statement from query """

    # get s_query and strip within statement
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


def node2cooc(row):
    """ convert one row of df_node to info for df_cooc """

    # take values from row
    match = row['match']
    matchend = row['matchend']
    start = row['start']
    end = row['end']

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
        row = df.loc[df['anchor'] == anchor]

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

        row_start = df.loc[df['anchor'] == region_start]
        row_end = df.loc[df['anchor'] == region_end]

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


# s-att handling
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


def concordance_lines2df(lines, meta=None, kwic=True):
    """ convert dict of concordance lines to one dataframe """

    # init variables
    match_ids = list()
    meta_ids = list()
    left_contexts = list()
    matches = list()
    right_contexts = list()

    # loop through lines
    for line in list(lines.values()):

        # get and append left / match / right
        left = line.loc[line['offset'] < 0]
        match = line.loc[line['offset'] == 0]
        right = line.loc[line['offset'] > 0]
        left_contexts.append(" ".join(list(left['word'].values)))
        matches.append(" ".join(list(match['word'].values)))
        right_contexts.append(" ".join(list(right['word'].values)))

        # append match id
        match_ids.append(match.index[0])

        # append meta id
        if meta is not None:
            meta_ids.append(meta.loc[match.index[0]]['s_id'])
        else:
            meta_ids.append(None)

    # convert to DataFrame
    df = DataFrame(
        index=match_ids,
        data={
            'meta_id': meta_ids,
            'left': left_contexts,
            'match': matches,
            'right': right_contexts
        }
    )
    df.index.name = 'match_id'

    # convert to KWIC (optional) and bring columns in order
    if not kwic:
        df['text'] = df[['left', 'match', 'right']].apply(
            lambda x: ' '.join(x), axis=1
        )
        df = df[['meta_id', 'text']]
    else:
        df = df[['meta_id', 'left', 'match', 'right']]

    # drop meta column if meta is None
    if meta is None:
        df.drop('meta_id', inplace=True, axis=1)

    return df


# word post-processing
def fold_item(item, flags="%cd"):

    if flags is None:
        return item

    if "d" in flags:
        # remove diacritica
        item = unidecode(item)

    if "c" in flags:
        # lower-case
        item = item.lower()

    return item


def fold_df(df, flags="%cd"):
    df.index = df.index.map(lambda x: fold_item(x, flags))
    grouped = df.groupby(df.index)
    df = grouped.aggregate(np.sum)
    return df
