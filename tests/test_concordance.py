from ccc import Corpus
from ccc.concordances import Concordance
from ccc.concordances import line2simple
from ccc.concordances import line2df
from ccc.concordances import line2extended
import pandas as pd
import pytest


@pytest.mark.meta
def test_concordance_meta(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'], data_path=None)
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query)
    concordance = Concordance(corpus, result.df)
    concordance.lines(s_show=['text_id', 'p_type'])


@pytest.mark.line
def test_concordance_line(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query)
    concordance = Concordance(corpus, result.df)
    line = result.df.iloc[0]
    text_line = concordance.text_line(
        line.name, line, p_show=['word', 'pos']
    )
    assert(type(text_line) == dict)


@pytest.mark.line
def test_concordance_line2simple(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query)
    concordance = Concordance(corpus, result.df)
    line = result.df.iloc[0]
    text_line = concordance.text_line(
        line.name, line, ['word']
    )
    # simple
    res = line2simple(text_line)
    assert(type(res) == dict)
    assert(type(res["text"]) == str)
    # kwic
    res = line2simple(text_line, kwic=True)
    assert(type(res) == dict)
    assert(type(res["left"]) == str)
    assert(type(res["node"]) == str)
    assert(type(res["right"]) == str)


@pytest.mark.line
def test_concordance_line2df(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query)
    concordance = Concordance(corpus, result.df)
    line = result.df.iloc[0]
    text_line = concordance.text_line(
        line.name, line, ['word']
    )
    res = line2df(text_line)
    assert(type(res) == dict)
    assert(type(res['df']) == pd.DataFrame)


@pytest.mark.line
def test_concordance_line2extended(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query)
    concordance = Concordance(corpus, result.df)
    line = result.df.iloc[0]
    text_line = concordance.text_line(
        line.name, line, ['word']
    )
    res = line2extended(text_line, p_slots='word')
    assert(type(res) == dict)
    assert(type(res['df']) == pd.DataFrame)
    assert(type(res['text']) == str)


@pytest.mark.lines
def test_concordance_lines(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '@0[lemma="Angela"]? @1[lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"] "und" @3[pos="NE"]? @4[pos="NE"]'
    )
    result = corpus.query(query, context_break='s',
                          match_strategy='longest')

    concordance = Concordance(corpus, result.df)

    # standard = raw
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


@pytest.mark.lines
def test_concordance_lines_dataframes(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '@0[lemma="Angela"]? @1[lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"] "und" @3[pos="NE"]? @4[pos="NE"]'
    )
    result = corpus.query(query, context_break='s',
                          match_strategy='longest')
    concordance = Concordance(corpus, result.df)
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
    result = corpus.query(query, context_break='s',
                          match_strategy='longest')
    concordance = Concordance(corpus, result.df)
    p_slots = 'lemma'
    slots = {'test': [3, 4]}
    lines = concordance.lines(form='extended',
                              p_show=['word', 'lemma'],
                              s_show=['text_id'],
                              slots=slots,
                              p_text='word',
                              p_slots=p_slots,
                              cut_off=10)

    assert('df' in lines.columns)
    assert(type(lines['df'].iloc[0]) == pd.DataFrame)

    assert(3 in lines.columns)

    assert('text' in lines.columns)


@pytest.mark.lines
def test_concordance_many(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '[lemma="oder"]'
    )
    result = corpus.query(query)
    concordance = Concordance(corpus, result.df)
    lines = concordance.lines()
    assert(len(lines) == 100)


@pytest.mark.lines
def test_concordance_p_atts(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query, context_break='s')
    concordance = Concordance(corpus, result.df)
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
    result = corpus.query(query, context_break='s')
    concordance = Concordance(corpus, result.df)
    lines = concordance.lines(p_show=['lemma', 'pos'], form='dataframes')
    assert(len(lines) == 100)


@pytest.mark.lines
def test_concordance_anchors_weird(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '@9[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query, context_break='s')
    concordance = Concordance(corpus, result.df)
    lines = concordance.lines(order='random', cut_off=100, form='dataframes')
    assert(len(lines) == 100)


@pytest.mark.format_lines
def test_concordance_form_simple(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '@9[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query, context_break='s')
    concordance = Concordance(corpus, result.df)
    lines = concordance.lines(order='random', cut_off=100, form='simple')
    assert(len(lines) == 100)


@pytest.mark.lines
def test_concordance_form_simple_kwic(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '@9[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query, context_break='s')
    concordance = Concordance(corpus, result.df)
    lines = concordance.lines(order='random', cut_off=100, form='kwic')
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
    result = corpus.query(query_1, context_break='s')
    concordance = Concordance(corpus, result.df)
    line_1 = concordance.lines(cut_off=1, form='dataframes')
    df_1 = line_1['df'].iloc[0]

    # will show results for query_1
    result = corpus.query(query_2, context_break='s')
    line_2 = concordance.lines(cut_off=1, form='dataframes')
    df_2 = line_2['df'].iloc[0]

    # will show results for query_2
    concordance = Concordance(corpus, result.df)
    line_3 = concordance.lines(cut_off=1, form='dataframes')
    df_3 = line_3['df'].iloc[0]

    assert(df_1.equals(df_2))
    assert(not df_2.equals(df_3))


@pytest.mark.fail
def test_concordance_empty(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'], data_path=None)
    query = (
        '[lemma="Gerhard"]? [lemma="NAHH"]'
    )
    dump = corpus.query(query)
    conc = Concordance(corpus, dump.df)
    assert(conc.lines() is None)


@pytest.mark.fail
def test_concordance_p_text(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'], data_path=None)
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    dump = corpus.query(query)
    conc = Concordance(corpus, dump.df)
    assert(conc.lines(p_text='lemma') is None)


@pytest.mark.fail
def test_concordance_p_slots(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'], data_path=None)
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    dump = corpus.query(query)
    conc = Concordance(corpus, dump.df)
    assert(conc.lines(p_slots='lemma') is None)


@pytest.mark.fail
def test_concordance_form(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'], data_path=None)
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    dump = corpus.query(query)
    conc = Concordance(corpus, dump.df)
    with pytest.raises(NotImplementedError):
        conc.lines(form='bla')


@pytest.mark.fail
def test_concordance_order(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'], data_path=None)
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    dump = corpus.query(query)
    conc = Concordance(corpus, dump.df)
    with pytest.raises(NotImplementedError):
        conc.lines(order='fail')


def test_concordance_last(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'], data_path=None)
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    dump = corpus.query(query)
    conc = Concordance(corpus, dump.df)
    assert(type(conc.lines(order='last')) == pd.DataFrame)


@pytest.mark.now
def test_concordance_fallback(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'], data_path=None)
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    dump = corpus.query(query)
    conc = Concordance(corpus, dump.df)
    assert(type(
        conc.lines(order='last', form='simple', p_show=['word', 'lemma'])
    ) == pd.DataFrame)
