from ccc import Corpus
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
s_query = 'tweet'
query = '[lemma="test"]'
query_wordlist = (
    '<np>[pos_simple!="P"] []*</np> [lemma = $verbs_cause] [pos_simple="R"]? '
    '<np>[]*</np> (<np>[]*</np> | <vp>[]*</vp> | <pp>[]*</pp>)+'
)

# SZ CORPUS
corpus_name_2 = 'SZ_FULL'
s_query_2 = 's'
s_break_2 = 'text'
query_2 = '[lemma="Angela"] [lemma="Merkel"] | [lemma="CDU"]'
anchor_query_2 = (
    '@0[lemma="Angela"]? @1[lemma="Merkel"] '
    '[word="\\("] @2[lemma="CDU"] [word="\\)"]'
)
anchors_2 = [0, 1, 2]


# tests
@pytest.mark.corpus_init
def test_corpus_init():
    corpus = Corpus(corpus_name, registry_path, lib_path)
    assert(corpus.corpus_size > 1000)


@pytest.mark.corpus_init
def test_corpus_init_alt():
    corpus = Corpus(corpus_name_2, registry_path)
    assert(corpus.corpus_size > 1000)


@pytest.mark.corpus_descriptor
def test_corpus_descriptor():
    corpus = Corpus(corpus_name_2, registry_path)
    assert(type(corpus.attributes_available) == pd.DataFrame)


@pytest.mark.corpus_node
def test_df_node_from_query():
    corpus = Corpus(corpus_name, registry_path, lib_path, cache_path=None)
    df_node = corpus.df_node_from_query(
        query=query,
        s_query=s_query,
        anchors=[],
        s_break=s_break,
        context=context,
        match_strategy='standard'
    )
    assert(type(df_node) == pd.DataFrame)
    assert(all(x in df_node.columns for x in ['region_start',
                                              'region_end']))


@pytest.mark.corpus_anchor
def test_df_anchor_from_query():
    corpus = Corpus(corpus_name_2, registry_path, cache_path=None)
    df_node = corpus.df_node_from_query(
        query=anchor_query_2,
        s_query=s_query_2,
        anchors=anchors_2,
        s_break=s_break_2,
        context=context,
        match_strategy='standard'
    )
    assert(type(df_node) == pd.DataFrame)
    assert(all(x in df_node.columns for x in [0,
                                              1,
                                              'region_start',
                                              'region_end']))


@pytest.mark.subcorpus
def test_subcorpus_from_query():
    corpus = Corpus(corpus_name, registry_path)
    assert(int(corpus.cqp.Exec('size SBCRPS1')) == 0)
    corpus.define_subcorpus(
        query="[lemma='test*']",
        name='SBCRPS1'
    )
    assert(int(corpus.cqp.Exec('size SBCRPS1')) > 0)


@pytest.mark.subcorpus
def test_subcorpus_from_df():
    corpus = Corpus(corpus_name, registry_path)
    assert(int(corpus.cqp.Exec('size SBCRPS2')) == 0)
    df = corpus.df_node_from_query(
        query=query,
        s_query=s_query,
        anchors=[],
        s_break=s_break,
        context=context
    )
    corpus.define_subcorpus(
        df_node=df,
        name='SBCRPS2'
    )
    assert(int(corpus.cqp.Exec('size SBCRPS2')) > 0)


@pytest.mark.subcorpus
def test_deactivate_subcorpus():

    corpus = Corpus(corpus_name, registry_path)
    df1 = corpus.df_node_from_query(
        query, s_query, [], s_break, context=20
    )

    # activation
    corpus.define_subcorpus(query="[lemma='be'] expand to tweet",
                            name='SBCRPS3', activate=True)
    df2 = corpus.df_node_from_query(
        query, s_query, [], s_break, context=20
    )

    # deactivation
    corpus.activate_subcorpus()
    df3 = corpus.df_node_from_query(
        query, s_query, [], s_break, context=20
    )

    assert(len(df1) == len(df3))
    assert(len(df1) > len(df2))


@pytest.mark.anchor_subcorpus
def test_subcorpus_anchor():
    corpus = Corpus(corpus_name_2, registry_path, lib_path)
    df1 = corpus.df_node_from_query("[lemma='Angela']", s_query_2, [], s_break_2, 20)
    df_anchor = corpus.df_node_from_query(
        anchor_query_2,
        s_query_2,
        anchors_2,
        s_break_2,
        20
    )
    corpus.define_subcorpus(
        df_node=df_anchor,
        name='SBCRPS5',
        activate=True
    )
    df2 = corpus.df_node_from_query("[lemma='Angela']", None, [], s_break_2, 20)
    assert(len(df1) > len(df_anchor) > len(df2))


@pytest.mark.cpos2token
def test_cpos2token():
    corpus = Corpus(corpus_name_2, registry_path)
    token = corpus.cpos2token(124345)
    assert(type(token) == str)


@pytest.mark.marginals
@pytest.mark.cwb_counts
def test_marginals():
    corpus = Corpus(corpus_name_2, registry_path)
    counts = corpus.marginals(["Angela", "Merkel", "CDU"])
    assert(len(counts) == 3)


@pytest.mark.cwb_counts
def test_item_freq_subcorpora():

    corpus = Corpus(corpus_name_2, registry_path)

    # whole corpus
    counts1 = corpus.marginals(["Angela", "Merkel", "CDU"])
    counts2 = corpus.item_freq(["Angela", "Merkel", "CDU"])
    assert(counts1.equals(counts2))

    # subcorpus
    corpus.define_subcorpus(query='[lemma="Bundesregierung"] expand to s',
                            name='Bundesregierung', activate=True)

    counts1 = corpus.marginals(["Angela", "Merkel", "CDU"])
    counts2 = corpus.item_freq(["Angela", "Merkel", "CDU"])
    assert(counts1.loc['Angela', 'freq'] > counts2.loc['Angela', 'freq'])

    # whole corpus
    corpus.activate_subcorpus()
    counts1 = corpus.marginals(["Angela", "Merkel", "CDU"])
    counts2 = corpus.item_freq(["Angela", "Merkel", "CDU"])
    assert(counts1.equals(counts2))


@pytest.mark.cwb_counts
def test_item_freq_mwu():
    corpus = Corpus(corpus_name_2, registry_path)

    # whole corpus
    counts = corpus.item_freq(["Horst Seehofer", r"( CSU )", "CSU", "WES324", "CSU"])
    assert(counts.loc['Horst Seehofer', 'freq'] > 0)
    assert(counts.loc[r'( CSU )', 'freq'] > 0)
    assert(counts.loc['WES324', 'freq'] == 0)
    assert(counts.loc['CSU', 'freq'].iloc[0] > counts.loc[r'( CSU )', 'freq'])
    assert(counts.loc['CSU', 'freq'].iloc[0] == counts.loc['CSU', 'freq'].iloc[1])


@pytest.mark.cwb_counts_speed
@time_it
def test_item_freq_1():
    corpus = Corpus(corpus_name_2, registry_path)
    corpus.item_freq(["Horst Seehofer", r"( CSU )", "CSU",
                      "WES324", "CSU"])


@time_it
@pytest.mark.cwb_counts_speed
def test_item_freq_2():
    corpus = Corpus(corpus_name_2, registry_path)
    corpus.item_freq_2(["Horst Seehofer", r"( CSU )", "CSU",
                        "WES324", "CSU"])


@pytest.mark.subcorpus2
def test_subcorpus_2():
    corpus = Corpus(corpus_name, registry_path)
    corpus.define_subcorpus('[lemma="make"]', name='make', activate=True)
    corpus.activate_subcorpus()
    corpus.define_subcorpus('[lemma="nigel"] expand to tweet',
                            name='nigel', activate=True)
    corpus.define_subcorpus('[lemma="make"]', name='make', activate=True)


@pytest.mark.s_ids
def test_get_s_ids():
    corpus = Corpus(corpus_name, registry_path, s_meta='tweet_id')
    df_node = corpus.df_node_from_query("[lemma='make']", s_query,
                                        [], s_break, 20)
    assert('s_id' in df_node.columns)
    meta_regions = corpus.get_meta_regions()
    assert('match' in meta_regions.columns)
