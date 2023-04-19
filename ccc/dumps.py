#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""dumps.py

definition of Dump and Dumps classes

"""
import logging

# part of module
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

    def keywords(self, p_query=['lemma'], order='log_likelihood', cut_off=100,
                 ams=None, min_freq=2, frequencies=True, flags=None,
                 subset=None):
        """
        :return: dictionary of {subcorpus_name: table}
        :rtype: dict
        """

        subset = list(self.s_dict.keys()) if subset is None else subset

        logger.info("computing keyword tables ...")
        # TODO: multiproc
        tables = dict()
        i = 0
        for s in subset:
            i += 1
            logger.info(f"... table {i} of {len(subset)}")
            dump = self.dumps[s]
            tables[s] = dump.keywords(
                p_query=p_query, order=order, cut_off=cut_off,
                ams=ams, min_freq=min_freq,
                frequencies=frequencies, flags=flags
            )

        return tables

    def collocates(self, cqp_query, window=5, p_query=['lemma'],
                   order='log_likelihood', cut_off=100, ams=None, min_freq=2,
                   frequencies=True, flags=None, subset=None, context_break=None,
                   reference='local'):
        """
        reference:
        .. local: window freq. compared to marginals of subcorpus (excl. nodes)
        .. global: window freq. compared to marginals in whole corpus (excl. nodes)
        .. DataFrame:

        :param str reference: 'local' | 'global' | DataFrame
        :return: dictionary of {subcorpus_name: table}
        :rtype: dict
        """

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
        # TODO: multiproc
        tables = dict()
        i = 0
        for s in subset:
            i += 1
            logger.info(f"... table {i} of {len(subset)}")

            # determine reference frequencies
            if isinstance(reference, str):
                if reference == 'local':
                    # get local marginals
                    marginals = self.corpus.counts.dump(
                        self.dumps[s].df, split=True, p_atts=p_query
                    )
                elif reference == 'global':
                    marginals = 'corpus'

            # create collocates table
            df_loc = df_glob.loc[
                df_glob[self.s_att].isin(self.s_dict[s])
            ]
            collocates = Collocates(
                self.corpus, df_loc, p_query=p_query, mws=window
            )
            tables[s] = collocates.show(
                window=window, order=order, cut_off=cut_off,
                ams=ams, min_freq=min_freq, frequencies=frequencies,
                flags=flags, marginals=marginals
            )

        return tables
