#! /usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
from io import StringIO
from collections import Counter
from tempfile import NamedTemporaryFile
# part of module
from .utils import time_it
# requirements
from CWB.CL import Corpus as Crps
from pandas import DataFrame, MultiIndex, read_csv
# logging
import logging
logger = logging.getLogger(__name__)


def cwb_scan_corpus(path, corpus_name, p_atts=['word'], cmd='cwb-scan-corpus'):

    logger.info("running cwb-scan-corpus ...")
    scan = subprocess.Popen(
        [cmd, '-R', path, corpus_name] + p_atts,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    ret = scan.communicate()[0].decode()

    logger.info("... collecting results")
    df_counts = read_csv(StringIO(ret), sep="\t", header=None,
                         quoting=3, keep_default_na=False)
    df_counts.columns = ['freq'] + p_atts
    df_counts = df_counts.set_index(p_atts)
    return df_counts


class Counts:
    """
    returns df_counts:
    def: (p_att_1, p_att_2, ...), freq
    all p_atts are strings, " "-delimited for MWUs (split=NO)

    attributes:
    .corpus_name
    .attributes

    methods:
    ._cpos2patts

    .cpos      (cpos_list, p_atts)

    .dump      (df_dump, start, end, p_atts, split)
      - strategy 1: split NO|YES; flags  ; combo x
      - strategy 2: split   |YES; flags  ; combo

    .matches   (name, p_att, split, flags)
      - strategy 1: split NO|   ; flags x; combo
      - strategy 2: split NO|YES; flags x; combo
      - strategy 3: split   |YES; flags  ; combo x

    .mwus      (queries)
      - strategy 1: split NO| - ; flags x; combo x; mwu NO
      - strategy 2: split NO| - ; flags x; combo x; mwu YES
      - strategy 3: split NO| - ; flags x; combo  ; mwu YES

    TODO: counting with group?

    """
    def __init__(self, corpus_name,
                 registry_path='/usr/local/share/cwb/registry/'):

        self.corpus_name = corpus_name
        self.attributes = Crps(
            self.corpus_name,
            registry_dir=registry_path
        )

    def _cpos2patts(self, cpos, p_atts=['word'], ignore_missing=True):
        """Retrieves p-attributes of corpus position.

        :param int cpos: corpus position to fill
        :param list p_atts: p-attribute(s) to fill position with
        :param bool ignore_missing: whether to return -1 for out-of-bounds

        :return: p_att(s)
        :rtype: tuple

        """

        if ignore_missing and cpos == -1:
            token = [None] * len(p_atts)
        else:
            token = [self.attributes.attribute(p_att, 'p')[cpos] for p_att in p_atts]

        return tuple(token)

    def cpos(self, cpos_list, p_atts=['word']):
        """Creates a frequency table for the p_att-values of the cpos-list.

        :param list cpos_list: corpus positions to fill
        :param list p_atts: p-attribute (combinations) to count

        :return: counts of the p_attribute (combinations) of the positions
        :rtype: DataFrame

        """
        lex_items = [self._cpos2patts(p, p_atts=p_atts) for p in cpos_list]
        counts = Counter(lex_items)
        df_counts = DataFrame.from_dict(counts, orient='index', columns=['freq'])
        df_counts.index = MultiIndex.from_tuples(df_counts.index, names=p_atts)
        return df_counts

    @time_it
    def dump(self, df_dump, start='match', end='matchend',
             p_atts=['word'], split=False, strategy=2):
        """Counts tokens in [start .. end] (columns in df_dump).

        :param list df_dump: corpus positions to fill
        :param str start: column name where to start counting
        :param str end: column name where to end counting
        :param list p_atts: p-attribute (combinations) to count
        :param bool split: token-based count? (default: MWU)
        :param int strategy: strategy 2 (cwb-scan-corpus) is faster,
                             does not support MWU counts though

        :return: counts of the p_attribute (combinations) of the positions
        :rtype: DataFrame

        """

        # choose strategy
        if strategy == 2 and not split:
            logger.warning("dump: cannot use cwb-scan-corpus for MWUs")
            strategy = 1
        logger.info("dump: strategy %d" % strategy)

        df_dump = df_dump.reset_index()  # for working with match, matchend

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

            logger.info("... counting")
            counts = Counter(tokens)
            df_counts = DataFrame.from_dict(
                counts, orient='index', columns=['freq']
            )
            df_counts.index = MultiIndex.from_tuples(
                df_counts.index, names=p_atts
            )

        elif strategy == 2:

            with NamedTemporaryFile(mode="wt") as f:
                logger.info("... writing dump to disk")
                df_dump[[start, end]].to_csv(f.name, sep="\t", header=None, index=False)
                df_counts = cwb_scan_corpus(f.name, self.corpus_name, p_atts)

        df_counts = df_counts.sort_values(by='freq', ascending=False)

        return df_counts

    @time_it
    def matches(self, cqp, name, p_atts=["word"], split=False, flags=None, strategy=3):
        """Counts tokens in [match .. matchend] of named subcorpus defined in
        running cqp.

        :param CQP cqp: running cqp process
        :param list name: name of the subcorpus
        :param list p_atts: p-attribute(-combinations) to count
        :param bool split: token-based count? (default: MWU)
        :param str flags: %c, %d, %cd

        :return: counts of the p_attribute (combinations) of the positions
        :rtype: DataFrame

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
                names=["freq", "unknown", "item"]
            )
            df_counts = df_counts.set_index('item')
            df_counts = df_counts[['freq']]
            df_counts.index.name = p_atts[0]

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
            logger.info("... counting %d tokens" % len(tokens))
            df_counts = DataFrame.from_dict(
                Counter(tokens), orient='index', columns=['freq']
            )
            df_counts = df_counts[['freq']]
            df_counts.index.name = p_atts[0]

        elif strategy == 3:
            # split YES; flags NO; combo YES
            # generally fastest
            with NamedTemporaryFile(mode="wt") as f:
                logger.info("... writing dump to disk")
                cqp.Exec('dump %s > "%s";' % (name, f.name))
                df_counts = cwb_scan_corpus(f.name, self.corpus_name, p_atts)

        df_counts = df_counts.sort_values(by='freq', ascending=False)

        return df_counts

    @time_it
    def mwus(self, cqp, queries, p_atts=None, fill_missing=True, strategy=1):
        """Calculates frequencies for MWU queries in activated subcorpus.
        queries are a list of valid CQP queries, e.g.
        '[lemma="Angela"%cd & pos="NE"] [lemma="Merkel"%cd & pos="NE"]?'

        caveat: different indices for different strategies

        :param CQP cqp: running cqp process
        :param set queries: set of query strings to get frequency breakdown for
        :param bool fill_missing: count 0 for missing items?
        :param int strategy: strategy to use (see below)

        :return: counts (index: queries(strategy 1) or tokens (, column: freq)
        :rtype: DataFrame

        Strategy 1:
        for each item
            (1) run query for item
            (2) get size of corpus via cqp

        Strategy 2:
        (1) run query for all items at the same time
        (2) dump df
        (3) count_dump()

        Strategy 3:
        (1) run query for all items at the same time
        (2) count_matches()

        """

        queries = set(queries)  # only process each one query once
        name = 'tmp'            # subcorpus name to use

        if strategy == 1:
            if p_atts:
                logger.warning(
                    "mwus: cannot get frequency breakdown when not inspecting dump"
                )
                strategy = 2

        if not p_atts:
            p_atts = ['word']   # necessary for strategies 2 & 3

        if strategy == 3 and len(p_atts) > 1:
            logger.warning(
                "mwus: cannot combine query when looking at several p-attributes"
            )
            strategy = 2

        logger.info("mwus: strategy %s" % strategy)

        if strategy == 1:
            logger.info("... running each query")
            freqs = list()
            for query in queries:
                cqp.Exec('%s=%s;' % (name, query))
                freq = cqp.Exec('size %s;' % name)
                freqs.append(freq)
            df = DataFrame(data=freqs, index=queries, columns=['freq'])
            df.index.name = 'query'

        elif strategy == 2:
            query = "|".join(queries)
            cqp.Exec('%s=%s;' % (name, query))
            df_dump = cqp.Dump(name)
            df = self.dump(df_dump, start='match', end='matchend',
                           p_atts=p_atts, split=False, strategy=1)
            if len(p_atts) == 1:
                df.index = [item[0] for item in df.index]
                df.index.name = p_atts[0]

        elif strategy == 3:
            query = "|".join(queries)
            cqp.Exec('%s=%s;' % (name, query))
            df = self.matches(cqp, name, p_atts=p_atts,
                              split=False, flags=None, strategy=2)

        # post-process dataframe
        df["freq"] = df["freq"].astype(int)
        df = df.sort_values(by=["freq"], ascending=False)

        # df = df.loc[df["freq"] != 0]

        return df
