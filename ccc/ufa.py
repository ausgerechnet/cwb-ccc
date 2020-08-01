from .collocates import Collocates
# logging
import logging
logger = logging.getLogger(__name__)


class UFA:

    def __init__(self, corpus, ids, context_break='text_id'):
        """
        :param Corpus corpus: corpus to work on
        :param dict ids: dicitonary of {subcorpus_name: set of values for context_break}
        :param str context_break: s-attribute that is used for definition of regions
        """

        self.corpus = corpus.copy()
        self.ids = ids
        self.context_break = context_break

        logger.info("creating subcorpora ...")
        subcorpora = dict()
        i = 0
        for s in self.ids.keys():
            i += 1
            logger.info("... subcorpus %d of %d" % (i, len(self.ids)))
            subcorpora[s] = corpus.dump_from_s_att(
                self.context_break, self.ids[s]
            )

        self.subcorpora = subcorpora

    def keywords(self, p_query='lemma', order='f', cut_off=100,
                 ams=None, min_freq=2, frequencies=True, flags=None,
                 subset=None):
        """
        :return: dictionary of {subcorpus_name: table}
        :rtype: dict
        """
        if subset is None:
            subset = list(self.ids.keys())

        logger.info("computing keyword tables ...")
        tables = dict()
        i = 0
        for s in subset:
            i += 1
            logger.info("... table %d of %d" % (i, len(subset)))
            dump = self.subcorpora[s]
            tables[s] = dump.keywords(
                p_query=p_query, order=order, cut_off=cut_off,
                ams=ams, min_freq=min_freq,
                frequencies=frequencies, flags=flags
            )

        return tables

    def collocates(self, cqp_query, window=5, p_query='lemma',
                   order='f', cut_off=100, ams=None, min_freq=2,
                   frequencies=True, flags=None, subset=None):
        """
        :return: dictionary of {subcorpus_name: table}
        :rtype: dict
        """
        if subset is None:
            subset = list(self.ids.keys())

        tables = dict()

        # run query and de-construct dump
        dump_glob = self.corpus.query(
            cqp_query,
            context=window,
            context_break=self.context_break
        )
        df_glob = dump_glob.df.join(
            self.corpus.get_s_annotations(
                dump_glob.df, [self.context_break]
            )
        )

        logger.info("computing collocate tables ...")
        tables = dict()
        i = 0
        for s in subset:
            i += 1
            logger.info("... table %d of %d" % (i, len(subset)))
            dump = self.subcorpora[s]
            # get local marginals (f2)
            marginals_loc = self.corpus.counts.dump(
                dump.df, split=True, p_atts=[p_query]
            )
            # create collocates table
            df_loc = df_glob.loc[
                df_glob[self.context_break].isin(self.ids[s])
            ]
            collocates = Collocates(self.corpus, df_loc, p_query=p_query)
            tables[s] = collocates.show(
                window=window, order=order, cut_off=cut_off,
                ams=ams, min_freq=min_freq, frequencies=frequencies,
                flags=flags, marginals=marginals_loc
            )

        return tables
