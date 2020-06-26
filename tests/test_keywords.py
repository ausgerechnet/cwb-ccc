from ccc import Corpus
from pandas import read_csv
import pytest


@pytest.mark.meta
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
    lines = keywords.show(order='log_ratio')
    assert('@pama1969' in lines.index)


@pytest.mark.query
def test_keywords_from_query(brexit_corpus):

    name = 'test_keywords'

    # create subcorpus
    corpus = Corpus(corpus_name=brexit_corpus['corpus_name'])
    corpus.subcorpus_from_query(brexit_corpus['query'] + 'expand to tweet',
                                name=name,
                                return_dump=False)

    # keywords
    keywords = corpus.keywords(name=name)
    lines = keywords.show(order='log_ratio')
    assert('test' in lines.index)


@pytest.mark.query
def test_keywords_from_dump(sz_corpus):

    name = 'test_keywords'

    # get some regions
    corpus = Corpus(corpus_name=sz_corpus['corpus_name'])
    df_1 = corpus.subcorpus_from_query(sz_corpus['query'] + 'expand to text',
                                       name=name,
                                       return_dump=True)

    # will show keywords for df_1
    keywords = corpus.keywords(df_dump=df_1)
    line_1 = keywords.show(order='log_likelihood', min_freq=10)
    assert('CDU' in line_1.index)


@pytest.mark.query
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
