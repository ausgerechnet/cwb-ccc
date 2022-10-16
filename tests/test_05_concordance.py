import pandas as pd
import pytest

from ccc import Corpus
from ccc.concordances import Concordance

from .conftest import DATA_PATH


def get_corpus(corpus_settings, data_path=DATA_PATH):

    return Corpus(
        corpus_settings['corpus_name'],
        registry_path=corpus_settings['registry_path'],
        lib_path=corpus_settings.get('lib_path', None),
        data_path=data_path
    )


@pytest.mark.raw
def test_concordance_simple(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.query('"CSU"').df
    concordance = Concordance(corpus, df_dump)
    lines = concordance.simple(
        df_dump,
        p_show=['word', 'lemma']
    )
    assert(len(lines) == len(df_dump))
    assert(all(col in lines.columns for col in [
        'word', 'lemma'
    ]))


@pytest.mark.raw
def test_concordance_simple_nocontext(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.query('[lemma="gehen"]', context=None).df
    concordance = Concordance(corpus, df_dump)
    lines = concordance.simple(
        df_dump,
        p_show=['word']
    )
    assert(len(lines) == len(df_dump))
    assert(all(col in lines.columns for col in [
        'word'
    ]))


@pytest.mark.raw
def test_concordance_kwic(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.query('[lemma="gehen"]').df
    concordance = Concordance(corpus, df_dump)
    lines = concordance.kwic(
        df_dump,
        p_show=['word', 'lemma']
    )
    assert(len(lines) == len(df_dump))
    assert(all(col in lines.columns for col in [
        'left_word', 'node_word', 'right_word',
        'left_lemma', 'node_lemma', 'right_lemma'
    ]))


@pytest.mark.raw
def test_concordance_kwic_nocontext(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.query('[lemma="gehen"]', context=None).df
    concordance = Concordance(corpus, df_dump)
    lines = concordance.kwic(
        df_dump,
        p_show=['word']
    )
    assert(len(lines) == len(df_dump))
    assert(all(col in lines.columns for col in [
        'left_word', 'node_word', 'right_word'
    ]))


@pytest.mark.raw
def test_concordance_slots_singletons(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        r'[pos="NE"]? @1[pos="NE"] @2"\[" ([word="[A-Z]+"]+ "/"?)+ @3"\]"'
    )
    df_dump = corpus.query(query, context=2, context_break='s',
                           match_strategy='longest', corrections={2: +1, 3: -1}).df
    concordance = Concordance(corpus, df_dump)
    lines = concordance.slots(
        df_dump,
        ['word', 'lemma']
    )
    assert(set(lines.columns) == {
        "word", "lemma",
        "1_word", "1_lemma", "2_word", "2_lemma", "3_word", "3_lemma",
        "match..matchend_word", "match..matchend_lemma"
    })


@pytest.mark.raw
def test_concordance_slots_regions(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        r'[pos="NE"]? @1[pos="NE"] @2"\[" ([word="[A-Z]+"]+ "/"?)+ @3"\]"'
    )
    df_dump = corpus.query(query, context=10, context_break='s',
                           match_strategy='longest', corrections={2: +1, 3: -1}).df
    concordance = Concordance(corpus, df_dump)
    lines = concordance.slots(
        df_dump,
        ['word'],
        slots=[['match', 1], [2, 3]]
    )
    assert(set(lines.columns) == {
        "word", "match..1_word", "2..3_word"
    })


@pytest.mark.raw
def test_concordance_slots_regions_dict(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        r'[pos="NE"]? @1[pos="NE"] @2"\[" ([word="[A-Z]+"]+ "/"?)+ @3"\]"'
    )
    df_dump = corpus.query(query, context=10, context_break='s',
                           match_strategy='longest', corrections={2: +1, 3: -1}).df
    concordance = Concordance(corpus, df_dump)
    lines = concordance.slots(
        df_dump,
        ['word'],
        slots={'mp': ['match', 1], 'party': [2, 3]}
    )
    assert(set(lines.columns) == {
        'word', 'mp_word', 'party_word'
    })


@pytest.mark.line
def test_concordance_export_dict(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[word="\\["] @1[lemma="CDU"] "/" "CSU" [word="\\]"]'
    )
    result = corpus.query(query)
    concordance = Concordance(corpus, result.df)
    line = result.df.iloc[0]
    text_line = concordance._export(
        line.name, line, p_show=['word', 'pos'], form='dict'
    )
    assert(isinstance(text_line, dict))
    assert('cpos' in text_line)


@pytest.mark.line
def test_concordance_export_dataframe(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[word="\\["] @1[lemma="CDU"] "/" "CSU" [word="\\]"]'
    )
    result = corpus.query(query, context_break='s')
    concordance = Concordance(corpus, result.df)
    line = result.df.iloc[0]
    text_line = concordance._export(
        line.name, line, p_show=['word', 'pos'], form='dataframe'
    )
    assert(isinstance(text_line, pd.DataFrame))


@pytest.mark.raw
def test_concordance_dict(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.query('[lemma="gehen"]', context=None).df
    concordance = Concordance(corpus, df_dump)
    lines = concordance.dict(
        df_dump,
        p_show=['word']
    )
    assert(isinstance(lines['dict'].iloc[0], dict))
    assert('word' in lines['dict'].iloc[0])


@pytest.mark.raw
def test_concordance_dataframes(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[word="\\["] @1[lemma="CDU"] "/" "CSU" [word="\\]"]'
    )
    result = corpus.query(query, context_break='s',
                          match_strategy='longest')
    concordance = Concordance(corpus, result.df)
    df = concordance.dict(result.df, p_show=['word', 'lemma'])
    lines = concordance.dataframe(df, p_show=['word', 'lemma'])
    assert('dataframe' in lines.columns)
    assert(isinstance(lines['dataframe'].iloc[0], pd.DataFrame))


@pytest.mark.lines
def test_concordance_lines(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[word="\\["] @1[lemma="CDU"] "/" "CSU" [word="\\]"]'
    )
    result = corpus.query(query, context_break='s',
                          match_strategy='longest')

    concordance = Concordance(corpus, result.df)

    # default = simple
    lines = concordance.lines()
    assert(len(lines) > 10)
    assert('word' in lines.columns)

    # kwic
    lines = concordance.lines(form='kwic', cut_off=10)
    assert(all(
        elem in lines.columns for elem in ['left_word', 'node_word', 'right_word']
    ))
    assert(len(lines) == 10)

    # kwic with s-attribute
    lines = concordance.lines(form='kwic', s_show=['text_id'], cut_off=10)
    assert(len(lines) == 10)
    assert('text_id' in lines.columns)

    # slots
    lines = concordance.lines(form='slots', s_show=['text_id'], cut_off=10)
    assert(len(lines) == 10)
    assert(all(
        elem in lines.columns for elem in ['match..matchend_word', '1_word']
    ))

    # dict
    lines = concordance.lines(form='dict', s_show=['text_id'], cut_off=10)
    assert(len(lines) == 10)
    assert(all(
        elem in lines.columns for elem in ['dict', 'text_id']
    ))

    # dict
    lines = concordance.lines(form='dataframe', s_show=['text_id'], cut_off=10)
    assert(len(lines) == 10)
    assert(all(
        elem in lines.columns for elem in ['dataframe', 'text_id']
    ))


@pytest.mark.lines
def test_concordance_many(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[lemma="oder"]'
    )
    result = corpus.query(query)
    concordance = Concordance(corpus, result.df)
    lines = concordance.lines()
    assert(len(lines) == 100)


@pytest.mark.lines
def test_concordance_p_atts(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[word="\\["] [lemma="CDU"] "/" ".*" [word="\\]"]'
    )
    result = corpus.query(query, context_break='s')
    concordance = Concordance(corpus, result.df)
    lines = concordance.lines(p_show=['lemma', 'pos'], form='dataframe')
    assert('pos' in lines.iloc[0]['dataframe'].columns)
    assert(len(lines) == 13)


@pytest.mark.lines
def test_concordance_anchors(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[word="\\["] @1[lemma="CDU"] "/" @2".*" [word="\\]"]'
    )
    result = corpus.query(query, context_break='s')
    concordance = Concordance(corpus, result.df)
    lines = concordance.lines(p_show=['lemma', 'pos'], form='dataframe')
    assert(len(lines) == 13)


@pytest.mark.lines
def test_concordance_anchors_weird(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[word="\\["] @9[lemma="CDU"] "/" @2".*" @5[word="\\]"]'
    )
    result = corpus.query(query, context_break='s')
    concordance = Concordance(corpus, result.df)
    lines = concordance.lines(order='random', cut_off=100, form='dataframe')
    assert(len(lines) == 13)


@pytest.mark.lines
def test_concordance_form_simple(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[word="\\["] @1[lemma="CDU"] "/" @2".*" [word="\\]"]'
    )
    result = corpus.query(query, context_break='s')
    concordance = Concordance(corpus, result.df)
    lines = concordance.lines(order='random', cut_off=100, form='simple')
    assert(len(lines) == 13)


@pytest.mark.lines
def test_concordance_form_kwic(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[word="\\["] @1[lemma="CDU"] "/" @2".*" [word="\\]"]'
    )
    result = corpus.query(query, context_break='s')
    concordance = Concordance(corpus, result.df)
    lines = concordance.lines(order='random', cut_off=100, form='kwic')
    assert(len(lines) == 13)


@pytest.mark.lines
def test_concordance_persistence(germaparl):
    corpus = get_corpus(germaparl)
    query_1 = (
        '[word="\\["] @1[lemma="CDU"] "/" @2".*" [word="\\]"]'
    )
    query_2 = (
        '"und"'
    )

    # will show results for query_1
    dump = corpus.query(query_1, context_break='s')
    concordance = Concordance(corpus, dump.df)
    line_1 = concordance.lines(cut_off=1, form='dataframe')
    df_1 = line_1['dataframe'].iloc[0]

    # will show results for query_1
    dump = corpus.query(query_2, context_break='s')
    line_2 = concordance.lines(cut_off=1, form='dataframe')
    df_2 = line_2['dataframe'].iloc[0]

    # will show results for query_2
    concordance = Concordance(corpus, dump.df)
    line_3 = concordance.lines(cut_off=1, form='dataframe')
    df_3 = line_3['dataframe'].iloc[0]

    assert(df_1.equals(df_2))
    assert(not df_2.equals(df_3))


@pytest.mark.fail
def test_concordance_empty(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[lemma="Gerhard"]? [lemma="NAHH"]'
    )
    dump = corpus.query(query)
    conc = Concordance(corpus, dump.df)
    assert(conc.lines().empty)


@pytest.mark.fail
def test_concordance_format(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    dump = corpus.query(query)
    conc = Concordance(corpus, dump.df)
    conc.lines(form='fail')


@pytest.mark.fail
def test_concordance_order(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    dump = corpus.query(query)
    conc = Concordance(corpus, dump.df)
    conc.lines(order='fail')


def test_concordance_last(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    dump = corpus.query(query)
    conc = Concordance(corpus, dump.df)
    assert(isinstance(conc.lines(order='last'), pd.DataFrame))


def test_concordance_fallback(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    dump = corpus.query(query)
    conc = Concordance(corpus, dump.df)
    assert(isinstance(
        conc.lines(order='last', form='simple', p_show=['word', 'lemma']),
        pd.DataFrame)
    )


@pytest.mark.benchmark
def test_perf_concordance(benchmark, germaparl):
    benchmark.pedantic(test_concordance_dataframes, kwargs={'germaparl': germaparl}, rounds=10, iterations=5)
