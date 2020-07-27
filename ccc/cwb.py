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
from CWB.CL import Corpus as Crps
from pandas import DataFrame, read_csv, to_numeric
from pandas.errors import EmptyDataError
# logging
import logging
logger = logging.getLogger(__name__)


def start_cqp(cqp_bin, registry_path, data_path=None, corpus_name=None):
    cqp = CQP(
        bin=cqp_bin,
        options='-c -r ' + registry_path
    )
    if data_path is not None:
        cqp.Exec('set DataDirectory "%s"' % data_path)
    if corpus_name is not None:
        cqp.Exec(corpus_name)
    return cqp


class Corpora:
    """ interface to CWB-indexed corpora """

    def __init__(self,
                 cqp_bin='cqp',
                 registry_path='/usr/local/share/cwb/registry/'):

        self.registry_path = registry_path
        self.cqp_bin = cqp_bin

    def start_cqp(self):
        return start_cqp(self.cqp_bin, self.registry_path)

    def show_corpora(self):
        cqp = self.start_cqp()
        corpora = cqp.Exec("show corpora;").split("\n")
        return corpora


class Corpus:
    """ interface to CWB-indexed corpus """

    def __init__(self, corpus_name, lib_path=None, cqp_bin='cqp',
                 registry_path='/usr/local/share/cwb/registry/',
                 data_path="/tmp/ccc-data/"):
        """Establishes connection to CQP and corpus attributes; imports macros
        and wordlists. Raises KeyError if corpus not in registry.

        attributes:
        .registry_path
        .corpus_name
        .data_path
        .attributes_available
        .corpus_size
        .lib_path
        .subcorpus [None]

        methods:
        .__str__
        .read_lib

        .get_s_extents
        .get_s_id
        .get_s_annotation
        .get_s_annotations

        .cpos2patts

        .show_subcorpora
        .activate_subcorpus
        .save_subcorpus
        .subcorpus_from_query
        .subcorpus_from_dump
        .subcorpus_from_s_att

        .dump_from_query
        .extend_df_dump
        .query_cache
        .query

        classes:
        .cache
        .cqp
        .attributes
        .counts

        :param str corpus_name: name of corpus in CWB registry
        :param str lib_path: path/to/macros/and/wordlists
        :param str cqp_bin: cqp binary
        :param str registry_path: path/to/cwb/registry/
        :param str data_path: path/to/store/cwb/data/and/cache

        """

        # process data path
        if data_path is not None:
            self.data_path = os.path.join(data_path, corpus_name)
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

        # init Attributes
        self.attributes = Crps(
            self.corpus_name,
            registry_dir=self.registry_path
        )
        # get corpus size
        self.corpus_size = len(self.attributes.attribute('word', 'p'))

        # init CQP
        self.cqp = start_cqp(
            self.cqp_bin, self.registry_path, self.data_path, self.corpus_name
        )
        # get available corpus attributes
        self.attributes_available = read_csv(
            StringIO(self.cqp.Exec('show cd;')),
            sep='\t', names=['att', 'name', 'annotation', 'active']
        ).fillna(False)
        # load macros and wordlists
        self.lib_path = lib_path
        if self.lib_path:
            self.read_lib(self.lib_path)

        # init Cache
        self.cache = Cache(
            cache_path
        )

        # init Counts
        self.counts = Counts(
            self.corpus_name, self.registry_path
        )

    def __str__(self):
        return "\n".join([
            "name     : %s" % self.corpus_name,
            "size     : %s" % str(self.corpus_size),
            "subcorpus: %s" % str(self.subcorpus),
            "data     : %s" % str(self.data_path),
            "available attributes:",
            self.attributes_available.to_string(),
        ])

    def read_lib(self, lib_path):
        """Reads macros and worldists. Folder has to contain two sub-folders
        ("macros" and "wordlists").

        :param str lib_path: path/to/macros/and/wordlists

        """

        logger.info("enter read_lib")

        # wordlists
        wordlists = glob(os.path.join(lib_path, 'wordlists', '*'))
        for wordlist in wordlists:
            name = wordlist.split('/')[-1].split('.')[0]
            abs_path = os.path.abspath(wordlist)
            cqp_exec = 'define $%s < "%s";' % (
                name, abs_path
            )
            self.cqp.Exec(cqp_exec)

        # macros
        macros = glob(os.path.join(lib_path, 'macros', '*'))
        for macro in macros:
            abs_path = os.path.abspath(macro)
            cqp_exec = 'define macro < "%s";' % abs_path
            self.cqp.Exec(cqp_exec)

        # execute each macro once (avoids CQP shortcoming for nested macros)
        macros = self.cqp.Exec("show macro;")
        for macro in macros:
            self.cqp.Exec(macro)

    def copy(self):
        return Corpus(
            self.corpus_name,
            self.lib_path,
            self.cqp_bin,
            self.registry_path,
            self.data_path
        )

    ################
    # s-attributes #
    ################
    def get_s_extents(self, s_att):
        """Maps s_att to corresponding extents, returns DataFrame.

        :param str s_att: s-attribute to get extents for

        :return: df indexed by match, matchend; CWBID, annotation
        :rtype: DataFrame

        """

        logger.info("enter get_s_extents")

        # retrieve from cache
        parameters = ['s_extents', s_att]
        df = self.cache.get(parameters)
        if df is not None:
            logger.info('using cached version of extents of "%s"' % s_att)
            return df

        # compute
        logger.info('computing extents of "%s"' % s_att)
        s_regions = self.attributes.attribute(s_att, 's')

        # check if there's annotations
        annotation = self.attributes_available.loc[
            self.attributes_available['name'] == s_att
        ]['annotation'].values[0]

        records = list()
        for s in s_regions:
            s_id = self.get_s_id(s[0], s_att)
            if annotation:
                ann = s[2].decode()
            else:
                ann = True
            records.append({
                'match': s[0],
                'matchend': s[1],
                s_att + '_CWBID': s_id,
                s_att: ann
            })
        df = DataFrame(records)
        df = df.set_index(['match', 'matchend'])

        # put into cache
        self.cache.set(parameters, df)

        return df

    def get_s_id(self, cpos, s_att):
        """gets ID of s_att at cpos"""
        s_regions = self.attributes.attribute(s_att, "s")
        try:
            return s_regions.cpos2struc(cpos)
        except KeyError:
            return -1

    def get_s_annotation(self, df, s_att):
        """Retrieves CWBIDs and annotations of s-attribute of match.

        :param DataFrame df_dump: DataFrame indexed by (match, matchend)
        :param str s_att: s-attribute to retrieve

        """
        # TODO remove double entries (tweet_id_CWBID = tweet_CWBID etc.)

        logger.info("cwb.get_s_annotation")

        # get IDs
        df[s_att + "_CWBID"] = df.match.apply(
                lambda x: self.get_s_id(x, s_att)
            )

        # check if there is any annotation
        annotation = self.attributes_available.loc[
            self.attributes_available['name'] == s_att
        ]['annotation'].values[0]
        if not annotation:
            logger.info('no annotation in s-att "%s"' % s_att)
        else:
            # only retrieve where applicable
            s_regions = self.attributes.attribute(s_att, "s")
            df_applicable = df.loc[df[s_att + "_CWBID"] != -1]
            s_region = DataFrame(
                index=df_applicable.index,
                data=df_applicable.match.apply(
                    lambda x: s_regions.find_pos(x)
                ).to_list()
            )

            # decode annotations
            s_region[s_att] = s_region[2].apply(
                lambda x: x.decode('utf-8')
            )

            nr = len(s_region[s_att]) - s_region[s_att].isna().sum()
            logger.info(
                'retrieved %d annotations of s-att %s' % (nr, s_att)
            )
            # join to dataframe
            df = df.join(s_region[s_att])

        return df

    def get_s_annotations(self, df_dump, s_atts):
        """Gets all annotations of all s-att in s_atts at match positions.

        :param DataFrame df_dump: DataFrame indexed by (match, matchend)
        :param list s_atts: s-attributes to show (id + annotation)

        :return: s_annotations
        :rtype: DataFrame

        """
        df = df_dump.reset_index()
        df = df[['match', 'matchend']]
        for s in s_atts:
            df = self.get_s_annotation(df, s)
        df = df.set_index(['match', 'matchend'])
        return df

    ################
    # p-attributes #
    ################
    def cpos2patts(self, cpos, p_atts=['word'], ignore_missing=True):
        """Retrieves p-attributes of corpus position.

        :param int cpos: corpus position to fill
        :param list p_atts: p-attribute(s) to fill position with
        :param bool ignore_missing: whether to return -1 for out-of-bounds

        :return: p_att(s) to retrieve
        :rtype: tuple

        """

        if ignore_missing and cpos == -1:
            token = [None] * len(p_atts)
        else:
            token = [
                self.attributes.attribute(p_att, 'p')[cpos] for p_att in p_atts
            ]

        return tuple(token)

    def marginals(self, items, p_att='word', flags=0, pattern=False):
        """Extracts marginal frequencies for given unigram patterns.
        0 if not in corpus.

        :param list items: items to get marginals for
        :param str p_att: p-attribute to get counts for
        :param int flags: 1 = %c, 2 = %d, 3 = %cd
        :param bool pattern: activate wildcards?

        :return: counts of the items in the whole corpus
        :rtype: DataFrame

        """
        tokens_all = self.attributes.attribute(p_att, 'p')
        if flags:
            pattern = True
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
        df = DataFrame(data=counts, index=items, columns=['freq'])
        df.index.name = p_att
        df = df.sort_values(by='freq', ascending=False)
        return df

    ##############
    # subcorpora #
    ##############
    def show_subcorpora(self):
        """Returns subcorpora defined in CQP as DataFrame.

        :return: available subcorpora
        :rtype: DataFrame

        """
        cqp_return = self.cqp.Exec("show named;")
        try:
            df = read_csv(StringIO(cqp_return), sep="\t", header=None)
            df.columns = ["storage", "corpus:subcorpus", "size"]
            crpssbcrps = df["corpus:subcorpus"].str.split(":", 1).str
            df['corpus'] = crpssbcrps[0]
            df['subcorpus'] = crpssbcrps[1]
            df.drop('corpus:subcorpus', axis=1, inplace=True)
            df = df[['corpus', 'subcorpus', 'size', 'storage']]
            return df
        except EmptyDataError:
            logger.warning("no subcorpora defined")
            return DataFrame()

    def activate_subcorpus(self, subcorpus=None):
        """Activates subcorpus or switches to main corpus.

        :param str subcorpus: named subcorpus to activate

        """
        if subcorpus is not None:
            self.cqp.Exec(subcorpus)
            self.subcorpus = subcorpus
            logger.info('CQP switched to subcorpus "%s"' % subcorpus)
        else:
            self.cqp.Exec(self.corpus_name)
            self.subcorpus = self.corpus_name
            logger.info('CQP switched to corpus "%s"' % self.corpus_name)

    def save_subcorpus(self, name='Last'):
        """Saves subcorpus to disk.

        :param str name: named subcorpus to save

        """
        self.cqp.Exec("save %s;" % name)
        logger.info(
            'CQP saved subcorpus "%s:%s" to disk' % (self.corpus_name, name)
        )

    def subcorpus_from_query(self, query, name='Last',
                             match_strategy='longest',
                             return_dump=True):
        """Defines subcorpus from query, returns dump.

        :param str query: valid CQP query
        :param str name: subcorpus name
        :param str match_strategy: CQP matching strategy

        :return: df_dump
        :rtype: DataFrame

        """

        logger.info('defining subcorpus "%s" from query' % name)
        subcorpus_query = '%s=%s;' % (name, query)
        self.cqp.Query(subcorpus_query)
        if return_dump:
            logger.info('dumping result')
            df_dump = self.cqp.Dump(name)
            return df_dump

    def subcorpus_from_dump(self, df_dump, name='Last'):
        """Defines subcorpus from dump.

        :param DataFrame df_dump: DataFrame indexed by (match, matchend)
                                  with optional columns 'target' and 'keyword'
        :param str name: subcorpus name

        """
        logger.info('defining subcorpus "%s" from dump ' % name)
        self.cqp.Undump(name, df_dump)

    def subcorpus_from_s_att(self, s_att, values, name='Last'):
        """Defines a subcorpus via s-attribute restriction.

        :param str s_att: s-att that stores values
        :param set values: set (or list) of values
        :param str name: subcorpus name to create

        """
        extents = self.dump_from_s_att(s_att, values).df
        self.subcorpus_from_dump(extents, name=name)

    def dump_from_s_att(self, s_att, values):
        values = set(values)
        logger.info("defining subcorpus from %d values" % len(values))
        extents = self.get_s_extents(s_att)
        extents = extents.loc[extents[s_att].isin(values)]
        extents = extents.drop(extents.columns, axis=1)
        return Dump(
            self.copy(),
            extents,
            name_cache=None,
            name_cqp=None
        )

    #########
    # query #
    #########
    def dump_from_query(self, query, s_query=None, anchors=[],
                        match_strategy='standard', name='Last'):
        """Executes query, gets DataFrame of corpus positions (dump of CWB).
        df_dump is indexed by (match, matchend).  Optional columns for
        each anchor:

        === (match, matchend), 0, ..., 9 ===

        :param str query: valid CQP query (without 'within' clause)
        :param str s_query: s-attribute used for initial query
        :param list anchors: anchors to search for
        :param str match_strategy: CQP matching strategy

        :return: df_dump
        :rtype: DataFrame

        """

        # match strategy
        self.cqp.Exec('set MatchingStrategy "%s";' % match_strategy)

        # optional within statement
        if s_query is None:
            start_query = query
        else:
            start_query = query + ' within ' + s_query

        # first run: 0 and 1 (considering within statement)
        logger.info("running CQP query")
        self.cqp.Exec('set ant 0; ank 1;')
        self.subcorpus_from_query(
            query=start_query, name=name
        )
        df_dump = self.cqp.Dump(name)
        df_dump.columns = [0, 1]
        logger.info("found %d matches" % len(df_dump))

        # if there's nothing to return ...
        if df_dump.empty:
            return df_dump

        # join all other anchors
        if len(anchors) > 0:

            # restrict subsequent queries on initial matches
            current_subcorpus = self.subcorpus
            self.activate_subcorpus(name)

            for pair in chunk_anchors(anchors, 2):
                logger.info(".. running query for anchor(s) %s" % str(pair))
                # set appropriate anchors
                self.cqp.Exec('set ant %d;' % pair[0])
                if len(pair) == 2:
                    self.cqp.Exec('set ank %d;' % pair[1])
                else:
                    self.cqp.Exec('set ank %d;' % 1)
                # dump new anchors
                self.cqp.Query('tmp = <match> ( %s );' % query)
                df = self.cqp.Dump("tmp")
                # select columns and join to global df
                if len(pair) == 2:
                    df.columns = [pair[0], pair[1]]
                else:
                    df.columns = [pair[0], 1]
                    df = df.drop(1, axis=1)
                df_dump = df_dump.join(df)

            # NA handling
            logger.info("post-processing dataframe")
            df_dump.dropna(axis=1, how='all', inplace=True)
            df_dump = df_dump.apply(to_numeric, downcast='integer')
            df_dump.fillna(-1, inplace=True)

            # re-set CQP
            self.cqp.Exec('set ant 0; ank 1;')
            self.activate_subcorpus(current_subcorpus)

        # drop constant columns (contain only -1)
        df_dump = df_dump.loc[:, (df_dump != df_dump.iloc[0]).any()]

        return df_dump

    def extend_df_dump(self, df_dump, context_left, context_right, context_break):
        """Extends a df_dump to context, breaking the context at context_break:

        === (match, matchend), 0, ..., 9, context, contextend ===

        left_context -> context
        (1) context_break is None, context_left is None
            => context = match
        (2) context_break is None, context_left is not None
            => context = match - context_left
        (3) context_break is not None, context_left is None
            => context = s_start
        (4) context_break is not None, context_left is not None
            => context = max(match - context_left, s_start)
        right_context -> contextend analogous

        :param DataFrame df_dump: DataFrame indexed by (match, matchend)
        :param int context_left: maximum context to the left of match
        :param int context_right: maximum context to the right of matchend
        :param str context_break: s-attribute to confine context

        """

        # move index to columns
        df = df_dump.reset_index()

        if context_break is None:
            # left
            if context_left is None:
                df['context'] = df.match
            else:
                df['context'] = df.match - context_left
            # right
            if context_right is None:
                df['contextend'] = df.matchend
            else:
                df['contextend'] = df.matchend + context_right
        else:
            # get context confined by s-attribute if necessary
            s_regions = self.attributes.attribute(context_break, 's')
            s_region = DataFrame(
                df.match.apply(lambda x: s_regions.find_pos(x)).tolist()
            )
            df['s_start'] = s_region[0]
            df['s_end'] = s_region[1]
            df['context_id'] = df.match.apply(lambda x: s_regions.cpos2struc(x))

            # left
            if context_left is None:
                df['context'] = df['s_start']
            else:
                df['context'] = df.match - context_left
                df['context'] = df[['context', 's_start']].max(axis=1)
            # right
            if context_right is None:
                df['contextend'] = df['s_end']
            else:
                df['contextend'] = df.matchend + context_right
                df['contextend'] = df[['contextend', 's_end']].min(axis=1)

        # drop columns, downcast dataframe
        df = df.drop(['s_start', 's_end'], axis=1, errors='ignore')
        df = df.apply(to_numeric, downcast='integer')

        # move (match, matchend) back to index
        df = df.set_index(['match', 'matchend'])

        return df

    def query_cache(self, query, context_left, context_right,
                    context_break, corrections, match_strategy):
        """Queries the corpus, computes (context-extended) df_dump and caches
        the result. Name will be generated automatically from query
        parameters and returned.  Otherwise see query() for
        parameters.

        """

        # check subcorpus size to avoid confusion when re-naming
        if self.subcorpus is not None:
            subcorpus = self.cqp.Exec("size %s" % self.subcorpus)
            subcorpus = str(subcorpus) + self.subcorpus
        else:
            subcorpus = None

        # identify query
        identifiers = ['df_dump', query, context_left, context_right,
                       context_break, corrections, match_strategy, subcorpus]
        name_cache = self.cache.generate_idx(identifiers)

        # retrieve from cache
        df_dump = self.cache.get(name_cache)
        if df_dump is not None:
            logger.info('using version "%s" of df_dump' % name_cache)
            logger.info('df_dump has %d matches' % len(df_dump))
            return df_dump, name_cache

        # compute
        dump = self.query(query, None, context_left, context_right,
                          context_break, corrections, match_strategy, name_cache)
        df_dump = dump.df

        # put into cache
        self.cache.set(name_cache, df_dump)

        return df_dump, name_cache

    def query(self, cqp_query, context=20, context_left=None,
              context_right=None, context_break=None, corrections=dict(),
              match_strategy='standard', name='mnemosyne'):
        """Queries the corpus, computes df_dump.

        === (match, matchend), 0*, ..., 9*, context*, contextend* ===

        If the magic word 'mnemosyne' is given as name of the result,
        the query parameters will be used to create an identifier and
        the resulting subcorpus will be saved, so that the result can
        be accessed directly by later queries with the same parameters
        on the same subcorpus.

        :param str query: CQP query
        :param int context: maximum context around match (symmetric)
        :param int context_left: maximum context left to the match
        :param int context_right: maximum context right to the match
        :param str context_break: s-attribute to confine context
        :param dict corrections: corrections to apply to anchors {nr: offset}
        :param str match_strategy: CQP matching strategy
        :param str name: name for resulting subcorpus

        :return: df_dump
        :rtype: DataFrame

        """

        name_cache = None
        name_cqp = None

        # preprocess input
        query, s_query, anchors = preprocess_query(cqp_query)
        s_query, context_break, s_meta = merge_s_atts(s_query, context_break, None)  # ToDo
        if context_left is None:
            context_left = context
        if context_right is None:
            context_right = context

        # use cached version?
        if name == 'mnemosyne':
            df_dump, name_cache = self.query_cache(
                query, context_left, context_right,
                context_break, corrections, match_strategy
            )
            self.cqp.Exec("%s = %s;" % (name, name_cache))
            self.cqp.Exec("save %s;" % name_cache)  # save to disk

        else:
            # get df_dump
            logger.info("running query to get df_dump")
            df_dump = self.dump_from_query(
                query=query,
                s_query=s_query,
                anchors=anchors,
                match_strategy=match_strategy,
                name=name
            )
            # empty return?
            if len(df_dump) == 0:
                logger.warning("found 0 matches")
                df_dump = DataFrame()
            else:
                # extend dump
                df_dump = self.extend_df_dump(
                    df_dump, context_left, context_right, context_break
                )
                # apply corrections to anchor points
                df_dump = correct_anchors(df_dump, corrections)

        # create return object
        dump = Dump(
            self.copy(),
            df_dump,
            name_cache,
            name_cqp
        )

        return dump
