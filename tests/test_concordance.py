from ccc.cwb import CWBEngine
from ccc.concordances import Concordance
import pytest


# registry path
registry_path = "/home/ausgerechnet/corpora/cwb/registry/"
corpus_name = "SZ_FULL"


@pytest.mark.concordance_simple
def test_query_default():
    engine = CWBEngine(corpus_name, registry_path, cache_path=None)
    concordance = Concordance(engine,
                              order='last',
                              cut_off=10,
                              context=5,
                              s_break='s')
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    c = concordance.query(query)
    assert(len(c) == 10)


@pytest.mark.concordance
@pytest.mark.concordance_anchors
def test_anchor_query_default():
    engine = CWBEngine(corpus_name, registry_path)
    concordance = Concordance(engine,
                              order='last',
                              cut_off=10,
                              context=5,
                              s_break='s')
    query = (
        '@0[lemma="Angela"]? @1[lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"]'
    )
    c = concordance.query(query)
    assert(len(c) == 10)


@pytest.mark.concordance
@pytest.mark.concordance_anchors
def test_anchor_query_False():
    engine = CWBEngine(corpus_name, registry_path)
    concordance = Concordance(engine,
                              order='last',
                              cut_off=10,
                              context=5,
                              s_break='s')
    query = (
        '@0[lemma="Angela"]? @1[lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"]'
    )
    c = concordance.query(query, anchored=False)
    assert(len(c) == 10)


@pytest.mark.concordance
@pytest.mark.concordance_anchors
def test_anchor_query_True():
    engine = CWBEngine(corpus_name, registry_path)
    concordance = Concordance(engine,
                              order='last',
                              cut_off=10,
                              context=5,
                              s_break='s')
    query = (
        '@0[lemma="Angela"]? @1[lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"]'
    )
    c = concordance.query(query, anchored=True)
    # print(c)
    assert(len(c) == 10)
