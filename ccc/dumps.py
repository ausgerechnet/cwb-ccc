#! /usr/bin/env python
# -*- coding: utf-8 -*-

# part of module
from .concordances import Concordance
from .collocates import Collocates
from .keywords import Keywords
from .utils import merge_intervals
# requirements
from pandas import DataFrame
# logging
import logging
logger = logging.getLogger(__name__)


class Dump:
    """ result of a query """

    def __init__(self, corpus, df_dump, name_cache, name_cqp):

        # parameters = {
        #     'query': query,
        #     'context_left': context_left,
        #     'context_right': context_right,
        #     'context_break': context_break,
        #     'corrections': corrections,
        #     'match_strategy': match_strategy
        # }
        # self.parameters = parameters

        # TODO: check context against collocates.mws

        self.df = df_dump
        self.corpus = corpus
        self.name_cache = name_cache
        self.name_cqp = name_cqp
        self.size = len(self.df)

        self._breakdown = None
        self._matches = None
        self._context = None

    def __str__(self):
        desc = ['Object "Dump"']
        if self.corpus.subcorpus:
            crpssbcrps = self.corpus.corpus_name + ":" + self.corpus.subcorpus
        else:
            crpssbcrps = self.corpus.corpus_name
        desc.append('- corpus "%s" (%d tokens)' % (
            crpssbcrps, self.corpus.corpus_size
        ))
        desc.append('- %d matches' % self.size)
        if self.name_cache is not None:
            desc.append('- name in cache: "%s"' % self.name_cache)
        if self.name_cqp is not None:
            desc.append('- name in cqp  : "%s"' % self.name_cqp)
        return "\n".join(desc)

    def breakdown(self, max_matches=None):

        if self._breakdown is None:
            if max_matches is not None and self.size > max_matches:
                logger.warning(
                    'no frequency breakdown (%d matches)' % self.size
                )
                breakdown = DataFrame(
                    index=['NODE'],
                    data=[self.size],
                    columns=['freq']
                )
                breakdown.index.name = 'word'
                return breakdown
            else:
                logger.info('creating frequency breakdown')
                breakdown = self.corpus.counts.dump(
                    df_dump=self.df,
                    start='match', end='matchend',
                    p_atts=['word']
                )
                self._breakdown = breakdown

        return self._breakdown

    def matches(self):
        """
        :return: cpos of (match .. matchend) regions
        :rtype: set
        """
        if self._matches is None:
            f1 = set()
            for match, matchend in self.df.index:
                f1.update(range(match, matchend + 1))
            self._matches = f1

        return self._matches

    def context(self):
        """
        :return: cpos of (context .. contextend) regions including matches
        :rtype: DataFrame
        """
        if self._context is None:
            self._context = DataFrame.from_records(merge_intervals(
                self.df[['context', 'contextend']].values.tolist()
            ), columns=['context', 'contextend'])

        return self._context

    def concordance(self, matches=None, p_show=['word'], s_show=[],
                    p_text=None, p_slots=None, regions=[], order='first',
                    cut_off=100, form='raw'):

        conc = Concordance(
            self.corpus.copy(),
            df_dump=self.df
        )

        return conc.lines(
            matches=matches,
            p_show=p_show,
            s_show=s_show,
            p_text=p_text,
            p_slots=p_slots,
            regions=regions,
            order=order,
            cut_off=cut_off,
            form=form
        )

    def collocates(self, p_query='lemma', mws=10, window=5, order='f',
                   cut_off=100, ams=None, min_freq=2, frequencies=True,
                   flags=None):

        coll = Collocates(
            self.corpus.copy(),
            df_dump=self.df,
            p_query=p_query,
            mws=mws
        )

        return coll.show(
            window=window,
            order=order,
            cut_off=cut_off,
            ams=ams,
            min_freq=min_freq,
            frequencies=frequencies,
            flags=flags
        )

    def keywords(self, p_query='lemma', order='f', cut_off=100,
                 ams=None, min_freq=2, frequencies=True, flags=None):

        kw = Keywords(
            self.corpus.copy(),
            self.name_cqp,
            self.df,
            p_query
        )

        return kw.show(
            order=order,
            cut_off=cut_off,
            ams=ams,
            min_freq=min_freq,
            frequencies=frequencies,
            flags=flags
        )
