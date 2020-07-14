from ccc.cwb import Corpus
from ccc.utils import preprocess_query
from ccc.utils import fold_item
from ccc.utils import merge_intervals
import pytest


def test_preprocess_anchor_query():
    query = (
        '@0[lemma="Angela"]? @1[lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"]'
    )
    query_1, s_query_1, anchors_1 = preprocess_query(query)

    query = (
        '@0[lemma="Angela"]? @1[lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"];'
    )
    query_2, s_query_2, anchors_2 = preprocess_query(query)

    query = (
        '@0[lemma="Angela"]? @1[lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"] within tweet;'
    )
    query_3, s_query_3, anchors_3 = preprocess_query(query)

    query = (
        '@0[lemma="Angela"]? @1[lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"] within s'
    )
    query_4, s_query_4, anchors_4 = preprocess_query(query)

    assert(s_query_1 == s_query_2 is None)
    assert(s_query_3 == 'tweet')
    assert(s_query_4 == 's')
    assert(query_1 == query_2 == query_3 == query_4)
    assert(anchors_1 == anchors_2 == anchors_3 == anchors_4)


@pytest.mark.fold
def test_fold_items():
    items_aber = ['aber', 'äber', 'AbEr', 'ÄBER']
    items_francais = ['français', 'Fráncàis', 'FRA¢aiş']
    print([fold_item(item) for item in items_aber])
    print([fold_item(item) for item in items_francais])


def test_lines_raw():
    corpus = Corpus('SZ_2009_14')
    result = corpus.query(
        '[lemma="Volk*"] | [lemma="Bürger*"] | [lemma="Wähler*"]',
        context=None, s_context='s'
    )
    conc = corpus.concordance(result)
    df_lines = conc.lines(form='raw')
    print(df_lines)


def test_lines_simple():
    corpus = Corpus('SZ_2009_14')
    result = corpus.query(
        '[lemma="Volk*"] | [lemma="Bürger*"] | [lemma="Wähler*"]',
        context=None, s_context='s'
    )
    conc = corpus.concordance(result)
    df_lines = conc.lines(form='simple')
    print(df_lines)


def test_lines_kwic():
    corpus = Corpus('SZ_2009_14')
    result = corpus.query(
        '[lemma="Volk*"] | [lemma="Bürger*"] | [lemma="Wähler*"]',
        context=None, s_context='s'
    )
    conc = corpus.concordance(result)
    df_lines = conc.lines(form='kwic')
    print(df_lines)


def test_lines_dataframes():
    corpus = Corpus('SZ_2009_14')
    result = corpus.query(
        '[lemma="Volk*"] | [lemma="Bürger*"] | [lemma="Wähler*"]',
        context=None, s_context='s'
    )
    conc = corpus.concordance(result)
    df_lines = conc.lines(form='dataframes')
    print(df_lines)


def test_lines_extended():
    corpus = Corpus('SZ_2009_14')
    result = corpus.query(
        '[lemma="Volk*"] | [lemma="Bürger*"] | [lemma="Wähler*"]',
        context=None, s_context='s'
    )
    conc = corpus.concordance(result)
    df_lines = conc.lines(form='extended')
    print(df_lines)


@pytest.mark.now
def test_merge_intervals():
    intervals = [[1, 3], [2, 4], [5, 9], [6, 10]]
    merge = merge_intervals(intervals)
    print(merge)
