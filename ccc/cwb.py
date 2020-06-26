#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
from io import StringIO
from glob import glob
from collections import Counter
from tempfile import NamedTemporaryFile
# part of module
from .cqp_interface import CQP
from .utils import Cache, preprocess_query
from .utils import time_it
from .utils import merge_s_atts
from .utils import chunk_anchors, correct_anchors
from .concordances import Concordance
from .collocates import Collocates
from .keywords import Keywords
# requirements
from pandas import DataFrame, read_csv, to_numeric, MultiIndex
from pandas.errors import EmptyDataError
from CWB.CL import Corpus as Crps
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


class Engine:
    """ interface to CQP """

    def __init__(self,
                 registry_path='/usr/local/share/cwb/registry/',
                 cqp_bin='cqp'):

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

        :param str corpus_name: name of corpus in CWB registry
        :param str lib_path: path/to/macros/and/wordlists
        :param str cqp_bin: cqp binary
        :param str registry_path: path/to/cwb/registry/
        :param str data_path: path/to/store/cwb/data/and/cache

        """

        # init data and cache
        self.data = data_path
        if self.data is not None:
            if not os.path.isdir(self.data):
                os.makedirs(data_path)
            cache_path = os.path.join(data_path, corpus_name + "-CACHE_dataframes")
        else:
            cache_path = None
        self.cache = Cache(
            corpus_name,
            cache_path
        )

        # set registry path
        self.registry_path = registry_path

        # init (sub-)corpus information
        self.corpus_name = corpus_name
        self.subcorpus = None

        # active corpus in CQP
        self.cqp = start_cqp(
            cqp_bin, self.registry_path, self.data, self.corpus_name
        )

        # get corpus attributes
        self.attributes = Crps(
            self.corpus_name,
            registry_dir=self.registry_path
        )
        self.attributes_available = read_csv(
            StringIO(self.cqp.Exec('show cd;')),
            sep='\t', names=['att', 'name', 'annotation', 'active']
        ).fillna(False)

        # get corpus size
        self.corpus_size = len(self.attributes.attribute('word', 'p'))

        # load macros and wordlists
        self.lib_path = lib_path
        if self.lib_path:
            self.read_lib(self.lib_path)

        # init counting module
        self.counts = Counts(self.corpus_name, self.registry_path)

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

    # s-attributes
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
            logger.info('using cached version of extents of s-attribute "%s"' % s_att)
            return df

        # compute
        logger.info('computing extents of s-attribute "%s"' % s_att)
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

    # p-attributes
    def cpos2patts(self, cpos, p_atts=['word'], ignore_missing=True):
        """Fills corpus position. Raises IndexError if out-of-bounds.

        :param int cpos: corpus position to fill
        :param list p_atts: p-attribute(s) to fill position with

        :return: p_att(s) of the position
        :rtype: tuple

        """

        if ignore_missing and cpos == -1:
            token = [None] * len(p_atts)
        else:
            token = [self.attributes.attribute(p_att, 'p')[cpos] for p_att in p_atts]

        return tuple(token)

    # working with subcorpora
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
        self.cqp.Exec(subcorpus_query)
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
        values = set(values)
        logger.info("defining subcorpus from %d values" % len(values))
        extents = self.get_s_extents(s_att)
        extents = extents.loc[extents[s_att].isin(values)]
        extents = extents.drop(extents.columns, axis=1)
        self.subcorpus_from_dump(extents, name=name)

    # dump
    def dump_from_query(self, query, s_query=None, anchors=[],
                        match_strategy='standard',
                        name='Last'):
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
        # TODO: improve cache
        # strategy:
        # do not work with target / keyword; additional anchors only in df_dump
        # save match .. matchend to disk
        # name: cache_name
        # dataframes: cache_name_dataframes

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

    def extend_df_dump(self, df_dump, context_left, context_right, s_context):
        """Extends a df_dump to context, breaking the context at s_context:

        === (match, matchend), 0, ..., 9, context, contextend ===

        left_context -> context
        (1) s_context is None, context_left is None
            => context = match
        (2) s_context is None, context_left is not None
            => context = match - context_left
        (3) s_context is not None, context_left is None
            => context = s_start
        (4) s_context is not None, context_left is not None
            => context = max(match - context_left, s_start)
        right_context -> contextend analogous

        :param DataFrame df_dump: DataFrame indexed by (match, matchend)
        :param int context_left: maximum context to the left of match
        :param int context_right: maximum context to the right of matchend
        :param str s_context: s-attribute to confine context

        """

        # move index to columns
        df = df_dump.reset_index()

        # get context confined by s-attribute if necessary
        if s_context is not None:
            s_regions = self.attributes.attribute(s_context, 's')
            s_region = DataFrame(
                df.match.apply(lambda x: s_regions.find_pos(x)).tolist()
            )
            df['s_start'] = s_region[0]
            df['s_end'] = s_region[1]
            df['context_id'] = df.match.apply(lambda x: s_regions.cpos2struc(x))

        if s_context is None:
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

    # query
    def query_cache(self, query, context_left, context_right,
                    s_context, corrections, match_strategy):
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
                       s_context, corrections, match_strategy, subcorpus]
        name_cache = self.cache.generate_idx(identifiers)

        # retrieve from cache
        if self.data is not None:
            df_dump = self.cache.get(name_cache)
            if df_dump is not None:
                logger.info('using version "%s" of df_dump' % name_cache)
                logger.info('df_dump has %d matches' % len(df_dump))
                return df_dump, name_cache

        # compute
        df_dump = self.query(query, None, context_left, context_right,
                             s_context, corrections, match_strategy, name_cache)

        # put into cache
        self.cache.set(name_cache, df_dump)

        return df_dump, name_cache

    def query(self, query, context=20, context_left=None,
              context_right=None, s_context=None, corrections=dict(),
              match_strategy='standard', name='mnemosyne'):
        """Queries the corpus, computes df_dump.

        === (match, matchend), 0*, ..., 9*, context*, contextend* ===

        If the magic word 'mnemosyne' is given as name of the result,
        the query parameters will be used to create an identifier and
        the resulting subcorpus will be saved, so that the result of
        the can be accessed directly by later queries with the same
        parameters on the same subcorpus.

        :param str query: CQP query
        :param int context: maximum context around match (symmetric)
        :param int context_left: maximum context left to the match
        :param int context_right: maximum context right to the match
        :param str s_context: s-attribute to confine context
        :param dict corrections: corrections to apply to anchors {name: offset}
        :param str match_strategy: CQP matching strategy
        :param str name: name for resulting subcorpus

        :return: df_dump
        :rtype: DataFrame

        """

        # preprocess input
        query, s_query, anchors = preprocess_query(query)
        s_query, s_context, s_meta = merge_s_atts(s_query, s_context, None)
        if context_left is None:
            context_left = context
        if context_right is None:
            context_right = context

        # use cached version?
        if name == 'mnemosyne':
            df_dump, name_cache = self.query_cache(
                query, context_left, context_right,
                s_context, corrections, match_strategy
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
                    df_dump, context_left, context_right, s_context
                )
                # apply corrections to anchor points
                df_dump = correct_anchors(df_dump, corrections)

        return df_dump

    # high-level methods
    def concordance(self, df_dump, max_matches=100000):
        return Concordance(
            self,
            df_dump=df_dump,
            max_matches=max_matches
        )

    def collocates(self, df_dump, p_query='lemma'):
        return Collocates(
            self,
            df_dump=df_dump,
            p_query=p_query
        )

    def keywords(self, name=None, df_dump=None, p_query='lemma'):
        return Keywords(
            self,
            name=name,
            df_dump=df_dump,
            p_query=p_query
        )


class Counts:
    """
    returns df_counts:
    def: (p_att_1, p_att_2, ...), freq
    all p_atts are strings, " "-delimited for MWUs (split=NO)

    methods:

    - dump      (df_dump, start, end, p_atts, split)
      - strategy 1: split NO|YES; flags  ; combo x
      - strategy 2: split   |YES; flags  ; combo

    - matches   (name, p_att, split, flags)
      - strategy 1: split NO|   ; flags x; combo
      - strategy 2: split NO|YES; flags x; combo
      - strategy 3: split   |YES; flags  ; combo x

    - mwus      (queries)
      - strategy 1: split NO| - ; flags x; combo x; mwu NO
      - strategy 2: split NO| - ; flags x; combo x; mwu YES
      - strategy 3: split NO| - ; flags x; combo  ; mwu YES

    - marginals (items, p_att, flags, pattern, [fill_missing])
      - strategy 1: split NO| - ; flags x; combo

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
        """Fills corpus position. Raises IndexError if out-of-bounds.

        :param int cpos: corpus position to fill
        :param list p_atts: p-attribute(s) to fill position with

        :return: p_att(s) of the position
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
             p_atts=['word'], split=False, strategy=1):
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
            if flags:
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
                              split=False, flags=None)

        # post-process dataframe
        df["freq"] = df["freq"].astype(int)
        df = df.sort_values(by=["freq"], ascending=False)

        # df = df.loc[df["freq"] != 0]

        return df

    @time_it
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
