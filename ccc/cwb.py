#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
from io import StringIO
from glob import glob
from collections import Counter
# part of module
from .cqp_interface import CQP
from .utils import Cache, formulate_cqp_query, preprocess_query
# requirements
from pandas import DataFrame, read_csv, to_numeric
from CWB.CL import Corpus
import logging
logger = logging.getLogger(__name__)


class CWBEngine:
    """ interface to CWB """

    def __init__(self,
                 corpus_name,
                 registry_path='/usr/local/share/cwb/registry/',
                 lib_path=None,
                 meta_path=None,
                 s_meta=None,
                 cqp_bin='cqp',
                 cache_path='/tmp/ccc-cache'):
        """Establishes connection to indexed corpus. Raises KeyError if corpus
        not in registry.

        """

        # set cache
        self.cache = Cache(corpus_name, cache_path)

        # registry path
        self.registry_path = registry_path

        # (sub-)corpus information
        self.corpus_name = corpus_name
        self.subcorpus = corpus_name

        # meta data
        self.meta_path = meta_path
        if self.meta_path:
            self.meta = read_csv(meta_path, sep='\t', index_col=0)
        self.s_meta = s_meta

        # set interface
        self.corpus = Corpus(
            self.corpus_name,
            registry_dir=self.registry_path
        )
        self.cqp = CQP(
            bin=cqp_bin,
            options='-c -r ' + self.registry_path
        )

        # activate corpus
        self.cqp.Exec(self.corpus_name)

        # get corpus attributes
        df = read_csv(StringIO(self.cqp.Exec('show cd;')), sep='\t',
                      names=['att', 'value', 'annotation'])
        self.corpus_attributes = df

        # get corpus size
        self.corpus_size = len(self.corpus.attribute('word', 'p'))

        # load macros and wordlists
        self.lib_path = lib_path
        if self.lib_path:
            self.read_lib(self.lib_path)

    def read_lib(self, path_lib):
        """Reads macros and worldists."""

        # wordlists
        wordlists = glob(os.path.join(path_lib, 'wordlists', '*'))
        for wordlist in wordlists:
            name = wordlist.split('/')[-1].split('.')[0]
            abs_path = os.path.abspath(wordlist)
            cqp_exec = 'define $%s < "%s";' % (
                name, abs_path
            )
            self.cqp.Exec(cqp_exec)

        # macros
        macros = glob(os.path.join(path_lib, 'macros', '*'))
        for macro in macros:
            abs_path = os.path.abspath(macro)
            cqp_exec = 'define macro < "%s";' % abs_path
            self.cqp.Exec(cqp_exec)

    def get_meta_regions(self):
        s_regions = self.corpus.attribute(self.s_meta, 's')
        records = list()
        for s in s_regions:
            records.append({
                'idx': s[2].decode(),
                'match': s[0],
                'matchend': s[1]
            })
        df = DataFrame(records)
        df.set_index('idx', inplace=True)
        df = df[['match', 'matchend']]
        return df

    def show_subcorpora(self):
        cqp_return = self.cqp.Exec("show named;")
        df = read_csv(StringIO(cqp_return), sep="\t", header=None)
        if not df.empty:
            df.columns = ["storage", "corpus:subcorpus", "size"]
            crpssbcrps = df["corpus:subcorpus"].str.split(":", 1).str
            df['corpus'] = crpssbcrps[0]
            df['subcorpus'] = crpssbcrps[1]
            df.drop('corpus:subcorpus', axis=1, inplace=True)
            df = df[['corpus', 'subcorpus', 'size', 'storage']]
        return df

    def activate_subcorpus(self, subcorpus=None):
        """Activates subcorpus or corpus."""
        if subcorpus is not None:
            self.cqp.Exec(subcorpus)
            self.subcorpus = subcorpus
            logger.info('CQP switched to subcorpus "%s"' % subcorpus)
        else:
            self.cqp.Exec(self.corpus_name)
            self.subcorpus = self.corpus_name
            logger.info('CQP switched to corpus "%s"' % self.corpus_name)
        # logger.info("subcorpora:\n" + str(self.show_subcorpora()))

    def define_subcorpus(self, query, name='Last',
                         match_strategy='longest', activate=False):
        """Defines a subcorpus via a query and activates it."""

        self.cqp.Exec('set MatchingStrategy "%s";' % match_strategy)

        if type(query) == DataFrame:
            self.cqp.Undump(name, query)
        elif type(query) == str:
            subcorpus_query = '{name}={query};'.format(
                name=name, query=query
            )
            self.cqp.Exec(subcorpus_query)
        if activate:
            self.activate_subcorpus(name)

    def _df_node_from_query(self, query, s_query, anchors,
                            s_break, context, match_strategy):
        """see df_node_from_query, which is a cached version of this method"""

        # match strategy
        self.cqp.Exec('set MatchingStrategy "%s";' % match_strategy)

        # strip within statement from query and check which anchors there are
        query, s_query, anchors = preprocess_query(query)

        # process s_query and s_break
        if s_query is None:
            s_query = s_break
        if s_query is None:
            start_query = query
        else:
            start_query = query + ' within ' + s_query

        # first run: 0 and 1 (considering within statement)
        logger.info("running query for anchor pair (0, 1)")
        self.cqp.Exec('set ant 0; ank 1;')
        # find matches and dump result
        self.define_subcorpus(start_query, 'tmp_nodes')
        df_node = self.cqp.Dump('tmp_nodes')
        df_node.columns = [0, 1]
        logger.info("found %d matches" % len(df_node))

        # if there's nothing to return ...
        if df_node.empty:
            return df_node

        # join all other anchors
        if len(anchors) > 0:

            # restrict subsequent queries on results
            current_subcorpus = self.subcorpus
            self.activate_subcorpus('tmp_nodes')

            for pair in [(2, 3), (4, 5), (6, 7), (8, 9)]:
                if pair[0] in anchors or pair[1] in anchors:
                    logger.info("running query for anchor pair %s" % str(pair))
                    # set appropriate anchors
                    self.cqp.Exec('set ant %d; set ank %d;' % pair)
                    # dump new anchors
                    self.cqp.Exec('tmp = <match> ( %s );' % query)
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

    def df_node_from_query(self, query, s_query=None, anchors=None,
                           s_break="text", context=20,
                           match_strategy="standard"):
        """Executes anchored query within s_break to get df_anchor.

        :param str query: valid CQP query (without 'within' clause)
        :param str s_query: s-attribute use for initial query
        :param list anchors: anchors to search for
        :param str s_break: s-attribute to confine regions
        :param int context: maximum context around match (symmetric)
        :param str match_strategy: CQP matching strategy

        :return: df_node (match, matchend) + (region_start, region_end, s_id)
        + additional columns for each anchor
        :rtype: pd.DataFrame

        """
        identifiers = ['df_node_from_query', self.corpus_name, self.subcorpus,
                       query, s_query, anchors, s_break, context, match_strategy]

        df_node = self.cache.get(identifiers)

        if df_node is None:
            # create result
            df_node = self._df_node_from_query(
                query, s_query, anchors, s_break, context, match_strategy
            )
            # put in cache
            self.cache.set(identifiers, df_node)

        return df_node

    def confine_df_node(self, df, s_break, context):
        """Confines a df_node by given context size, taking s_breaks into
        consideration and annotating self.s_meta ids.

        """

        # move index to columns
        df = df.reset_index()

        # meta data handling:
        if self.s_meta is None:
            logger.info('meta: no meta data available')
            s_regions = self.corpus.attribute(s_break, "s")
            s_region = DataFrame(
                df.match.apply(lambda x: s_regions.find_pos(x)).tolist()
            )
            df['s_start'] = s_region[0]
            df['s_end'] = s_region[1]
            s_id = df.match.apply(lambda x: s_regions.cpos2struc(x))
        elif self.s_meta.startswith(s_break):
            logger.info('meta: s_break="%s", s_meta="%s"' % (s_break, self.s_meta))
            s_regions = self.corpus.attribute(self.s_meta, 's')
            print(s_regions)
            s_region = DataFrame(
                df.match.apply(lambda x: s_regions.find_pos(x)).tolist()
            )
            df['s_start'] = s_region[0]
            df['s_end'] = s_region[1]
            s_id = s_region[2].apply(lambda x: x.decode('utf-8'))
        else:
            logger.info('meta: s_break="%s", s_meta="%s"' % (s_break, self.s_meta))
            s_regions = self.corpus.attribute(s_break, 's')
            s_region = DataFrame(
                df.match.apply(lambda x: s_regions.find_pos(x)).tolist()
            )
            df['s_start'] = s_region[0]
            df['s_end'] = s_region[1]
            meta_regions = self.corpus.attribute(self.s_meta, 's')
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
                return None
        tokens_all = self.corpus.attribute(p_att, 'p')
        return tokens_all[cpos]

    def cpos2counts(self, cpos, p_att='word'):
        """Creates a frequency table for the p_att-values of the cpos."""
        lex_items = [self.cpos2token(p, p_att=p_att) for p in cpos]
        counts = Counter(lex_items)
        df_counts = DataFrame.from_dict(counts, orient='index', columns=['freq'])
        return df_counts

    def marginals(self, items, p_att='word', flags=3, regex=False):
        """Extracts marginal frequencies for given items (0 if not in corpus).

        :param list items: items to get marginals for
        :param str p_att: p-attribute to get counts for
        :param int flags: 1 = %c, 2 = %d, 3 = %cd

        :return: counts for each item (indexed by items, column "f2")
        :rtype: DataFrame

        """
        tokens_all = self.corpus.attribute(p_att, 'p')
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
        f2 = DataFrame(index=items)
        f2['freq'] = counts
        return f2

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

        query = formulate_cqp_query(items, p_att)
        df_node = self.df_node_from_query(query, s_query, context=0)
        df = self.count_matches(df_node, p_att)
        # fill missing values
        missing = set(items) - set(df.index)
        df_missing = DataFrame(data=0, index=missing, columns=['freq'])
        df = df.append(df_missing)

        return df

    def count_matches(self, df_node, p_att="word", split=False):
        """counts strings or tokens in df_nodes.index"""

        # undump the dump
        self.define_subcorpus(df_node, name='tmp_counts', activate=False)

        # tabulate matches
        match_strings = self.cqp.Exec(
            'tabulate tmp_counts match .. matchend %s;' % p_att
        ).split('\n')

        # optionally split strings into tokens
        if split:
            tokens = list()
            for t in match_strings:
                tokens += t.split(" ")
        else:
            tokens = match_strings

        # count
        counts = Counter(tokens)
        df_counts = DataFrame.from_dict(counts, orient='index', columns=['freq'])

        return df_counts
