#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
from io import StringIO
from glob import glob
# part of module
from .counts import Counts
from .cqp import CQP
from .cache import Cache
# from .query import Query
# from .concordances import Concordance
# from .collocates import Collocates
# from .keywords import Keywords
# from .ufa import UFA
# requirements
from CWB.CL import Corpus as Crps
from pandas import DataFrame, read_csv
from pandas.errors import EmptyDataError
# logging
import logging
logger = logging.getLogger(__name__)


def start_cqp(cqp_bin, registry_path, data_path=None, corpus_name=None):
    cqp = CQP(
        bin=cqp_bin,
        options='-c -r ' + registry_path
    )
    if data_path is not None:
        cqp.Exec('set DataDirectory "%s"' % data_path)
    if corpus_name is not None:
        cqp.Exec(corpus_name)
    return cqp


class Corpora:
    """ interface to CWB-indexed corpora """

    def __init__(self,
                 cqp_bin='cqp',
                 registry_path='/usr/local/share/cwb/registry/'):

        self.registry_path = registry_path
        self.cqp_bin = cqp_bin

    def start_cqp(self):
        return start_cqp(self.cqp_bin, self.registry_path)

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

        attributes:
        .registry_path
        .corpus_name
        .data
        .cache
        .attributes
        .attributes_available
        .corpus_size
        .lib_path

        .subcorpus [None]
        .cqp
        .counts

        :param str corpus_name: name of corpus in CWB registry
        :param str lib_path: path/to/macros/and/wordlists
        :param str cqp_bin: cqp binary
        :param str registry_path: path/to/cwb/registry/
        :param str data_path: path/to/store/cwb/data/and/cache

        """

        # process data path
        if data_path is not None:
            self.data = os.path.join(data_path, corpus_name)
            if not os.path.isdir(self.data):
                os.makedirs(self.data)
            cache_path = os.path.join(self.data, "CACHE")
        else:
            self.data = None
            cache_path = None

        # init cache
        self.cache = Cache(
            cache_path
        )

        # set registry path and cqp_bin
        self.registry_path = registry_path
        self.cqp_bin = cqp_bin

        # init (sub-)corpus information
        self.corpus_name = corpus_name
        self.subcorpus = None

        # active corpus in CQP
        self.cqp = start_cqp(
            self.cqp_bin, self.registry_path, self.data, self.corpus_name
        )

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

        # init counting module
        self.counts = Counts(self.corpus_name, self.registry_path)

    def read_lib(self, lib_path):
        """Reads macros and worldists. Folder has to contain two sub-folders
        ("macros" and "wordlists").

        :param str lib_path: path/to/macros/and/wordlists

        """

        logger.info("enter read_lib")

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

    ################
    # s-attributes #
    ################
    def get_s_extents(self, s_att):
        """Maps s_att to corresponding extents, returns DataFrame.

        :param str s_att: s-attribute to get extents for

        :return: df indexed by match, matchend; CWBID, annotation
        :rtype: DataFrame

        """

        logger.info("enter get_s_extents")

        # retrieve from cache
        parameters = ['s_extents', s_att]
        df = self.cache.get(parameters)
        if df is not None:
            logger.info('using cached version of extents of "%s"' % s_att)
            return df

        # compute
        logger.info('computing extents of "%s"' % s_att)
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

    def get_s_annotation(self, df, s_att):
        """Retrieves CWBIDs and annotations of s-attribute of match.

        :param DataFrame df_dump: DataFrame indexed by (match, matchend)
        :param str s_att: s-attribute to retrieve

        """
        # TODO remove double entries (tweet_id_CWBID = tweet_CWBID etc.)

        logger.info("cwb.get_s_annotation")

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

        return df

    def get_s_annotations(self, df_dump, s_atts):
        """Gets all annotations of all s-att in s_atts at match positions.

        :param DataFrame df_dump: DataFrame indexed by (match, matchend)
        :param list s_atts: s-attributes to show (id + annotation)

        :return: s_annotations
        :rtype: DataFrame

        """
        df = df_dump.reset_index()
        df = df[['match', 'matchend']]
        for s in s_atts:
            df = self.get_s_annotation(df, s)
        df = df.set_index(['match', 'matchend'])
        return df

    ################
    # p-attributes #
    ################
    def cpos2patts(self, cpos, p_atts=['word'], ignore_missing=True):
        """Retrieves p-attributes of corpus position.

        :param int cpos: corpus position to fill
        :param list p_atts: p-attribute(s) to fill position with
        :param bool ignore_missing: whether to return -1 for out-of-bounds

        :return: p_att(s) to retrieve
        :rtype: tuple

        """

        if ignore_missing and cpos == -1:
            token = [None] * len(p_atts)
        else:
            token = [
                self.attributes.attribute(p_att, 'p')[cpos] for p_att in p_atts
            ]

        return tuple(token)

    ##############
    # subcorpora #
    ##############
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

    # # register classes
    # def query(self):
    #     return Query(
    #         self
    #     )

    # def concordance(self, df_dump, max_matches=100000):
    #     return Concordance(
    #         self,
    #         df_dump=df_dump,
    #         max_matches=max_matches
    #     )

    # def collocates(self, df_dump, p_query='lemma'):
    #     return Collocates(
    #         self,
    #         df_dump=df_dump,
    #         p_query=p_query
    #     )

    # def keywords(self, name=None, df_dump=None, p_query='lemma'):
    #     return Keywords(
    #         self,
    #         name=name,
    #         df_dump=df_dump,
    #         p_query=p_query
    #     )

    # def ufa(self, splits, s_query, p_query='lemma'):
    #     return UFA(
    #         self,
    #         splits=splits,
    #         p_query=p_query,
    #         s_query=s_query
    #     )
