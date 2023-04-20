#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""dumps.py

definition of Dump and Dumps classes

"""
import logging

from pandas import DataFrame

from .collocates import Collocates

logger = logging.getLogger(__name__)


class Dumps:
    """ collection of dumps, i.e. query matches in different subcorpora """

    def __init__(self, corpus, s_dict, s_att='text_id'):
        """
        :param Corpus corpus: corpus to work on
        :param dict s_dict: dicitonary of {subcorpus_name: set of values for s_att}
        :param str s_att: s-attribute that is used for definition of subcorpora
        """

        self.corpus = corpus.copy()
        self.s_dict = s_dict
        self.s_att = s_att

        logger.info("creating subcorpora ...")
        df_spans = corpus.dump_from_s_att(s_att)
        dumps = dict()
        for i, s in enumerate(self.s_dict.keys()):
            logger.info(f"... subcorpus {i+1} of {len(s_dict)}")
            df_dump = df_spans.loc[df_spans[s_att].isin(s_dict[s])]
            dumps[s] = corpus.subcorpus(None, df_dump)

        self.dumps = dumps

    def keywords(self, p_query=['lemma'], order='log_likelihood',
                 cut_off=100, ams=None, min_freq=2, flags=None,
                 subset=None, marginals='corpus', show_negative=False):
        """
        :return: dictionary of {subcorpus_name: table}
        :rtype: dict
        """
        # TODO: multiproc

        subset = list(self.s_dict.keys()) if subset is None else subset

        logger.info("computing keyword tables ...")
        tables = dict()
        for i, s in enumerate(subset):
            logger.info(f"... table {i+1} of {len(subset)}")
            dump = self.dumps[s]
            tables[s] = dump.keywords(
                p_query=p_query, order=order, cut_off=cut_off,
                ams=ams, min_freq=min_freq, flags=flags, marginals=marginals,
                show_negative=show_negative
            )

        return tables

    def collocates(self, cqp_query, window=5, p_query=['lemma'],
                   order='log_likelihood', cut_off=100, ams=None,
                   min_freq=2, flags=None, subset=None,
                   context_break=None, marginals='corpus',
                   show_negative=False):
        """
        reference:
        .. local: window freq. compared to marginals of subcorpus (excl. nodes)
        .. global: window freq. compared to marginals in whole corpus (excl. nodes)
        .. DataFrame:

        :param str reference: 'local' | 'global' | DataFrame
        :return: dictionary of {subcorpus_name: table}
        :rtype: dict
        """
        # TODO: multiproc

        subset = list(self.s_dict.keys()) if subset is None else subset
        context_break = self.s_att if context_break is None else context_break

        # run query once and extend dump
        dump_glob = self.corpus.query_cqp(
            cqp_query,
            context=window,
            context_break=context_break
        ).df
        df_glob = self.corpus.dump2satt(dump_glob, self.s_att)

        logger.info("computing collocate tables ...")
        tables = dict()
        for i, s in enumerate(subset):
            logger.info(f"... table {i+1} of {len(subset)}")

            # determine reference frequencies
            if isinstance(marginals, str):
                if marginals == 'local':
                    # get local marginals
                    # THIS is expensive, use subcorpus.marginals instead!
                    marginals = self.corpus.counts.dump(
                        self.dumps[s].df, split=True, p_atts=p_query
                    )
                    # marginals = self.corpus.marginals(p_atts=p_query)
                elif marginals == 'corpus':
                    pass
                else:
                    raise NotImplementedError()
            elif not isinstance(marginals, DataFrame):
                raise NotImplementedError()

            # create collocates table
            df_loc = df_glob.loc[
                df_glob[self.s_att].isin(self.s_dict[s])
            ]
            collocates = Collocates(
                self.corpus, df_loc, p_query=p_query, mws=window
            )
            tables[s] = collocates.show(
                window=window, order=order, cut_off=cut_off,
                ams=ams, min_freq=min_freq, flags=flags, marginals=marginals
            )

        return tables
