#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""cwb.py

definition of the Corpora, Corpus and SubCorpus classes

"""
import logging
import os
from io import StringIO

# requirements
from numpy import maximum, minimum
from pandas import DataFrame, concat, read_csv
from pandas.errors import EmptyDataError

# part of module
from .cache import Cache, generate_idx, generate_library_idx
from .cl import Corpus as Attributes
from .collocates import Collocates
from .concordances import Concordance, format_line
from .counts import Counts, cwb_scan_corpus
from .cqp import start_cqp
from .keywords import Keywords
from .utils import (aggregate_matches, chunk_anchors, correct_anchors,
                    decode, dump_left_join, fold_df, format_roles,
                    intersect_intervals, merge_intervals,
                    preprocess_query, time_it)
from .version import __version__

logger = logging.getLogger(__name__)


class Corpora:
    """Interface to CWB-indexed corpora.

    """

    def __init__(self, cqp_bin='cqp',
                 registry_dir='/usr/local/share/cwb/registry/'):
        """Establish connection to registry and CQP.

        :param str cqp_bin: /path/to/cqp-binary
        :param str registry_dir: /path/to/cwb/registry/

        """

        self.registry_dir = registry_dir
        self.cqp_bin = cqp_bin

    def __str__(self):
        """Method for printing.

        :return: paths, available corpora
        :rtype: str

        """

        corpora = self.show()

        return '\n' + '\n'.join([
            f'registry directory: "{self.registry_dir}"',
            f'cqp binary:         "{self.cqp_bin}"',
            f'found {len(corpora)} corpora:',
            corpora.to_string(),
        ])

    def __repr__(self):
        """Info string

        """
        return self.__str__()

    def show(self):
        """Show all corpora defined in registry and available via CQP
        alongside corpus size (number of tokens).

        :return: available corpora
        :rtype: DataFrame

        """

        # get all corpora defined in registry
        cqp = start_cqp(self.cqp_bin, self.registry_dir)
        corpora = cqp.Exec("show corpora;").split("\n")
        cqp.__del__()

        # check availability and corpus sizes
        sizes = list()
        names = list()
        for corpus_name in corpora:
            try:
                sizes.append(len(Attributes(
                    corpus_name, registry_dir=self.registry_dir
                ).attribute('word', 'p')))
                names.append(corpus_name)
            except SystemError:
                logger.warning(
                    f'corpus "{corpus_name}" defined in registry but not available'
                )

        # create dataframe
        corpora = DataFrame({'corpus': names, 'size': sizes}).set_index('corpus')

        return corpora

    def corpus(self, corpus_name,
               lib_dir=None, data_dir=None):
        """Activate a corpus.

        :param str corpus_name: name of corpus in CWB registry
        :param str lib_dir: /path/to/macros/and/wordlists/
        :param str data_dir: /path/to/data/and/cache/

        :return: corpus
        :rtype: Corpus

        """

        return Corpus(corpus_name,
                      lib_dir=lib_dir,
                      cqp_bin=self.cqp_bin,
                      registry_dir=self.registry_dir,
                      data_dir=data_dir)


def init_data_dir(data_dir, corpus_name, lib_dir=None):
    """ get a data directory / ensure that the given one complies with schema

    """

    if data_dir is None:
        data_dir = os.path.join("/tmp", "ccc-" + str(__version__))
    if not isinstance(data_dir, str):
        raise ValueError("parameter data_dir must be str")

    # generate library idx to invalidate cache when updated
    if lib_dir is not None:
        lib_idx = generate_library_idx(lib_dir, 'lib-', 7)
    else:
        lib_idx = "lib-vanilla"

    # each corpus has its separate directory for each library
    subdir = corpus_name + "-" + lib_idx
    if not data_dir.endswith(subdir):
        data_dir = os.path.join(data_dir, subdir)

    # create directory
    try:
        os.makedirs(data_dir, exist_ok=True)
    except PermissionError:
        logger.error(f'no write permission at "{data_dir}"')
    else:
        return data_dir


class Corpus:
    """Interface to CWB-indexed corpus.

    """

    def __init__(self, corpus_name, lib_dir=None, cqp_bin='cqp',
                 registry_dir='/usr/local/share/cwb/registry/',
                 data_dir=None):
        """Establish connection to CQP and corpus attributes, set paths, read
        library.

        Raises KeyError if corpus not in registry.

        data directory contains subdirectories for each corpus and
        each library (/<data-dir>/<corpus>-<lib-idx>/CACHE)
        - marginals_complex
        - dump_from_s_att
        - dump_from_query

        :param str corpus_name: name of corpus in CWB registry
        :param str lib_dir: /path/to/macros/and/wordlists/
        :param str cqp_bin: /path/to/cqp-binary
        :param str registry_dir: /path/to/cwb/registry/
        :param str data_dir: /path/to/data/and/cache/

        """

        # preprocess data dir
        data_dir = init_data_dir(data_dir, corpus_name, lib_dir)

        # save paths
        self.data_dir = data_dir
        self.registry_dir = registry_dir
        self.cqp_bin = cqp_bin
        self.lib_dir = lib_dir

        # init (sub-)corpus information
        self.corpus_name = corpus_name
        self.subcorpus_name = None

        # init attributes
        self.attributes = Attributes(self.corpus_name, registry_dir=self.registry_dir)

        # get corpus size
        self.corpus_size = len(self.attributes.attribute('word', 'p'))

        # init cache
        self.cache = Cache(os.path.join(self.data_dir, "CACHE"))

        # init counts
        self.counts = Counts(self.corpus_name, self.registry_dir)

    def __str__(self):
        """Method for printing.

        :return: settings and paths
        :rtype: str

        """

        return '\n' + '\n'.join([
            f'corpus: {self.corpus_name} ({self.corpus_size} tokens)',
            f'data:   {self.data_dir}',
        ])

    def __repr__(self):
        """Info string.

        """
        return self.__str__()

    def available_macros(self):
        """Get available macros (either system-defined or via library).

        :return: defined macros
        :rtype: list

        """

        cqp = self.start_cqp()
        defined_macros = cqp.Exec("show macro;").split("\n")
        cqp.__del__()

        return defined_macros

    def available_wordlists(self):
        """Get available wordlists.

        :return: defined wordlists
        :rtype: list

        """

        cqp = self.start_cqp()
        defined_wordlists = cqp.Exec("show var;").split("\n")
        cqp.__del__()

        names = sorted(
            [n.rstrip(" =") for n in defined_wordlists if n.startswith("$") and n.endswith(" =")]
        )

        return names

    def available_attributes(self):
        """Get indexed p- and s-attributes. Will be run once when initializing
        the corpus.

        :return: attributes and annotation info
        :rtype: DataFrame

        """

        # use CQP's context descriptor
        cqp = self.start_cqp()
        cqp_ret = cqp.Exec('show cd;')
        cqp.__del__()

        # read as dataframe
        attributes = read_csv(
            StringIO(cqp_ret), sep='\t',
            names=['type', 'attribute', 'annotation', 'active']
        ).fillna(False)

        # post-process Boolean columns
        attributes['active'] = (attributes['active'] == "*")
        attributes['annotation'] = (attributes['annotation'] == '-V')

        return attributes

    def start_cqp(self):
        """Start CQP process.

        :return: CQP process
        :rtype: CQP

        """

        return start_cqp(
            self.cqp_bin,
            self.registry_dir,
            self.data_dir,
            self.corpus_name,
            self.lib_dir,
            self.subcorpus_name
        )

    def copy(self):
        """Get a fresh initialization of the corpus.

        :return: corpus
        :rtype: Corpus

        """

        return Corpus(
            self.corpus_name,
            self.lib_dir,
            self.cqp_bin,
            self.registry_dir,
            self.data_dir
        )

    ################
    # p-attributes #
    ################
    def cpos2patts(self, cpos, p_atts=['word'], ignore=True):
        """Retrieve p-attributes at corpus position.

        :param int cpos: corpus position to fill
        :param list p_atts: p-attribute(s) to fill position with
        :param bool ignore: whether to return (None, ..) for -1

        :return: p-attribute(s) at cpos
        :rtype: tuple

        """

        return self.counts._cpos2patts(cpos, p_atts, ignore)

    def marginals(self, items=None, p_atts=['word'], flags=0, pattern=False):
        """Extract marginal frequencies. If no items are given, return
        frequencies of all items.

        :param list items: items to get marginals for
        :param str p_att: p-attribute to get frequencies for
        :param int flags: 1 = %c, 2 = %d, 3 = %cd (will activate wildcards)
        :param bool pattern: activate wildcards?

        :return: frequencies of the items in the whole corpus indexed by items
        :rtype: FreqFrame

        """

        # allow lazy evocation
        p_atts = [p_atts] if isinstance(p_atts, str) else p_atts

        # simple
        if len(p_atts) == 1 and items is not None:
            return self._marginals_simple(items, p_atts[0], flags, pattern)

        else:
            return self._marginals_complex(items, p_atts)

    def _marginals_simple(self, items, p_att='word', flags=0, pattern=False):
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

        if self.subcorpus_name is not None:
            logger.warning('retrieving corpus marginals, not subcorpus marginals')

        pattern = True if flags > 0 else pattern
        att = self.attributes.attribute(p_att, 'p')

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

    def _marginals_complex(self, items, p_atts=['word']):
        """Extract marginal frequencies for p-attribute combinations,
        e.g. ["lemma", "pos"].  0 if not in corpus.  Marginals are
        retrieved using cwb-scan-corpus, result is cached.

        :param list items: list of tuples
        :param list p_atts: list of p-attributes

        :return: counts of the items in the whole corpus indexed by items
        :rtype: FreqFrame

        """

        if self.subcorpus_name is not None:
            logger.warning('retrieving corpus marginals, not subcorpus marginals')

        # get all marginals for p-att combination
        identifier = "-".join(p_atts) + "-marginals"
        df = self.cache.get(identifier)
        if df is not None:
            # get from cache if possible
            logger.info('using cached version of marginals of "%s"' % "_".join(p_atts))
        else:
            # calculate all marginals for p-att combination
            df, R = cwb_scan_corpus(
                self.corpus_name, self.registry_dir, p_atts=p_atts, min_freq=0
            )
            self.cache.set(identifier, df)

        if items is not None:
            # preprocess tuples
            items = [" ".join(i) for i in items] if isinstance(items[0], tuple) else items
            # select relevant rows
            df = df.reindex(items)
            df = df.fillna(0, downcast='infer')

        # sort by frequency
        df = df.sort_values(by=['freq', 'item'], ascending=False)

        return df

    ################
    # s-attributes #
    ################
    def cpos2sid(self, cpos, s_att):
        """Get cwb-id of s-att at cpos. -1 if not present.

        :param int cpos: corpus position
        :param str s_atts: s-attribute to get cwb-id for

        :return: cwb-id
        :rtype: int

        """
        s_attributes = self.attributes.attribute(s_att, "s")
        try:
            return s_attributes.cpos2struc(cpos)
        except KeyError:
            return -1

    ##############
    # subcorpora #
    ##############
    def show_nqr(self):
        """Get subcorpora defined in CQP as DataFrame.

        :return: available subcorpora
        :rtype: DataFrame

        """
        cqp = self.start_cqp()
        cqp_return = cqp.Exec("show named;")

        try:
            df = read_csv(StringIO(cqp_return), sep="\t", header=None)
            df.columns = ["storage", "corpus:subcorpus", "size"]
            crpssbcrps = df["corpus:subcorpus"].str.split(":", n=1).str
            df['corpus'] = crpssbcrps[0]
            df['subcorpus'] = crpssbcrps[1]
            df.drop('corpus:subcorpus', axis=1, inplace=True)
            df = df[['corpus', 'subcorpus', 'size', 'storage']]
        except EmptyDataError:
            logger.info("no subcorpora defined")
            df = DataFrame(columns=['corpus', 'subcorpus', 'size', 'storage'])

        cqp.__del__()

        return df

    ##################
    # CREATING DUMPS #
    ##################
    def dump_from_s_att(self, s_att, annotation=True):
        """Create s-attribute spans as DataFrame of corpus positions.
        Resulting df_dump is indexed by (match, matchend).

        Note that s-attribute values are not indexed by the CWB.
        CWB.CL implementation just iterates over all annotations.

        This method thus creates a dataframe with the
        (non-overlapping) spans encoded as matches

        === (match, matchend) $s_cwbid, $s* ===

        and caches the result.

        $s is only created if annotation is True and attribute is
        actually annotated.

        :param str s_att: s-attribute to get spans and annotation for
        :param bool annotation: whether to retrieve annotation (if present)

        :return: df_dump
        :rtype: DataFrame

        """

        # retrieve from cache if possible
        identifier = s_att + "-spans"
        df = self.cache.get(identifier)
        if df is not None:
            logger.info(f'using cached version of spans of "{s_att}"')
            return df

        # compute
        logger.info(f'creating dataframe of spans of "{s_att}"')

        df = DataFrame(list(self.attributes.attribute(s_att, 's')))
        # two or three columns: 0 (start), 1 (end), 2* (annotation)
        if annotation:
            annotation = (2 in df.columns)  # just to make sure ...
            if not annotation:
                logger.info(f's-att "{s_att}" does not have any annotation')
            else:
                df[2] = df[2].apply(decode)

        # post-process
        df = df.reset_index()
        df = df.rename({'index': s_att + '_cwbid',
                        0: 'match',
                        1: 'matchend',
                        2: s_att}, axis=1)
        df = df.set_index(['match', 'matchend'])

        # put into cache
        self.cache.set(identifier, df)

        return df

    def dump_from_query(self, query, s_query=None, anchors=[],
                        match_strategy='standard', name='Last', save=False,
                        cwb_version=None, propagate_error=False):
        """Execute query, get DataFrame of corpus positions (CWB dump).
        Resulting df_dump is indexed by (match, matchend).

        Note that in the CWB, only two anchors can be active
        simultaneously. The method thus runs the query once with
        anchors set to [0, 1], and then collects the remaining anchor
        points by running the query again on the NQR of the first
        query run for each pair of remaining anchor points.  Optional
        columns for each anchor:

        === (match, matchend), 0*, ..., 9* ===

        The result is cached.

        :param str query: valid CQP query (without 'within' clause)
        :param str s_query: s-attribute used for initial query
        :param list anchors: anchors to search for
        :param str match_strategy: CQP matching strategy
        :param str name: name for NQR
        :param bool save: whether to save NQR to disk

        :return: df_dump
        :rtype: DataFrame

        """

        # identify query
        if self.subcorpus_name is not None:
            # check subcorpus size to avoid confusion when re-naming
            cqp = self.start_cqp()
            sbcrpssize = cqp.Exec(f"size {self.subcorpus_name}")
            cqp.__del__()
        else:
            sbcrpssize = None

        identifier = generate_idx([
             query, s_query, anchors, match_strategy, self.subcorpus_name, sbcrpssize
        ], prefix="df_dump:")

        # retrieve from cache if possible
        df_dump = self.cache.get(identifier)
        if df_dump is not None:
            logger.info(f'using cached version "{identifier}" of df_dump with {len(df_dump)} matches')
            return df_dump

        # init cqp and set matching strategy
        cqp = self.start_cqp()
        cqp.Exec(f'set MatchingStrategy "{match_strategy}";')

        # get CWB version
        if cwb_version is None:
            cwb_version = {'major': cqp.major_version,
                           'minor': cqp.minor_version,
                           'patch': cqp.beta_version}

        # include optional within clause
        if s_query is None:
            start_query = query
        else:
            start_query = query + ' within ' + s_query

        # get anchors
        remaining_anchors = list(chunk_anchors(anchors, 2))

        # run the query
        logger.info("running CQP query")
        # first run: anchors at 0 and 1 (considering within clause)
        cqp.Exec('set ant 0; ank 1;')
        df_dump = cqp.nqr_from_query(
            query=start_query,
            name=name,
            match_strategy=match_strategy,
            return_dump=True,
            propagate_error=propagate_error
        )
        if propagate_error and isinstance(df_dump, str):
            return df_dump

        logger.info(f"found {len(df_dump)} matches")

        # if there's nothing to return ...
        if len(df_dump) == 0:
            cqp.__del__()
            return df_dump

        df_dump.columns = [0, 1]

        if len(remaining_anchors) > 0:

            # restrict subsequent queries on initial matches
            if (cwb_version['minor'] >= 5) or (cwb_version['minor'] == 4 and cwb_version['patch'] >= 31):
                cqp.Exec(f"Temp = <<{name}/>> ( {query} );")
            elif cwb_version['minor'] == 4 and cwb_version['patch'] >= 16:
                cqp.nqr_activate(self.corpus_name, name)
            else:
                raise NotImplementedError("cannot work with several anchors for CWB versions older than 3.4.16")

            for pair in remaining_anchors:

                logger.info(f".. running query for anchor(s) {str(pair)}")
                # set appropriate anchors
                cqp.Exec(f'set ant {pair[0]};')
                if len(pair) == 2:
                    cqp.Exec(f'set ank {pair[1]};')
                else:
                    cqp.Exec('set ank 1;')

                # dump new anchors
                if (cwb_version['minor'] >= 5) or (cwb_version['minor'] == 4 and cwb_version['patch'] >= 31):
                    cqp.Query(f"Temp = <<{name}/>> ( {query} );")
                elif cwb_version['minor'] == 4 and cwb_version['patch'] >= 16:
                    cqp.Query(f'Temp = <match> ( {query} );')
                df = cqp.Dump("Temp")

                # select columns and join to global df
                if len(pair) == 2:
                    df.columns = [pair[0], pair[1]]
                else:
                    df.columns = [pair[0], 1]
                    df = df.drop(1, axis=1)
                df_dump = df_dump.join(df)

            # NA handling
            logger.info("post-processing dataframe")
            # df_dump = df_dump.dropna(axis=1, how='all')
            # it is more reasonable to yield all requested columns
            # (even if some are all NA) -- instead of silently
            # dropping columns
            df_dump = df_dump.fillna(-1, downcast='infer')

        # restrict output to requested anchors
        df_dump = df_dump[anchors]

        # put into cache
        self.cache.set(identifier, df_dump)

        if save:
            cqp.nqr_save(self.corpus_name, name)

        cqp.__del__()

        return df_dump

    #################################################
    # WORKING ON DUMPS ##############################
    #################################################
    def _dump2patt_row(self, row, p_att, start, end):
        """Retrieve p-attribute annotation from start to end of one row.

        :param Series row: dataframe row that contains start and end keys
        :param str p_att: p-attribute to retrieve
        :param str start: key of start column (int or str)
        :param str end: key of end column (int or str)

        :return: p-attribute annotation
        :rtype: str
        """

        # treat missing columns like missing values
        cpos_start = row.get(start, -1)
        cpos_end = row.get(end, -1)

        # if both are missing, return empty string
        if cpos_start == cpos_end == -1:
            return ""
        # if one of them is missing, set start = end or end = start
        if cpos_start == -1:
            cpos_start = cpos_end
        if cpos_end == -1:
            cpos_end = cpos_start

        # lexicalize
        p = self.attributes.attribute(p_att, 'p')
        return " ".join(p[int(cpos_start): int(cpos_end) + 1])

    def dump2patt(self, df_dump, p_att='word', start='match', end='matchend'):
        """Retrieve p-attribute annotation from start to end.

        === (match, matchend), $p ===

        Any additional columns of df_dump are preserved as long as
        there are no conflicts (in which case the original column will
        be overwritten).

        :param DataFrame df_dump: DataFrame with specified columns (possibly as index)
        :param str p_att: p-attribute to retrieve
        :param str start: key of start column (int or str)
        :param str end: key of end column (int or str)

        :return: df_dump
        :rtype: DataFrame

        """

        # pre-process
        index_names = df_dump.index.names
        df = df_dump.reset_index()

        # retrieve attribute
        df[p_att] = df.apply(
            lambda row: self._dump2patt_row(row, p_att, start, end), axis=1
        )

        # post-process
        df = df.set_index(index_names)

        return df

    def dump2satt(self, df_dump, s_att, annotation=True):
        """Retrieve cwb-id, span, and annotation of s-attribute at match.

        Note that this only takes into account the match, not the
        matchend. This is reasonable assuming that the retrieved s-att
        comprises complete matches (match..matchend).

        === (match, matchend), $s_cwbid, $s_span, $s_spanend, $s*  ===

        $s is only created if annotation is True and attribute is
        actually annotated.

        Any additional columns of df_dump are preserved as long as
        there are no conflicts (in which case the original columns
        will be overwritten).

        :param DataFrame df_dump: DataFrame indexed by (match, matchend)
        :param str s_att: s-attribute to retrieve
        :param bool annotation: whether to retrieve annotation of s-att

        :return: df_dump
        :rtype: DataFrame

        """

        # init dataframe
        df = df_dump.reset_index()[['match', 'matchend']]

        # get $s_id
        df[s_att + "_cwbid"] = df.match.apply(
            lambda x: self.cpos2sid(x, s_att)
        )
        nr_missing = (df[s_att + '_cwbid'] == -1).sum()
        logger.info(f's-att "{s_att}" exists at {len(df)-nr_missing} of {len(df)} matches')

        # retrieve where possible
        s_attributes = self.attributes.attribute(s_att, "s")
        df_s = df.loc[~(df[s_att + "_cwbid"] == -1)]
        df = df.join(DataFrame(
            index=df_s.index,
            data=df_s[s_att + "_cwbid"].apply(lambda x: s_attributes[int(x)]).to_list()
        ))

        # two or three columns: 0 (start), 1 (end), 2* (annotation)
        if annotation:
            annotation = (2 in df.columns)  # just to make sure ...
            if not annotation:
                logger.info(f's-att "{s_att}" does not have any annotation')
            else:
                df[2] = df[2].apply(decode)

        # restore original index and post-process
        df = df.set_index(['match', 'matchend'])
        df = df.rename({0: s_att + '_span',
                        1: s_att + '_spanend',
                        2: s_att}, axis=1)

        # join to original dataframe
        df_dump = df_dump.join(df, lsuffix='_bak')
        df_dump = df_dump[[col for col in df_dump if not str(col).endswith('_bak')]]
        if s_att + '_span' in df.columns and s_att + '_spanend' in df.columns:
            df_dump[[
                s_att + '_span', s_att + '_spanend'
            ]] = df[[
                s_att + '_span', s_att + '_spanend'
            ]].fillna(-1, downcast='infer')
        else:
            df_dump[[
                s_att + '_span', s_att + '_spanend'
            ]] = -1

        return df_dump

    def dump2context(self, df_dump, context_left, context_right, context_break):
        """Extend df_dump to context, breaking the context at context_break.

        === (match, matchend), contextid*, context, contextend  ===

        Columns for $context_break, $context_break_cwbid,
        $context_break_span, $context_break_spanend, are also created
        (if applicable).

        Any additional columns of df_dump are preserved.

        Note that in contrast to matches, contexts may overlap.

        For positions where the s-att specified by context_break does
        not exist, context_break is ignored.

        The context creation algorithm does not take into account that
        match and matchend may be part of different spans defined by
        context_break; it only looks at the s-attributes of match, not
        of matchend.

        For the _context_ column (left hand side), the strategy is as
        follows; the strategy for _contextend_ (right hand side) is
        analogous (using context_right, matchend and
        context_break_spanend).

        - if context_break_span is None and context_left is None
          => context = match
        - if context_break_span is None and context_left is not None
          => context = max(0, match - context_left)
        - if context_break_span is not None and context_left is None
          => context = context_break_span
        - if context_break_span is not None and context_left is not None
          => context = max(match - context_left, s_start)

        :param DataFrame df_dump: DataFrame indexed by (match, matchend)
        :param int context_left: maximum context to the left of match
        :param int context_right: maximum context to the right of matchend
        :param str context_break: s-attribute to confine context

        """

        if context_break is None:
            df = df_dump.reset_index()
            # left
            if context_left is None:
                df['context'] = df.match
            else:
                df['context'] = maximum(0, df.match - context_left)
            # right
            if context_right is None:
                df['contextend'] = df.matchend
            else:
                df['contextend'] = minimum(
                    self.corpus_size - 1, df.matchend + context_right
                )
        else:
            # get context confined by s-attribute
            df = self.dump2satt(df_dump, context_break, annotation=False).reset_index()

            # save contextid
            df['contextid'] = df[context_break + '_cwbid']

            # replace -1 to not confuse min()
            df[[
                context_break + '_spanend'
            ]] = df[[context_break + '_spanend']].replace(-1, self.corpus_size + 1)

            # left
            if context_left is None:
                df['context'] = df[context_break + '_span']
            else:
                df['context'] = df.match - context_left
                df['context'] = df[[
                    'context', context_break + '_span'
                ]].max(axis=1)
            # right
            if context_right is None:
                df['contextend'] = df[context_break + '_spanend']
            else:
                df['contextend'] = df.matchend + context_right
                df['contextend'] = df[[
                    'contextend', context_break + '_spanend'
                ]].min(axis=1)

            # revert replacement
            df[[
                context_break + '_spanend'
            ]] = df[[context_break + '_spanend']].replace(self.corpus_size + 1, -1)

        # restore original index
        df = df.set_index(['match', 'matchend'])

        return df

    #################################################
    # QUERY ALIASES #################################
    #################################################
    def query_s_att(self, s_att, values=set(), name=None, overwrite=True):
        """Get s-attribute spans as Dump, optionally restricting the spans by
        matching the provided values against the s-att annotations.

        === (match, matchend), $s_cwbid, $s* ===

        :param str s_att: s-attribute to use for spans
        :param set values: values of s-att annotation to restrict spans to

        :return: dump
        :rtype: Dump

        """

        df_spans = self.dump_from_s_att(s_att)

        # restrict to certain values
        if len(values) > 0:
            if s_att not in df_spans.columns:
                logger.error("cannot restrict spans without annotation")
                df_spans = DataFrame(columns=['match', 'matchend']).set_index(
                    ['match', 'matchend']
                )
            else:
                values = set(values)
                logger.info(f"restricting spans using {len(values)} values")
                df_spans = df_spans.loc[df_spans[s_att].isin(values)]

        # if this is a subcorpus, only return intersection
        if self.subcorpus_name is not None:
            columns_left = list(self.df.columns)
            columns_right = list(df_spans.columns)
            intersection = intersect_intervals(
                self.df.reset_index()[['match', 'matchend'] + columns_left].values.tolist(),
                df_spans.reset_index()[['match', 'matchend'] + columns_right].values.tolist()
            )
            df_spans = DataFrame(intersection)
            df_spans.columns = ['match', 'matchend'] + columns_left + columns_right
            df_spans = df_spans.set_index(['match', 'matchend'])

        # return SubCorpus
        return self.subcorpus(subcorpus_name=name, df_dump=df_spans, overwrite=overwrite)

    def query_cqp(self, cqp_query, context=20, context_left=None,
                  context_right=None, context_break=None, corrections=dict(),
                  match_strategy='standard', name=None, propagate_error=False,
                  overwrite=True):
        """Get query result as (context-extended) Dump (with corrected
        anchors). If a name is given, the resulting NQR (without
        context and before anchor correction) will be written to disk
        in CWB binary format.

        === (match, matchend), 0*, ..., 9*, contextid*, context*, contextend* ===

        :param str query: CQP query
        :param int context: maximum context around match..matchend (symmetric)
        :param int context_left: maximum context left to the match
        :param int context_right: maximum context right to the matchend
        :param str context_break: s-attribute to confine context to
        :param dict corrections: corrections {anchor: offset}
        :param str match_strategy: CQP matching strategy
        :param str name: name for NQR

        :return: dump
        :rtype: Dump

        """

        # preprocess input
        save = False if name is None else True  # save NQR from CQP to disk?
        query_dict = preprocess_query(cqp_query)
        query = query_dict['query']
        s_query = query_dict['s_query']
        anchors = query_dict['anchors']
        s_query = context_break if s_query is None else s_query
        context_left = context if context_left is None else context_left
        context_right = context if context_right is None else context_right

        # get dump from query
        df_dump = self.dump_from_query(
            query=query,
            s_query=s_query,
            anchors=anchors,
            match_strategy=match_strategy,
            name=name,
            save=save,
            propagate_error=propagate_error
        )

        if propagate_error and isinstance(df_dump, str):
            return df_dump

        # empty return?
        if len(df_dump) == 0:
            logger.info("found 0 matches")
            df_dump = DataFrame(columns=['match', 'matchend']).set_index(
                ['match', 'matchend']
            )
        else:
            # extend dump to context
            df_dump = self.dump2context(
                df_dump, context_left, context_right, context_break
            )
            # apply corrections to anchor points
            df_dump = correct_anchors(df_dump, corrections)

        # return SubCorpus
        return self.subcorpus(subcorpus_name=name, df_dump=df_dump, overwrite=overwrite)

    def query(self, cqp_query=None, context=20, context_left=None,
              context_right=None, context_break=None,
              corrections=dict(), s_query=None, s_values=None,
              match_strategy='standard', name=None, propagate_error=False):
        """Query the corpus, get the result as Dump.

        query wrapper

        - cqp-query (with or without s-query = context-break)

        - s-query (with or without s-values)

        - cqp-query + s-query + s-values (not implemented)

        """
        s_query = context_break if s_query is None else s_query

        if cqp_query is None and s_query is None:
            raise ValueError("you have to provide cqp_query or s_query")

        if cqp_query is None:
            return self.query_s_att(s_query, s_values, name)

        elif s_values is None:
            return self.query_cqp(cqp_query, context, context_left,
                                  context_right, s_query, corrections,
                                  match_strategy, name, propagate_error)

        else:
            raise NotImplementedError()

    def quick_query(self, s_context, topic_query="", filter_queries=[], match_strategy='longest'):
        """makes sure query result is saved in CWB binary format

        without topic query:
        - finds all s_context spans that contain at least one filter_query
        with topic query:
        - finds all s_context spans that contain topic_query and all filter_queries

        the distinction between with and without topic_query is made
        because in collocation analyses, one topic is combined with
        different other filters; the topic-query then does not have to
        be queried again, only the filters on the topic-context

        :return: identifier (name of NQR on disk)
        :rtype: str

        """

        logger.info("-"*20 + " enter quick-query " + "-"*20)
        if len(topic_query) == 0:

            identifier = generate_idx([self.subcorpus_name, filter_queries, s_context, match_strategy], prefix='Query')

            cqp = self.start_cqp()
            cqp.Exec(f'set MatchingStrategy "{match_strategy}";')
            size = int(cqp.Exec(f'size {identifier};'))

            if size == 0:
                disjunction = " | ".join(['(' + q + ')' for q in filter_queries])
                logger.info(f'disjunction query: {disjunction}')
                cqp.Query(f'{identifier} = {disjunction} within {s_context} expand to {s_context};')
                logger.info(f'.. saving {identifier} in CWB binary format')
                cqp.Exec(f'save {identifier};')

            cqp.__del__()

            return identifier

        # IDENTIFY
        topic_identifier = generate_idx([self.subcorpus_name, topic_query, s_context, match_strategy], prefix='Query')
        filter_identifier = generate_idx([self.subcorpus_name, topic_query, s_context, match_strategy, filter_queries], prefix='Query')

        # CHECK CQP
        cqp = self.start_cqp()
        cqp.Exec(f'set MatchingStrategy "{match_strategy}";')

        # does filter already exist? then we're done
        size = int(cqp.Exec(f'size {filter_identifier};'))
        if size == 0:

            # does topic already exist?
            size = int(cqp.Exec(f'size {topic_identifier};'))
            logger.info(f'topic query: {topic_query}')
            if size == 0:
                # TOPIC
                cqp.Query(f'{topic_identifier} = {topic_query} expand to {s_context};')
                logger.info(f'.. saving {topic_identifier} in CWB binary format')
                cqp.Exec(f'save {topic_identifier};')
            logger.info('.. size: ' + cqp.Exec(f'size {topic_identifier};'))

            # FILTER
            cqp.Exec(f'{filter_identifier} = {topic_identifier};')
            for query in filter_queries:
                logger.info(f'filter query: {query}')
                cqp.Exec(f'{filter_identifier} expand to {s_context};')
                cqp.Query(f'{filter_identifier} = {query} expand to {s_context};')
                logger.info('.. size: ' + cqp.Exec(f'size {filter_identifier};'))

            # SAVE
            logger.info(f'.. saving {filter_identifier} in CWB binary format')
            cqp.Exec(f'save {filter_identifier};')

        cqp.__del__()

        logger.info("-"*20 + " exit quick-query  " + "-"*20)

        return filter_identifier

    @time_it
    def quick_conc(self, topic_query, s_context, window, order=42,
                   cut_off=100, highlight_queries=dict(),
                   filter_queries=dict(), p_show=['word'], s_show=[],
                   match_strategy='longest', htmlify_meta=True, cwb_ids=False):
        """

        :return: concordance lines, each one a dict
        :rtype: list(dict)
        """

        logger.info('quick-conc :: quick concordancing should be quick')

        if order == 'first':
            cqp_order = ""

        elif isinstance(order, int):
            cqp_order = f'randomize {order}'

        else:
            raise ValueError

        if len(topic_query) == 0:

            queries = {**highlight_queries, **filter_queries}

            # INIT CQP
            identifier = self.quick_query(s_context, topic_query="", filter_queries=list(queries.values()), match_strategy=match_strategy)
            cqp = self.start_cqp()

            # init CONTEXT (TextConstellation)
            cqp.Exec(f'sort {identifier} {cqp_order};')
            cqp.Exec(f'cut {identifier} {cut_off};')
            df_context = cqp.Dump(f'{identifier};')
            subcorpus_context = self.subcorpus(None, df_context).set_context(context_break=s_context)
            df_context = subcorpus_context.df[['contextid']]
            df_context = df_context.reset_index().set_index('contextid')

            # HIGHLIGHT
            cqp.Exec(f'{identifier};')
            cqp.Exec(f'set MatchingStrategy "{match_strategy}";')
            for name, query in queries.items():
                cqp.Exec(f'Temp = {query};')
                df_query = cqp.Dump('Temp;')
                if len(df_query) > 0:
                    subcorpus_query = self.subcorpus(None, df_query).set_context(context_break=s_context)
                    df_query = subcorpus_query.df[['contextid']]
                    df_agg = aggregate_matches(df_query, name)
                    df_context = df_context.join(df_agg)
                else:
                    df_context[name] = None
                    df_context[name + '_BOOL'] = False
                    df_context[name + '_COUNTS'] = 0
            cqp.__del__()

            # index by CONTEXT MATCHES
            df = df_context.set_index(['match', 'matchend'])
            names = list(queries.keys())
            names_bool = [n + '_BOOL' for n in names]
            names_count = [n + '_COUNTS' for n in names]
            for b, c in zip(names_bool, names_count):
                df[b] = df[b].fillna(False)
                df[c] = df[c].fillna(0)

            # ACTUAL CONCORDANCING
            conc = Concordance(self.copy(), df)
            lines = conc.lines(form='dict', p_show=p_show, s_show=s_show, order=order, cut_off=cut_off, cwb_ids=cwb_ids)
            output = lines.apply(lambda row: format_roles(row, names, s_show=names_bool+s_show, window=0,
                                                          htmlify_meta=htmlify_meta), axis=1)

        else:

            if len(filter_queries.keys() & highlight_queries.keys()) > 0:
                logger.warning("query names for filter and highlighting overlap")
                highlight_queries = {name: query for (name, query) in highlight_queries.items() if name not in filter_queries.keys()}

            # INIT CQP
            logger.info("quick-conc :: getting context")
            identifier = self.quick_query(s_context, topic_query, list(filter_queries.values()), match_strategy)
            cqp = self.start_cqp()
            cqp.Exec(f'{identifier};')
            cqp.Exec(f'set MatchingStrategy "{match_strategy}";')
            full_size = int(cqp.Exec(f'size {identifier};'))

            if len(filter_queries) == 0:
                cut_off_pre = cut_off
                logger.info(f"quick-conc :: no further filtering according to window, applying cut-off ({cut_off_pre})")

            else:
                # we still have to filter according to window size and highlight all discoursemes
                # we just take a maximum of n*cut_off
                # TODO take next batch if needed
                cut_off_pre = 10 * cut_off
                logger.info(f"quick-conc :: further filtering according to window, applying extended cut-off ({cut_off_pre})")

            cqp.Exec(f'sort {identifier} {cqp_order};')
            cqp.Exec(f'cut {identifier} {cut_off_pre};')
            cqp.Exec(f'{identifier} = {identifier} expand to {s_context};')

            df_context = cqp.Dump(f'{identifier};')
            subcorpus_context = self.subcorpus(df_dump=df_context, overwrite=False).set_context(window, s_context, overwrite=False)
            df_context = subcorpus_context.df[['contextid', 'context', 'contextend']]

            # index by TOPIC MATCHES
            logger.info("quick-conc :: index by topic")
            cqp.Exec(f'Temp = {topic_query};')
            df_query = cqp.Dump('Temp;')
            subcorpus_query = self.subcorpus(df_dump=df_query, overwrite=False).set_context(window, s_context, overwrite=False)
            df_context = dump_left_join(df_context, subcorpus_query.df, 'topic', drop=True, window=window)
            df_context = df_context.set_index(['match_topic', 'matchend_topic'])
            df_context.index.names = ['match', 'matchend']
            df_context = df_context.astype({'offset_topic': 'int'})

            # collect cpos of filter
            logger.info("quick-conc :: collecting cpos of filter")
            matches_filter = dict()
            for name, query in list(filter_queries.items()):
                cqp.Exec(f'Temp = {query};')
                matches_filter[name] = self.subcorpus(df_dump=cqp.Dump('Temp;'), overwrite=False).matches()

            # .. and highlight
            logger.info("quick-conc :: collecting cpos of highlight")
            matches_highlight = dict()
            for name, query in list(highlight_queries.items()):
                cqp.Exec(f'Temp = {query};')
                matches_highlight[name] = self.subcorpus(df_dump=cqp.Dump('Temp;'), overwrite=False).matches()

            logger.info("quick-conc :: formatting")
            output = df_context.apply(
                lambda row: format_line(self, row.name, row, p_show, s_show, matches_filter, matches_highlight, window,
                                        htmlify_meta=htmlify_meta, cwb_ids=cwb_ids),
                axis=1
            )
            output = [line for line in output.values if line is not None]
            output = output[:cut_off]

            actual_size = len(output)
            if cut_off and (cut_off_pre < full_size) and (actual_size < cut_off):
                logger.warning("quick-conc :: potentially missing concordance lines")
                logger.warning(f'- full size:           {full_size}')
                logger.warning(f'- retrieved size       {actual_size}')
                logger.warning(f'- cut-off:             {cut_off}')
                logger.warning(f'- preliminary cut-off: {cut_off_pre}')

        logger.info("quick-conc :: exit")
        return list(output)

    def subcorpus(self, subcorpus_name=None, df_dump=None, overwrite=True):

        return SubCorpus(subcorpus_name, df_dump, self.corpus_name,
                         self.lib_dir, self.cqp_bin, self.registry_dir, self.data_dir, overwrite)


class SubCorpus(Corpus):

    def __init__(self, subcorpus_name, df_dump, corpus_name,
                 lib_dir=None, cqp_bin='cqp',
                 registry_dir='/usr/local/share/cwb/registry/',
                 data_dir=None, overwrite=True):
        """
        :param str subcorpus_name: name of NQR in CQP
        :param DataFrame df_dump: a "DumpFrame"

        a "DumpFrame" is a dataframe indexed by (match, matchend),
        i.e. non-overlapping corpus spans represented by integers,
        and without missing values.

        CREATION

        dump_from_query:
        - index <int, int> match, matchend: cpos
        - columns <int> 0*, .., 9*: anchor points (optional; missing = -1)

        dump_from_s_att:
        - index <int, int> match, matchend: cpos
        - column <int> $s_cwbid: id
        - column <str> $s: annotation (optional)

        TRANSFORMATION (additional columns are preserved)

        dump2patt:
        - index <int, int> match, matchend: cpos
        - column <str> $p: " "-joined tokens (match..matchend or regions of input columns)

        dump2satt:
        - index <int, int> match, matchend: cpos
        - column <int> $s_cwbid: id (missing = -1) of s_att at match cpos
        - column <int> $s_span: cpos (missing = -1)
        - column <int> $s_spanend: cpos (missing = -1)
        - column <str> $s*: annotation (optional)

        dump2context:
        - index <int, int> match, matchend: cpos
        - column <int> contextid: of id (optional; duplicate of $s_cwbid)
        - column <int> context: cpos
        - column <int> contextend: cpos
        - column <int> $s_cwbid: id (optional; missing = -1)
        - column <int> $s_span: cpos (missing = -1)
        - column <int> $s_spanend: cpos (missing = -1)

        QUERY ALIASES

        query_cqp:
        - index <int, int> match, matchend: cpos
        - columns <int> 0*, .., 9*: anchor points (optional; missing = -1)
        - column <int> contextid: of id (optional)
        - column <int> context: cpos (optional)
        - column <int> contextend: cpos (optional)

        query_s_att:
        - index <int, int> match, matchend: cpos
        - column <int> $s_cwbid: id
        - column <str> $s: annotation (optional)

        """

        super().__init__(corpus_name, lib_dir, cqp_bin, registry_dir, data_dir)

        if (subcorpus_name is None and df_dump is None):
            logger.warning('no subcorpus information provided, returning Corpus')

        else:
            if subcorpus_name is None:  # (and df_dump is not None)
                subcorpus_name = generate_idx([df_dump], prefix='df_')
                self._assign(subcorpus_name, df_dump, overwrite)

            elif df_dump is None:  # (and subcorpus_name is not None)
                cqp = self.start_cqp()
                df_dump = cqp.Dump(subcorpus=subcorpus_name)
                cqp.__del__()

            else:      # (both df_dump and subcorpus_name are given)
                self._assign(subcorpus_name, df_dump, overwrite)

            self.df = df_dump
            self.subcorpus_name = subcorpus_name

    def _assign(self, subcorpus_name, df_dump, overwrite):

        if subcorpus_name in self.show_nqr()['subcorpus'].values:
            # NQR exists
            if overwrite:
                logger.info(f'NQR "{subcorpus_name}" exists, overwriting')
                # create in CQP
                cqp = self.start_cqp()
                cqp.nqr_from_dump(df_dump, subcorpus_name)
                cqp.nqr_save(self.corpus_name, subcorpus_name)
                cqp.__del__()
            # else:
            #     logger.info(f'NQR "{subcorpus_name}" already exists')

        else:
            # create in CQP
            cqp = self.start_cqp()
            cqp.nqr_from_dump(df_dump, subcorpus_name)
            cqp.nqr_save(self.corpus_name, subcorpus_name)
            cqp.__del__()

        if subcorpus_name not in self.show_nqr()['subcorpus'].values:
            logger.error(f'could not assigne NQR "{subcorpus_name}" from dataframe')
        elif overwrite:
            logger.info(f'assigned NQR "{subcorpus_name}" from dataframe')

    def __str__(self):

        return '\n' + '\n'.join([
            f'corpus:    {self.corpus_name} ({self.corpus_size} tokens)',
            f'subcorpus: {self.subcorpus_name} ({self.size()} tokens in {len(self.df)} spans)',
            f'data:      {self.data_dir}'
        ]) + '\n'

    def __repr__(self):
        """Info string.

        """
        return self.__str__()

    def set_context(self, context=None, context_break=None,
                    context_left=None, context_right=None, overwrite=True):
        """Set context in the dump.

        """
        # pre-process context
        if context_left is None:
            context_left = context
        if context_right is None:
            context_right = context

        # set context
        df = self.dump2context(
            self.df, context_left, context_right, context_break
        )

        return self.subcorpus(self.subcorpus_name, df, overwrite=overwrite)

    def set_context_as_matches(self, subcorpus_name=None, overwrite=True):
        """Set match spans in the dump.

        """

        df_context = self.context()

        df_context['match'] = df_context['context']
        df_context['matchend'] = df_context['contextend']
        df_context = df_context.set_index(['match', 'matchend'])

        return self.subcorpus(subcorpus_name=subcorpus_name, df_dump=df_context, overwrite=overwrite)

    def correct_anchors(self, corrections):
        """Correct anchors by integer offsets.

        """
        self.df = correct_anchors(self.df, corrections)

    def breakdown(self, p_atts=['word'], flags=""):
        """Frequency breakdown of match..matchend.

        """

        logger.info('creating frequency breakdown')
        breakdown = self.counts.dump(
            df_dump=self.df,
            start='match', end='matchend',
            p_atts=p_atts, strategy=1
        )

        breakdown = fold_df(breakdown, flags)

        return breakdown

    def matches(self):
        """
        :return: cpos of (match .. matchend) regions
        :rtype: set
        """

        identifier = generate_idx([self.df.reset_index()[['match', 'matchend']]]) + "-matches"
        f1 = self.cache.get(identifier)
        if not isinstance(f1, set):
            f1 = set()
            for match, matchend in self.df.index:
                f1.update(range(match, matchend + 1))
            self.cache.set(identifier, f1)
        return f1

    def size(self):
        return (self.df.reset_index()['matchend'] - self.df.reset_index()['match'] + 1).sum()

    def context(self):
        """
        :return: cpos of (context .. contextend) regions including matches
        :rtype: DataFrame
        """

        identifier = generate_idx([self.df[['context', 'contextend']]]) + "-contexts"
        df = self.cache.get(identifier)
        if not isinstance(df, DataFrame):
            intervals = self.df[['context', 'contextend']].drop_duplicates().values.tolist()
            df = DataFrame.from_records(merge_intervals(intervals), columns=['context', 'contextend'])
            self.cache.set(identifier, df)
        return df

    def marginals(self, items=None, p_atts=['word'], start='match', end='matchend'):
        """
        :return: counts of (start .. end) regions including matches
        :rtype: DataFrame
        """

        identifier = generate_idx([self.df.reset_index()[[start, end]]]) + "-".join(p_atts) + "-marginals"
        df = self.cache.get(identifier)
        if not isinstance(df, DataFrame):
            df = self.counts.dump(
                self.df, start=start, end=end, p_atts=p_atts, split=True
            )
            self.cache.set(identifier, df)

        if items is not None:
            # preprocess tuples
            items = [" ".join(i) for i in items] if isinstance(items[0], tuple) else items
            # select relevant rows
            df = df.reindex(items)
            df = df.fillna(0, downcast='infer')

        # sort by frequency
        df = df.sort_values(by=['freq', 'item'], ascending=False)

        return df

    def concordance(self, form='simple', p_show=['word'], s_show=[],
                    order='first', cut_off=100, matches=None,
                    slots=None, cwb_ids=False):

        conc = Concordance(
            self.copy(),
            df_dump=self.df
        )

        return conc.lines(
            form=form,
            p_show=p_show,
            s_show=s_show,
            order=order,
            cut_off=cut_off,
            matches=matches,
            slots=slots,
            cwb_ids=cwb_ids
        )

    def collocates(self, p_query=['lemma'], mws=20, window=5,
                   order='O11', cut_off=100, ams=None, min_freq=2,
                   flags=None, marginals='corpus',
                   show_negative=False):

        mws = max(mws, window)

        coll = Collocates(self.copy(), self.df, p_query, mws)

        return coll.show(
            window=window,
            order=order,
            cut_off=cut_off,
            ams=ams,
            min_freq=min_freq,
            flags=flags,
            marginals=marginals,
            show_negative=show_negative
        )

    def keywords(self, p_query=['lemma'], order='O11', cut_off=100,
                 ams=None, min_freq=2, flags=None,
                 marginals='corpus', show_negative=False):

        kw = Keywords(self.copy(), self.df, p_query)

        return kw.show(
            order=order,
            cut_off=cut_off,
            ams=ams,
            min_freq=min_freq,
            flags=flags,
            marginals=marginals,
            show_negative=show_negative
        )


class SubCorpora:
    """
    partitioning of corpus
    - non-overlapping sets of regions (= match..matchend)
    - does not have to be exhaustive → complement
    """
    def __init__(self, corpus_name, mapping,
                 lib_dir=None,
                 cqp_bin='cqp',
                 registry_dir='/usr/local/share/cwb/registry/',
                 data_dir=None):
        """
        :param Corpus corpus: CWB corpus
        :param dict mapping: dictionary of {name: query} or DataFrame indexed by (match, matchend) with column 'subcorpus'

        query can be one of
        + <text>-query
        + cqp-query
        """

        self.corpus = Corpus(corpus_name, lib_dir, cqp_bin, registry_dir, data_dir)

        subcorpora = dict()
        if isinstance(mapping, DataFrame):
            column = 'subcorpus'
            for name, df in mapping.groupby(column):
                subcorpora[name] = self.corpus.subcorpus(None, df.drop(column, axis=1))

        elif isinstance(mapping, dict):
            raise NotImplementedError()

        else:
            raise ValueError()

        self.subcorpora = subcorpora

    def keywords(self):
        """
        - one vs. complement
        - one vs. another
        - one vs. rest
        """
        pass

    def query(self, cqp_query=None, context=20, context_left=None,
              context_right=None, context_break=None,
              corrections=dict(), s_query=None, s_values=None,
              match_strategy='longest', propagate_error=False):
        """
        - query each subcorpus defined in partioning
        - note that this finds at most the number of matches as querying the whole corpus
        - because matches might overlap with boundaries
        """

        s_query = context_break if s_query is None else s_query

        if cqp_query is None and s_query is None:
            raise ValueError("you have to provide cqp_query or s_query")

        out = list()
        if cqp_query is None:
            for name, subcorpus in self.subcorpora.items():
                df = self.query_s_att(s_query, s_values).df
                df['subcorpus'] = name
                out.append(df)

        elif s_values is None:
            for name, subcorpus in self.subcorpora.items():
                df = subcorpus.query_cqp(cqp_query, context, context_left,
                                         context_right, s_query, corrections,
                                         match_strategy, propagate_error=propagate_error).df
                df['subcorpus'] = name
                out.append(df)

        else:
            raise NotImplementedError()

        nodes = concat(out)
        # just in case
        nodes['context'] = nodes['context'].astype(int)
        nodes['contextend'] = nodes['contextend'].astype(int)

        self.nodes = nodes

    def concordance(self, form='kwic', p_show=['word'], s_show=[],
                    order='random', cut_off=100, matches=None,
                    slots=None, cwb_ids=False):

        if self.nodes is None:
            raise ValueError("you first have to run a query")

        dfs = list()
        for name, df in self.nodes.groupby('subcorpus'):
            conc = Concordance(
                self.corpus,
                df_dump=df
            ).lines(
                form=form,
                p_show=p_show,
                s_show=s_show,
                order=order,
                cut_off=cut_off,
                matches=matches,
                slots=slots,
                cwb_ids=cwb_ids
            )
            conc['subcorpus'] = name
            dfs.append(conc)

        return concat(dfs)

    def collocates(self, p_query=['lemma'], window=5,
                   order='log_likelihood', cut_off=100, ams=None,
                   min_freq=2, flags=None, marginals='corpus',
                   show_negative=False):
        """
        - find collocates of query matches in each subcorpus
        """

        if self.nodes is None:
            raise ValueError("you first have to run a query")

        dfs = list()
        for name, df in self.nodes.groupby('subcorpus'):
            coll = Collocates(
                self.corpus,
                df,
                p_query=p_query,
                mws=10
            ).show(
                window,
                order,
                cut_off,
                ams,
                min_freq,
                flags,
                marginals,
                show_negative
            )
            coll['subcorpus'] = name
            dfs.append(coll)

        return concat(dfs)
