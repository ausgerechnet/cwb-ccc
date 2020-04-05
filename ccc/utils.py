import shelve
import re
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
        return sha256(str(string).encode()).hexdigest()

    def get(self, identifiers, subcorpus=None):
        key = self.generate_idx(identifiers + [subcorpus])
        if self.path is not None:
            with shelve.open(self.path) as db:
                try:
                    return db[key]
                except KeyError:
                    return None
        else:
            return None

    def set(self, identifiers, value, subcorpus=None):
        if self.path is not None:
            key = self.generate_idx(identifiers + [subcorpus])
            with shelve.open(self.path) as db:
                db[key] = value


# dataframe corrections
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
    escaped = token.translate(str.maketrans({".": r"\.", "?": r"\?",
                                             "*": r"\*", "+": r"\+",
                                             "|": r"\|", "(": r"\(",
                                             ")": r"\)", "[": r"\[",
                                             "]": r"\]", "{": r"\{",
                                             "}": r"\}", "^": r"\^",
                                             "$": r"\$"}))
    return escaped


def formulate_cqp_query(items, p_query='word', s_query=None, flags=None):
    """ wrapper for easy queries """

    mwu_queries = list()
    for item in items:
        item = cqp_escape(item)
        tokens = item.split(" ")
        mwu_query = ""
        for token in tokens:
            if flags is None:
                mwu_query += '[{p_query}="{token}"]'.format(
                    p_query=p_query, token=token
                )
            else:
                mwu_query += '[{p_query}="{token}" {flags}]'.format(
                    p_query=p_query, token=token, flags=flags
                )
        mwu_queries.append("(" + mwu_query + ")")
    query = '|'.join(mwu_queries)
    if s_query is not None:
        cqp_exec = '({query}) within {s_query};'.format(query=query, s_query=s_query)
    else:
        cqp_exec = query
    return cqp_exec


def preprocess_query(query):
    """parse anchors and within statement from query"""

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


def lines2df(lines, meta=None, kwic=True):

    # lines

    match_ids = list()
    meta_ids = list()
    left_contexts = list()
    matches = list()
    right_contexts = list()

    for line in list(lines.values()):

        left = line.loc[line['offset'] < 0]
        match = line.loc[line['offset'] == 0]
        right = line.loc[line['offset'] > 0]

        left_contexts.append(" ".join(list(left['word'].values)))
        matches.append(" ".join(list(match['word'].values)))
        right_contexts.append(" ".join(list(right['word'].values)))

        match_ids.append(match.index[0])
        if meta is not None:
            meta_ids.append(meta.loc[match.index[0]]['s_id'])
        else:
            meta_ids.append(None)

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

    if not kwic:
        df['text'] = " ".join([
            df['left'], df['match'], df['right']
        ])
        df = df[['meta_id', 'text']]
    else:
        df = df[['meta_id', 'left', 'match', 'right']]
    if meta is None:
        df.drop('meta_id', inplace=True, axis=1)

    return df
