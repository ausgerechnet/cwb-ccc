from ccc import Corpus
import pytest


@pytest.mark.breakdown
def test_concordance_breakdown(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query)
    concordance = corpus.concordance(result)
    print(concordance.breakdown)


@pytest.mark.skip
@pytest.mark.breakdown
@pytest.mark.many
def test_concordance_breakdown_many(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '[lemma="oder"]'
    )
    result = corpus.query(query)
    concordance = corpus.concordance(result)
    print(concordance.breakdown)


@pytest.mark.skip
@pytest.mark.concordance_many
def test_query_many(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = '[lemma="oder"]'
    result = corpus.query(query, s_context='s')
    concordance = corpus.concordance(result)
    lines = concordance.lines(p_show=['lemma', 'pos'], order='random', cut_off=100)
    assert(len(lines) == 100)


@pytest.mark.concordance_simple
def test_concordance_simple(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query)
    concordance = corpus.concordance(result)
    lines = concordance.lines(order='random', cut_off=100)
    assert(len(concordance.breakdown) > 0)
    assert(len(lines) == 100)


@pytest.mark.concordance_simple
def test_concordance_simple_p_atts(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query)
    concordance = corpus.concordance(result)
    lines = concordance.lines(
        p_show=['pos', 'lemma'],
        order='random',
        cut_off=100
    )
    # print(lines[list(lines.keys())[0]])
    assert(len(concordance.breakdown) > 0)
    assert(len(lines) == 100)


@pytest.mark.concordance_anchors
def test_concordance_anchors_simple(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '@0[lemma="Angela"]? @1[lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query, s_context='s')
    concordance = corpus.concordance(result)
    lines = concordance.lines()
    assert(len(concordance.breakdown) > 0)
    assert(len(lines) == 100)
    # print(lines[list(lines.keys())[0]])


@pytest.mark.concordance_anchors
def test_concordance_anchors(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '@9[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query, s_context='s')
    concordance = corpus.concordance(result)
    lines = concordance.lines(order='random', cut_off=100)
    # print(lines[list(lines.keys())[0]])
    assert(len(concordance.breakdown) > 0)
    assert(len(lines) == 100)


@pytest.mark.switch_queries
def test_concordance_persistence(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query_1 = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    query_2 = (
        '[lemma="Horst"]? [lemma="Seehofer"]'
    )

    # will show results for query_1
    result = corpus.query(query_1, s_context='s')
    concordance = corpus.concordance(result)
    line_1 = concordance.lines(cut_off=1)
    df_1 = line_1[list(line_1.keys())[0]]
    breakdown_1 = concordance.breakdown

    # will show results for query_1
    result = corpus.query(query_2, s_context='s')
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
    print(corpus.show_subcorpora())


@pytest.mark.meta
def test_concordance_meta(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'], data_path=None)
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query, s_meta=['text_id', 'text_rubrik'])
    concordance = corpus.concordance(result)
    assert('text_rubrik' in concordance.meta.columns)
