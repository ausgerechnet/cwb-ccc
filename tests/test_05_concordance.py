from ccc import Corpus
from ccc.concordances import Concordance
from ccc.concordances import line2simple
from ccc.concordances import line2df
from ccc.concordances import line2extended
import pandas as pd
import pytest


from .conftest import DATA_PATH


def get_corpus(corpus_settings, data_path=DATA_PATH):

    return Corpus(
        corpus_settings['corpus_name'],
        registry_path=corpus_settings['registry_path'],
        lib_path=corpus_settings.get('lib_path', None),
        data_path=data_path
    )


@pytest.mark.now
def test_concordance_set_context(germaparl):

    corpus = get_corpus(germaparl)
    df_dump = corpus.query('"CSU"', context_break='text').df
    print(df_dump)
    concordance = Concordance(corpus, df_dump)
    concordance.set_context(10, context_break='text', context_right=10)
    print(concordance.df_dump)


@pytest.mark.lines1
def test_concordance_simple(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.query('"CSU"').df
    concordance = Concordance(corpus, df_dump)
    lines = concordance.simple(
        p_show=['word', 'lemma'],
        s_show=['text_party', 'text_name', 'p_type']
    )
    assert(len(lines) == len(df_dump))
    assert(all(col in lines.columns for col in [
        'word', 'lemma', 'text_party', 'text_name', 'p_type'
    ]))


@pytest.mark.lines1
def test_concordance_simple_nocontext(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.query('[lemma="gehen"]', context=None).df
    concordance = Concordance(corpus, df_dump)
    lines = concordance.simple(
        p_show='word',
        s_show=['text_party', 'text_name', 'p_type']
    )
    assert(len(lines) == len(df_dump))
    assert(all(col in lines.columns for col in [
        'word', 'text_party', 'text_name', 'p_type'
    ]))
    print(lines)


@pytest.mark.lines1
def test_concordance_kwic(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.query('[lemma="gehen"]').df
    concordance = Concordance(corpus, df_dump)
    lines = concordance.kwic(
        p_show='word',
        s_show=['text_party', 'text_name', 'p_type']
    )
    assert(len(lines) == len(df_dump))
    assert(all(col in lines.columns for col in [
        'left', 'node', 'right', 'text_party', 'text_name', 'p_type'
    ]))


@pytest.mark.lines1
def test_concordance_kwic_nocontext(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.query('[lemma="gehen"]', context=None).df
    concordance = Concordance(corpus, df_dump)
    lines = concordance.kwic(
        p_show='word',
        s_show=['text_party', 'text_name', 'p_type']
    )
    assert(len(lines) == len(df_dump))
    assert(all(col in lines.columns for col in [
        'left', 'node', 'right', 'text_party', 'text_name', 'p_type'
    ]))
    print(lines)


@pytest.mark.line
def test_concordance_line(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query = (
        '[word="\\["] [lemma="CDU"] "/" "CSU" [word="\\]"]'
    )
    result = corpus.query(query)
    concordance = Concordance(corpus, result.df)
    line = result.df.iloc[0]
    text_line = concordance.text_line(
        line.name, line, p_show=['word', 'pos']
    )
    assert(type(text_line) == dict)
    assert('cpos' in text_line)


@pytest.mark.line
def test_concordance_line2simple(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query = (
        '[word="\\["] [lemma="CDU"] "/" "CSU" [word="\\]"]'
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
def test_concordance_line2df(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query = (
        '[word="\\["] [lemma="CDU"] "/" "CSU" [word="\\]"]'
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
def test_concordance_line2extended(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query = (
        '[word="\\["] [lemma="CDU"] "/" "CSU" [word="\\]"]'
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
def test_concordance_lines(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query = (
        '[word="\\["] @1[lemma="CDU"] "/" "CSU" [word="\\]"]'
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
def test_concordance_lines_dataframes(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query = (
        '[word="\\["] @1[lemma="CDU"] "/" "CSU" [word="\\]"]'
    )
    result = corpus.query(query, context_break='s',
                          match_strategy='longest')
    concordance = Concordance(corpus, result.df)
    lines = concordance.lines(form='dataframes', s_show=['text_id'], cut_off=10)
    assert('df' in lines.columns)
    assert(type(lines['df'].iloc[0]) == pd.DataFrame)


@pytest.mark.lines
def test_concordance_lines_extended(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query = (
        '[word="\\["] @1[lemma="CDU"] "/" @2 ".*" @3[word="\\]"]'
    )
    result = corpus.query(query, context_break='s',
                          match_strategy='longest')
    concordance = Concordance(corpus, result.df)
    p_slots = 'lemma'
    slots = {'test': [1, 3]}
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
def test_concordance_many(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query = (
        '[lemma="oder"]'
    )
    result = corpus.query(query)
    concordance = Concordance(corpus, result.df)
    lines = concordance.lines()
    assert(len(lines) == 100)


@pytest.mark.lines
def test_concordance_p_atts(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query = (
        '[word="\\["] [lemma="CDU"] "/" ".*" [word="\\]"]'
    )
    result = corpus.query(query, context_break='s')
    concordance = Concordance(corpus, result.df)
    lines = concordance.lines(p_show=['lemma', 'pos'], form='dataframes')
    assert('pos' in lines.iloc[0]['df'].columns)
    assert(len(lines) == 13)


@pytest.mark.lines
def test_concordance_anchors(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query = (
        '[word="\\["] @1[lemma="CDU"] "/" @2".*" [word="\\]"]'
    )
    result = corpus.query(query, context_break='s')
    concordance = Concordance(corpus, result.df)
    lines = concordance.lines(p_show=['lemma', 'pos'], form='dataframes')
    assert(len(lines) == 13)


@pytest.mark.lines
def test_concordance_anchors_weird(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query = (
        '[word="\\["] @9[lemma="CDU"] "/" @2".*" @5[word="\\]"]'
    )
    result = corpus.query(query, context_break='s')
    concordance = Concordance(corpus, result.df)
    lines = concordance.lines(order='random', cut_off=100, form='dataframes')
    assert(len(lines) == 13)


@pytest.mark.lines
def test_concordance_form_simple(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query = (
        '[word="\\["] @1[lemma="CDU"] "/" @2".*" [word="\\]"]'
    )
    result = corpus.query(query, context_break='s')
    concordance = Concordance(corpus, result.df)
    lines = concordance.lines(order='random', cut_off=100, form='simple')
    assert(len(lines) == 13)


@pytest.mark.lines
def test_concordance_form_simple_kwic(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query = (
        '[word="\\["] @1[lemma="CDU"] "/" @2".*" [word="\\]"]'
    )
    result = corpus.query(query, context_break='s')
    concordance = Concordance(corpus, result.df)
    lines = concordance.lines(order='random', cut_off=100, form='kwic')
    assert(len(lines) == 13)


@pytest.mark.lines
def test_concordance_persistence(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query_1 = (
        '[word="\\["] @1[lemma="CDU"] "/" @2".*" [word="\\]"]'
    )
    query_2 = (
        '"und"'
    )

    # will show results for query_1
    dump = corpus.query(query_1, context_break='s')
    concordance = Concordance(corpus, dump.df)
    line_1 = concordance.lines(cut_off=1, form='dataframes')
    df_1 = line_1['df'].iloc[0]

    # will show results for query_1
    dump = corpus.query(query_2, context_break='s')
    line_2 = concordance.lines(cut_off=1, form='dataframes')
    df_2 = line_2['df'].iloc[0]

    # will show results for query_2
    concordance = Concordance(corpus, dump.df)
    line_3 = concordance.lines(cut_off=1, form='dataframes')
    df_3 = line_3['df'].iloc[0]

    assert(df_1.equals(df_2))
    assert(not df_2.equals(df_3))


@pytest.mark.fail
def test_concordance_empty(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query = (
        '[lemma="Gerhard"]? [lemma="NAHH"]'
    )
    dump = corpus.query(query)
    conc = Concordance(corpus, dump.df)
    assert(conc.lines() is None)


@pytest.mark.fail
def test_concordance_p_text(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    dump = corpus.query(query)
    conc = Concordance(corpus, dump.df)
    assert(conc.lines(p_text='lemma') is None)


@pytest.mark.fail
def test_concordance_p_slots(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    dump = corpus.query(query)
    conc = Concordance(corpus, dump.df)
    assert(conc.lines(p_slots='lemma') is None)


@pytest.mark.fail
def test_concordance_form(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    dump = corpus.query(query)
    conc = Concordance(corpus, dump.df)
    with pytest.raises(NotImplementedError):
        conc.lines(form='bla')


@pytest.mark.fail
def test_concordance_order(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    dump = corpus.query(query)
    conc = Concordance(corpus, dump.df)
    with pytest.raises(NotImplementedError):
        conc.lines(order='fail')


def test_concordance_last(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    dump = corpus.query(query)
    conc = Concordance(corpus, dump.df)
    assert(type(conc.lines(order='last')) == pd.DataFrame)


def test_concordance_fallback(germaparl):
    corpus = Corpus(germaparl['corpus_name'], registry_path=germaparl["registry_path"])
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    dump = corpus.query(query)
    conc = Concordance(corpus, dump.df)
    assert(type(
        conc.lines(order='last', form='simple', p_show=['word', 'lemma'])
    ) == pd.DataFrame)
