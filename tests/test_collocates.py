from ccc import Corpus
from ccc.collocates import Collocates
from ccc.keywords import Keywords

import pandas as pd
import pytest


@pytest.mark.default
def test_query_default(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    df_dump = corpus.query(query).df
    collocates = Collocates(corpus, df_dump, 'lemma')
    c = collocates.show(order='log_likelihood')
    assert(type(c) == pd.DataFrame)
    assert(len(c) == 100)
    assert('Bundeskanzlerin' in c.index)


@pytest.mark.fallback
def test_query_logging(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    df_dump = corpus.query(query).df
    collocates = Collocates(corpus, df_dump, 'fail')
    c = collocates.show(order='log_likelihood', window=15)
    assert(type(c) == pd.DataFrame)
    assert(len(c) > 9)
    assert('Bundeskanzlerin' in c.index)


def compare_counts(lemma, window, min_freq=0):

    # CCC
    corpus = Corpus("GERMAPARL_1114")
    query = '[lemma="' + lemma + '"]'
    df_dump = corpus.query(query, context=window, context_break='s').df
    collocates = Collocates(corpus, df_dump, p_query='lemma')
    col = collocates.show(window=5, cut_off=None,
                          min_freq=min_freq)

    # UCS
    ucs = pd.read_csv("tests/gold/ucs-germaparl1114-" + lemma +
                      ".ds.gz", sep="\t", index_col=2, comment="#",
                      quoting=3, na_filter=False)
    ucs.index.name = 'item'
    try:
        O11_ucs_node = ucs.loc[lemma]['f']
        ucs.drop(lemma, inplace=True)
    except KeyError:
        O11_ucs_node = 0

    # identities that should hold between counting strategies
    # (1) N_ccc + f1_ccc = N_ucs
    # (2) f1_infl_ccc = f1_infl_ucs - O11_ucs_node
    nr = {
        'f1_ccc': int(corpus.marginals([lemma], "lemma")[['freq']].values[0]),
        'N_ccc': int(col[['N']].values[0]),
        'f1_infl_ccc': int(col[['f1']].values[0]),
        'N_ucs': int(ucs[['N']].values[0]),
        'f1_infl_ucs': int(ucs[['f1']].values[0]),
        'O11_ucs_node': O11_ucs_node
    }

    # make dataframes comparable
    ucs = ucs[['f', 'f2']]
    ucs.columns = ['O11', 'f2']
    ucs.sort_values(by=['O11', 'item'], ascending=False, inplace=True)

    assert(nr['N_ccc'] + nr['f1_ccc'] == nr['N_ucs'])
    assert(nr['f1_infl_ccc'] == nr['f1_infl_ucs'] - nr['O11_ucs_node'])


@pytest.mark.collocates_gold
def test_compare_counts():
    compare_counts('Atomkraft', 5)


@pytest.mark.collocates_gold
def test_compare_counts_2():
    compare_counts('Angela', 5)


@pytest.mark.collocates_speed
@pytest.mark.skip
def test_compare_counts_3():
    compare_counts('und', 2)


@pytest.mark.collocates_speed
def test_collocates_speed_many():
    corpus = Corpus("GERMAPARL_1114")
    query = '[lemma="sagen"]'
    df_dump = corpus.query(query, context=2, context_break='s').df
    collocates = Collocates(corpus, df_dump, p_query='lemma')
    c2 = collocates.show(window=2, cut_off=50)
    assert(type(c2) == pd.DataFrame)


@pytest.mark.persistence
def test_collocates_persistence(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query_1 = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    query_2 = (
        '[lemma="Horst"]? [lemma="Seehofer"]'
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
def test_query_keywords_collocates(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    query = (
        r'[lemma="Angela"]? [lemma="Merkel"] '
        r'[word="\("] [lemma="CDU"] [word="\)"] expand to s'
    )
    dump = corpus.query(query)
    keywords = Keywords(corpus, df_dump=dump.df, p_query='lemma')
    assert('Angela' == keywords.show(order='log_likelihood').head(1).index[0])


@pytest.mark.mwu_marginals
def test_collactes_mwu(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'], data_path=None)
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    result = corpus.query(query)
    collocates = Collocates(corpus, result.df, 'lemma')
    c = collocates.show(order='log_likelihood', cut_off=None)
    assert(type(c) == pd.DataFrame)
    assert(len(c) > 9)
    assert('Bundeskanzler' in c.index)
    c.loc['Gerhard']['in_nodes'] > c.loc['Gerhard']['f']
    c.loc['in']['in_nodes'] == 0


@pytest.mark.fold_items
def test_collocates_pp(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'], data_path=None)
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    result = corpus.query(query)
    collocates = Collocates(corpus, result.df, p_query='word')
    c = collocates.show(order='log_likelihood', cut_off=None)
    assert(c.loc['In']['O11'] < c.loc['in']['O11'])
    c = collocates.show(order='log_likelihood', cut_off=None, flags="%cd")
    assert('in' in c.index and 'In' not in c.index)


@pytest.mark.fail
def test_collocates_empty(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'], data_path=None)
    query = (
        '[lemma="Gerhard"]? [lemma="NAHH"]'
    )
    dump = corpus.query(query)
    collocates = Collocates(corpus, dump.df, p_query='word')
    collocates.show()


@pytest.mark.fail
def test_collocates_no_context(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'], data_path=None)
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    dump = corpus.query(query)
    collocates = Collocates(corpus, dump.df, p_query='word', mws=0)
    collocates.show()


@pytest.mark.fail
def test_collocates_no_mws(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'], data_path=None)
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    dump = corpus.query(query)
    collocates = Collocates(corpus, dump.df, p_query='word', mws=None)
    collocates.show()
