#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
from io import StringIO
from glob import glob
from collections import Counter
# part of module
from .cqp_interface import CQP
from .utils import Cache, formulate_cqp_query, preprocess_query, merge_s_atts
from .concordances import Concordance
from .collocates import Collocates
from .keywords import Keywords
from .utils import time_it
# requirements
from pandas import DataFrame, read_csv, to_numeric
from pandas.errors import EmptyDataError
from CWB.CL import Corpus as Crps
# logging
import logging
logger = logging.getLogger(__name__)


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

    def __init__(self,
                 corpus_name,
                 registry_path='/usr/local/share/cwb/registry/',
                 lib_path=None,
                 s_meta=None,
                 s_break=None,
                 cqp_bin='cqp',
                 data_path="/tmp/ccc-data/"):
        """Establishes connection to indexed corpus. Raises KeyError if corpus
        not in registry.

        :param str corpus_name: name of the corpus in CWB registry
        :param str registry_path: path/to/your/cwb/registry/
        :param str lib_path: path to macros and wordlists
        :param str s_meta: s-att referencing meta data rows ([text_id])
        :param str s_break: s-att to break queries and contexts ([s])
        :param str cqp_bin: cqp binary
        :param str cache_path: path/to/store/cache

        """

        # set cache
        self.data = data_path
        if self.data is not None:
            if not os.path.isdir(self.data):
                os.makedirs(data_path)
            self.cache = Cache(corpus_name, os.path.join(data_path, "cache"))
        else:
            self.cache = None

        # registry path
        self.registry_path = registry_path

        # (sub-)corpus information
        self.corpus_name = corpus_name
        self.subcorpus = None

        # connect to corpus
        self.attributes = Crps(
            self.corpus_name,
            registry_dir=self.registry_path
        )
        self.cqp = CQP(
            bin=cqp_bin,
            options='-c -r ' + self.registry_path
        )
        if self.data is not None:
            self.cqp.Exec('set DataDirectory "%s"' % self.data)
        self.cqp.Exec(self.corpus_name)

        # important s-attributes
        self.s_meta = s_meta
        self.s_break = s_break
        # ToDo: load meta data when necessary (AFTER querying: s_break)
        # if s_meta is not None:
        #     self.meta = self.get_meta_regions()

        # get corpus attributes
        self.attributes_available = read_csv(
            StringIO(self.cqp.Exec('show cd;')),
            sep='\t', names=['att', 'value', 'annotation', 'active']
        )

        # get corpus size
        self.corpus_size = len(self.attributes.attribute('word', 'p'))

        # load macros and wordlists
        self.lib_path = lib_path
        if self.lib_path:
            self.read_lib(self.lib_path)

    def read_lib(self, lib_path):
        """Reads macros and worldists. Folder has to contain to sub-folders
        ("macros" and "wordlists").

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

        # execute each macro once (avoid CQP bug for nested macros)
        macros = self.cqp.Exec("show macro;")
        for macro in macros:
            self.cqp.Exec(macro)

    def get_meta_regions(self, ids=None):
        """Maps self.s_meta to corresponding regions, returns DataFrame."""

        # TODO cache

        s_regions = self.attributes.attribute(self.s_meta, 's')
        records = list()
        for s in s_regions:
            idx = s[2].decode()
            add = True
            if ids is not None:
                if idx not in ids:
                    add = False
            if add:
                records.append({
                    's_id': idx,
                    'match': s[0],
                    'matchend': s[1]
                })
        df = DataFrame(records)
        df.set_index('s_id', inplace=True)
        df = df[['match', 'matchend']]
        return df

    def show_subcorpora(self):
        """Returns subcorpora defined in CQP as DataFrame."""
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

    def activate_subcorpus(self, subcorpus=None):
        """Activates subcorpus or switches to corpus."""
        if subcorpus is not None:
            self.cqp.Exec(subcorpus)
            self.subcorpus = subcorpus
            logger.info('CQP switched to subcorpus "%s"' % subcorpus)
        else:
            self.cqp.Exec(self.corpus_name)
            self.subcorpus = self.corpus_name
            logger.info('CQP switched to corpus "%s"' % self.corpus_name)

    def save_subcorpus(self, name='Last', df_node=None):
        self.cqp.Exec("save %s;" % name)

    def define_subcorpus(self, query=None, df_node=None, name='Last',
                         match_strategy='longest', activate=False):
        """Defines a subcorpus via a query. If the query is a dataframe,
        undumps the corpus positions"""

        if query is None and df_node is None and name is None:
            logger.error("cannot define subcorpus without query *or* df_node")
            return

        elif query is not None and df_node is not None:
            logger.error("cannot define subcorpus from query *and* df_node")
            return

        elif df_node is not None:
            logger.info('defining subcorpus "%s" from dataframe' % name)
            self.cqp.Undump(name, df_node)
            parameters = {
                'query': 'directly defined by dataframe',
                'type': 'dataframe',
                'context': None,
                'corpus': self.corpus_name,
                'subcorpus': self.subcorpus
            }

        elif query is not None:
            logger.info('defining subcorpus "%s" from query' % name)
            subcorpus_query = '%s=%s;' % (name, query)
            self.cqp.Exec(subcorpus_query)
            parameters = {
                'query': query,
                'type': 'query',
                'context': None,
                'corpus': self.corpus_name,
                'subcorpus': self.subcorpus
            }
            df_node = self.cqp.Dump(name)

        subcorpus_info = {
            'name': name,
            'parameters': parameters,
            'df_node': df_node
        }
        if activate:
            self.subcorpus_info = subcorpus_info
            self.activate_subcorpus(name)
        else:
            return subcorpus_info

    def subcorpus_from_ids(self, ids, name='tmp_keywords'):
        """ defines a subcorpus by provided s_meta ids. """
        logger.info("defining subcorpus from provided ids")
        meta = self.get_meta_regions(ids)
        meta.reset_index(inplace=True)
        meta.set_index(['match', 'matchend'], inplace=True, drop=False)
        meta.columns = ['s_id', 'region_start', 'region_end']
        self.define_subcorpus(df_node=meta, activate=True, name=name)

    def df_node_from_query(self, query, s_query, anchors, s_break,
                           context, match_strategy='standard',
                           name='tmp_nodes'):
        """Executes query, gets DataFrame of nodes. df_node is indexed by
        (match, matchend). Necessary columns: (region_start, region_end, s_id)
        Additional columns for each anchor.

        :param str query: valid CQP query (without 'within' clause)
        :param str s_query: s-attribute used for initial query
        :param list anchors: anchors to search for
        :param str s_break: s-attribute to confine regions
        :param int context: maximum context around match (symmetric)
        :param str match_strategy: CQP matching strategy

        :return: df_node

        :rtype: pd.DataFrame

        """

        # match strategy
        self.cqp.Exec('set MatchingStrategy "%s";' % match_strategy)

        # process s_query and s_break
        if s_query is None:
            s_query = s_break
        if s_query is None:
            start_query = query
        else:
            start_query = query + ' within ' + s_query

        # first run: 0 and 1 (considering within statement)
        self.cqp.Exec('set ant 0; ank 1;')
        # find matches and dump result
        self.define_subcorpus(query=start_query, name=name, activate=False)
        df_node = self.cqp.Dump(name)
        df_node.columns = [0, 1]
        logger.info("found %d matches" % len(df_node))

        # if there's nothing to return ...
        if df_node.empty:
            return df_node

        # join all other anchors
        if len(anchors) > 0:

            # restrict subsequent queries on results
            current_subcorpus = self.subcorpus
            self.activate_subcorpus(name)

            for pair in [(2, 3), (4, 5), (6, 7), (8, 9)]:
                if pair[0] in anchors or pair[1] in anchors:
                    logger.info(".. running query for anchor pair %s" % str(pair))
                    # set appropriate anchors
                    self.cqp.Exec('set ant %d; set ank %d;' % pair)
                    # dump new anchors
                    self.cqp.Query('tmp = <match> ( %s );' % query)
                    df = self.cqp.Dump("tmp")
                    # selet columns and join to global df
                    df.columns = [pair[0], pair[1]]
                    df_node = df_node.join(df)

            # NA handling
            logger.info("post-processing dataframe")
            df_node.dropna(axis=1, how='all', inplace=True)
            df_node = df_node.apply(to_numeric, downcast='integer')
            df_node.fillna(-1, inplace=True)
            # drop constant columns (contain only -1)
            df_node = df_node.loc[:, (df_node != df_node.iloc[0]).any()]

            # re-set CQP
            self.cqp.Exec('set ant 0; ank 1;')
            self.activate_subcorpus(current_subcorpus)

        # confine regions
        df_node = self.confine_df_node(df_node, s_break, context)

        return df_node

    def confine_df_node(self, df, s_break, context):
        """Confines a df_node by given context size, taking s_breaks into
        consideration and annotating self.s_meta ids.

        """

        # move index to columns
        df = df.reset_index()

        # s_break handling:
        if s_break is None:
            if self.s_meta is not None:
                s_break = self.s_meta
                logger.info('s_break was None, using "%s" (s_meta)' % self.s_meta)
            else:
                s_break = 'text'
                logger.info('s_break was None, using "text" (default)')

        # meta data handling:
        if self.s_meta is None:
            logger.info('meta: no meta data available')
            s_regions = self.attributes.attribute(s_break, "s")
            s_region = DataFrame(
                df.match.apply(lambda x: s_regions.find_pos(x)).tolist()
            )
            df['s_start'] = s_region[0]
            df['s_end'] = s_region[1]
            s_id = df.match.apply(lambda x: s_regions.cpos2struc(x))
        elif self.s_meta.startswith(s_break):
            logger.info('meta: s_break="%s", s_meta="%s"' % (s_break, self.s_meta))
            s_regions = self.attributes.attribute(self.s_meta, 's')
            s_region = DataFrame(
                df.match.apply(lambda x: s_regions.find_pos(x)).tolist()
            )
            df['s_start'] = s_region[0]
            df['s_end'] = s_region[1]
            s_id = s_region[2].apply(lambda x: x.decode('utf-8'))
        else:
            logger.info('meta: s_break="%s", s_meta="%s"' % (s_break, self.s_meta))
            s_regions = self.attributes.attribute(s_break, 's')
            s_region = DataFrame(
                df.match.apply(lambda x: s_regions.find_pos(x)).tolist()
            )
            df['s_start'] = s_region[0]
            df['s_end'] = s_region[1]
            meta_regions = self.attributes.attribute(self.s_meta, 's')
            meta_region = DataFrame(
                df.match.apply(lambda x: meta_regions.find_pos(x)).tolist()
            )
            s_id = meta_region[2].apply(lambda x: x.decode('utf-8'))

        # confine regions by s_break and context
        if context is None:
            df['region_start'] = df.s_start
            df['region_end'] = df.s_end
        else:
            df['region_start'] = df.match - context
            df['region_end'] = df.matchend + context
            df.region_start = df[['region_start', 's_start']].max(axis=1)
            df.region_end = df[['region_end', 's_end']].min(axis=1)

        # downcast dataframe, add and drop columns
        df = df.drop(['s_start', 's_end'], axis=1)
        df = df.apply(to_numeric, downcast='integer')
        df['s_id'] = s_id

        # move match, matchend to index
        df.set_index(['match', 'matchend'], inplace=True)

        return df

    def cpos2token(self, cpos, p_att='word', ignore_missing=True):
        """Fills corpus position. Raises IndexError if out-of-bounds.

        :param list position: corpus position to fill
        :param str p_att: p-attribute to fill position with

        :return: lexicalization of the position
        :rtype: str

        """
        if ignore_missing:
            if cpos == -1:
                token = None
        tokens_all = self.attributes.attribute(p_att, 'p')
        token = tokens_all[cpos]
        return token

    def cpos2counts(self, cpos_list, p_att='word'):
        """Creates a frequency table for the p_att-values of the cpos-list."""
        lex_items = [self.cpos2token(p, p_att=p_att) for p in cpos_list]
        counts = Counter(lex_items)
        df_counts = DataFrame.from_dict(counts, orient='index', columns=['freq'])
        return df_counts

    def marginals(self, items, p_att='word', flags=3, regex=False):
        """Extracts marginal frequencies for given items (0 if not in corpus).

        :param list items: items to get marginals for
        :param str p_att: p-attribute to get counts for
        :param int flags: 1 = %c, 2 = %d, 3 = %cd

        :return: counts for each item (indexed by items, column "freq")
        :rtype: DataFrame

        """
        tokens_all = self.attributes.attribute(p_att, 'p')
        counts = list()
        for item in items:
            if not regex:
                try:
                    counts.append(tokens_all.frequency(item))
                except KeyError:
                    counts.append(0)
            else:
                cpos = tokens_all.find_pattern(item, flags=flags)
                counts.append(len(cpos))
        df = DataFrame(data=counts, index=items, columns=['freq'])
        return df

    def item_freq(self, items, p_att='word', s_query='text'):
        """Calculates item frequencies."""

        freqs = list()
        # run query for each item
        for item in items:
            query = formulate_cqp_query([item], p_att, s_query)
            freq = self.cqp.Exec('tmp_freq=%s; size tmp_freq;' % query)
            if freq is None:
                freq = 0
            else:
                freq = int(freq)
            freqs.append(freq)

        # convert to dataframe
        df = DataFrame(data=freqs, index=items, columns=['freq'])

        return df

    def item_freq_2(self, items, p_att='word', s_query='text'):
        """Calculates item frequencies."""

        query = "tmp_query=" + formulate_cqp_query(items, p_att)
        self.cqp.Exec(query)
        df_node = self.cqp.Dump("tmp_query")
        df = self.count_matches(df=df_node, p_att=p_att)
        # fill missing values
        missing = set(items) - set(df.index)
        df_missing = DataFrame(data=0, index=missing, columns=['freq'])
        df = df.append(df_missing)

        return df

    @time_it
    def count_matches(self, name=None, df=None, p_att="word", split=False):
        """counts strings or tokens ([match .. matchend] for df)"""

        # undump the dump
        if name is not None and df is not None:
            logger.error("cannot count name *and* df")
            return DataFrame()
        elif name is None and df is None:
            logger.error("cannot count *nothing*")
            return DataFrame()
        elif name is None:
            name = "tmp_counts"
            self.define_subcorpus(df_node=df, name=name, activate=False)

        # tabulate matches
        logger.info("tabulating ...")
        cqp_return = self.cqp.Exec(
            'tabulate %s match .. matchend %s;' % (name, p_att)
        )

        # optionally split strings into tokens
        if split:
            tokens = cqp_return.replace("\n", " ").split(" ")
        else:
            tokens = cqp_return.split("\n")
        logger.info("... found %d tokens" % len(tokens))

        # count
        counts = Counter(tokens)
        df_counts = DataFrame.from_dict(counts, orient='index', columns=['freq'])

        return df_counts

    @time_it
    def count_matches_2(self, df_node, p_att="word", split=False):
        """counts tokens in [region_start .. region_end]"""

        logger.info("count tokens in each region")
        ls = df_node.apply(lambda x: self.node2regions(x, p_att), axis=1).values
        logger.info("counting")
        counts = Counter([token for tokens in ls for token in tokens])
        df_counts = DataFrame.from_dict(counts, orient='index', columns=['freq'])
        logger.info("... done counting")

        return df_counts

    def node2regions(self, row, p_att):
        start = row['region_start']
        end = row['region_end']
        tokens = [
            self.attributes.attribute(p_att, 'p')[pos] for pos in range(start, end + 1)
        ]
        return tokens

    def query(self, query, context=20, s_break=None,
              match_strategy='standard', name='tmp_query', info=False):
        """Query the corpus, cache the result."""

        query, s_query, anchors_query = preprocess_query(query)

        # get default s_break
        if s_break is None:
            s_break = self.s_break

        s_query, s_break, s_meta = merge_s_atts(s_query, s_break, self.s_meta)

        parameters = {
            'query': query,
            's_query': s_query,
            'anchors_query': anchors_query,
            'context': context,
            's_break': s_break,
            'match_strategy': match_strategy,
            'corpus': self.corpus_name,
            'subcorpus': self.subcorpus
        }

        # cache
        if self.cache is not None:
            df_node = self.cache.get(list(parameters.values()))
        else:
            df_node = None
        if df_node is not None:
            logger.info("retrieved df_node from cache")
        else:
            # retrieve
            logger.info("running query to get df_node")
            df_node = self.df_node_from_query(
                query=query,
                s_query=s_query,
                anchors=anchors_query,
                s_break=s_break,
                context=context,
                match_strategy=match_strategy,
                name=name
            )
            # put in cache
            if self.cache is not None:
                self.cache.set(list(parameters.values()), df_node)

        # logging
        if len(df_node) == 0:
            logger.warning('0 query hits')
            return
        else:
            logger.info("df_node has %d matches" % len(df_node))

        if info:
            return df_node, parameters

        return df_node

    def concordance(self, df_node, max_matches=None):
        return Concordance(
            self,
            df_node=df_node,
            max_matches=max_matches
        )

    def collocates(self, df_node, p_query='lemma'):
        return Collocates(
            self,
            df_node=df_node,
            p_query=p_query
        )

    def keywords(self, name=None, df_node=None, p_query='lemma'):
        return Keywords(
            self,
            name=name,
            df_node=df_node,
            p_query=p_query
        )
