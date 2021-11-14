#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
from io import StringIO
from glob import glob
# part of module
from .cqp import CQP
from .cache import Cache
from .counts import Counts
from .utils import preprocess_query
from .utils import chunk_anchors, correct_anchors
from .dumps import Dump
from .counts import cwb_scan_corpus
from .cl import Corpus as Attributes
# requirements
from pandas import DataFrame, read_csv
from pandas.errors import EmptyDataError
from numpy import minimum, maximum
# logging
import logging
logger = logging.getLogger(__name__)


def start_cqp(cqp_bin, registry_path,
              data_path=None, corpus_name=None,
              lib_path=None, subcorpus=None):
    """Start CQP process, activate (sub-)corpus, set paths, and read
    library (macros and wordlists).

    :param str cqp_bin: /path/to/cqp-binary
    :param str registry_path: /path/to/cwb/registry/
    :param str data_path: /path/to/data/and/cache/
    :param str corpus_name: name of corpus in CWB registry
    :param str lib_path: /path/to/macros/and/wordlists/
    :param str subcorpus: name of subcorpus (NQR)

    :return: CQP process
    :rtype: CQP

    """

    cqp = CQP(
        binary=cqp_bin,
        options='-c -r ' + registry_path
    )

    if data_path is not None:
        cqp.Exec('set DataDirectory "%s"' % data_path)
    if corpus_name is not None:
        cqp.Exec(corpus_name)
    if subcorpus is not None:
        cqp.Exec(subcorpus)

    if lib_path is not None:

        # wordlists
        wordlists = glob(os.path.join(lib_path, 'wordlists', '*'))
        for wordlist in wordlists:
            name = wordlist.split('/')[-1].split('.')[0]
            abs_path = os.path.abspath(wordlist)
            cqp_exec = 'define $%s < "%s";' % (name, abs_path)
            cqp.Exec(cqp_exec)

        # macros
        macros = glob(os.path.join(lib_path, 'macros', '*'))
        for macro in macros:
            abs_path = os.path.abspath(macro)
            cqp_exec = 'define macro < "%s";' % abs_path
            cqp.Exec(cqp_exec)
        # execute each macro once (avoids CQP shortcoming for nested macros)
        macros = cqp.Exec("show macro;").split("\n")
        for macro in macros:
            cqp.Exec(macro)

    return cqp


class Corpora:
    """Interface to CWB-indexed corpora.

    """

    def __init__(self, cqp_bin='cqp',
                 registry_path='/usr/local/share/cwb/registry/'):
        """Establish connection to registry and CQP.

        :param str cqp_bin: /path/to/cqp-binary
        :param str registry_path: /path/to/cwb/registry/

        """

        self.registry_path = registry_path
        self.cqp_bin = cqp_bin

    def __str__(self):
        """Method for printing.

        :return: paths, available corpora
        :rtype: str

        """

        corpora = self.show()

        return '\n' + '\n'.join([
            'registry path: "%s"' % self.registry_path,
            'cqp binary   : "%s"' % self.cqp_bin,
            'found %d corpora:' % len(corpora),
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
        cqp = start_cqp(self.cqp_bin, self.registry_path)
        corpora = cqp.Exec("show corpora;").split("\n")
        cqp.__kill__()

        # check availability and corpus sizes
        corpora_available = list()
        sizes = list()
        for corpus_name in corpora:

            try:
                corpus = Corpus(
                    corpus_name, cqp_bin=self.cqp_bin,
                    registry_path=self.registry_path, data_path=None
                )
                corpora_available.append(corpus_name)
                sizes.append(corpus.corpus_size)

            except SystemError:
                logger.warning(
                    'corpus "%s" defined in registry but not available' % corpus_name
                )

        # create dataframe
        corpora = DataFrame({'corpus': corpora_available,
                             'tokens': sizes})
        corpora = corpora.set_index('corpus')

        return corpora

    def activate(self, corpus_name,
                 lib_path=None, data_path='/tmp/ccc-data/'):
        """Activate a corpus.

        :param str corpus_name: name of corpus in CWB registry
        :param str lib_path: /path/to/macros/and/wordlists/
        :param str data_path: /path/to/data/and/cache/

        :return: corpus
        :rtype: Corpus

        """

        return Corpus(corpus_name,
                      lib_path=lib_path,
                      cqp_bin=self.cqp_bin,
                      registry_path=self.registry_path,
                      data_path=data_path)


class Corpus:
    """Interface to CWB-indexed corpus.

    """

    def __init__(self, corpus_name, lib_path=None, cqp_bin='cqp',
                 registry_path='/usr/local/share/cwb/registry/',
                 data_path='/tmp/ccc-data/'):
        """Establish connection to CQP and corpus attributes, set paths, read
        library.

        Raises KeyError if corpus not in registry.

        :param str corpus_name: name of corpus in CWB registry
        :param str lib_path: /path/to/macros/and/wordlists/
        :param str cqp_bin: /path/to/cqp-binary
        :param str registry_path: /path/to/cwb/registry/
        :param str data_path: /path/to/data/and/cache/

        """

        # process data path
        if data_path is not None:
            if not data_path.endswith(corpus_name):
                data_path = os.path.join(data_path, corpus_name)
            self.data_path = data_path
            if not os.path.isdir(self.data_path):
                os.makedirs(self.data_path)
            cache_path = os.path.join(self.data_path, "CACHE")
        else:
            self.data_path = None
            cache_path = None

        # set registry path and cqp_bin
        self.registry_path = registry_path
        self.cqp_bin = cqp_bin

        # macros and wordlists
        self.lib_path = lib_path

        # init (sub-)corpus information
        self.corpus_name = corpus_name
        self.subcorpus = None

        # init attributes
        self.attributes = Attributes(self.corpus_name, registry_dir=self.registry_path)

        # get corpus size
        self.corpus_size = len(self.attributes.attribute('word', 'p'))

        # get available corpus attributes
        self.attributes_available = self._attributes_available()

        # init cache
        self.cache = Cache(cache_path)

        # init counts
        self.counts = Counts(self.corpus_name, self.registry_path)

    def __str__(self):
        """Method for printing.

        :return: settings and paths
        :rtype: str

        """

        return '\n' + '\n'.join([
            'ccc.Corpus: "%s"' % self.corpus_name,
            'size      : %s' % str(self.corpus_size),
            'data      : %s' % str(self.data_path),
            'subcorpus : %s' % str(self.subcorpus),
            'available positional and structural attributes:',
            self.attributes_available.to_string(),
        ])

    def __repr__(self):
        """Info string.

        """
        return self.__str__()

    def _macros_available(self):
        """Get available macros (either system-defined or via library).

        :return: defined macros
        :rtype: list

        """
        cqp = self.start_cqp()
        defined_macros = cqp.Exec("show macro;").split("\n")
        cqp.__kill__()
        return defined_macros

    def _attributes_available(self):
        """Get indexed p- and s-attributes. Will be run once when initializing
        the corpus.

        :return: attributes and annotation info
        :rtype: DataFrame

        """

        # use CQP's context descriptor
        cqp = self.start_cqp()
        cqp_ret = cqp.Exec('show cd;')
        cqp.__kill__()

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
            self.registry_path,
            self.data_path,
            self.corpus_name,
            self.lib_path,
            self.subcorpus
        )

    def copy(self):
        """Get a fresh initialization of the corpus.

        :return: corpus
        :rtype: Corpus

        """

        return Corpus(
            self.corpus_name,
            self.lib_path,
            self.cqp_bin,
            self.registry_path,
            self.data_path
        )

    ################
    # p-attributes #
    ################
    def cpos2patts(self, cpos, p_atts=['word'], ignore=True):
        """Retrieve p-attributes of corpus position.

        :param int cpos: corpus position to fill
        :param list p_atts: p-attribute(s) to fill position with
        :param bool ignore: whether to return (None, ..) for -1

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

    def marginals(self, items, p_att='word', flags=0, pattern=False):
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

        tokens_all = self.attributes.attribute(p_att, 'p')

        # loop through items and collect frequencies
        counts = list()
        for item in items:
            if not pattern:
                try:
                    counts.append(tokens_all.frequency(item))
                except KeyError:
                    counts.append(0)
            else:
                cpos = tokens_all.find_pattern(item, flags=flags)
                counts.append(len(cpos))

        # create dataframe
        df = DataFrame({'freq': counts, p_att: items})
        df = df.set_index(p_att, drop=False)
        df.index.name = 'item'
        df = df.sort_values(['freq', 'item'], ascending=False)

        return df

    def marginals_complex(self, items, p_atts=['word']):
        """Extract marginal frequencies for p-attribute combinations,
        e.g. ["lemma", "pos"].  0 if not in corpus.  Marginals are
        retrieved using cwb-scan-corpus, result is cached.

        :param list items: list of tuples
        :param list p_atts: list of p-attributes

        :return: counts of the items in the whole corpus indexed by items
        :rtype: FreqFrame

        """

        # retrieve all marginals for p-att combination from cache if possible
        identifier = "_".join(p_atts) + "_marginals"
        df = self.cache.get(identifier)
        if df is not None:
            logger.info('using cached version of marginals of "%s"' % "_".join(p_atts))
        else:
            # calculate all marginals for p-att combination
            df, R = cwb_scan_corpus(
                self.corpus_name, self.registry_path, p_atts=p_atts, min_freq=0
            )
            self.cache.set(identifier, df)

        # select relevant rows
        df = df.reindex([" ".join(i) for i in items])
        df = df.fillna(0, downcast='infer')
        df.sort_values(by='freq')

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
            crpssbcrps = df["corpus:subcorpus"].str.split(":", 1).str
            df['corpus'] = crpssbcrps[0]
            df['subcorpus'] = crpssbcrps[1]
            df.drop('corpus:subcorpus', axis=1, inplace=True)
            df = df[['corpus', 'subcorpus', 'size', 'storage']]
        except EmptyDataError:
            logger.info("no subcorpora defined")
            df = DataFrame()

        cqp.__kill__()
        return df

    def activate_subcorpus(self, nqr=None, df_dump=None):
        """Activate a Named Query Result (NQR).

        - If no df_dump is given, this sets self.subcorpus and logs an
          error if NQR is not defined.
        - If a df_dump is given, the df_dump will be undumped and named
          NQR.

        :param str nqr: NQR defined in CQP
        :param DataFrame df_dump: DataFrame indexed by (match, matchend)
                                  with optional columns 'target' and 'keyword'

        """

        if nqr is not None:

            if df_dump is not None:
                cqp = self.start_cqp()
                cqp.nqr_from_dump(df_dump, nqr)
                cqp.nqr_save(self.corpus_name, nqr)
                cqp.__kill__()

            if nqr not in self.show_nqr()['subcorpus'].values:
                # raise an error if subcorpus not available
                logger.error('subcorpus "%s" not defined)' % nqr)
                self.activate_subcorpus()
            else:
                logger.info('switched to subcorpus "%s"' % nqr)

        else:
            logger.info('switched to corpus "%s"' % self.corpus_name)

        # activate subcorpus
        self.subcorpus = nqr

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
        identifier = s_att + "_spans"
        df = self.cache.get(identifier)
        if df is not None:
            logger.info('using cached version of spans of "%s"' % s_att)
            return df

        # compute
        logger.info('creating dataframe of spans of "%s"' % s_att)

        df = DataFrame(list(self.attributes.attribute(s_att, 's')))

        # two or three columns: 0 (start), 1 (end), 2* (annotation)
        if annotation:
            annotation = (2 in df.columns)  # just to make sure ...
            if not annotation:
                logger.info('s-att "%s" does not have any annotation' % s_att)
            else:
                df[2] = df[2].apply(lambda x: x.decode('utf-8'))

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
                        match_strategy='standard', name='Last', save=False):
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
        if self.subcorpus is not None:
            # check subcorpus size to avoid confusion when re-naming
            cqp = self.start_cqp()
            sbcrpssize = cqp.Exec("size %s" % self.subcorpus)
            cqp.__kill__()
        else:
            sbcrpssize = None
        identifier = self.cache.generate_idx([
             query, s_query, anchors, match_strategy, self.subcorpus, sbcrpssize
        ], prefix="df_dump:")

        # retrieve from cache if possible
        df_dump = self.cache.get(identifier)
        if df_dump is not None:
            logger.info(
                'using cached version "%s" of df_dump with %d matches' % (
                    identifier, len(df_dump)
                )
            )
            return df_dump

        # init cqp and set matching strategy
        cqp = self.start_cqp()
        cqp.Exec('set MatchingStrategy "%s";' % match_strategy)

        # include optional within clause
        if s_query is None:
            start_query = query
        else:
            start_query = query + ' within ' + s_query

        # first run: anchors at 0 and 1 (considering within clause)
        logger.info("running CQP query")
        cqp.Exec('set ant 0; ank 1;')
        df_dump = cqp.nqr_from_query(
            query=start_query,
            name=name,
            match_strategy=match_strategy,
            return_dump=True
        )
        if len(df_dump) == 0:
            return df_dump

        logger.info("found %d matches" % len(df_dump))
        df_dump.columns = [0, 1]

        # if there's nothing to return ...
        if df_dump.empty:
            cqp.__kill__()
            return df_dump

        # join all other anchors
        remaining_anchors = list(chunk_anchors(anchors, 2))
        if len(remaining_anchors) > 0:

            # restrict subsequent queries on initial matches
            cqp.nqr_activate(self.corpus_name, name)

            for pair in remaining_anchors:
                logger.info(".. running query for anchor(s) %s" % str(pair))
                # set appropriate anchors
                cqp.Exec('set ant %d;' % pair[0])
                if len(pair) == 2:
                    cqp.Exec('set ank %d;' % pair[1])
                else:
                    cqp.Exec('set ank %d;' % 1)
                # dump new anchors
                cqp.Query('tmp = <match> ( %s );' % query)
                df = cqp.Dump("tmp")
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

        cqp.__kill__()

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
        logger.info('s-att "%s" exists at %d of %d matches' % (
            s_att, len(df) - nr_missing, len(df)
        ))

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
                logger.info('s-att "%s" does not have any annotation' % s_att)
            else:
                df[2] = df[2].apply(lambda x: x.decode('utf-8'))

        # restore original index and post-process
        df = df.set_index(['match', 'matchend'])
        df = df.rename({0: s_att + '_span',
                        1: s_att + '_spanend',
                        2: s_att}, axis=1)

        # join to original dataframe
        df_dump = df_dump.join(df, lsuffix='_bak')
        df_dump = df_dump[[col for col in df_dump if not str(col).endswith('_bak')]]
        df_dump[[
            s_att + '_span', s_att + '_spanend'
        ]] = df[[
            s_att + '_span', s_att + '_spanend'
        ]].fillna(-1, downcast='infer')

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
    def query_s_att(self, s_att, values=set(), name=None):
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
                logger.info("restricting spans using %d values" % len(values))
                df_spans = df_spans.loc[df_spans[s_att].isin(values)]

        # save as NQR
        if name is not None:
            # undump the dump and save to disk
            cqp = self.start_cqp()
            cqp.nqr_from_dump(df_spans, name)
            cqp.nqr_save(self.corpus_name, name)
            cqp.__kill__()

        # return proper Dump
        return Dump(self.copy(), df_spans, name_cqp=name)

    def query(self, cqp_query, context=20, context_left=None,
              context_right=None, context_break=None, corrections=dict(),
              match_strategy='standard', name=None):
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
        # name = 'Last' if name is None else name  # name in CQP
        query, s_query, anchors = preprocess_query(cqp_query)
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
            save=save
        )

        # if dump has been retrieved from cache, NQR might not exist
        if name is not None and (
            self.show_nqr().empty or
            name not in self.show_nqr()['subcorpus'].values
        ):
            # undump the dump and save to disk
            cqp = self.start_cqp()
            cqp.nqr_from_dump(df_dump, name)
            cqp.nqr_save(self.corpus_name, name)
            cqp.__kill__()

        # empty return?
        if len(df_dump) == 0:
            logger.warning("found 0 matches")
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

        # return proper dump
        return Dump(
            self.copy(),
            df_dump,
            name_cqp=name
        )
