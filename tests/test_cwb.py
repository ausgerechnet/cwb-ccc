from ccc import Corpus
import pandas as pd
import pytest


@pytest.mark.corpus_init
def test_corpus(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'],
                    registry_path=sz_corpus['registry_path'])
    assert(corpus.corpus_size > 1000)


@pytest.mark.corpus_init
def test_corpus_lib(brexit_corpus):
    corpus = Corpus(brexit_corpus['corpus_name'],
                    lib_path=brexit_corpus['lib_path'],
                    registry_path=brexit_corpus['registry_path'])
    assert(corpus.corpus_size > 1000)


@pytest.mark.corpus_init
@pytest.mark.cqp3
def test_corpus_cqp3(sz_corpus):
    cqp3 = "/home/ausgerechnet/tools/cwb-software/cwb-3.0.0/bin/cqp"
    corpus = Corpus(sz_corpus['corpus_name'],
                    cqp_bin=cqp3,
                    registry_path=sz_corpus['registry_path'])
    assert(corpus.corpus_size > 1000)


@pytest.mark.corpus_init
@pytest.mark.cqp3
def test_corpus_cqp3_lib(brexit_corpus):
    cqp3 = "/home/ausgerechnet/tools/cwb-software/cwb-3.0.0/bin/cqp"
    corpus = Corpus(brexit_corpus['corpus_name'],
                    lib_path=brexit_corpus['lib_path'],
                    cqp_bin=cqp3,
                    registry_path=brexit_corpus['registry_path'])
    assert(corpus.corpus_size > 1000)


@pytest.mark.corpus_init
def test_corpus_descriptor(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    assert(type(corpus.attributes_available) == pd.DataFrame)


@pytest.mark.df_dump
def test_df_dump_from_query(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'],
                    data_path=None)
    df_dump = corpus.df_dump_from_query(
        query=sz_corpus['query'],
        s_query=sz_corpus['s_query'],
        match_strategy='standard'
    )
    assert(type(df_dump) == pd.DataFrame)
    assert(df_dump.shape[0] > 99)


@pytest.mark.df_dump
def test_df_dump_from_query_lib(brexit_corpus):
    corpus = Corpus(brexit_corpus['corpus_name'],
                    lib_path=brexit_corpus['lib_path'],
                    data_path=None)
    df_dump = corpus.df_dump_from_query(
        query=brexit_corpus['query_lib'],
        s_query=brexit_corpus['s_query'],
        match_strategy='longest'
    )
    assert(type(df_dump) == pd.DataFrame)
    assert(df_dump.shape[0] > 99)


@pytest.mark.df_dump
def test_df_dump_from_query_1(brexit_corpus):
    corpus = Corpus(brexit_corpus['corpus_name'])
    df_dump = corpus.df_dump_from_query(
        query='[lemma="angela"] @1[lemma="merkel"]',
        match_strategy='longest'
    )
    assert(type(df_dump) == pd.DataFrame)
    assert(df_dump.shape[0] > 99)


@pytest.mark.df_dump
def test_df_dump_from_query_anchors(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    df_dump = corpus.df_dump_from_query(
        query=sz_corpus['anchor_query'],
        s_query=sz_corpus['s_query'],
        anchors=sz_corpus['anchors'],
        match_strategy='standard'
    )
    assert(type(df_dump) == pd.DataFrame)
    assert(df_dump.shape[0] > 99)
    assert(all(elem in df_dump.columns for elem in sz_corpus['anchors']))


@pytest.mark.subcorpus
def test_subcorpus_from_query(brexit_corpus):
    corpus = Corpus(brexit_corpus['corpus_name'])
    assert(int(corpus.cqp.Exec('size SBCRPS1')) == 0)
    corpus.subcorpus_from_query(
        query="[lemma='test*']",
        name='SBCRPS1'
    )
    assert(int(corpus.cqp.Exec('size SBCRPS1')) > 0)


@pytest.mark.subcorpus
def test_subcorpus_from_df(brexit_corpus):
    corpus = Corpus(brexit_corpus['corpus_name'])
    assert(int(corpus.cqp.Exec('size SBCRPS2')) == 0)
    df = corpus.df_dump_from_query(
        query=brexit_corpus['query']
    )
    corpus.subcorpus_from_dump(
        df_dump=df,
        name='SBCRPS2'
    )
    assert(int(corpus.cqp.Exec('size SBCRPS2')) > 0)


@pytest.mark.subcorpus
def test_deactivate_subcorpus(brexit_corpus):

    corpus = Corpus(brexit_corpus['corpus_name'])
    df1 = corpus.df_dump_from_query(
        brexit_corpus['query'], brexit_corpus['s_query']
    )

    # activation
    corpus.subcorpus_from_query(
        query="[lemma='be'] expand to tweet",
        name='SBCRPS3'
    )
    corpus.activate_subcorpus('SBCRPS3')

    df2 = corpus.df_dump_from_query(
        brexit_corpus['query'], brexit_corpus['s_query']
    )

    # deactivation
    corpus.activate_subcorpus()
    df3 = corpus.df_dump_from_query(
        brexit_corpus['query'], brexit_corpus['s_query']
    )

    assert(len(df1) == len(df3))
    assert(len(df1) > len(df2))


@pytest.mark.subcorpus
def test_subcorpus_anchor(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    df1 = corpus.df_dump_from_query(
        "[lemma='Angela']", sz_corpus['s_break']
    )
    df_anchor = corpus.df_dump_from_query(
        sz_corpus['anchor_query'],
        sz_corpus['s_query'],
        sz_corpus['anchors']
    )
    corpus.subcorpus_from_dump(
        df_dump=df_anchor,
        name='SBCRPS5'
    )
    corpus.activate_subcorpus('SBCRPS5')
    df2 = corpus.df_dump_from_query(
        "[lemma='Angela']", None
    )
    assert(len(df1) > len(df_anchor) > len(df2))


@pytest.mark.lexicalization
def test_cpos2patt(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    token = corpus.cpos2patts(124345)
    assert(type(token) == tuple)


@pytest.mark.lexicalization
def test_cpos2patts(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    token = corpus.cpos2patts(124345, ['word', 'pos'])
    assert(type(token) == tuple)


@pytest.mark.counts_now
def test_cpos2counts(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    counts = corpus.cpos2counts(list(range(1, 1000)), p_atts=['word'])
    assert(type(counts) == pd.DataFrame)


@pytest.mark.counts_now
def test_cpos2combo_counts(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    counts = corpus.cpos2counts(list(range(1, 1000)), p_atts=['lemma', 'pos'])
    assert(type(counts) == pd.DataFrame)
    assert(counts.index.names == ['lemma', 'pos'])


@pytest.mark.counts
def test_marginals(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    counts = corpus.marginals(["Angela", "Merkel", "CDU"])
    assert(len(counts) == 3)


@pytest.mark.skip
@pytest.mark.counts
def test_marginals_patterns(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    counts = corpus.marginals(["Ang*", "Merkel", "CDU"])
    assert(len(counts) == 3)
    counts = corpus.marginals(["Angel*", "Merkel", "CDU"], pattern=True)
    assert(len(counts) == 3)


@pytest.mark.cwb_counts
def test_item_freq_subcorpora(sz_corpus):

    corpus = Corpus(sz_corpus['corpus_name'])

    # whole corpus
    counts1 = corpus.marginals(["Angela", "Merkel", "CDU"])
    counts2 = corpus.item_freq(["Angela", "Merkel", "CDU"])
    assert(counts1.equals(counts2))

    # subcorpus
    corpus.subcorpus_from_query(query='[lemma="Bundesregierung"] expand to s',
                                name='Bundesregierung')
    corpus.activate_subcorpus('Bundesregierung')

    counts1 = corpus.marginals(["Angela", "Merkel", "CDU"])
    counts2 = corpus.item_freq(["Angela", "Merkel", "CDU"])
    assert(counts1.loc['Angela', 'freq'] > counts2.loc['Angela', 'freq'])

    # whole corpus
    corpus.activate_subcorpus()
    counts1 = corpus.marginals(["Angela", "Merkel", "CDU"])
    counts2 = corpus.item_freq(["Angela", "Merkel", "CDU"])
    assert(counts1.equals(counts2))


@pytest.mark.query
def test_query_context_1(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    df = corpus.query(
        query=sz_corpus['query_full'],
        context=None,
    )
    assert(type(df) == pd.DataFrame)
    columns = sz_corpus['anchors'] + ['context', 'contextend']
    assert(all(elem in df.columns for elem in columns))


@pytest.mark.query
def test_query_context_2(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    df = corpus.query(
        query=sz_corpus['query_full'],
        context_left=10,
        context=15,
    )
    assert(type(df) == pd.DataFrame)
    columns = sz_corpus['anchors'] + ['context', 'contextend']
    assert(all(elem in df.columns for elem in columns))


@pytest.mark.query
def test_query_context_3(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    df = corpus.query(
        query=sz_corpus['query_full'],
        context=None,
        s_context='s'
    )
    assert(type(df) == pd.DataFrame)
    columns = sz_corpus['anchors'] + ['context_id', 'context', 'contextend']
    assert(all(elem in df.columns for elem in columns))


@pytest.mark.query
def test_query_context_4(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    df = corpus.query(
        query=sz_corpus['query_full'],
        context=10,
        s_context='s'
    )
    assert(type(df) == pd.DataFrame)
    columns = sz_corpus['anchors'] + ['context_id', 'context', 'contextend']
    assert(all(elem in df.columns for elem in columns))


@pytest.mark.query
def test_query_meta(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    df = corpus.query(
        query=sz_corpus['query_full'],
        context=10,
        s_context='s',
        s_meta=['s', 'text', 'text_id']
    )
    assert(type(df) == pd.DataFrame)
    columns = sz_corpus['anchors'] + ['context_id', 'context', 'contextend']
    assert(all(elem in df.columns for elem in columns))


@pytest.mark.query
def test_query_meta_brexit(brexit_corpus):
    corpus = Corpus(brexit_corpus['corpus_name'])
    df = corpus.query(
        query='[lemma="nigel"]',
        context=10,
        s_context='tweet',
        s_meta=['ner_type', 'tweet_id', 'tweet']
    )
    assert(type(df) == pd.DataFrame)
    columns = ['context_id', 'context', 'contextend']
    columns += [a + '_CWBID' for a in ['ner_type', 'tweet_id', 'tweet']]
    columns += ['ner_type', 'tweet_id']
    assert(all(elem in df.columns for elem in columns))


@pytest.mark.s_extents
def test_get_s_extents(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    df = corpus.get_s_extents('text_id')
    print(df)


@pytest.mark.s_extents
def test_get_s_extents_2(brexit_corpus):
    corpus = Corpus(brexit_corpus['corpus_name'])
    df = corpus.get_s_extents('ner_type')
    print(df)


@pytest.mark.subcorpus
def test_subcorpus_from_s_att(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    corpus.subcorpus_from_s_att('text_id', ['A44320331'])


@pytest.mark.subcorpus
@pytest.mark.now
def test_subcorpus_from_s_att_wo(brexit_corpus):
    corpus = Corpus(brexit_corpus['corpus_name'])
    corpus.subcorpus_from_s_att('np', [True])


# @pytest.mark.cwb_counts
# def test_item_freq_mwu():
#     corpus = Corpus(corpus_name_2, registry_path)

#     # whole corpus
#     counts = corpus.item_freq(["Horst Seehofer", r"( CSU )", "CSU", "WES324", "CSU"])
#     assert(counts.loc['Horst Seehofer', 'freq'] > 0)
#     assert(counts.loc[r'( CSU )', 'freq'] > 0)
#     assert(counts.loc['WES324', 'freq'] == 0)
#     assert(counts.loc['CSU', 'freq'].iloc[0] > counts.loc[r'( CSU )', 'freq'])
#     assert(counts.loc['CSU', 'freq'].iloc[0] == counts.loc['CSU', 'freq'].iloc[1])


# @pytest.mark.cwb_counts_speed
# @time_it
# def test_item_freq_1():
#     corpus = Corpus(corpus_name_2, registry_path)
#     corpus.item_freq(["Horst Seehofer", r"( CSU )", "CSU",
#                       "WES324", "CSU"])


# @time_it
# @pytest.mark.cwb_counts_speed
# def test_item_freq_2():
#     corpus = Corpus(corpus_name_2, registry_path)
#     corpus.item_freq_2(["Horst Seehofer", r"( CSU )", "CSU",
#                         "WES324", "CSU"])


# @pytest.mark.subcorpus2
# def test_subcorpus_2():
#     corpus = Corpus(corpus_name, registry_path)
#     corpus.define_subcorpus('[lemma="make"]', name='make', activate=True)
#     corpus.activate_subcorpus()
#     corpus.define_subcorpus('[lemma="nigel"] expand to tweet',
#                             name='nigel', activate=True)
#     corpus.define_subcorpus('[lemma="make"]', name='make', activate=True)


# @pytest.mark.s_ids
# def test_get_s_ids():
#     corpus = Corpus(corpus_name, registry_path, s_meta='tweet_id')
#     df_node = corpus.df_node_from_query("[lemma='make']", s_query,
#                                         [], s_break, 20)
#     assert('s_id' in df_node.columns)
#     meta_regions = corpus.get_meta_regions()
#     assert('match' in meta_regions.columns)
