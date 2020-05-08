from ccc import Corpus
import pytest
import pandas as pd


# registry path
registry_path = "/home/ausgerechnet/corpora/cwb/registry/"
corpus_name = "SZ_2009_14"


def test_concordance_new():
    corpus = Corpus(corpus_name, registry_path, s_meta='text_id')
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query)
    concordance = corpus.concordance(result)
    lines = concordance.lines(p_show=[], order='random', cut_off=100)
    assert(len(concordance.breakdown) > 0)
    assert(type(concordance.meta) == pd.DataFrame)
    assert(len(lines) == 100)


@pytest.mark.concordance_simple
def test_query_default():
    corpus = Corpus(corpus_name, registry_path, s_meta='text_id', data_path=None)
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query, s_break='s')
    concordance = corpus.concordance(result)
    lines = concordance.lines(p_show=[], order='random', cut_off=100)
    assert(len(concordance.breakdown) > 0)
    assert(type(concordance.meta) == pd.DataFrame)
    assert(len(lines) == 100)


@pytest.mark.concordance
@pytest.mark.concordance_anchors
def test_anchor_query_default():
    corpus = Corpus(corpus_name, registry_path)
    query = (
        '@0[lemma="Angela"]? @1[lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query, s_break='s')
    concordance = corpus.concordance(result)
    lines = concordance.lines()
    for df in lines.values():
        assert(all(x in set(df['anchor']) for x in [1, 2]))


@pytest.mark.skip
@pytest.mark.concordance_many
def test_query_many():
    corpus = Corpus(corpus_name, registry_path, s_meta='text_id', cache_path=None)
    query = "[lemma='und']"
    result = corpus.query(query, s_break='s')
    concordance = corpus.concordance(result)
    lines = concordance.lines(p_show=['lemma', 'pos'], order='random', cut_off=100)
    assert(concordance.breakdown is None)
    assert(type(concordance.meta) == pd.DataFrame)
    assert(len(lines) == 100)


@pytest.mark.switch_corpora
def test_concordance_persistence():
    corpus = Corpus(corpus_name, registry_path)
    query_1 = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    query_2 = (
        '[lemma="Horst"]? [lemma="Seehofer"]'
    )

    # will show results for query_1
    result = corpus.query(query_1, s_break='s')
    concordance = corpus.concordance(result)
    line_1 = concordance.lines(cut_off=1)
    df_1 = line_1[list(line_1.keys())[0]]
    breakdown_1 = concordance.breakdown

    # will show results for query_1
    result = corpus.query(query_2, s_break='s')
    line_2 = concordance.lines(cut_off=1)
    df_2 = line_2[list(line_2.keys())[0]]
    breakdown_2 = concordance.breakdown

    # will show results for query_2
    concordance = corpus.concordance(result)
    line_3 = concordance.lines(cut_off=1)
    df_3 = line_3[list(line_3.keys())[0]]
    breakdown_3 = concordance.breakdown

    assert(df_1.equals(df_2))
    assert(breakdown_1.equals(breakdown_2))
    assert(not df_2.equals(df_3))
    assert(not breakdown_2.equals(breakdown_3))
