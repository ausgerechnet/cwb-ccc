from ccc.cwb import CWBEngine
from ccc.utils import time_it
import pandas as pd
import pytest


# global settings
registry_path = "/home/ausgerechnet/corpora/cwb/registry/"
context = 50

# BREXIT CORPUS
corpus_name = "BREXIT_V20190522"
lib_path = "/home/ausgerechnet/projects/spheroscope/app/instance-stable/lib/"
s_break = 'tweet'
query = '[lemma="test"]'
query_wordlist = (
    '<np>[pos_simple!="P"] []*</np> [lemma = $verbs_cause] [pos_simple="R"]? '
    '<np>[]*</np> (<np>[]*</np> | <vp>[]*</vp> | <pp>[]*</pp>)+'
)

# SZ CORPUS
corpus_name_2 = 'SZ_FULL'
s_break_2 = 's'
query_2 = '[lemma="Angela"] [lemma="Merkel"] | [lemma="CDU"]'
anchor_query_2 = (
    '@0[lemma="Angela"]? @1[lemma="Merkel"] '
    '[word="\\("] @2[lemma="CDU"] [word="\\)"]'
)


# tests
@pytest.mark.engine_init
def test_engine_init():
    engine = CWBEngine(corpus_name, registry_path, lib_path)
    assert(engine.corpus_size > 1000)


@pytest.mark.engine_init
def test_engine_init_alt():
    engine = CWBEngine(corpus_name_2, registry_path)
    assert(engine.corpus_size > 1000)


@pytest.mark.engine_descriptor
def test_engine_descriptor():
    engine = CWBEngine(corpus_name_2, registry_path)
    assert(type(engine.corpus_attributes) == pd.DataFrame)


@pytest.mark.engine_node
def test_df_node_from_query():
    engine = CWBEngine(corpus_name, registry_path, lib_path, cache_path=None)
    df_node = engine.df_node_from_query(
        query,
        s_break,
        context
    )
    assert(type(df_node) == pd.DataFrame)
    assert(all(x in df_node.columns for x in ['region_start',
                                              'region_end']))


@pytest.mark.engine_anchor
def test_df_anchor_from_query():
    engine = CWBEngine(corpus_name_2, registry_path, cache_path=None)
    df_node = engine.df_anchor_from_query(
        anchor_query_2,
        s_break_2,
        context
    )
    assert(type(df_node) == pd.DataFrame)
    assert(all(x in df_node.columns for x in [0,
                                              1,
                                              'region_start',
                                              'region_end']))


@pytest.mark.subcorpus
def test_subcorpus_from_query():
    engine = CWBEngine(corpus_name, registry_path)
    assert(int(engine.cqp.Exec('size SBCRPS1')) == 0)
    engine.subcorpus_from_query(
        "[lemma='test*']",
        'SBCRPS1'
    )
    assert(int(engine.cqp.Exec('size SBCRPS1')) > 0)


@pytest.mark.subcorpus
def test_subcorpus_from_df():
    engine = CWBEngine(corpus_name, registry_path)
    assert(int(engine.cqp.Exec('size SBCRPS2')) == 0)
    df = engine.df_node_from_query(query, 'tweet')
    engine.subcorpus_from_df(
        df,
        'SBCRPS2'
    )
    assert(int(engine.cqp.Exec('size SBCRPS2')) > 0)


@pytest.mark.subcorpus
def test_deactivate_subcorpus():

    engine = CWBEngine(corpus_name, registry_path)
    df1 = engine.df_node_from_query(query, 'tweet')

    # activation
    engine.subcorpus_from_query("[lemma='be'] expand to tweet", 'SBCRPS3')
    df2 = engine.df_node_from_query(query, 'tweet')

    # deactivation
    engine.deactivate_subcorpus()
    df3 = engine.df_node_from_query(query, 'tweet')

    assert(len(df1) == len(df3))
    assert(len(df1) > len(df2))


@pytest.mark.anchor_subcorpus
def test_subcorpus_anchor():
    engine = CWBEngine(corpus_name_2, registry_path, lib_path)
    df1 = engine.df_node_from_query("[lemma='Angela']", s_break_2)
    df_anchor = engine.df_node_from_query(
        anchor_query_2,
        s_break_2
    )
    engine.subcorpus_from_df(
        df_anchor,
        'SBCRPS5'
    )
    df2 = engine.df_node_from_query("[lemma='Angela']", s_break_2)
    assert(len(df1) > len(df_anchor) > len(df2))


@pytest.mark.cpos2token
def test_cpos2token():
    engine = CWBEngine(corpus_name_2, registry_path)
    token = engine.cpos2token(124345)
    assert(type(token) == str)


@pytest.mark.marginals
@pytest.mark.cwb_counts
def test_marginals():
    engine = CWBEngine(corpus_name_2, registry_path)
    counts = engine.marginals(["Angela", "Merkel", "CDU"])
    assert(len(counts) == 3)


@pytest.mark.cwb_counts
def test_item_freq_subcorpora():
    engine = CWBEngine(corpus_name_2, registry_path)

    # whole corpus
    counts1 = engine.marginals(["Angela", "Merkel", "CDU"])
    counts2 = engine.item_freq(["Angela", "Merkel", "CDU"])
    assert(counts1.equals(counts2))

    # subcorpus
    engine.subcorpus_from_query('[lemma="Bundesregierung"] expand to s',
                                'Bundesregierung')

    counts1 = engine.marginals(["Angela", "Merkel", "CDU"])
    counts2 = engine.item_freq(["Angela", "Merkel", "CDU"])
    assert(counts1.loc['Angela', 'freq'] > counts2.loc['Angela', 'freq'])

    # whole corpus
    engine.deactivate_subcorpus()
    counts1 = engine.marginals(["Angela", "Merkel", "CDU"])
    counts2 = engine.item_freq(["Angela", "Merkel", "CDU"])
    assert(counts1.equals(counts2))


@pytest.mark.cwb_counts
def test_item_freq_mwu():
    engine = CWBEngine(corpus_name_2, registry_path)

    # whole corpus
    counts = engine.item_freq(["Horst Seehofer", r"( CSU )", "CSU", "WES324", "CSU"])
    assert(counts.loc['Horst Seehofer', 'freq'] > 0)
    assert(counts.loc[r'( CSU )', 'freq'] > 0)
    assert(counts.loc['WES324', 'freq'] == 0)
    assert(counts.loc['CSU', 'freq'].iloc[0] > counts.loc[r'( CSU )', 'freq'])
    assert(counts.loc['CSU', 'freq'].iloc[0] == counts.loc['CSU', 'freq'].iloc[1])


@pytest.mark.cwb_counts_speed
@time_it
def test_item_freq_1():
    engine = CWBEngine(corpus_name_2, registry_path)
    engine.item_freq(["Horst Seehofer", r"( CSU )", "CSU",
                      "WES324", "CSU"])


@time_it
@pytest.mark.cwb_counts_speed
def test_item_freq_2():
    engine = CWBEngine(corpus_name_2, registry_path)
    engine.item_freq_2(["Horst Seehofer", r"( CSU )", "CSU",
                        "WES324", "CSU"])


@pytest.mark.subcorpus2
def test_subcorpus_2():
    engine = CWBEngine(corpus_name, registry_path)
    df = engine.df_node_from_query(query, 'tweet')
    engine.subcorpus_from_df(
        df,
        'SBCRPS2'
    )


@pytest.mark.s_ids
def test_get_s_ids():
    engine = CWBEngine(corpus_name, registry_path, meta_s='tweet_id')
    df_node = engine.df_node_from_query("[lemma='make']", s_break='tweet')
    assert('s_id' in df_node.columns)
    meta_regions = engine.get_meta_regions()
    assert('match' in meta_regions.columns)
