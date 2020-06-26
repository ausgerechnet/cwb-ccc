from ccc import Corpus
from pandas import read_csv, to_numeric
import pytest


def test_keywords_from_meta(brexit_corpus):

    name = 'test_keywords'

    # get relevant ids
    meta = read_csv(brexit_corpus['meta_path'], dtype=str, sep="\t")
    ids_replies = set(meta.loc[meta['in_reply_status'] == "1"]['id'])

    # create subcorpus
    corpus = Corpus(corpus_name=brexit_corpus['corpus_name'])
    corpus.subcorpus_from_s_att('tweet_id', ids_replies, name=name)

    # keywords
    keywords = corpus.keywords(name=name)
    print(keywords.show(order='log_ratio'))


def test_keywords_from_query(brexit_corpus):

    name = 'test_keywords'

    # create subcorpus
    corpus = Corpus(corpus_name=brexit_corpus['corpus_name'])
    corpus.subcorpus_from_query(brexit_corpus['query'] + 'expand to tweet',
                                name=name,
                                return_dump=False)

    # keywords
    keywords = corpus.keywords(name=name)
    print(keywords.show(order='log_ratio'))


def test_keywords_from_dump(sz_corpus):

    name = 'test_keywords'

    # get some regions
    corpus = Corpus(corpus_name=sz_corpus['corpus_name'])
    df_1 = corpus.subcorpus_from_query(sz_corpus['query'] + 'expand to text',
                                       name=name,
                                       return_dump=True)

    # will show keywords for df_1
    # corpus.subcorpus_from_dump(df_dump=df_1, name=name)
    keywords = corpus.keywords(df_dump=df_1)
    line_1 = keywords.show(order='log_likelihood', min_freq=10)
    print(line_1)


@pytest.mark.now
def test_keywords_switch(sz_corpus):

    name = 'test_keywords'

    # get some regions
    corpus = Corpus(corpus_name=sz_corpus['corpus_name'])
    df = corpus.subcorpus_from_query(sz_corpus['query'] + 'expand to text',
                                     name=name,
                                     return_dump=True)
    df_1 = df.head(5000)
    df_2 = df.tail(5000)

    # will show keywords for df_1
    corpus.subcorpus_from_dump(df_dump=df_1, name=name)
    keywords = corpus.keywords(name=name)
    line_1 = keywords.show(order='log_likelihood')

    # will show collocates for query_1
    corpus.subcorpus_from_dump(df_dump=df_2, name=name)
    line_2 = keywords.show(order='log_likelihood')

    # will show collocates for query_2
    keywords = corpus.keywords(name=name)
    line_3 = keywords.show(order='log_likelihood')

    assert(line_1.equals(line_2))
    assert(not line_2.equals(line_3))


@pytest.mark.keywords_from_ids
def test_keywords_ids():

    # get some ids
    df_dup = read_csv('tests/gold/test_dump.tsv', sep="\t", dtype=str)

    ids_1 = set(df_dup.head(5000)['s_id'])
    ids_2 = set(df_dup.tail(5000)['s_id'])

    # init corpus
    corpus = Corpus(corpus_name=corpus_name,
                    registry_path=registry_path, lib_path=lib_path,
                    s_meta=s_meta)

    # will show keywords for ids_1
    corpus.subcorpus_from_ids(ids_1)
    keywords = corpus.keywords('tmp_keywords')
    line_1 = keywords.show(order='log_likelihood')

    # will show keywords for ids_1
    corpus.subcorpus_from_ids(ids_2)
    line_2 = keywords.show(order='log_likelihood')

    # will show keywords for ids_2
    keywords = corpus.keywords('tmp_keywords')
    line_3 = keywords.show(order='log_likelihood')

    assert(line_1.equals(line_2))
    assert(not line_2.equals(line_3))


def test_collocates_error():

    # get some regions
    df_dup = read_csv('tests/gold/test_dump.tsv', sep="\t", index_col=[0, 1], dtype=str)
    df_dup = df_dup.apply(lambda x: to_numeric(x, downcast='integer') if x.name != 's_id' else x)
    df_1 = df_dup.head(5000)
    df_2 = df_dup.tail(5000)
    # init corpus
    corpus = Corpus(corpus_name=corpus_name,
                    registry_path=registry_path, lib_path=lib_path,
                    s_meta=s_meta)

    corpus.define_subcorpus(df_node=df_1, name='test_keywords', activate=True)
    keywords = corpus.collocates(corpus.subcorpus_info['df_node'])
    line_1 = keywords.show(order='log_likelihood')

    corpus.define_subcorpus(df_node=df_2, name='test_keywords', activate=True)
    line_2 = keywords.show(order='log_likelihood')

    keywords = corpus.collocates(corpus.subcorpus_info['df_node'])
    line_3 = keywords.show(order='log_likelihood')

    assert(line_1.empty and line_2.empty and line_3.empty)
