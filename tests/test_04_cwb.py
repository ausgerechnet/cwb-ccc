from glob import glob

import pandas as pd
import pytest

from ccc import Corpora, Corpus, SubCorpus

from .conftest import DATA_PATH


def get_corpus(corpus_settings, data_path=DATA_PATH, lib=True):

    if lib:
        lib_path = corpus_settings.get('lib_path', None)
    else:
        lib_path = None

    return Corpus(
        corpus_settings['corpus_name'],
        registry_path=corpus_settings['registry_path'],
        lib_path=lib_path,
        data_path=data_path
    )


###############################################
# INIT ########################################
###############################################

@pytest.mark.init
def test_corpora(germaparl):
    corpora = Corpora(registry_path=germaparl['registry_path'])
    assert type(corpora.show()) == pd.DataFrame
    assert "GERMAPARL1386" in corpora.show().index


@pytest.mark.init
def test_corpus(germaparl):
    corpus = get_corpus(germaparl)
    assert corpus.corpus_size > 1000


@pytest.mark.init
def test_get_corpus(germaparl):
    corpus = get_corpus(germaparl)
    assert corpus.corpus_size > 1000


@pytest.mark.init
def test_corpus_descriptor(germaparl):
    corpus = get_corpus(germaparl)
    assert isinstance(corpus.available_attributes(), pd.DataFrame)


@pytest.mark.init
def test_data_dir(germaparl):
    get_corpus(germaparl, lib=False, data_path=None)
    paths = glob("/tmp/ccc-*")
    assert len(paths) >= 1


#####################################################
# MACROS AND WORDLISTS ##############################
#####################################################
@pytest.mark.init
def test_macros(germaparl):
    corpus = get_corpus(germaparl, lib=False)
    assert '/np(0)' not in corpus.available_macros()
    corpus = get_corpus(germaparl, lib=True)
    assert '/np(0)' in corpus.available_macros()


@pytest.mark.init
def test_wordlists(germaparl):
    corpus = get_corpus(germaparl, lib=True)
    assert "$parties" in corpus.available_wordlists()


#####################################################
# ATTRIBUTES ########################################
#####################################################

@pytest.mark.attributes
def test_cpos2patt(germaparl):
    corpus = get_corpus(germaparl)
    token = corpus.cpos2patts(124345)
    assert isinstance(token, tuple)
    assert token[0] == 'gilt'


@pytest.mark.attributes
def test_cpos2patts(germaparl):
    corpus = get_corpus(germaparl)
    token = corpus.cpos2patts(124345, ['word', 'pos'])
    assert isinstance(token, tuple)
    assert token == ('gilt', 'VVFIN')


#####################################################
# MARGINALS #########################################
#####################################################
@pytest.mark.marginals
def test_marginals_word(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.marginals(["Merkel", "Seehofer", "gehen"])
    assert df['freq']['gehen'] == 44
    assert len(df) == 3


@pytest.mark.marginals
def test_marginals_lemma(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.marginals(["Merkel", "Seehofer", "gehen"], p_atts=['lemma'])
    assert df['freq']['gehen'] == 224
    assert len(df) == 3


@pytest.mark.marginals
def test_marginals_pattern(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.marginals(["Merkel", "Seehofer", "geh.*"], pattern=True)
    assert df['freq']['geh.*'] == 310


@pytest.mark.marginals
def test_marginals_complex(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus._marginals_complex(
        [("gehen", "VVFIN"), ("Seehofer", "NE"), ("Merkel", "NE")],
        ["lemma", "pos"]
    )
    assert len(df) == 3
    assert df['freq']['gehen VVFIN'] == 186


################################################
# CREATING DUMPS ###############################
################################################

@pytest.mark.dump
def test_dump_from_s_att(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.dump_from_s_att('text_id')
    assert df.iloc[0]['text_id'] == "i13_86_1_1"


@pytest.mark.dump
def test_dump_from_s_att_wo(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.dump_from_s_att('p')
    assert df.shape[0] == 7332


@pytest.mark.dump
def test_dump_from_query(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.dump_from_query(
        query=germaparl['query'],
        s_query=germaparl['s_query'],
        match_strategy='standard'
    )
    assert isinstance(df_dump, pd.DataFrame)
    assert df_dump.shape[0] == 30


@pytest.mark.dump
def test_dump_from_query_1(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.dump_from_query(
        query='[lemma="Horst"] @1[lemma="Seehofer"]',
        anchors=[1],
        match_strategy='longest'
    )
    assert isinstance(df_dump, pd.DataFrame)
    assert len(df_dump) == 11
    assert 1 in df_dump.columns


@pytest.mark.dump
def test_dump_from_query_anchors(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.dump_from_query(
        query=germaparl['query_anchor'],
        s_query=germaparl['s_query'],
        anchors=germaparl['anchors'],
        match_strategy='standard'
    )
    assert isinstance(df_dump, pd.DataFrame)
    assert df_dump.shape[0] == 30
    assert all(elem in df_dump.columns for elem in germaparl['anchors'])


@pytest.mark.dump
def test_dump_from_query_anchors_implementation(germaparl):

    corpus = get_corpus(germaparl)
    df_dump1 = corpus.dump_from_query(
        query=germaparl['query_anchor'],
        s_query=germaparl['s_query'],
        anchors=germaparl['anchors'],
        match_strategy='standard'
    )

    corpus = get_corpus(germaparl)
    df_dump2 = corpus.dump_from_query(
        query=germaparl['query_anchor'],
        s_query=germaparl['s_query'],
        anchors=germaparl['anchors'],
        match_strategy='standard',
        cwb_version={'minor': 4, 'patch': 16}
    )

    assert df_dump1.equals(df_dump2)


#################################################
# WORKING ON DUMPS ##############################
#################################################

@pytest.mark.dumpp
def test_dump2satt(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.dump_from_query(
        query=germaparl['query'],
        s_query=germaparl['s_query'],
        match_strategy='standard'
    )
    df_dump['test'] = None
    df = corpus.dump2satt(df_dump, germaparl['s_meta'])
    assert 'test' in df.columns
    assert len(df) == 30
    assert df.iloc[0]['text_id_span'] == 10628


@pytest.mark.dumpp
def test_dump2satt_2(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.dump_from_query(
        query=germaparl['query'],
        s_query=germaparl['s_query'],
        match_strategy='longest'
    )
    df = corpus.dump2satt(df_dump, 'p')
    assert df.iloc[0]['p_cwbid'] == 456


@pytest.mark.dumpp
def test_dump2context(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.dump_from_query(
        query=germaparl['query'],
        s_query=germaparl['s_query'],
        match_strategy='standard'
    )
    df_dump = corpus.dump2context(df_dump, 20, 20, 's')
    assert all(
        elem in df_dump.columns for elem in ['context', 'contextid', 'contextend']
    )


@pytest.mark.dumpp
def test_dump2context2(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.dump_from_query(
        query=germaparl['query'],
        s_query=germaparl['s_query'],
        match_strategy='standard'
    )
    df_dump = corpus.dump2context(df_dump, 20, 20, 'text_id')
    assert all(elem in df_dump.columns for elem in [
        'context', 'contextid', 'contextend', 'text_id_cwbid', 'text_id'
    ])


@pytest.mark.dumpp
def test_dump2context3(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.dump_from_query(
        query=germaparl['query'],
        s_query=germaparl['s_query'],
        match_strategy='longest'
    )
    df_dump = corpus.dump2context(df_dump, 20, 20, 's')
    assert all(elem in df_dump.columns for elem in [
        'context', 'contextid', 'contextend', 's_cwbid'
    ])


@pytest.mark.dumpp
def test_dump2context4(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.dump_from_query(
        query=germaparl['query'],
        s_query=germaparl['s_query'],
        match_strategy='longest'
    )
    df_dump = corpus.dump2context(df_dump, None, 5, 'text_id')
    assert all(elem in df_dump.columns for elem in [
        'context', 'contextid', 'contextend', 'text_id_cwbid', 'text_id'
    ])


@pytest.mark.dumpp
def test_dump2patt(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.dump_from_query(
        query=germaparl['query'],
        s_query=germaparl['s_query'],
        match_strategy='standard'
    )
    # df = corpus.dump2context(df_dump, 20, 20, 'text_id')
    df_dump = corpus.dump2patt(df_dump)
    assert 'word' in df_dump.columns


@pytest.mark.dumpp
def test_dump2patt2(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.dump_from_query(
        query=germaparl['query'],
        s_query=germaparl['s_query'],
        match_strategy='standard'
    )
    df_dump = corpus.dump2context(df_dump, 20, 20, 'text_id')
    df_dump = corpus.dump2patt(df_dump, start='context', end='contextend')
    assert 'word' in df_dump.columns


#################################################
# QUERY ALIASES #################################
#################################################

@pytest.mark.query
def test_query_fail(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.query('"tesdsf"').df
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0


@pytest.mark.query
def test_query_context_1(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.query(
        cqp_query=germaparl['query_anchor'],
        context=None
    ).df
    assert isinstance(df, pd.DataFrame)
    columns = germaparl['anchors'] + ['context', 'contextend']
    assert all(elem in df.columns for elem in columns)


@pytest.mark.query
def test_query_context_2(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.query(
        cqp_query=germaparl['query_anchor'],
        context_left=10,
        context=15
    ).df
    assert isinstance(df, pd.DataFrame)
    columns = germaparl['anchors'] + ['context', 'contextend']
    assert all(elem in df.columns for elem in columns)


@pytest.mark.query
def test_query_context_3(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.query(
        cqp_query=germaparl['query_anchor'],
        context=None,
        context_break='s'
    ).df
    assert isinstance(df, pd.DataFrame)
    columns = germaparl['anchors'] + ['contextid', 'context', 'contextend']
    assert all(elem in df.columns for elem in columns)


@pytest.mark.query
def test_query_context_4(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.query(
        cqp_query=germaparl['query_anchor'],
        context=10,
        context_break='s'
    ).df
    assert isinstance(df, pd.DataFrame)
    columns = germaparl['anchors'] + ['contextid', 'context', 'contextend']
    assert all(elem in df.columns for elem in columns)


@pytest.mark.query
def test_query_context_5(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.query(
        cqp_query='[lemma="Horst"]',
        context=10,
        context_break='s'
    ).df
    assert isinstance(df, pd.DataFrame)


@pytest.mark.query
def test_query_lib(germaparl):

    corpus = get_corpus(germaparl)

    nps = corpus.query('/np[]', context=0, match_strategy='longest')

    assert len(nps.df) == 34432
    parties = corpus.query('$parties', context=0)
    assert len(parties.df) == 2140

    dump = corpus.query(
        cqp_query=germaparl['query_lib'],
        context_break=germaparl['s_query'],
        match_strategy='longest'
    )
    assert isinstance(dump.df, pd.DataFrame)
    assert len(dump.df) == 16


def test_query_anchor(germaparl):

    corpus = get_corpus(germaparl)
    query = r'@1[pos="V.*"] @2"\." </s>'
    d = corpus.query(
        query, context_left=3, context_right=None, context_break='s',
        corrections={2: 1}
    )
    assert (d.df[2] == d.df['contextend']).all()


def test_ccc_quick_query(germaparl):

    corpus = get_corpus(germaparl)

    topic_query = '[lemma="die"]'
    s_context = 's'
    filter_queries = {
        'CSU': '[lemma="CSU"]',
        'CDU': '[lemma="CDU"]'
    }

    identifier = corpus.quick_query(
        s_context=s_context,
        topic_query=topic_query,
        filter_queries=filter_queries.values()
    )

    assert identifier in corpus.show_nqr()['subcorpus'].values


def test_ccc_quick_query_2(germaparl):

    corpus = get_corpus(germaparl)

    s_context = 's'
    queries = {
        'Angela': '[lemma="Angela"]',
        'CSU': '[lemma="CSU"]',
        'CDU': '[lemma="CDU"]'
    }

    identifier = corpus.quick_query(
        s_context=s_context,
        filter_queries=queries.values()
    )

    assert identifier in corpus.show_nqr()['subcorpus'].values


#####################################################
# SUBCORPORA ########################################
#####################################################

@pytest.mark.subcorpus
def test_activate_subcorpus(germaparl):

    corpus = get_corpus(germaparl)

    df1 = corpus.dump_from_query(
        "[lemma='Seehofer']"
    )
    corpus.query(
        "[lemma='Horst'] expand to s",
        name='Horst'
    ).df

    horst = corpus.subcorpus('Horst')
    df2 = horst.dump_from_query(
        "[lemma='Seehofer']"
    )
    assert len(df1) > len(df2)


@pytest.mark.subcorpus
def test_deactivate_subcorpus(germaparl):

    corpus = get_corpus(germaparl)
    # query corpus
    df1 = corpus.dump_from_query(
        '[lemma="die"]',
        germaparl['s_query']
    )

    # query subcorpus
    sein = corpus.query(
        cqp_query="[lemma='sein'] expand to s",
        name='Sein'
    )
    df2 = sein.dump_from_query(
        '[lemma="die"]',
        germaparl['s_query']
    )

    # query corpus
    df3 = corpus.dump_from_query(
        '[lemma="die"]',
        germaparl['s_query']
    )

    assert len(df1) == len(df3)
    assert len(df1) > len(df2)


@pytest.mark.subcorpus
def test_create_cached_nqr(germaparl):

    # problem: if a query runs once without having been given a name,
    # the CQP dump (NQR) is not saved to disk
    # if the same query runs again *with a name*, it should be saved to disk

    corpus = get_corpus(germaparl)

    subcorpus = corpus.query('[lemma="jetzt"]')
    assert isinstance(subcorpus, SubCorpus)
    # assert "Jetzt" not in corpus.show_nqr().values

    subcorpus = corpus.query('[lemma="jetzt"]', name='Jetzt')
    assert isinstance(subcorpus, SubCorpus)
    # assert "Jetzt" in corpus.show_nqr().values


@pytest.mark.subcorpus
def test_nqr_from_s_att(germaparl):

    corpus = get_corpus(germaparl)
    corpus.query_s_att("text_party", values={"CDU", "CSU"}, name="Union")
    assert "Union" in corpus.show_nqr().values
    assert isinstance(corpus.subcorpus("Union"), SubCorpus)


@pytest.mark.subcorpus
def test_subcorpus(germaparl):

    corpus = get_corpus(germaparl)
    subcorpus = corpus.query(
        cqp_query='[lemma="und"]',
        context_break=germaparl['s_query'],
        name='Test'
    )

    # init
    assert isinstance(subcorpus, SubCorpus)
    assert len(subcorpus.df) == 2880
    assert all(elem in subcorpus.df.columns for elem in
               ["s_cwbid", "s_span", "s_spanend", "contextid", "context", "contextend"])


@pytest.mark.subcorpus
def test_subcorpus_keywords(germaparl):

    corpus = get_corpus(germaparl)
    subcorpus = corpus.query(
        cqp_query='[lemma="und"]',
        context_break=germaparl['s_query'],
        name='Test'
    )

    # keywords
    assert len(subcorpus.keywords()) == 1
    assert "und" in subcorpus.keywords().index


@pytest.mark.subcorpus
def test_subcorpus_collocates(germaparl):

    corpus = get_corpus(germaparl)
    subcorpus = corpus.query(
        cqp_query='[lemma="und"]',
        context_break=germaparl['s_query'],
        name='Test'
    )
    assert len(subcorpus.collocates(window=1)) == 71
    assert len(subcorpus.collocates(window=10)) == 57


@pytest.mark.subcorpus
def test_subcorpus_context(germaparl):

    corpus = get_corpus(germaparl)
    subcorpus = corpus.query(
        cqp_query='[lemma="und"]',
        context_break=germaparl['s_query'],
        name='Test'
    )
    assert len(subcorpus.collocates(window=10)) == 57
    assert len(subcorpus.collocates(window=20)) == 61
    # collocates
    subcorpus = subcorpus.set_context(20)
    assert len(subcorpus.collocates()) == 54
    assert len(subcorpus.collocates(window=10)) == 56


@pytest.mark.subcorpus
def test_subcorpus_marginals(germaparl):

    corpus = get_corpus(germaparl)
    assert len(corpus.marginals()) == 14034
    subcorpus = corpus.query(
        cqp_query='[lemma="und"]',
        context_break=germaparl['s_query'],
        name='Test'
    )
    assert len(subcorpus.marginals()) == 2


@pytest.mark.subcorpus
def test_subcorpus_query_s_att(germaparl):

    corpus = get_corpus(germaparl)
    black = corpus.query_s_att("text_party", values={"CDU", "CSU"}, name="Union")
    assert "Union" in corpus.show_nqr().values
    assert isinstance(black, SubCorpus)

    interjection = corpus.query_s_att("p_type", values={"interjection"})
    black_interjection = black.query_s_att("p_type", values={"interjection"})
    assert len(black.matches()) > len(interjection.matches()) > len(black_interjection.matches())
