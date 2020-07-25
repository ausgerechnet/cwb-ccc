#! /usr/bin/env python
# -*- coding: utf-8 -*-

# part of module
from .utils import (
    preprocess_query, merge_s_atts,
    chunk_anchors, correct_anchors
)
# requirements
from pandas import DataFrame, to_numeric
# logging
import logging
logger = logging.getLogger(__name__)


# class QueryResult:
#     """ result of a query """

#     def __init__(self, df_dump, parameters, corpus, subcorpus,
#                  name_cache=None):

#         # parameters = {
#         #     'query': query,
#         #     'context_left': context_left,
#         #     'context_right': context_right,
#         #     's_context': s_context,
#         #     's_meta': s_meta,
#         #     'match_strategy': match_strategy
#         # }

#         self.dump = df_dump
#         self.parameters = parameters
#         self.corpus = corpus
#         self.subcorpus = subcorpus
#         self.name_cache = name_cache
#         self.size = len(self.dump)

#     def __str__(self):
#         desc = 'query result on corpus "%s" ("%s") with %d matches' % (
#             self.corpus, self.subcorpus, self.size
#         )
#         if self.name_cache is not None:
#             desc += '\nresult can be accessed via cache: ""'
#         return desc


class Query(Corpus):

    def __init__(self, corpus_name, subcorpus):
        # cqp / start_cqp
        # subcorpus_from_query
        # activate_subcorpus
        # attributes
        # cache
        pass

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
              match_strategy='standard', name='mnemosyne', return_name=False):
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
        :param str s_context: s-attribute to confine context
        :param dict corrections: corrections to apply to anchors {name: offset}
        :param str match_strategy: CQP matching strategy
        :param str name: name for resulting subcorpus

        :return: df_dump
        :rtype: DataFrame

        """

        # preprocess input
        query, s_query, anchors = preprocess_query(query)
        s_query, s_context, s_meta = merge_s_atts(s_query, s_context, None)  # ToDo
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

        if return_name:
            return df_dump, name_cache
        else:
            return df_dump
