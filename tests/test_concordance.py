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
    assert(type(concordance.breakdown) == pd.DataFrame)


@pytest.mark.breakdown
@pytest.mark.many
def test_concordance_breakdown_many(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '[lemma="oder"]'
    )
    result = corpus.query(query)
    concordance = corpus.concordance(result)
    assert(type(concordance.breakdown) == pd.DataFrame)


@pytest.mark.meta
def test_concordance_meta(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'], data_path=None)
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query)
    concordance = corpus.concordance(result)
    concordance.lines(s_show=['text_id', 'p_type'])


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
    line = concordance.text_line(index, columns, p_show=['word', 'pos'])
    assert(type(line) == dict)


@pytest.mark.lines
def test_concordance_lines(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '@0[lemma="Angela"]? @1[lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"] "und" @3[pos="NE"]? @4[pos="NE"]'
    )
    result = corpus.query(query, s_context='s',
                          match_strategy='longest')

    concordance = corpus.concordance(result)

    # standard = raw
    assert(len(concordance.breakdown) > 0)
    lines = concordance.lines()
    assert(len(lines) > 10)
    assert('raw' in lines.columns)
    assert(all(elem in lines.iloc[0]['raw'] for elem in ['cpos', 'match', 'word']))

    # simple
    lines = concordance.lines(form='simple', cut_off=10)
    assert('text' in lines.columns)
    assert(len(lines) == 10)

    # kwic
    lines = concordance.lines(form='kwic', cut_off=10)
    assert(all(elem in lines.columns for elem in ['left', 'node', 'right']))
    assert(len(lines) == 10)

    # kwic with s-attribute
    lines = concordance.lines(form='kwic', s_show=['text_id'], cut_off=10)
    assert(len(lines) == 10)
    assert('text_id' in lines.columns)


@pytest.mark.now
@pytest.mark.lines
def test_concordance_lines_dataframes(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '@0[lemma="Angela"]? @1[lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"] "und" @3[pos="NE"]? @4[pos="NE"]'
    )
    result = corpus.query(query, s_context='s',
                          match_strategy='longest')
    concordance = corpus.concordance(result)
    lines = concordance.lines(form='dataframes', s_show=['text_id'], cut_off=10)
    assert('df' in lines.columns)
    assert(type(lines['df'].iloc[0]) == pd.DataFrame)


@pytest.mark.lines
def test_concordance_lines_extended(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '@0[lemma="Angela"]? @1[lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"] "und" @3[pos="NE"]? @4[pos="NE"]'
    )
    result = corpus.query(query, s_context='s',
                          match_strategy='longest')
    concordance = corpus.concordance(result)
    p_slots = 'lemma'
    region = (3, 4)
    lines = concordance.lines(form='extended',
                              p_show=['word', 'lemma'],
                              s_show=['text_id'],
                              regions=[region],
                              p_text='word',
                              p_slots=p_slots,
                              cut_off=10)

    assert('df' in lines.columns)
    assert(type(lines['df'].iloc[0]) == pd.DataFrame)

    assert('_'.join(['_'.join([
        str(region[0]), str(region[1])
    ]), p_slots]) in lines.columns)
    assert(3 in lines.columns)

    assert('text' in lines.columns)


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


@pytest.mark.lines
def test_concordance_p_atts(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query, s_context='s')
    concordance = corpus.concordance(result)
    lines = concordance.lines(p_show=['lemma', 'pos'], form='dataframes')
    assert('pos' in lines.iloc[0]['df'].columns)
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
    lines = concordance.lines(p_show=['lemma', 'pos'], form='dataframes')
    assert(len(concordance.breakdown) > 0)
    assert(len(lines) == 100)


@pytest.mark.lines
def test_concordance_anchors_weird(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '@9[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query, s_context='s')
    concordance = corpus.concordance(result)
    lines = concordance.lines(order='random', cut_off=100, form='dataframes')
    assert(len(concordance.breakdown) > 0)
    assert(len(lines) == 100)


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
    assert(len(concordance.breakdown) > 0)
    assert(len(lines) == 100)


@pytest.mark.lines
def test_concordance_form_simple_kwic(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '@9[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query, s_context='s')
    concordance = corpus.concordance(result)
    lines = concordance.lines(order='random', cut_off=100, form='kwic')
    assert(len(concordance.breakdown) > 0)
    assert(len(lines) == 100)


@pytest.mark.lines
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
    line_1 = concordance.lines(cut_off=1, form='dataframes')
    df_1 = line_1['df'].iloc[0]
    breakdown_1 = concordance.breakdown

    # will show results for query_1
    result = corpus.query(query_2, s_context='s')
    line_2 = concordance.lines(cut_off=1, form='dataframes')
    df_2 = line_2['df'].iloc[0]
    breakdown_2 = concordance.breakdown

    # will show results for query_2
    concordance = corpus.concordance(result)
    line_3 = concordance.lines(cut_off=1, form='dataframes')
    df_3 = line_3['df'].iloc[0]
    breakdown_3 = concordance.breakdown

    assert(df_1.equals(df_2))
    assert(breakdown_1.equals(breakdown_2))
    assert(not df_2.equals(df_3))
    assert(not breakdown_2.equals(breakdown_3))
