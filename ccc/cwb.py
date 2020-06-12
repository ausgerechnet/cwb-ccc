#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
from io import StringIO
from glob import glob
from collections import Counter
# part of module
from .cqp_interface import CQP
from .utils import Cache, formulate_cqp_query, preprocess_query
from .utils import time_it
# , merge_s_atts
from .utils import chunk_anchors
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


# TODO: save subcopora independently from post-processing
# TODO: result object (cache-key, name, df_dump, concordance, collocates, keywords)
# TODO: counting with group?


class Engine:
    """ interface to CQP """

    def __init__(self,
                 registry_path='/usr/local/share/cwb/registry/',
                 cqp_bin='cqp'):

        self.registry_path = registry_path
        self.cqp_bin = cqp_bin

    def start_cqp(self):
        return CQP(
            bin=self.cqp_bin,
            options='-c -r ' + self.registry_path
        )

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
        self.cqp = CQP(
            bin=cqp_bin,
            options='-c -r ' + self.registry_path
        )
        if self.data is not None:
            self.cqp.Exec('set DataDirectory "%s"' % self.data)
        self.cqp.Exec(self.corpus_name)

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

    def read_lib(self, lib_path):
        """Reads macros and worldists. Folder has to contain two sub-folders
        ("macros" and "wordlists").

        :param str lib_path: path/to/macros/and/wordlists

        """

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

    def get_s_extents(self, s_att):
        """Maps s_att to corresponding extents, returns DataFrame.

        :param str s_att: s-attribute to get extents for

        :return: df indexed by match, matchend; CWBID, annotation
        :rtype: DataFrame

        """

        logger.info("cwb.get_s_extents")

        # retrieve from cache
        parameters = ['s_extents', s_att]
        df = self.cache.get(parameters)
        if df is not None:
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

    def get_s_annotation(self, df_dump, s_att):
        """Retrieves CWBIDs (and annotations) of s-attribute of match.

        :param DataFrame df_dump: DataFrame indexed by (match, matchend)
        :param str s_att: s-attribute to retrieve

        """
        # TODO remove double entries (tweet_id_CWBID = tweet_CWBID etc)

        logger.info("cwb.get_s_annotation")

        # move index to columns
        df = df_dump.reset_index()

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

        # move (match, matchend) back to index
        df = df.set_index(['match', 'matchend'])

        return df

    def get_s_annotations(self, df_dump, s_atts):
        """gets all annotations of all s-att in s_atts at match positions"""
        for s in s_atts:
            df_dump = self.get_s_annotation(df_dump, s)
        return df_dump

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

    def dump_from_query(self, query, s_query=None, anchors=[],
                        match_strategy='standard',
                        name='Last'):
        """Executes query, gets DataFrame of corpus positions (dump of CWB).
        df_dump is indexed by (match, matchend).  Optional columns for
        each anchor.

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
            token = list()
            for p_att in p_atts:
                tokens_all = self.attributes.attribute(p_att, 'p')
                token.append(tokens_all[cpos])

        return tuple(token)

    def count_cpos(self, cpos_list, p_atts=['word']):
        """Creates a frequency table for the p_att-values of the cpos-list.

        :param list cpos_list: corpus positions to fill
        :param list p_atts: p-attribute (combinations) to count

        :return: counts of the p_attribute (combinations) of the positions
        :rtype: DataFrame

        """
        lex_items = [self.cpos2patts(p, p_atts=p_atts) for p in cpos_list]
        counts = Counter(lex_items)
        df_counts = DataFrame.from_dict(counts, orient='index', columns=['freq'])
        df_counts.index = MultiIndex.from_tuples(df_counts.index, names=p_atts)
        return df_counts

    def count_dump(self, df_dump, start='match', end='matchend',
                   p_atts=['word'], split=False):
        """counts tokens in [start .. end] where start and end are columns in
        df_dump.

        :param list df_dump: corpus positions to fill
        :param str start: column name where to start counting
        :param str end: column name where to end counting
        :param list p_atts: p-attribute (combinations) to count
        :param bool split: token-based count? (default: MWU)

        :return: counts of the p_attribute (combinations) of the positions
        :rtype: DataFrame
        """

        logger.info("extracting tokens in each region")
        df_dump = df_dump.reset_index()  # for working with match, matchend
        ls = df_dump.apply(
            lambda x: [
                self.cpos2patts(cpos, p_atts) for cpos in range(
                    x[start], x[end] + 1
                )
            ],
            axis=1
        ).values

        logger.info("counting ...")
        if split:
            counts = Counter([token for tokens in ls for token in tokens])
            df_counts = DataFrame.from_dict(counts, orient='index', columns=['freq'])
            df_counts.index = MultiIndex.from_tuples(df_counts.index, names=p_atts)
        else:
            counts = Counter([" ".join(["_".join(t) for t in tokens]) for tokens in ls])
            df_counts = DataFrame.from_dict(counts, orient='index', columns=['freq'])
            df_counts.index.name = " ".join(p_atts)
        return df_counts

    def marginals(self, items, p_att='word', flags=3, pattern=False):
        """Extracts marginal frequencies for given items (0 if not in corpus).

        :param list items: items to get marginals for
        :param str p_att: p-attribute to get counts for
        :param int flags: 1 = %c, 2 = %d, 3 = %cd
        :param bool pattern: activate wildcards?

        :return: counts for each item (indexed by items, column "freq")
        :rtype: DataFrame

        """
        tokens_all = self.attributes.attribute(p_att, 'p')
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
        return df

    def confine_df_dump(self, df_dump, context_left, context_right, s_context):
        """Extends a df_dump to context, breaking the context at s_context.

        left context:
        (1) s_context is None, context_left is None
            => context = match
        (2) s_context is None, context_left is not None
            => context = match - context_left
        (3) s_context is not None, context_left is None
            => context = s_start
        (4) s_context is not None, context_left is not None
            => context = max(match - context_left, s_start)
        right context analogous

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

    def count_matches(self, name, p_att="word", split=False, flags="%cd"):
        """counts tokens in [match .. matchend] of subcorpus

        :param list name: name of the subcorpus
        :param list p_atts: p-attribute
        :param bool split: token-based count? (default: MWU)

        :return: counts of the p_attribute (combinations) of the positions
        :rtype: DataFrame
        """

        if not split:
            logger.info("cqp is counting ...")
            cqp_return = self.cqp.Exec(
                'count %s by %s %s;' % (name, p_att, flags)
            )
            df_counts = read_csv(
                StringIO(cqp_return), sep="\t", header=None,
                names=["freq", "unknown", "item"]
            )
            df_counts = df_counts.set_index('item')
            df_counts.index.name = None
            df_counts = df_counts[['freq']]

        else:
            # tabulate matches
            logger.info("tabulating ...")
            cqp_return = self.cqp.Exec(
                'tabulate %s match .. matchend %s;' % (name, p_att)
            )

            # split strings into tokens
            logger.info("splitting tokens ...")
            tokens = cqp_return.replace("\n", " ").split(" ")
            logger.info("... found %d tokens" % len(tokens))

            # count
            logger.info("counting")
            counts = Counter(tokens)
            df_counts = DataFrame.from_dict(counts, orient='index', columns=['freq'])

        return df_counts

    @time_it
    def count_items(self, items, p_att='word', s_query='text',
                    strategy=1, name='Last', fill_missing=True):
        """Calculates item frequencies in given subcorpus.

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

        # only count once for each item
        items = set(items)

        if strategy == 1:
            logger.info("count_items: strategy 1")
            freqs = list()
            for item in items:
                query = formulate_cqp_query([item], p_att, s_query)
                self.subcorpus_from_query(query, name)
                freq = self.cqp.Exec('size %s;' % name)
                freqs.append(freq)
            df = DataFrame(data=freqs, index=items, columns=['freq'])

        elif strategy == 2:
            logger.info("count_items: strategy 2")
            query = formulate_cqp_query(items, p_att, s_query)
            df_node = self.subcorpus_from_query(query, name)
            df = self.count_dump(df_node, p_atts=[p_att])

        elif strategy == 3:
            logger.info("count_items: strategy 3")
            query = formulate_cqp_query(items, p_att, s_query)
            self.subcorpus_from_query(query, name)
            df = self.count_matches(name, p_att=p_att)

        # post-process dataframe
        df["freq"] = df["freq"].astype(int)
        df = df.sort_values(by=["freq"], ascending=False)

        if fill_missing:
            missing = set(items) - set(df.index)
            df_missing = DataFrame(data=0, index=missing, columns=['freq'])
            df = df.append(df_missing)
        else:
            df = df.loc[df["freq"] != 0]

        return df

    # high-level methods
    def query_cache(self, query, context=20, context_left=None,
                    context_right=None, s_context=None, s_meta=[],
                    match_strategy='standard'):
        """Query the corpus, compute df_dump and cache the result. See query()
        for parameters.
        """

        # check subcorpus size to avoid confusion when re-naming
        if self.subcorpus is not None:
            subcorpus = self.cqp.Exec("size %s" % self.subcorpus)
            subcorpus = str(subcorpus) + self.subcorpus
        else:
            subcorpus = None

        # set parameters
        parameters = ['df_dump', query, context, context_left,
                      context_right, s_context, s_meta, match_strategy,
                      subcorpus]
        name_cache = self.cache.generate_idx(parameters)

        # retrieve from cache
        if self.data is not None:
            df_dump = self.cache.get(name_cache)
            if df_dump is not None:
                logger.info('using version "%s" of df_dump' % name_cache)
                logger.info('df_dump has %d matches' % len(df_dump))
                return df_dump, name_cache

        # compute
        df_dump = self.query(query, context, context_left,
                             context_right, s_context, s_meta,
                             match_strategy, name_cache)

        # put into cache
        self.cache.set(name_cache, df_dump)

        return df_dump, name_cache

    def query(self, query, context=20, context_left=None,
              context_right=None, s_context=None, s_meta=[],
              match_strategy='standard', name='mnemosyne'):
        """Query the corpus, compute df_dump.

        If the magic word 'mnemosyne' is given as name of
        the result, the query parameters will be used to create and
        identifier and the resulting subcorpus will be saved, so that
        the same query (on the same subcorpus) can be retrieved for
        later queries.

        :param str query: CQP query
        :param int context: maximum context around match (symmetric)
        :param int context_left: maximum context left to the match
        :param int context_right: maximum context right to the match
        :param str s_context: s-attribute to confine context
        :param list s_meta: s-attributes to show (id + annotation)
        :param str match_strategy: CQP matching strategy
        :param str name: name for resulting subcorpus

        """

        # use cached version
        if name == 'mnemosyne':

            df_dump, name_cache = self.query_cache(query, context, context_left,
                                                   context_right, s_context,
                                                   s_meta, match_strategy)
            self.cqp.Exec("%s = %s;" % (name, name_cache))
            self.cqp.Exec("save %s;" % name_cache)
            return df_dump

        # get df_dump
        logger.info("running query to get df_dump")
        query, s_query, anchors = preprocess_query(query)
        df_dump = self.dump_from_query(
            query=query,
            s_query=s_query,
            anchors=anchors,
            match_strategy=match_strategy,
            name=name
        )

        # empty return?
        if len(df_dump) == 0:
            logger.warning("can't work on zero matches")
            return DataFrame()

        # get context
        if context_left is None:
            context_left = context
        if context_right is None:
            context_right = context
        df_dump = self.confine_df_dump(
            df_dump, context_left, context_right, s_context
        )

        # get s_annotations
        if len(s_meta) > 0:
            df_dump = self.get_s_annotations(df_dump, s_meta)

        return df_dump

    def concordance(self, df_dump, max_matches=None):
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
