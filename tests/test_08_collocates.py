from ccc import Corpus
from ccc.collocates import Collocates
from ccc.keywords import Keywords

from .conftest import DATA_PATH

import pandas as pd
import pytest


def get_corpus(corpus_settings, data_path=DATA_PATH):

    return Corpus(
        corpus_settings['corpus_name'],
        registry_path=corpus_settings['registry_path'],
        lib_path=corpus_settings.get('lib_path', None),
        data_path=data_path
    )


@pytest.mark.default
def test_collo_single(germaparl):
    corpus = get_corpus(germaparl)
    query = ('[word="\\("] [lemma=".*"]+ [word="\\)"]')
    df_dump = corpus.query(query).df
    collocates = Collocates(corpus, df_dump, 'lemma')
    c = collocates.show(order='log_likelihood')
    assert(type(c) == pd.DataFrame)
    assert('Dr.' in c.index)


@pytest.mark.default
def test_collo_combo(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[word="\\("] [lemma=".*"]+ [word="\\)"]'
    )
    df_dump = corpus.query(query).df
    collocates = Collocates(corpus, df_dump, ['lemma', 'pos'])
    c = collocates.show(order='log_likelihood')
    assert(type(c) == pd.DataFrame)


@pytest.mark.fallback
def test_query_logging(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[word="\\("] [lemma=".*"]+ [word="\\)"]'
    )
    df_dump = corpus.query(query).df
    collocates = Collocates(corpus, df_dump, 'fail')
    c = collocates.show(order='log_likelihood', window=15)
    assert(type(c) == pd.DataFrame)
    assert('Dr.' in c.index)


@pytest.mark.collocates_speed
def test_collocates_speed_many(germaparl):
    corpus = get_corpus(germaparl)
    query = '[lemma="die"]'
    df_dump = corpus.query(query, context_break='text').df
    collocates = Collocates(corpus, df_dump, p_query='lemma', mws=100)
    c2 = collocates.show(window=50, cut_off=50)
    assert c2.index[0] == ','
    assert type(c2) == pd.DataFrame


@pytest.mark.persistence
def test_collocates_persistence(germaparl):
    corpus = get_corpus(germaparl)
    query_1 = (
        '"SPD"'
    )
    query_2 = (
        '"CSU"'
    )

    # will show collocates for query_1
    result = corpus.query(query_1, context_break='s').df
    collocates = Collocates(corpus, result, 'lemma')
    line_1 = collocates.show()

    # will show collocates for query_1
    result = corpus.query(query_2, context_break='s').df
    line_2 = collocates.show()

    # will show collocates for query_2
    collocates = Collocates(corpus, result, 'lemma')
    line_3 = collocates.show()

    assert(line_1.equals(line_2))
    assert(not line_2.equals(line_3))


@pytest.mark.keywords_collocates
def test_query_keywords_collocates(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '"Horst" expand to s'
    )
    dump = corpus.query(query)
    keywords = Keywords(corpus, df_dump=dump.df, p_query='lemma')
    assert('Horst' == keywords.show(order='log_likelihood').head(1).index[0])


@pytest.mark.mwu_marginals
def test_collocates_mwu(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[lemma="CDU"] "/"? [lemma="CSU"]?'
    )
    result = corpus.query(query, match_strategy='longest')
    collocates = Collocates(corpus, result.df, 'lemma')
    c = collocates.show(order='log_likelihood', cut_off=None)
    assert(type(c) == pd.DataFrame)
    assert(len(c) > 9)
    assert('CSU' in c.index)
    assert(int(c.loc['CSU']['in_nodes']) > int(c.loc['CSU']['O11']))


@pytest.mark.fold_items
def test_collocates_pp(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '"SPD"'
    )
    result = corpus.query(query)
    collocates = Collocates(corpus, result.df, p_query='word')
    c = collocates.show(order='log_likelihood', cut_off=None)
    assert(int(c.loc['Bündnis']['O11']) < int(c.loc['BÜNDNIS']['O11']))
    c = collocates.show(order='log_likelihood', cut_off=None, flags="%cd")
    assert('bundnis' in c.index and 'Bündnis' not in c.index)


@pytest.mark.fail
def test_collocates_empty(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[lemma="Armin"]? [lemma="NAHH"]'
    )
    dump = corpus.query(query)
    collocates = Collocates(corpus, dump.df, p_query='word')
    collocates.show()


@pytest.mark.fail
def test_collocates_no_context(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[lemma="Armin"]? [lemma="Laschet"]'
    )
    dump = corpus.query(query)
    collocates = Collocates(corpus, dump.df, p_query='word', mws=0)
    collocates.show()


@pytest.mark.fail
def test_collocates_no_mws(germaparl):
    corpus = get_corpus(germaparl)
    query = (
        '[lemma="Armin"]? [lemma="Laschet"]'
    )
    dump = corpus.query(query)
    collocates = Collocates(corpus, dump.df, p_query='word', mws=None)
    collocates.show()


def test_collocates_nodes(germaparl):

    corpus = get_corpus(germaparl)
    query = (
        '[lemma=","] | [lemma="\\."] | [lemma="\\)"] | [lemma="\\("]'
    )
    # three discoursemes
    dump = corpus.query(query)
    collocates = Collocates(corpus, dump.df)
    df = collocates.show(cut_off=None)
    assert("," not in df.index)
    assert("(" not in df.index)


@pytest.mark.collocates_gold
def test_compare_counts(germaparl, ucs_counts):
    # identities that should hold between counting strategies:
    # O11 = f_ucs
    # O11 + O21 = f2_ucs
    # O11 + O12 + O21 + O22 + freq[node] = N_ucs
    # O11 + O12 = f1_ucs - O11_ucs[node]

    corpus = get_corpus(germaparl)

    # [lemma="Land"]
    lemma = "Land"
    context = 10
    min_freq = 0

    df_dump = corpus.query('[lemma="%s"]' % lemma, context=context, context_break='s').df
    collocates = Collocates(corpus, df_dump, p_query='lemma')
    counts = collocates.show(window=context, cut_off=None, min_freq=min_freq)[[
        'O11', 'O12', 'O21', 'O22', 'in_nodes'
    ]]
    counts = counts.join(ucs_counts[lemma])
    ucs_node_cooc = ucs_counts[lemma].loc[lemma]
    ccc_node_freq = corpus.marginals([lemma], "lemma")['freq'].values[0]

    assert(counts['O11'].equals(counts['f_ucs']))
    assert((counts['O11'] + counts['O21']).equals(counts['f2_ucs']))
    assert((counts['O11'] + counts['O12'] + counts['O21'] + counts['O22'] + ccc_node_freq).equals(counts['N_ucs']))
    assert((counts['O11'] + counts['O12']).equals(counts['f1_ucs'] - ucs_node_cooc['f_ucs']))

    # [lemma="und"]
    lemma = "und"
    context = 5
    min_freq = 2

    df_dump = corpus.query('[lemma="%s"]' % lemma, context=context, context_break='s').df
    collocates = Collocates(corpus, df_dump, p_query='lemma')
    counts = collocates.show(window=context, cut_off=None, min_freq=min_freq)[[
        'O11', 'O12', 'O21', 'O22', 'in_nodes'
    ]]
    counts = counts.join(ucs_counts['und'])
    ucs_node_cooc = ucs_counts['und'].loc['und']
    ccc_node_freq = corpus.marginals(['und'], "lemma")['freq'].values[0]

    assert(counts['O11'].equals(counts['f_ucs']))
    assert((counts['O11'] + counts['O21']).equals(counts['f2_ucs']))
    assert((counts['O11'] + counts['O12'] + counts['O21'] + counts['O22'] + ccc_node_freq).equals(counts['N_ucs']))
    assert((counts['O11'] + counts['O12']).equals(counts['f1_ucs'] - ucs_node_cooc['f_ucs']))


@pytest.mark.benchmark
def test_perf_collocates(benchmark, germaparl):
    benchmark.pedantic(test_collo_combo, kwargs={'germaparl': germaparl}, rounds=5, iterations=2)
