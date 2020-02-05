import shelve
import re
from hashlib import sha256
from timeit import default_timer
from functools import wraps


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


def cqp_escape(token):
    escaped = token.translate(str.maketrans({".": r"\.", "?": r"\?",
                                             "*": r"\*", "+": r"\+",
                                             "|": r"\|", "(": r"\(",
                                             ")": r"\)", "[": r"\[",
                                             "]": r"\]", "{": r"\{",
                                             "}": r"\}", "^": r"\^",
                                             "$": r"\$"}))
    return escaped


def formulate_cqp_query(items, p_att, s_att):
    """ wrapper for easy queries """

    mwu_queries = list()
    for item in items:
        item = cqp_escape(item)
        tokens = item.split(" ")
        mwu_query = ""
        for token in tokens:
            mwu_query += '[{p_att}="{token}"]'.format(p_att=p_att, token=token)
        mwu_queries.append("(" + mwu_query + ")")
    query = '|'.join(mwu_queries)
    if s_att is not None:
        cqp_exec = '({query}) within {s_att};'.format(query=query, s_att=s_att)
    else:
        cqp_exec = query
    return cqp_exec


def anchor_query_to_anchors(anchor_query, strict=False):
    """get anchors present in query"""

    anchors = dict()
    p = re.compile(r"@\d")

    for m in p.finditer(anchor_query):
        if strict:
            if m.group() in anchors.keys():
                raise KeyError('duplicate keys provided')
        anchors[m.group()] = [m.start(), m.end()]

    keys = [int(a[1]) for a in anchors.keys()]

    return keys


def time_it(func):
    """
    decorator for printing the execution time of a function call
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = default_timer()
        result = func(*args, **kwargs)
        end = default_timer()
        print("{} ran in {}s".format(func.__name__, round(end - start, 2)))
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
