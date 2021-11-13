#! /usr/bin/env python
# -*- coding: utf-8 -*-

# part of module
from .concordances import Concordance
from .collocates import Collocates
from .keywords import Keywords
from .utils import merge_intervals, correct_anchors
# requirements
from pandas import DataFrame
# logging
import logging
logger = logging.getLogger(__name__)


class Dump:
    """ result of a query """

    def __init__(self, corpus, df_dump, name_cqp):

        self.df = df_dump
        self.corpus = corpus
        self.name_cqp = name_cqp
        self.size = len(self.df)

        self._breakdown = None
        self._matches = None
        self._context = None

    def __str__(self):

        desc = ['a ccc.Dump with %d matches' % self.size]
        if self.corpus.subcorpus:
            crpssbcrps = self.corpus.corpus_name + ":" + self.corpus.subcorpus
        else:
            crpssbcrps = self.corpus.corpus_name
        desc.append('- corpus "%s" (%d tokens in whole corpus)' % (
            crpssbcrps, self.corpus.corpus_size
        ))
        if self.name_cqp is not None:
            desc.append('- name in cqp: "%s"' % self.name_cqp)
        desc.append('- columns: %s' % str(list(self.df.columns)))
        return "\n".join(desc)

    def set_context(self, context=None, context_break=None,
                    context_left=None, context_right=None):
        """Set context in the dump.

        """
        # pre-process context
        if context_left is None:
            context_left = context
        if context_right is None:
            context_right = context

        # set context
        self.df = self.corpus.dump2context(
            self.df, context_left, context_right, context_break
        )

    def correct_anchors(self, corrections):
        """Correct anchors by integer offsets.

        """
        self.df = correct_anchors(self.df, corrections)

    def breakdown(self, p_atts=['word'], max_matches=None):
        """Frequency breakdown of match..matchend.

        """

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
                breakdown.index.name = 'item'
                return breakdown
            else:
                logger.info('creating frequency breakdown')
                breakdown = self.corpus.counts.dump(
                    df_dump=self.df,
                    start='match', end='matchend',
                    p_atts=p_atts, strategy=1
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

    def concordance(self, form='simple', p_show=['word'], s_show=[],
                    order='first', cut_off=100, matches=None, slots=None):

        conc = Concordance(
            self.corpus.copy(),
            df_dump=self.df
        )

        return conc.lines(
            form=form,
            p_show=p_show,
            s_show=s_show,
            order=order,
            cut_off=cut_off,
            matches=matches,
            slots=slots
        )

    def collocates(self, p_query=['lemma'], mws=20, window=5, order='O11',
                   cut_off=100, ams=None, min_freq=2,
                   frequencies=True, flags=None, marginals='corpus'):

        mws = max(mws, window)

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
            flags=flags,
            marginals=marginals
        )

    def keywords(self, p_query=['lemma'], order='O11', cut_off=100,
                 ams=None, min_freq=2, frequencies=True, flags=None):

        kw = Keywords(
            self.corpus.copy(),
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
            logger.info("... subcorpus %d of %d" % (i + 1, len(s_dict)))
            df_dump = df_spans.loc[df_spans[s_att].isin(s_dict[s])]
            dumps[s] = Dump(corpus.copy(), df_dump, name_cqp=None)

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
            logger.info("... table %d of %d" % (i, len(subset)))
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
        dump_glob = self.corpus.query(
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
            logger.info("... table %d of %d" % (i, len(subset)))

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
