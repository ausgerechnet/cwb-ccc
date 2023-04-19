#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""cwb.py

definition of the Corpora, Corpus and SubCorpus classes

"""
import logging
import os
from glob import glob
from io import StringIO

# requirements
from numpy import maximum, minimum
from pandas import DataFrame, read_csv
from pandas.errors import EmptyDataError

# part of module
from .cache import Cache, generate_idx, generate_library_idx
from .cl import Corpus as Attributes
from .concordances import Concordance
from .counts import Counts, cwb_scan_corpus
from .cqp import CQP
from .utils import (chunk_anchors, correct_anchors, dump_left_join,
                    format_roles, group_lines, preprocess_query, aggregate_matches)
from .version import __version__
from .collocates import Collocates
from .keywords import Keywords
from .utils import fold_df, merge_intervals

logger = logging.getLogger(__name__)


def decode(text):
    """savely decode a string catching common errors

    """
    try:
        text = text.decode('utf-8')
    except (UnicodeDecodeError, AttributeError):
        text = ""
    return text


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
        cqp.Exec(f'set DataDirectory "{data_path}"')

    if lib_path is not None:

        # wordlists
        wordlists = glob(os.path.join(lib_path, 'wordlists', '*.txt'))
        for wordlist in wordlists:
            name = wordlist.split('/')[-1].split('.')[0]
            abs_path = os.path.abspath(wordlist)
            cqp_exec = f'define ${name} < "{abs_path}";'
            cqp.Exec(cqp_exec)

        # macros
        macros = glob(os.path.join(lib_path, 'macros', '*.txt'))
        for macro in macros:
            abs_path = os.path.abspath(macro)
            cqp_exec = f'define macro < "{abs_path}";'
            cqp.Exec(cqp_exec)
        # for wordlists defined in macros, it is necessary to execute the macro once
        macros = cqp.Exec("show macro;").split("\n")
        for macro in macros:
            # NB: this yields !cqp.Ok() if macro is not zero-valent
            cqp.Exec(macro.split("(")[0] + "();")

    # initialize corpus after macro definition, so execution of macro doesn't spend time
    if corpus_name is not None:
        cqp.Exec(corpus_name)
    if subcorpus is not None:
        cqp.Exec(subcorpus)

    if not cqp.Ok():
        raise NotImplementedError()

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
            f'registry path: "{self.registry_path}"',
            f'cqp binary   : "{self.cqp_bin}"',
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
        cqp = start_cqp(self.cqp_bin, self.registry_path)
        corpora = cqp.Exec("show corpora;").split("\n")
        cqp.__del__()

        # check availability and corpus sizes
        sizes = list()
        names = list()
        for corpus_name in corpora:
            try:
                sizes.append(len(Attributes(
                    corpus_name, registry_dir=self.registry_path
                ).attribute('word', 'p')))
                names.append(corpus_name)
            except SystemError:
                logger.warning(
                    f'corpus "{corpus_name}" defined in registry but not available'
                )

        # create dataframe
        corpora = DataFrame({'corpus': names, 'size': sizes}).set_index('corpus')

        return corpora

    def activate(self, corpus_name,
                 lib_path=None, data_path=None):
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


def init_data_path(data_path, corpus_name, lib_path=None):
    """ get a data directory / ensure that the given one complies with schema

    """

    if data_path is None:
        data_path = os.path.join("/tmp", "ccc-" + str(__version__))
    if not isinstance(data_path, str):
        raise ValueError("parameter data_path must be str")

    # generate library idx to invalidate cache when updated
    if lib_path is not None:
        lib_idx = generate_library_idx(lib_path, 'lib-', 7)
    else:
        lib_idx = "lib-vanilla"

    # each corpus has its separate directory for each library
    subdir = corpus_name + "-" + lib_idx
    if not data_path.endswith(subdir):
        data_path = os.path.join(data_path, subdir)

    # create directory
    try:
        os.makedirs(data_path, exist_ok=True)
    except PermissionError:
        logger.error(f'no write permission at "{data_path}"')
    else:
        return data_path


class Corpus:
    """Interface to CWB-indexed corpus.

    """

    def __init__(self, corpus_name, lib_path=None, cqp_bin='cqp',
                 registry_path='/usr/local/share/cwb/registry/',
                 data_path=None):
        """Establish connection to CQP and corpus attributes, set paths, read
        library.

        Raises KeyError if corpus not in registry.

        data directory contains subdirectories for each corpus and
        each library (/<data-path>/<corpus>-<lib-idx>/CACHE)
        - marginals_complex
        - dump_from_s_att
        - dump_from_query

        :param str corpus_name: name of corpus in CWB registry
        :param str lib_path: /path/to/macros/and/wordlists/
        :param str cqp_bin: /path/to/cqp-binary
        :param str registry_path: /path/to/cwb/registry/
        :param str data_path: /path/to/data/and/cache/

        """

        # preprocess data path
        data_path = init_data_path(data_path, corpus_name, lib_path)

        # save paths
        self.data_path = data_path
        self.registry_path = registry_path
        self.cqp_bin = cqp_bin
        self.lib_path = lib_path

        # init (sub-)corpus information
        self.corpus_name = corpus_name
        self.subcorpus_name = None

        # init attributes
        self.attributes = Attributes(self.corpus_name, registry_dir=self.registry_path)

        # get corpus size
        self.corpus_size = len(self.attributes.attribute('word', 'p'))

        # get available corpus attributes
        self.attributes_available = self._attributes_available()

        # init cache
        self.cache = Cache(os.path.join(self.data_path, "CACHE"))

        # init counts
        self.counts = Counts(self.corpus_name, self.registry_path)

    def __str__(self):
        """Method for printing.

        :return: settings and paths
        :rtype: str

        """

        return '\n' + '\n'.join([
            f'corpus: {self.corpus_name} ({self.corpus_size} tokens)',
            f'data:   {self.data_path}',
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
        cqp.__del__()

        return defined_macros

    def _wordlists_available(self):
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

    def _attributes_available(self):
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
            self.registry_path,
            self.data_path,
            self.corpus_name,
            self.lib_path,
            self.subcorpus_name
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

        return self.counts._cpos2patts(cpos, p_atts, ignore)

    def marginals(self, items=None, p_atts=['word'], flags=0, pattern=False):

        # allow lazy evocation
        p_atts = [p_atts] if isinstance(p_atts, str) else p_atts

        # simple
        if len(p_atts) == 1 and items is not None:
            return self.marginals_simple(items, p_atts[0], flags, pattern)

        else:
            return self.marginals_complex(items, p_atts)

    def marginals_simple(self, items, p_att='word', flags=0, pattern=False):
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

    def marginals_complex(self, items, p_atts=['word']):
        """Extract marginal frequencies for p-attribute combinations,
        e.g. ["lemma", "pos"].  0 if not in corpus.  Marginals are
        retrieved using cwb-scan-corpus, result is cached.

        :param list items: list of tuples
        :param list p_atts: list of p-attributes

        :return: counts of the items in the whole corpus indexed by items
        :rtype: FreqFrame

        """

        # get all marginals for p-att combination
        identifier = "_".join(p_atts) + "_marginals"
        df = self.cache.get(identifier)
        if df is not None:
            # get from cache if possible
            logger.info('using cached version of marginals of "%s"' % "_".join(p_atts))
        else:
            # calculate all marginals for p-att combination
            df, R = cwb_scan_corpus(
                self.corpus_name, self.registry_path, p_atts=p_atts, min_freq=0
            )
            self.cache.set(identifier, df)

        if items is not None:
            # preprocess tuples
            items = [" ".join(i) for i in items] if isinstance(items[0], tuple) \
                else items
            # select relevant rows
            df = df.reindex(items)
            df = df.fillna(0, downcast='infer')

        # sort by frequency
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
        identifier = s_att + "_spans"
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
                logger.info(f"restricting spans using {len(values)} values")
                df_spans = df_spans.loc[df_spans[s_att].isin(values)]

        # save as NQR
        if name is not None:
            # undump the dump and save to disk
            cqp = self.start_cqp()
            cqp.nqr_from_dump(df_spans, name)
            cqp.nqr_save(self.corpus_name, name)
            cqp.__del__()

        # return SubCorpus
        return self.subcorpus(subcorpus_name=name, df_dump=df_spans)

    def query_cqp(self, cqp_query, context=20, context_left=None,
                  context_right=None, context_break=None, corrections=dict(),
                  match_strategy='standard', name=None, propagate_error=False):
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
        name = 'Last' if name is None else name  # name in CQP
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

        # if dump has been retrieved from cache, NQR might not exist
        if save and (self.show_nqr().empty or name not in self.show_nqr()['subcorpus'].values):
            # undump the dump and save to disk
            cqp = self.start_cqp()
            cqp.nqr_from_dump(df_dump, name)
            cqp.nqr_save(self.corpus_name, name)
            cqp.__del__()

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

        # return SubCorpus
        return self.subcorpus(subcorpus_name=name, df_dump=df_dump)

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
        """makes sure query result is defined as subcorpus.

        without topic query:
        - finds all s_context spans that contain at least one filter_query
        with topic query:
        - finds all s_context spans that contain topic_query and all filter_queries

        :return: identifier (name of NQR on disk)
        :rtype: str

        """

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
        size = int(cqp.Exec(f'size {filter_identifier};'))

        if size == 0:

            # TODO: avoid saving twice if there's no filter
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
                cqp.Exec(f'{filter_identifier};')
                cqp.Query(f'{filter_identifier} = {query} expand to {s_context};')
                logger.info('.. size: ' + cqp.Exec(f'size {filter_identifier};'))

            # SAVE
            logger.info(f'.. saving {filter_identifier} in CWB binary format')
            cqp.Exec(f'save {filter_identifier};')

        cqp.__del__()

        return filter_identifier

    def quick_conc(self, topic_query, s_context, window, order=42,
                   cut_off=100, highlight_queries=dict(),
                   filter_queries=dict(), p_show=['word'], s_show=[],
                   match_strategy='longest'):
        """

        :return: concordance lines, each one a dict
        :rtype: list(dict)
        """

        if len(topic_query) == 0:

            queries = {**highlight_queries, **filter_queries}

            # INIT CQP
            identifier = self.quick_query(s_context, topic_query="", filter_queries=queries.values(), match_strategy=match_strategy)
            cqp = self.start_cqp()

            # init CONTEXT (TextConstellation)
            cqp.Exec(f'cut {identifier} {cut_off};')
            df_context = cqp.Dump(f'{identifier};')
            subcorpus_context = self.subcorpus(None, df_context).set_context(context_break=s_context)
            df_context = subcorpus_context.df[['contextid']]
            df_context = df_context.reset_index().set_index('contextid')

            # HIGHLIGHT
            cqp.Exec(f'{identifier};')
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
            lines = conc.lines(form='dict', p_show=p_show, s_show=s_show, order=order, cut_off=cut_off)
            output = lines.apply(lambda row: format_roles(row, names, s_show=names_bool+s_show, window=0, htmlify_meta=True), axis=1)

        else:

            # INIT CQP
            identifier = self.quick_query(s_context, topic_query, filter_queries.values(), match_strategy)
            cqp = self.start_cqp()

            # init CONTEXT (TextConstellation)
            cqp.Exec(f'{identifier};')
            df_context = cqp.Dump(f'{identifier};')
            subcorpus_context = self.subcorpus(None, df_context).set_context(window, s_context)
            df_context = subcorpus_context.df[['contextid', 'context', 'contextend']]

            # index by TOPIC MATCHES
            cqp.Exec(f'Temp = {topic_query};')
            df_query = cqp.Dump('Temp;')
            subcorpus_query = self.subcorpus(None, df_query).set_context(window, s_context)
            df_context = dump_left_join(df_context, subcorpus_query.df, 'topic', drop=True, window=window)
            df_context = df_context.set_index(['match_topic', 'matchend_topic'])
            df_context.index.names = ['match', 'matchend']

            # FILTER according to window size
            for name, query in filter_queries.items():
                cqp.Exec(f'Temp = {query};')
                df_query = cqp.Dump('Temp;')
                subcorpus_query = self.subcorpus(None, df_query).set_context(window, s_context)
                df_context = dump_left_join(df_context, subcorpus_query.df, name, drop=True, window=window)
                df_context = df_context.drop([c + "_" + name for c in ['match', 'matchend', 'offset']], axis=1)

            # HIGHLIGHT
            for name, query in highlight_queries.items():
                cqp.Exec(f'Temp = {query};')
                df_query = cqp.Dump('Temp;')
                subcorpus_query = self.subcorpus(None, df_query).set_context(window, s_context)
                df_context = dump_left_join(df_context, subcorpus_query.df, name, drop=False, window=window)

            cqp.__del__()

            # ACTUAL CONCORDANCING
            hkeys = list(highlight_queries.keys())
            df = group_lines(df_context, hkeys)
            conc = Concordance(self.copy(), df)
            lines = conc.lines(form='dict', p_show=p_show, s_show=s_show, order=order, cut_off=cut_off)
            output = lines.apply(lambda row: format_roles(row, hkeys, s_show, window, htmlify_meta=True), axis=1)

        return list(output)

    def subcorpus(self, subcorpus_name=None, df_dump=None):

        return SubCorpus(subcorpus_name, df_dump, self.corpus_name,
                         self.lib_path, self.cqp_bin, self.registry_path, self.data_path)


class SubCorpus(Corpus):

    def __init__(self, subcorpus_name, df_dump, corpus_name, lib_path, cqp_bin, registry_path, data_path):
        """
        takes care that (match, matchend)
        """

        super().__init__(corpus_name, lib_path, cqp_bin, registry_path, data_path)

        if subcorpus_name is None:

            if df_dump is None:
                logger.warning('no subcorpus information provided, returning Corpus')
            else:
                logger.warning('no subcorpus name given, you will not be able to use CQP')
                # TODO: create identifier, retrieve

        else:

            if df_dump is None:
                cqp = self.start_cqp()
                df_dump = cqp.Dump(subcorpus=subcorpus_name)
                cqp.__del__()
            else:
                self._assign(subcorpus_name, df_dump)

        self.df = df_dump
        self.subcorpus_name = subcorpus_name

        self._matches = None
        self._context = None

    def _assign(self, subcorpus_name, df_dump):

        if subcorpus_name in self.show_nqr()['subcorpus'].values:
            logger.warning(f'overwriting NQR "{subcorpus_name}"')

        # create in CQP
        cqp = self.start_cqp()
        cqp.nqr_from_dump(df_dump, subcorpus_name)
        cqp.nqr_save(self.corpus_name, subcorpus_name)
        cqp.__del__()

        if subcorpus_name not in self.show_nqr()['subcorpus'].values:
            logger.error(f'could not define NQR "{subcorpus_name}" from dataframe)')
        else:
            logger.info(f'activated  NQR "{subcorpus_name}"')

    def __str__(self):

        return '\n' + '\n'.join([
            f'corpus:    {self.corpus_name} ({self.corpus_size} tokens)',
            f'data:      {self.data_path}',
            f'subcorpus: {self.subcorpus_name} ({len(self.df)} spans)'
        ]) + '\n'

    def __repr__(self):
        """Info string.

        """
        return self.__str__()

    def set_context(self, context=None, context_break=None,
                    context_left=None, context_right=None):
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

        return self.subcorpus(self.subcorpus_name, df)

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
        if self._matches is None:
            f1 = set()
            for match, matchend in self.df.index:
                f1.update(range(match, matchend + 1))
            self._matches = f1

        return self._matches

    def context(self):
        """
        :return: cpos of (context .. contextend) regions including matches
        :rtype: DataFrame
        """
        if self._context is None:
            self._context = DataFrame.from_records(merge_intervals(
                self.df[['context', 'contextend']].values.tolist()
            ), columns=['context', 'contextend'])

        return self._context

    def marginals(self, start='match', end='matchend', p_atts=['word']):

        return self.counts.dump(
            self.df, start=start, end=end, p_atts=p_atts, split=True
        )

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

    def collocates(self, p_query=['lemma'], mws=20, window=5, order='O11',
                   cut_off=100, ams=None, min_freq=2,
                   frequencies=True, flags=None, marginals='corpus',
                   show_negative=False):

        mws = max(mws, window)

        coll = Collocates(
            self.copy(),
            df_dump=self.df,
            p_query=p_query,
            mws=mws
        )

        return coll.show(
            window=window,
            order=order,
            cut_off=cut_off,
            ams=ams,
            min_freq=min_freq,
            frequencies=frequencies,
            flags=flags,
            marginals=marginals,
            show_negative=show_negative
        )

    def keywords(self, p_query=['lemma'], order='O11', cut_off=100,
                 ams=None, min_freq=2, frequencies=True, flags=None):

        kw = Keywords(
            self.copy(),
            self.df,
            p_query,
        )

        return kw.show(
            order=order,
            cut_off=cut_off,
            ams=ams,
            min_freq=min_freq,
            frequencies=frequencies,
            flags=flags
        )
