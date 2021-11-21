#! /usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
from io import StringIO
from collections import Counter
from tempfile import NamedTemporaryFile
from association_measures import measures
# part of module
from .utils import time_it, fold_df
from .cl import Corpus as Crps
# requirements
from pandas import DataFrame, read_csv, MultiIndex
# logging
import logging
logger = logging.getLogger(__name__)


def count_items(items, names, tuples=True):
    """Get type frequency table of items.

    :param list items: list of values or tuples
    :param list names: name(s) for the attributes to count
    :param bool tuples: treat each item as a tuple?

    :return: frequency counts of items
    :rtype: FreqFrame
    """

    logger.info("... counting %d items" % len(items))
    counts = Counter(items)
    df_counts = DataFrame.from_dict(counts, orient='index', columns=['freq'])

    # transform index
    if tuples:
        df_counts.index = MultiIndex.from_tuples(df_counts.index, names=names)
        df_counts = df_counts.reset_index()
        df_counts['item'] = df_counts[names].agg(' '.join, axis=1)
        df_counts = df_counts.set_index('item')
    else:
        df_counts = df_counts.reset_index()
        df_counts.columns = names + ['freq']
        df_counts = df_counts.set_index(names[0], drop=False)
        df_counts.index.name = 'item'

    df_counts = df_counts[['freq'] + names]

    df_counts = df_counts.sort_values(by=['freq', 'item'], ascending=False)

    return df_counts


def read_freq_list(path, min_freq=2, columns=None):
    """Read frequency list, e.g. output of lexdecode (see below)

    :param str path: path to read from
    :param int min_freq: drop everything that doesn't appear at least this often

    :return: frequency list (index: item, columns: freq) and original size
    :rtype: tuple(DataFrame, int)

    """

    # read data
    logger.info('reading frequency list ...')
    df = read_csv(path, sep="\t", header=None, quoting=3,
                  keep_default_na=False)
    logger.info('reading frequency list ... %d items' % df.shape[0])

    # get corpus size
    R = df[0].sum()

    # apply frequency threshold
    logger.info('applying frequency threshold ...')
    df = df.loc[df[0] >= min_freq]
    logger.info('applying frequency threshold ... %d items' % df.shape[0])

    # indexing
    logger.info('combining relevant columns ...')
    col = list(df.columns[1:]) if columns is None else columns
    df.columns = ['freq'] + col
    if len(col) > 1:
        df['item'] = df[col].agg(' '.join, axis=1)
    else:
        df['item'] = df[col]
    df = df.set_index('item')
    logger.info(
        'combining relevant columns ... item="%s"' % " ".join([str(c) for c in col])
    )

    df = df.sort_values(['freq', 'item'], ascending=False)

    return df, R


def cwb_lexdecode(corpus_name, registry_path,
                  p_att='word', cmd='cwb-lexdecode', min_freq=2):
    """Run cwb-lexdecode: create frequency list of p-attribute
    CLI: cwb-lexdecode -f -s -P lemma CORPUS_NAME

    :param str corpus_name:
    :param str registry_path:
    :param str p_att:
    :param str cmd: path to binary
    :param int min_freq:

    :return: frequency list of p-attribute values and corpus size
    :rtype: tuple(DataFrame, int)

    """

    logger.info("running cwb-lexdecode ...")
    command = [cmd, '-f', '-P', p_att, '-r', registry_path, corpus_name]
    lexdecode = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    ret = lexdecode.communicate()[0].decode()
    df_counts, R = read_freq_list(StringIO(ret), min_freq=min_freq, columns=[p_att])

    return df_counts, R


def cwb_scan_corpus(corpus_name, registry_path, path=None,
                    p_atts=['word'], cmd='cwb-scan-corpus', min_freq=2):
    """Run cwb-lexdecode: create frequency list of p-attribute(s) at corpus positions.
    CLI: cwb-scan-corpus [-R path] CORPUS_NAME p_atts

    :return: counts of the p-attribute values (or their combinations)
             at the given positions (if any)
    :param str corpus_name:
    :param str registry_path:
    :param str p_att:
    :param str cmd: path to binary
    :param int min_freq:

    :return: frequency list of p-attribute values and corpus size
    :rtype: tuple(DataFrame, int)

    """

    logger.info("running cwb-scan-corpus ...")
    command = [cmd, '-r', registry_path]
    if path is not None:
        command += ['-R', path]
    command += [corpus_name] + p_atts
    scan = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    ret = scan.communicate()[0].decode()
    df_counts, R = read_freq_list(StringIO(ret), min_freq=min_freq, columns=p_atts)

    return df_counts, R


class Counts:
    """All methods return a FreqFrame

    == (item)* freq, p_atts[0], ...  ==

    where item = " ".join(p_atts)

    If index is not split, MWUs are " "-joined.

    TODO: counting with group?

    """
    def __init__(self, corpus_name,
                 registry_path='/usr/local/share/cwb/registry/'):

        self.corpus_name = corpus_name
        self.registry_path = registry_path
        self.attributes = Crps(
            self.corpus_name,
            registry_dir=registry_path
        )

    def _cpos2patts(self, cpos, p_atts=['word'], ignore=True):
        """Retrieve p-attributes of corpus position.

        :param int cpos: corpus position to fill
        :param list p_atts: p-attribute(s) to fill position with
        :param bool ignore: whether to return (None, .*) for -1

        :return: p-attribute(s) at cpos
        :rtype: tuple

        """

        if cpos == -1 and ignore:
            token = [None] * len(p_atts)
        else:
            token = [
                self.attributes.attribute(p_att, 'p')[cpos] for p_att in p_atts
            ]

        return tuple(token)

    def cpos(self, cpos_list, p_atts=['word']):
        """Create a frequency table for the p-attribute values of the
        cpos-list.

        - strategy: split   /YES; flags  ; combo x

        :param list cpos_list: corpus positions to fill
        :param list p_atts: p-attribute (combinations) to count

        :return: counts of the p_attribute (combinations) of the positions
        :rtype: FreqFrame

        """
        items = [self._cpos2patts(p, p_atts=p_atts) for p in cpos_list]
        df_counts = count_items(items, p_atts)
        return df_counts

    @time_it
    def dump(self, df_dump, start='match', end='matchend',
             p_atts=['word'], split=False, strategy=2):
        """Count tokens in [start .. end] (columns or index columns in df_dump).

        - strategy 1: split NO/YES; flags  ; combo x
        - strategy 2: split   /YES; flags  ; combo x

        :param list df_dump: corpus positions to fill
        :param str start: column name where to start counting
        :param str end: column name where to end counting
        :param list p_atts: p-attribute (combinations) to count
        :param bool split: token-based count? (default: MWU)
        :param int strategy: strategy 2 (cwb-scan-corpus) is faster,
                             does not support MWU counts though

        :return: counts of the p_att (combin.) in the spans of two columns of the dump
        :rtype: FreqFrame

        """

        # choose strategy
        if strategy == 2 and not split:
            logger.warning("dump: cannot use cwb-scan-corpus for MWUs")
            strategy = 1
        logger.info("dump: strategy %d" % strategy)

        # for working with match, matchend
        df_dump = df_dump.reset_index()

        if strategy == 1:

            logger.info("... extracting tokens")
            ls = df_dump.apply(
                lambda x: [self._cpos2patts(cpos, p_atts) for cpos in range(
                    x[start], x[end] + 1
                )], axis=1
            ).values            # list of list of tuples (p_att_1, p_att_2, ...)

            logger.info("... splitting")
            if split:
                tokens = [token for tokens in ls for token in tokens]
            else:
                tokens = [
                    tuple([" ".join(m) for m in zip(*mwu_list)]) for mwu_list in ls
                ]

            df_counts = count_items(tokens, p_atts)

        elif strategy == 2:
            df_dump = df_dump.reset_index()
            with NamedTemporaryFile(mode="wt") as f:
                logger.info("... writing dump temporarily to disk")
                df_dump[[start, end]].to_csv(f.name, sep="\t", header=None, index=False)
                df_counts, R = cwb_scan_corpus(
                    self.corpus_name, self.registry_path, f.name, p_atts
                )

        df_counts = df_counts.sort_values(by=['freq', 'item'], ascending=False)

        return df_counts

    @time_it
    def matches(self, cqp, name, p_atts=["word"], split=False, flags=None, strategy=3):
        """Counts tokens in [match .. matchend] of named subcorpus defined in
        running cqp.

        - strategy 1: split NO/   ; flags x; combo
        - strategy 2: split NO/YES; flags x; combo
        - strategy 3: split   /YES; flags  ; combo x

        :param CQP cqp: running cqp process
        :param list name: name of the subcorpus
        :param list p_atts: p-attribute(-combinations) to count
        :param bool split: token-based count? (default: MWU)
        :param str flags: %c, %d, %cd

        :return: counts of the p_attribute (combinations) of the matches
        :rtype: FreqFrame

        """

        # choose strategy
        combo = len(p_atts) > 1

        #    s f c
        # 1: - - -
        # 1: - x -
        # 2: - - -
        # 2: - x -
        # 2: x - -
        # 2: x x -
        # 3: x - -
        # 3: x - x

        # implemented:
        #    - - - 1,2
        #    - x - 1,2
        #    x - - 2,3
        #    x x - 2
        #    x - x 3

        # not implemented:
        #    - - x
        #    - x x
        #    x x x

        if combo:
            if flags or (not flags and not split):
                raise NotImplementedError(
                    "matches does not support parameter combination:",
                    str(" ".join(['x' if x else '-' for x in [
                        split, len(flags) > 0, combo
                        ]]))
                )

        if strategy == 1:
            if split or combo:
                logger.warning(
                    "matches: cannot use cqp-count"
                )
                strategy = 2
        if strategy == 2:
            if combo:
                logger.warning(
                    "matches: cannot use cqp-tabulate"
                )
                strategy = 3
        if strategy == 3:
            if flags or not split:
                logger.warning(
                    "matches: cannot use cwb-scan-corpus"
                )
                strategy = 2
        logger.info("matches: strategy %s" % strategy)

        if strategy == 1:
            # split NO; flags NO/YES; combo NO
            # generally slow
            logger.info("... cqp is counting")
            cqp_return = cqp.Exec(
                'count %s by %s %s;' % (name, p_atts[0], flags)
            )
            df_counts = read_csv(
                StringIO(cqp_return), sep="\t", header=None,
                names=["freq", "unknown", p_atts[0]]
            )
            df_counts = df_counts.set_index(p_atts[0], drop=False)
            df_counts.index.name = 'item'
            df_counts = df_counts.sort_values(['freq', 'item'], ascending=False)

        elif strategy == 2:
            # split NO/YES; flags NO/YES; combo NO
            # generally faster
            logger.info("... cqp is tabulating")
            cqp_return = cqp.Exec(
                'tabulate %s match .. matchend %s %s;' % (name, p_atts[0], flags)
            )
            logger.info("... splitting tokens")
            if split:           # split strings into tokens
                cqp_return = cqp_return.replace(" ", "\n")
            tokens = cqp_return.split("\n")
            df_counts = count_items(tokens, names=[p_atts[0]], tuples=False)

        elif strategy == 3:
            # split YES; flags NO; combo YES
            # generally fastest
            with NamedTemporaryFile(mode="wt") as f:
                logger.info("... writing dump temporarily to disk")
                cqp.Exec('dump %s > "%s";' % (name, f.name))
                df_counts, R = cwb_scan_corpus(
                    self.corpus_name, self.registry_path, f.name, p_atts
                )

        return df_counts

    @time_it
    def mwus(self, cqp, queries, p_atts=None, fill_missing=True, strategy=1):
        """Calculates frequencies for MWU queries in activated subcorpus.
        queries are a list of valid CQP queries, e.g.

        '[lemma="Angela"%cd & pos="NE"] [lemma="Merkel"%cd & pos="NE"]?'

        - strategy 1: split NO| - ; flags x; combo x; mwu NO
        - strategy 2: split NO| - ; flags x; combo x; mwu YES
        - strategy 3: split NO| - ; flags x; combo  ; mwu YES

        caveat: strategy 1 does not yield breakdown in attributes
        this implies also different indexing

        Strategies:
        - Strategy 1: for each item
          1. run query
          2. get size of NQR via CQP
        - Strategy 2:
          1. run query for all items at the same time
          2. dump df
          3. count_dump()
        - Strategy 3:
          1. run query for all items at the same time
          2. count_matches()

        :param CQP cqp: running cqp process
        :param set queries: set of query strings to get frequency breakdown for
        :param bool fill_missing: count 0 for missing items?
        :param int strategy: strategy to use (see below)

        :return: counts of the queries (strategy 1) or the items in the queries
        :rtype: FreqFrame

        """

        # subcorpus name to use
        name = 'Tmp'

        # choose strategy
        if strategy == 1:
            if p_atts:
                logger.warning(
                    "mwus: cannot get frequency breakdown when not inspecting dump"
                )
                strategy = 2

        # necessary for strategies 2 & 3:
        p_atts = ['word'] if not p_atts else p_atts

        if strategy == 3 and len(p_atts) > 1:
            logger.warning(
                "mwus: cannot combine query when looking at several p-attributes"
            )
            strategy = 2
        logger.info("mwus: strategy %s" % strategy)

        # count
        if strategy == 1:
            logger.info("... running each query")
            freqs = list()
            for query in queries:
                cqp.Exec('%s=%s;' % (name, query))
                freq = cqp.Exec('size %s;' % name)
                freqs.append(freq)
            df = DataFrame(data=freqs, index=queries, columns=['freq'])
            df.index.name = 'item'
            df['freq'] = df['freq'].astype(int)
            df = df.sort_values(by=['freq', 'item'], ascending=False)

        elif strategy == 2:
            query = "|".join(queries)
            cqp.Exec('%s=%s;' % (name, query))
            df_dump = cqp.Dump(name)
            df = self.dump(df_dump, start='match', end='matchend',
                           p_atts=p_atts, split=False, strategy=1)

        elif strategy == 3:
            query = "|".join(queries)
            cqp.Exec('%s=%s;' % (name, query))
            df = self.matches(cqp, name, p_atts=p_atts,
                              split=False, flags=None, strategy=2)

        # post-process dataframe
        df["freq"] = df["freq"].astype(int)
        # df = df.loc[df["freq"] != 0]

        return df


def score_counts(df1, df2, R1=None, R2=None, reference='right',
                 min_freq=2, order='log_likelihood', cut_off=1000,
                 flags=None, ams=None, freq=True, digits=6):
    """calculate association measures for two frequency lists df1, df2
    with respective sizes R1, R2.

    :param DataFrame df1: counts per item in corpus 1
    :param DataFrame df2: counts per item in corpus 2
    :param int R1: number of items in df1
    :param int R2: number of items in df2

    :param str reference: which dataframe is the reference?
    :param int min_freq: minimum number of occurrences in df1
    :param str order: association measure for sorting (in descending order)
    :param int cut_off: number of items to retrieve
    :param str flags: '%c' / '%d' / '%cd' (cwb-ccc algorithm)
    :param list ams: association measures to calculate (None=all)
    :param bool freq: include absolute and relative frequencies?
    :param int digits: round dataframe

    :return: scored counts
    :rtype: ScoreFrame

    """

    # which one should be treated as reference?
    if reference == 'left':
        return score_counts(df2, df1, R2, R1, reference='left',
                            order=order, cut_off=cut_off,
                            flags=flags, ams=ams, freq=freq,
                            digits=digits)

    logger.info('creating table of association measures')

    # preprocess
    df1.columns = ['O11']
    df2.columns = ['O21']

    # get corpus sizes if necessary
    R1 = df1['O11'].sum() if R1 is None else R1
    R2 = df2['O21'].sum() if R2 is None else R2

    # join dataframes respecting min_freq
    if min_freq == 0:
        df = df1.join(df2, how='outer')
    else:
        df1 = df1.loc[df1['O11'] >= min_freq]
        df = df1.join(df2, how='left')
    df = df.fillna(0, downcast='infer')

    # post-processing: fold items
    df = fold_df(df, flags)

    # calculate association
    df["O12"] = R1 - df["O11"]
    df["O22"] = R2 - df["O21"]
    df = measures.calculate_measures(df, freq=freq)

    if freq:
        # add instances per million
        df['ipm'] = df['O11'] / R1 * 1000000
        df['ipm_expected'] = df['E11'] / R1 * 1000000
        df['ipm_reference'] = df['O21'] / R2 * 1000000
        df['ipm_reference_expected'] = df['E21'] / R2 * 1000000

    # sort
    df = df.sort_values(by=[order, 'O11', 'O12'], ascending=False)

    # apply cut-off
    df = df.head(cut_off) if cut_off is not None else df

    # round
    df = round(df, digits) if digits is not None else df

    return df


def score_counts_signature(f, f1, f2, N, min_freq=2,
                           order='log_likelihood', cut_off=1000,
                           flags=None, ams=None, freq=True, digits=6):
    """wrapper of score_counts for input in frequency signature notation.

    :param DataFrame f: co-occurrence freq. of token and node
    :param int f1: number of tokens in W(node)
    :param DataFrame f2: marginal freq. of tokens
    :param int N: size of corpus

    :return: scored counts
    :rtype: ScoreFrame

    """

    f.columns = ['O11']
    f2.columns = ['C1']
    df = f.join(f2, how='outer').fillna(0, downcast='infer')
    df['O21'] = df['C1'] - df['O11']

    return score_counts(
        f, df[['O21']], f1, N-f1, reference='right', min_freq=min_freq,
        order=order, cut_off=cut_off, flags=flags, ams=ams,
        freq=freq, digits=digits
    )


#############
# re-factor #
#############
def _cpos2patts(attributes, cpos, p_atts=['word'], ignore=True):
    """Retrieve p-attributes of corpus position.

    :param int cpos: corpus position to fill
    :param list p_atts: p-attribute(s) to fill position with
    :param bool ignore: whether to return (None, .*) for -1

    :return: p-attribute(s) at cpos
    :rtype: tuple

    """
    if cpos == -1 and ignore:
        token = [None] * len(p_atts)
    else:

        token = [
            attributes.attribute(p_att, 'p')[cpos] for p_att in p_atts
        ]

    return tuple(token)


def count_cpos(corpus_name, cpos_list, p_atts=['word'],
               registry_path="/usr/local/share/cwb/registry/"):
    """Create a frequency table for the p-attribute values of the
    cpos-list.

    :param list cpos_list: corpus positions to fill
    :param list p_atts: p-attribute (combinations) to count

    :return: counts of the p_attribute (combinations) of the positions
    :rtype: FreqFrame

    """
    attributes = Crps(corpus_name, registry_dir=registry_path)
    items = [_cpos2patts(attributes, p, p_atts=p_atts, ignore=True) for p in cpos_list]
    df_counts = count_items(items, p_atts)
    return df_counts


def count_cooc_window(corpus_name, df_cooc, window=5, p_atts=['word'],
                      registry_path="/usr/local/share/cwb/registry/"):

    relevant = df_cooc.loc[abs(df_cooc['offset']) <= window]
    f1 = len(relevant)
    f = count_cpos(corpus_name, cpos_list=relevant['cpos'],
                   p_atts=p_atts, registry_path=registry_path)
    return f, f1


def marginals_simple(corpus_name, items, p_att='word', flags=0, pattern=False,
                     registry_path="/usr/local/share/cwb/registry/"):
    """Extract marginal frequencies for given unigrams or unigram patterns
    of a single p-attribute.  0 if not in corpus.  For
    combinations of p-attributes, see marginals_complex.

    :param list items: items to get marginals for
    :param str p_att: p-attribute to get frequencies for
    :param int flags: 1 = %c, 2 = %d, 3 = %cd (will activate wildcards)
    :param bool pattern: activate wildcards?

    :return: frequencies of the items in the whole corpus indexed by items
    :rtype: FreqFrame

    """

    pattern = True if flags > 0 else pattern
    attributes = Crps(corpus_name, registry_dir=registry_path)
    att = attributes.attribute(p_att, 'p')

    # loop through items and collect frequencies
    def att_frequency(att, item):
        """ small helper function for list comprehension:
        return frequency of 0 for items that are not in att
        """
        try:
            return att.frequency(item)
        except KeyError:
            return 0

    counts = [
        att_frequency(att, item) if not pattern else
        len(att.find_pattern(item, flags=flags)) for item in items
    ]

    # create dataframe
    df = DataFrame({'freq': counts, p_att: items})
    df = df.set_index(p_att, drop=False)
    df.index.name = 'item'
    df = df.sort_values(['freq', 'item'], ascending=False)

    return df


def marginals(corpus_name, items, p_atts=['word'], flags=0, pattern=False,
              registry_path="/usr/local/share/cwb/registry/"):

    if len(p_atts) == 1:
        return marginals_simple(corpus_name, items, p_atts[0],
                                flags, pattern, registry_path)
