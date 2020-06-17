from ccc import Corpus
import pandas as pd
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

    print(corpus.counts.matches(corpus.cqp, "CACHE_625721eb12"))


@pytest.mark.meta
def test_concordance_meta(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'], data_path=None)
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query)
    concordance = corpus.concordance(result)
    concordance.lines(s_meta=['text_id', 'p_type'])


@pytest.mark.line
def test_concordance_line(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query)
    concordance = corpus.concordance(result)
    assert(len(concordance.breakdown) > 0)
    for index, columns in concordance.df_dump.iterrows():
        break
    assert(
        type(
            concordance.text_line(index, columns, p_show=['word', 'pos'])
        ) == pd.DataFrame
    )


@pytest.mark.now
@pytest.mark.lines
def test_concordance_lines(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '@0[lemma="Angela"]? @1[lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"] "und" @3[pos="NE"]? @4[pos="NE"]'
    )
    result = corpus.query(query, s_context='s', match_strategy='longest')
    concordance = corpus.concordance(result)
    assert(len(concordance.breakdown) > 0)
    # lines = concordance.lines()
    # # print(lines)
    # lines = concordance.lines(form='simple')
    # # print(lines)
    # lines = concordance.lines(form='kwic')
    # # print(lines)
    # lines = concordance.lines(form='kwic', s_show=['text_id'])
    # # print(lines)
    # lines = concordance.lines(form='dataframes', s_show=['text_id'])
    # print(lines)
    lines = concordance.lines(form='extended',
                              p_show=['word', 'lemma'],
                              s_show=['text_id'],
                              regions=[(3, 4)],
                              p_text='word',
                              p_slots='lemma',
                              cut_off=None)
    print(lines)
    print(lines.keys())
    print(lines['3_4_lemma'].value_counts())
    # assert(len(lines) == 100)
    # one_match = list(lines.keys())[0]
    # assert(type(lines[one_match]) == pd.DataFrame)


@pytest.mark.lines
def test_concordance_many(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '[lemma="oder"]'
    )
    result = corpus.query(query)
    concordance = corpus.concordance(result)
    assert(len(concordance.breakdown) > 0)
    lines = concordance.lines()
    assert(len(lines) == 100)
    one_match = list(lines.keys())[0]
    assert(type(lines[one_match]) == pd.DataFrame)


@pytest.mark.lines
def test_concordance_p_atts(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query, s_context='s')
    concordance = corpus.concordance(result)
    lines = concordance.lines(p_show=['lemma', 'pos'])
    one_match = list(lines.keys())[0]
    assert('pos' in lines[one_match].columns)
    assert(len(lines) == 100)


@pytest.mark.lines
def test_concordance_anchors(sz_corpus):
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
    # one_match = list(lines.keys())[0]
    # print(lines[one_match])


@pytest.mark.lines
def test_concordance_anchors_weird(sz_corpus):
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
    # one_match = list(lines.keys())[0]
    # print(lines[one_match])


@pytest.mark.format_lines
def test_concordance_form_simple(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '@9[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query, s_context='s')
    concordance = corpus.concordance(result)
    lines = concordance.lines(order='random', cut_off=100, form='simple')
    print(lines)
    assert(len(concordance.breakdown) > 0)
    assert(len(lines) == 100)
    # one_match = list(lines.keys())[0]
    # print(lines[one_match])


@pytest.mark.format_lines
def test_concordance_form_simple_kwic(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '@9[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query, s_context='s')
    concordance = corpus.concordance(result)
    lines = concordance.lines(order='random', cut_off=100, form='simple-kwic')
    print(lines)
    assert(len(concordance.breakdown) > 0)
    assert(len(lines) == 100)
    # one_match = list(lines.keys())[0]
    # print(lines[one_match])


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
