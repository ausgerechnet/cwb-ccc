from ccc import Corpus
from ccc.keywords import Keywords
from pandas import read_csv
import pytest

from .conftest import local


@pytest.mark.skipif(not local, reason='works on my machine')
@pytest.mark.brexit
@pytest.mark.meta
def test_keywords_from_meta(brexit):

    # get relevant ids
    meta = read_csv(brexit['meta_path'], dtype=str, sep="\t")
    ids_replies = set(meta.loc[meta['in_reply_status'] == "1"]['id'])

    # create subcorpus
    corpus = Corpus(corpus_name=brexit['corpus_name'])
    dump = corpus.dump_from_s_att('tweet_id', ids_replies)

    # keywords
    keywords = Keywords(corpus, dump.df, p_query='lemma')
    lines = keywords.show(order='log_ratio')
    assert('@pama1969' in lines.index)


@pytest.mark.skipif(not local, reason='works on my machine')
@pytest.mark.brexit
@pytest.mark.query
def test_keywords_from_query(brexit):

    name = 'test_keywords'

    # create subcorpus
    corpus = Corpus(corpus_name=brexit['corpus_name'])
    dump = corpus.query(brexit['query'] + 'expand to tweet',
                        name=name)

    # keywords
    keywords = Keywords(corpus, dump.df, p_query="lemma")
    lines = keywords.show(order='log_ratio')
    assert('test' in lines.index)


@pytest.mark.query
def test_keywords_from_dump(germaparl):

    name = 'test_keywords'

    # get some regions
    corpus = Corpus(corpus_name=germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    df_1 = corpus.dump_from_query('"und" expand to s',
                                  name=name)

    # will show keywords for df_1
    keywords = Keywords(corpus, df_dump=df_1, p_query="lemma")
    line_1 = keywords.show(order='log_likelihood', min_freq=10)
    assert('CDU' in line_1.index)


@pytest.mark.switch
def test_keywords_switch(germaparl):

    name_all = 'test_all'

    # get some regions
    corpus = Corpus(corpus_name=germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    df_all = corpus.query(
        '"und" expand to s',
        name=name_all
    ).df
    df_head = df_all.head(500)
    df_tail = df_all.tail(500)

    # will show keywords for head
    keywords = Keywords(corpus, df_dump=df_head, p_query="lemma")
    line_head_name = keywords.show(order='log_likelihood')

    # will show keywords for head
    keywords = Keywords(corpus, df_dump=df_head, p_query="lemma")
    line_head_df = keywords.show(order='log_likelihood')

    assert(line_head_df.equals(line_head_name))

    # will show keywords for tail
    keywords = Keywords(corpus, df_dump=df_tail, p_query="lemma")
    line_tail_name = keywords.show(order='log_likelihood')

    # will show keywords for tail
    keywords = Keywords(corpus, df_dump=df_tail, p_query="lemma")
    line_tail_df = keywords.show(order='log_likelihood')

    assert(line_tail_df.equals(line_tail_name))

    assert(not line_tail_df.equals(line_head_df))
