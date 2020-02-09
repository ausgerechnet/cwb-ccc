from ccc import Corpus
from pandas import read_csv, to_numeric
import pytest

registry_path = "/home/ausgerechnet/corpora/cwb/registry/"
lib_path = "/home/ausgerechnet/projects/spheroscope/app/instance-stable/lib/"
corpus_name = "BREXIT_V20190522"
s_meta = "tweet_id"
meta_path = "/home/ausgerechnet/corpora/cwb/upload/brexit/rant/brexit_v20190522.tsv.gz"


@pytest.mark.skip
def test_create_meta():
    meta = read_csv(meta_path)
    df_dup = meta.loc[meta['duplicate_status'] == "1"][['match', 'matchend']]
    df_dup.reset_index(inplace=True)
    df_dup.set_index(['match', 'matchend'], inplace=True, drop=False)
    df_dup.columns = ['s_id', 'region_start', 'region_end']
    df_dup.head(10000).to_csv('tests/gold/test_dump.tsv', sep="\t")


def test_keywords():

    # get some regions
    df_dup = read_csv('tests/gold/test_dump.tsv', sep="\t", dtype=str)
    cols = ['match', 'matchend', 'region_start', 'region_end']
    df_dup[cols] = df_dup[cols].apply(to_numeric, downcast='integer')
    df_dup = df_dup.set_index(['match', 'matchend'])
    df_1 = df_dup.head(5000)
    df_2 = df_dup.tail(5000)
    # init corpus
    corpus = Corpus(corpus_name=corpus_name,
                    registry_path=registry_path, lib_path=lib_path,
                    s_meta=s_meta)

    # will show keywords for df_1
    corpus.define_subcorpus(df_node=df_1, name='test_keywords', activate=True)
    keywords = corpus.keywords()
    line_1 = keywords.show(order='log_likelihood')

    # will show collocates for query_1
    corpus.define_subcorpus(df_node=df_2, name='test_keywords', activate=True)
    line_2 = keywords.show(order='log_likelihood')

    # will show collocates for query_2
    keywords = corpus.keywords()
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
    keywords = corpus.keywords()
    line_1 = keywords.show(order='log_likelihood')

    # will show keywords for ids_1
    corpus.subcorpus_from_ids(ids_2)
    line_2 = keywords.show(order='log_likelihood')

    # will show keywords for ids_2
    keywords = corpus.keywords()
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
    keywords = corpus.collocates()
    line_1 = keywords.show(order='log_likelihood')

    corpus.define_subcorpus(df_node=df_2, name='test_keywords', activate=True)
    line_2 = keywords.show(order='log_likelihood')

    keywords = corpus.collocates()
    line_3 = keywords.show(order='log_likelihood')

    assert(line_1.empty and line_2.empty and line_3.empty)
