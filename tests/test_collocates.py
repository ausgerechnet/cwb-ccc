from ccc.cwb import CWBEngine
from ccc.collocates import Collocates

import pandas as pd
import pytest


# registry path
registry_path = "/home/ausgerechnet/corpora/cwb/registry/"
corpus_name = "SZ_FULL"


@pytest.mark.collocates
@pytest.mark.collocates_default
def test_query_default():
    engine = CWBEngine(corpus_name, registry_path)
    collocates = Collocates(engine)
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    collocates.query(query)
    c = collocates.show(order='log_likelihood')
    assert(type(c) == pd.DataFrame)
    assert(len(c) > 9)
    assert('Bundeskanzlerin' in c.index)


def compare_counts(lemma, window, drop_hapaxes=False):

    # CCC
    engine = CWBEngine("GERMAPARL_1114", registry_path)
    collocates = Collocates(engine, max_window_size=window,
                            s_break='s', p_query='lemma')
    query = '[lemma="' + lemma + '"]'
    collocates.query(query)
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
        'f1_ccc': int(engine.marginals([lemma], "lemma")[['freq']].values[0]),
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
    col = col[['O11', 'f2']]

    assert(col.equals(ucs))
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
    engine = CWBEngine("GERMAPARL_1114", registry_path)
    query = '[lemma="sagen"]'
    collocates = Collocates(engine, max_window_size=2, s_break='s',
                            p_query='lemma')
    collocates.query(query)
    c2 = collocates.show(window=2, cut_off=50, drop_hapaxes=True)
    print(c2[['O11']])
    assert(type(c2) == pd.DataFrame)
