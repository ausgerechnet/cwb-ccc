from ccc import Corpus

import pandas as pd
import pytest


# registry path
registry_path = "/home/ausgerechnet/corpora/cwb/registry/"
corpus_name = "SZ_2009_14"


@pytest.mark.collocates
@pytest.mark.collocates_default
def test_query_default():
    corpus = Corpus(corpus_name, registry_path)
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query)
    collocates = corpus.collocates(result)
    c = collocates.show(order='log_likelihood')
    assert(type(c) == pd.DataFrame)
    assert(len(c) > 9)
    assert('Bundeskanzlerin' in c.index)


@pytest.mark.logger
def test_query_logging():
    corpus = Corpus(corpus_name, registry_path)
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    result = corpus.query(query)
    collocates = corpus.collocates(result, p_query='fail')
    c = collocates.show(order='log_likelihood')
    assert(type(c) == pd.DataFrame)
    assert(len(c) > 9)
    assert('Bundeskanzlerin' in c.index)


def compare_counts(lemma, window, drop_hapaxes=False):

    # CCC
    corpus = Corpus("GERMAPARL_1114", registry_path)
    query = '[lemma="' + lemma + '"]'
    result = corpus.query(query, context=window, s_break='s')
    collocates = corpus.collocates(result, p_query='lemma')
    col = collocates.show(window=5, cut_off=None,
                          drop_hapaxes=drop_hapaxes)

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
    compare_counts('und', 2, drop_hapaxes=True)


@pytest.mark.collocates_speed
def test_collocates_speed_many():
    corpus = Corpus("GERMAPARL_1114", registry_path)
    query = '[lemma="sagen"]'
    result = corpus.query(query, context=2, s_break='s')
    collocates = corpus.collocates(result, p_query='lemma')
    c2 = collocates.show(window=2, cut_off=50, drop_hapaxes=True)
    assert(type(c2) == pd.DataFrame)


@pytest.mark.switch_corpora
def test_collocates_persistence():
    corpus = Corpus(corpus_name, registry_path)
    query_1 = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    query_2 = (
        '[lemma="Horst"]? [lemma="Seehofer"]'
    )

    # will show collocates for query_1
    result = corpus.query(query_1, s_break='s')
    collocates = corpus.collocates(result)
    line_1 = collocates.show()

    # will show collocates for query_1
    result = corpus.query(query_2, s_break='s')
    line_2 = collocates.show()

    # will show collocates for query_2
    collocates = corpus.collocates(result)
    line_3 = collocates.show()

    assert(line_1.equals(line_2))
    assert(not line_2.equals(line_3))


@pytest.mark.keywords_collocates
def test_query_keywords_collocates():
    corpus = Corpus(corpus_name, registry_path)
    query = (
        r'[lemma="Angela"]? [lemma="Merkel"] '
        r'[word="\("] [lemma="CDU"] [word="\)"] expand to s'
    )
    result = corpus.query(query)
    keywords = corpus.keywords(df_node=result)
    assert('Angela' == keywords.show(order='log_likelihood').head(1).index[0])


@pytest.mark.collocates
@pytest.mark.collocates_mwu_marginals
def test_collactes_mwu():
    corpus = Corpus(corpus_name, registry_path, data_path=None)
    query = (
        '[lemma="Gerhard"]? [lemma="Schröder"]'
    )
    result = corpus.query(query)
    collocates = corpus.collocates(result)
    c = collocates.show(order='log_likelihood', cut_off=None)
    assert(type(c) == pd.DataFrame)
    assert(len(c) > 9)
    assert('Bundeskanzler' in c.index)
    print(c.loc[['Gerhard', 'in']])
