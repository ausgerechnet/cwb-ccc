from ccc.cwb import CWBEngine
from ccc.concordances import Concordance
import pytest
import pandas as pd


# registry path
registry_path = "/home/ausgerechnet/corpora/cwb/registry/"
corpus_name = "SZ_FULL"


@pytest.mark.concordance_simple
def test_query_default():
    engine = CWBEngine(corpus_name, registry_path, s_meta='text_id', cache_path=None)
    query = (
        '[lemma="Angela"]? [lemma="Merkel"] '
        '[word="\\("] [lemma="CDU"] [word="\\)"]'
    )
    concordance = Concordance(engine, query, s_break='s')
    lines = concordance.lines(p_show=[], order='random', cut_off=100)
    assert(len(concordance.breakdown) > 0)
    assert(type(concordance.meta) == pd.DataFrame)
    assert(len(lines) == 100)


@pytest.mark.concordance
@pytest.mark.concordance_anchors
def test_anchor_query_default():
    engine = CWBEngine(corpus_name, registry_path)
    query = (
        '@0[lemma="Angela"]? @1[lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"]'
    )
    concordance = Concordance(engine, query, s_break='s')
    lines = concordance.lines()
    for df in lines.values():
        assert(all(x in set(df['anchor']) for x in [0, 1, 2]))


@pytest.mark.skip
@pytest.mark.concordance_many
def test_query_many():
    engine = CWBEngine(corpus_name, registry_path, s_meta='text_id', cache_path=None)
    query = ("[lemma='und']")
    concordance = Concordance(engine, query)
    lines = concordance.lines(p_show=['lemma', 'pos'], order='random', cut_off=100)
    assert(concordance.breakdown is None)
    assert(type(concordance.meta) == pd.DataFrame)
    assert(len(lines) == 100)
