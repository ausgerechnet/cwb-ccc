import shelve
import re
import numpy as np
from unidecode import unidecode
from pandas import DataFrame
from hashlib import sha256
from timeit import default_timer
from functools import wraps
import logging
logger = logging.getLogger(__name__)


class Cache:

    def __init__(self, corpus_name, path=None):
        self.path = path
        self.corpus = corpus_name

    def generate_idx(self, identifiers, prefix='CACHE_', length=10):
        string = ''.join([str(idx) for idx in identifiers])
        string += self.corpus
        h = sha256(str(string).encode()).hexdigest()
        return prefix + h[:length]

    def get(self, identifier):

        if self.path is None:
            return None

        if type(identifier) is str:
            key = identifier
        else:
            key = self.generate_idx(identifier)

        with shelve.open(self.path) as db:
            if key in db.keys():
                logger.info('cache: retrieving object "%s"' % key)
                return db[key]
            else:
                return None

    def set(self, identifier, value):

        if self.path is None:
            return

        if type(identifier) is str:
            key = identifier
        else:
            key = self.generate_idx(identifier)

        with shelve.open(self.path) as db:
            logger.info('cache: saving object "%s"' % key)
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


def concordance_line2simple(line, p_att='word', kwic=False):
    """

    :param dict line: return value of concordance.text_line

    """

    if not kwic:
        return {
            'text': line[p_att]
        }

    # get and append left / match / right
    left = list()
    node = list()
    right = list()
    for offset, word in zip(line['offset'], line[p_att]):
        if offset < 0:
            left.append(word)
        elif offset == 0:
            node.append(word)
        else:
            right.append(word)

    return {
        'left': " ".join(left),
        'node': " ".join(node),
        'right': " ".join(right),
    }


def concordance_line2df(line, p_show):
    """

    :param dict line: return value of concordance.text_line

    """

    # pop non-lists
    anchors = line.pop('anchors')
    line.pop('match')           # not needed

    # transform to df
    df = DataFrame.from_records(line).set_index('cpos')

    # append anchors
    for a in anchors:
        df[a] = False
        if anchors[a] != -1:
            df.at[anchors[a], a] = True

    # init output
    return {
        'df': df
    }


def concordance_line2extended(line, p_show, p_text, p_slots, regions=[]):
    """

    :param dict line: return value of concordance.text_line

    """

    if p_text is None:
        p_text = p_show[0]

    anchors = line['anchors']
    out = concordance_line2df(line, p_show)

    for a in anchors:
        anchor_value = anchors[a]
        if anchor_value != -1:
            out["_".join([str(a), p_slots])] = out['df'][p_slots][anchor_value]

    for region in regions:
        region_name = "_".join([str(x) for x in region])

        anchor_left = True in out['df'][region[0]].values
        anchor_right = True in out['df'][region[1]].values

        if not anchor_left and not anchor_right:
            slots_p = None
        elif anchor_left and anchor_right:
            start = out['df'].index[out['df'][region[0]]].tolist()[0]
            end = out['df'].index[out['df'][region[1]]].tolist()[0]
            slots_p = " ".join(out['df'][p_slots].loc[start: end].to_list())
        elif anchor_right:
            end = out['df'].index[out['df'][region[1]]].tolist()[0]
            slots_p = out['df'][p_slots].loc[end]
        elif anchor_left:
            start = out['df'].index[out['df'][region[0]]].tolist()[0]
            slots_p = out['df'][p_slots][start]

        out["_".join([region_name, p_slots])] = slots_p

    return out


def format_concordance_lines(df_lines, p_show=['word'], regions=[],
                             p_text=None, p_slots='lemma', form='dataframes'):

    if form == 'simple':
        df = DataFrame.from_records(
            index=df_lines.index,
            data=df_lines.apply(
                lambda row: concordance_line2simple(row, p_show[0], kwic=False)
            )
        )

    elif form == 'kwic':
        df = DataFrame.from_records(
            index=df_lines.index,
            data=df_lines.apply(
                lambda row: concordance_line2simple(row, p_show[0], kwic=True)
            )
        )

    elif form == 'dataframes':
        df = DataFrame.from_records(
            index=df_lines.index,
            data=df_lines.apply(
                lambda row: concordance_line2df(row, p_show)
            )
        )

    elif form == 'extended':
        df = DataFrame.from_records(
            index=df_lines.index,
            data=df_lines.apply(
                lambda row: concordance_line2extended(row,
                                                      p_show, p_text, p_slots,
                                                      regions)
            )
        )

    else:
        raise NotImplementedError('no support for format "%s"' % form)

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
