#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
from io import StringIO
from glob import glob
# part of module
from .cqp import CQP
from .cache import Cache
from .counts import Counts
from .utils import (
    preprocess_query, merge_s_atts,
    chunk_anchors, correct_anchors
)
from .dumps import Dump
# requirements
from CWB.CL import Corpus as Attributes
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
        bin=cqp_bin,
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
    """Interface to CWB-indexed corpora."""

    def __init__(self, cqp_bin='cqp',
                 registry_path='/usr/local/share/cwb/registry/'):
        """Establish connection to registry and CQP.

        :param str cqp_bin: /path/to/cqp-binary
        :param str registry_path: /path/to/cwb/registry/

        """

        self.registry_path = registry_path
        self.cqp_bin = cqp_bin

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


class Corpus:
    """Interface to CWB-indexed corpus.

    After initializing, the corpus class has ...

    ... the following attributes:
    .data_path
    .registry_path
    .cqp_bin
    .lib_path
    .corpus_name
    .subcorpus [None]
    .attributes_available
    .corpus_size

    ... the following initialized classes:
    .attributes
    .cache
    .counts

    ... the following methods:
    ._attributes_available()
    .start_cqp()
    .copy()
    # p-attributes
    .cpos2satt
    .marginals
    # s-attributes
    .cpos2sid
    .satt2spans

    # subcorpora
        # .show_subcorpora
        # .activate_subcorpus
        # .save_subcorpus
        # .subcorpus_from_query
        # .subcorpus_from_dump
        # .subcorpus_from_s_att

    # creating dumps
    .dump_from_s_att: creates and caches df
    .dump_from_query: creates df, saves nqr in cqp

    # working on dumps
    .dump2patt
    .dump2satt
        # .get_s_annotations
    .dump2context

    # query aliases
    .query_s_att
    .query

    """

    def __init__(self, corpus_name, lib_path=None, cqp_bin='cqp',
                 registry_path='/usr/local/share/cwb/registry/',
                 data_path='/tmp/ccc-data/'):
        """Establish connection to CQP and corpus attributes, set paths, read
        library. Raises KeyError if corpus not in registry.

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

        # init (sub-)corpus information
        self.corpus_name = corpus_name
        self.subcorpus = None

        # macros and wordlists
        self.lib_path = lib_path

        # init attributes
        self.attributes = Attributes(
            self.corpus_name, registry_dir=self.registry_path
        )
        # get corpus size
        self.corpus_size = len(self.attributes.attribute('word', 'p'))

        # get available corpus attributes
        self.attributes_available = self._attributes_available()

        # init Cache
        self.cache = Cache(cache_path)

        # init Counts
        self.counts = Counts(self.corpus_name, self.registry_path)

    def __str__(self):
        """Method for printing.

        :return: corpus_name, corpus_size, data_path, subcorpus
        :rtype: str

        """

        return "\n".join([
            'a ccc.Corpus: "%s"' % self.corpus_name,
            "size        : %s" % str(self.corpus_size),
            "data        : %s" % str(self.data_path),
            "subcorpus   : %s" % str(self.subcorpus),
            "attributes  :",
            self.attributes_available.to_string(),
        ])

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

    def marginals(self, items, p_att='word', flags=0, pattern=False):
        """Extract marginal frequencies for given unigram patterns.
        0 if not in corpus.

        :param list items: items to get marginals for
        :param str p_att: p-attribute to get counts for
        :param int flags: 1 = %c, 2 = %d, 3 = %cd
        :param bool pattern: activate wildcards?

        :return: counts of the items in the whole corpus indexed by items
        :rtype: DataFrame

        """

        if flags:
            pattern = True

        # init attribute
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

        # create and post-process dataframe
        df = DataFrame(data=counts, index=items, columns=['freq'])
        df.index.name = p_att
        df = df.sort_values(by='freq', ascending=False)

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
    def show_subcorpora(self):
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
            logger.warning("no subcorpora defined")
            df = DataFrame()

        cqp.__kill__()
        return df

    # def activate_subcorpus(self, cqp, subcorpus=None, save=True):
    #     """Activates subcorpus or switches to main corpus.

    #     :param str subcorpus: named subcorpus to activate

    #     """
    #     if subcorpus is not None:
    #         self.subcorpus = subcorpus
    #         cqp.Exec(self.subcorpus)
    #         if save:
    #             self.save_subcorpus(cqp, subcorpus)
    #         logger.info('switched to subcorpus "%s"' % subcorpus)
    #     else:
    #         self.subcorpus = self.corpus_name
    #         cqp.Exec(self.subcorpus)
    #         logger.info('switched to corpus "%s"' % self.corpus_name)

    # def save_subcorpus(self, cqp, name='Last'):
    #     """Saves subcorpus to disk.

    #     :param str name: named subcorpus to save

    #     """
    #     cqp.Exec("save %s;" % name)
    #     logger.info(
    #         'CQP saved subcorpus "%s:%s" to disk' % (self.corpus_name, name)
    #     )

    # def subcorpus_from_query(self, cqp, query, name='Last',
    #                          match_strategy='longest',
    #                          return_dump=True):
    #     """Defines subcorpus from query, returns dump.

    #     :param str query: valid CQP query
    #     :param str name: subcorpus name
    #     :param str match_strategy: CQP matching strategy

    #     :return: df_dump
    #     :rtype: DataFrame

    #     """

    #     logger.info('defining subcorpus "%s" from query' % name)
    #     subcorpus_query = '%s=%s;' % (name, query)
    #     cqp.Query(subcorpus_query)
    #     if return_dump:
    #         logger.info('dumping result')
    #         df_dump = cqp.Dump(name)
    #         return df_dump

    # def subcorpus_from_dump(self, cqp, df_dump, name='Last'):
    #     """Defines subcorpus from dump.

    #     :param DataFrame df_dump: DataFrame indexed by (match, matchend)
    #                               with optional columns 'target' and 'keyword'
    #     :param str name: subcorpus name

    #     """
    #     logger.info('defining subcorpus "%s" from dump ' % name)
    #     cqp.Undump(name, df_dump)

    # def subcorpus_from_s_att(self, cqp, s_att, values, name='Last'):
    #     """Defines a subcorpus via s-attribute restriction.

    #     :param str s_att: s-att that stores values
    #     :param set values: set (or list) of values
    #     :param str name: subcorpus name to create

    #     """
    #     extents = self.dump_from_s_att(s_att, values).df
    #     self.subcorpus_from_dump(cqp, extents, name=name)

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

        === (match, matchend) $s_cwbid, $s_ann* ===

        and caches the result.

        $s_ann is only created if annotation is True and attribute is
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
                        2: s_att + '_ann'}, axis=1)
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
        df_dump.columns = [0, 1]
        logger.info("found %d matches" % len(df_dump))

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
            df_dump = df_dump.dropna(axis=1, how='all')
            df_dump = df_dump.fillna(-1, downcast='integer')

        # drop constant columns (contain only -1)
        # TODO this does not seem right
        df_dump = df_dump.loc[:, (df_dump != df_dump.iloc[0]).any()]

        # put into cache
        self.cache.set(identifier, df_dump)

        if save:
            cqp.nqr_save(self.corpus_name, name)

        cqp.__kill__()

        return df_dump

    #################################################
    # WORKING ON DUMPS ##############################
    #################################################
    def dump2patt(self, df_dump, p_att='word', start='match', end='matchend'):
        """Retrieve p-attribute annotation from start to end.

        === (match, matchend), $p ===

        Any additional columns of df_dump are preserved.

        :param DataFrame df_dump: DataFrame with specified columns (possibly as index)
        :param str p_att: p-attribute to retrieve

        :return: df_dump
        :rtype: DataFrame

        """

        # pre-process
        index_names = df_dump.index.names
        df = df_dump.reset_index()

        # retrieve attribute
        p = self.attributes.attribute(p_att, 'p')
        df[p_att] = df.apply(
            lambda row: " ".join(p[int(row[start]): int(row[end]) + 1]), axis=1
        )

        # post-process
        df = df.set_index(index_names)

        return df

    def dump2satt(self, df_dump, s_att, annotation=True):
        """Retrieve cwb-id, span, and annotation of s-attribute at match.

        Note that this only takes into account the match, not the
        matchend. This is reasonable assuming that the retrieved s-att
        comprises complete matches (match .. matchend).

        === (match, matchend), $s_cwbid, $s_span, $s_spanend, $s_ann*  ===

        $s_ann is only created if annotation is True and attribute is
        actually annotated.

        Any additional columns of df_dump are preserved.

        :param DataFrame df_dump: DataFrame indexed by (match, matchend)
        :param str s_att: s-attribute to retrieve

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
                        2: s_att + '_ann'}, axis=1)

        # join to original dataframe
        df_dump = df_dump.join(df, lsuffix='_bak')
        df_dump[[
            s_att + '_span',
            s_att + '_spanend'
        ]] = df[[
            s_att + '_span',
            s_att + '_spanend'
        ]].fillna(-1, downcast='infer')

        return df_dump

    def dump2context(self, df_dump, context_left, context_right, context_break):
        """Extend df_dump to context, breaking the context at context_break.

        === (match, matchend), contextid*, context, contextend  ===

        Columns for $context_break_cwbid, $context_break_span,
        etc. are also created.

        Any additional columns of df_dump are preserved.

        Note that in contrast to matches, contexts may overlap.

        For positions where the s-att specified by context_break is
        not annotated, context_break is ignored.

        The context creation algorithm does not take into account that
        match and matchend may be part of different regions defined by
        context_break; it only looks at the annotation of match, not
        matchend.

        For the _context_ column (left hand side), the strategy is as
        follows; the strategy for _contextend_ (right hand side) is
        analogous (using s_end and matchend).
        (1) if context_break is None and context_left is None
            => context = match
        (2) if context_break is None and context_left is not None
            => context = match - context_left
        (3) if context_break is not None and context_left is None
            => context = s_start
        (4) if context_break is not None and context_left is not None
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
    def query_s_att(self, s_att, values=set()):
        """Special query alias that call corpus.dump_from_s_att, optionally
        restricts the resulting df_dump by matching the provided
        values against the s-att annotations, and returns a Dump.

        === (match, matchend), $s_cwbid, $s_ann* ===

        :param str s_att: s-attribute to use for spans
        :param set values: values of s-att annotation to restrict spans to

        :return: dump
        :rtype: Dump

        """

        spans = self.dump_from_s_att(s_att)

        # restrict to certain values
        if len(values) > 0:
            if s_att + "_ann" not in spans.columns:
                logger.error("cannot restrict spans without annotation")
                return DataFrame()
            values = set(values)
            logger.info("restricting spans using %d values" % len(values))
            spans = spans.loc[spans[s_att + "_ann"].isin(values)]

        # return proper Dump
        return Dump(
            self.copy(),
            spans,
            name_cqp=None
        )

    def query(self, cqp_query, context=20, context_left=None,
              context_right=None, context_break=None, corrections=dict(),
              match_strategy='standard', name='Last', save=False):
        """Query the corpus, compute context-extended df_dump, and correct
        anchors. If a name is given, the resulting NQR (without
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
        query, s_query, anchors = preprocess_query(cqp_query)
        # TODO
        s_query, context_break, s_meta = merge_s_atts(s_query, context_break, None)
        if context_left is None:
            context_left = context
        if context_right is None:
            context_right = context

        df_dump = self.dump_from_query(
            query=query,
            s_query=s_query,
            anchors=anchors,
            match_strategy=match_strategy,
            name=name,
            save=save
        )

        # empty return?
        if len(df_dump) == 0:
            logger.warning("found 0 matches")
            df_dump = DataFrame()
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
