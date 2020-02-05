#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
from io import StringIO
from glob import glob
from collections import Counter
# part of module
from .cqp_interface import CQP
from .utils import Cache, formulate_cqp_query, anchor_query_to_anchors
# requirements
from pandas import DataFrame, read_csv, to_numeric
from CWB.CL import Corpus


class CWBEngine:
    """ interface to CWB """

    def __init__(self,
                 corpus_name,
                 registry_path='/usr/local/share/cwb/registry/',
                 lib_path=None,
                 meta_path=None,
                 meta_s=None,
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
        self.meta_s = meta_s

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
        s_regions = self.corpus.attribute(self.meta_s, 's')
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

    def deactivate_subcorpus(self):
        """Deactivates subcorpus."""
        self.cqp.Exec(self.corpus_name)
        self.subcorpus = self.corpus_name
        # print(self.cqp.Exec("show named;"))
        print('CQP switched to corpus "%s"' % self.corpus_name)

    def subcorpus_from_query(self, query, name='Last', match_strategy='longest'):
        """Defines a subcorpus via a query and activates it."""

        self.cqp.Exec('set MatchingStrategy "%s";' % match_strategy)
        subcorpus_query = '{name}={subcorpus_query};'.format(
            name=name, subcorpus_query=query
        )
        self.cqp.Exec(subcorpus_query)
        self.cqp.Exec(name)
        self.subcorpus = name
        print('CQP switched to subcorpus "%s" of corpus "%s"' % (name, self.corpus_name))

    def subcorpus_from_df(self, df, name='Last'):
        """Defines a subcorpus via corpus positions and activates it."""

        self.cqp.Undump(name, df)
        self.cqp.Exec(name)
        self.subcorpus = name
        print('CQP switched to subcorpus "%s" of corpus "%s"' % (name, self.corpus_name))

    def _df_node_from_query(self, query, s_break, context, match_strategy):
        """see df_node_from_query, which is a cached version of this method"""

        # match strategy
        self.cqp.Exec('set MatchingStrategy "%s";' % match_strategy)

        # run query and dump results
        query += ' within %s;' % s_break
        self.cqp.Query(query)
        df = self.cqp.Dump()

        # return empty dataframe if query has no results
        if df.empty:
            return DataFrame()

        # confine regions
        df_node = self.confine_df_node(df, s_break, context)

        return df_node

    def df_node_from_query(self, query, s_break, context=50,
                           match_strategy='longest'):
        """Executes query within s_break to get df_node.

        :param str query: valid CQP query (without 'within' clause)
        :param str s_break: s-attribute to confine regions
        :param int context: maximum context around node (symmetric)

        :return: df_node (match, matchend) + (region_start, region_end, s_id)
        :rtype: pd.DataFrame

        """

        identifiers = ['df_node', query, s_break, context, match_strategy]
        cached_data = self.cache.get(identifiers, self.subcorpus)

        # create result
        if cached_data is None:
            df_node = self._df_node_from_query(query, s_break,
                                               context, match_strategy)
            self.cache.set(identifiers, df_node, self.subcorpus)
        else:
            df_node = cached_data

        return df_node

    def _df_anchor_from_query(self, anchor_query, s_break, context, match_strategy):
        """see df_anchor_from_query, which is a cached version of this method"""

        # match strategy
        self.cqp.Exec('set MatchingStrategy "%s";' % match_strategy)

        # check which anchors there are
        anchors = anchor_query_to_anchors(anchor_query)

        # first run: 0 and 1
        print("... running query for anchor pair (0, 1) ...", end="\r")
        self.cqp.Exec('set ant 0; ank 1;')
        self.cqp.Exec('tmp_anchor = ' + anchor_query + ' within ' + s_break + ';')

        # dump result
        df_anchor = self.cqp.Dump('tmp_anchor')
        df_anchor.columns = [0, 1]
        print("... running query for anchor pair (0, 1) ... found %d matches" % len(df_anchor))

        # if there's nothing to return ...
        if df_anchor.empty:
            return DataFrame()

        # join all the other ones
        for pair in [(2, 3), (4, 5), (6, 7), (8, 9)]:
            if pair[0] in anchors or pair[1] in anchors:
                print("... running query for anchor pair %s ..." % str(pair))
                # load initial matches
                self.cqp.Exec('tmp_anchor;')
                # set appropriate anchors
                self.cqp.Exec(
                    'set AnchorNumberTarget %d; set AnchorNumberKeyword %d;' % pair
                )
                self.cqp.Exec('tmp = <match> ( %s );' % anchor_query)
                df = self.cqp.Dump("tmp")
                df.columns = [pair[0], pair[1]]
                df_anchor = df_anchor.join(df)

        # re-set CQP
        self.cqp.Exec(self.subcorpus)
        self.cqp.Exec('set ant 0; ank 1;')

        # NA handling
        print("... collected all anchors ... post-processing dataframe ...")
        df_anchor.dropna(axis=1, how='all', inplace=True)
        df_anchor = df_anchor.apply(to_numeric, downcast='integer')
        df_anchor.fillna(-1, inplace=True)

        # drop constant columns (contain only -1)
        df_anchor = df_anchor.loc[:, (df_anchor != df_anchor.iloc[0]).any()]

        # confine regions
        df_anchor = self.confine_df_node(df_anchor, s_break, context)

        return df_anchor

    def df_anchor_from_query(self, anchor_query, s_break='text',
                             context=50, match_strategy='longest'):
        """Executes anchored query within s_break to get df_anchor.

        :param str anchor_query: anchored CQP query (without 'within' clause)
        :param str s_break: s-attribute to confine regions
        :param int context: maximum context around match (symmetric)

        :return: df_anchor with 5 base columns (match, matchend,
        region_start, region_end, s_id) and additional columns for each anchor
        :rtype: pd.DataFrame

        """

        identifiers = ['df_anchor_from_query', anchor_query, s_break,
                       context, match_strategy]
        cached_data = self.cache.get(identifiers, self.subcorpus)

        # create result
        if cached_data is None:
            df_anchor = self._df_anchor_from_query(anchor_query,
                                                   s_break, context,
                                                   match_strategy)
            self.cache.set(identifiers, df_anchor, self.subcorpus)
        else:
            df_anchor = cached_data

        return df_anchor

    def confine_df_node(self, df, s_break, context):
        """Confines a given df_node by given context size, taking s_breaks
        into consideration.

        """

        # move index to columns
        df = df.reset_index()

        # meta data handling:
        if self.meta_s is None:
            # case 1: just get s_break info
            s_regions = self.corpus.attribute(s_break, "s")
            s_region = DataFrame(
                df.match.apply(lambda x: s_regions.find_pos(x)).tolist()
            )
            df['s_start'] = s_region[0]
            df['s_end'] = s_region[1]
            s_id = df.match.apply(lambda x: s_regions.cpos2struc(x))
        elif self.meta_s.startswith(s_break):
            # case 2: use meta info from s_break variable
            s_regions = self.corpus.attribute(self.meta_s, 's')
            s_region = DataFrame(
                df.match.apply(lambda x: s_regions.find_pos(x)).tolist()
            )
            df['s_start'] = s_region[0]
            df['s_end'] = s_region[1]
            s_id = s_region[2].apply(lambda x: x.decode('utf-8'))
        else:
            # case 3: add additional meta_s info
            s_regions = self.corpus.attribute(s_break, 's')
            s_region = DataFrame(
                df.match.apply(lambda x: s_regions.find_pos(x)).tolist()
            )
            df['s_start'] = s_region[0]
            df['s_end'] = s_region[1]
            meta_regions = self.corpus.attribute(self.meta_s, 's')
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
        tokens_all = self.corpus.attribute(p_att, 'p')
        if ignore_missing:
            if cpos == -1:
                return None
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

    def item_freq(self, items, p_att='word', s_break='text'):
        """Calculates item frequencies."""

        freqs = list()
        # run query for each item
        for item in items:
            query = formulate_cqp_query([item], p_att, s_break)
            freq = self.cqp.Exec('tmp=%s; size tmp;' % query)
            if freq is None:
                freq = 0
            else:
                freq = int(freq)
            freqs.append(freq)

        # convert to dataframe
        df = DataFrame(data=freqs, index=items, columns=['freq'])

        return df

    def item_freq_2(self, items, p_att='word', s_break='text'):
        """Calculates item frequencies."""

        query = formulate_cqp_query(items, p_att, s_att=None)
        df_node = self._df_node_from_query(query, s_break, context=0,
                                           match_strategy='standard')
        df = self.count_matches(df_node, p_att)
        # fill missing values
        missing = set(items) - set(df.index)
        df_missing = DataFrame(data=0, index=missing, columns=['freq'])
        df = df.append(df_missing)

        return df

    def count_matches(self, df_node, p_att="word", split=False):
        """counts strings or tokens in df_nodes.index"""

        # undump the dump
        self.subcorpus_from_df(df_node, name='tmp_matches')

        # tabulate matches
        match_strings = self.cqp.Exec(
            'tabulate tmp_matches match .. matchend %s;' % p_att
        ).split('\n')

        # switch back to full corpus
        self.deactivate_subcorpus()

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
