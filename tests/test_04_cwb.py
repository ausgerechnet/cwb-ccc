from ccc import Corpus, Corpora
import pandas as pd
import pytest
from glob import glob

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
    assert isinstance(corpus.attributes_available, pd.DataFrame)


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
    assert '/np(0)' not in corpus._macros_available()
    corpus = get_corpus(germaparl, lib=True)
    assert '/np(0)' in corpus._macros_available()


@pytest.mark.init
def test_wordlists(germaparl):
    corpus = get_corpus(germaparl, lib=True)
    assert "$parties" in corpus._wordlists_available()


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
    df = corpus.marginals_complex(
        [("gehen", "VVFIN"), ("Seehofer", "NE"), ("Merkel", "NE")],
        ["lemma", "pos"]
    )
    assert len(df) == 3
    assert df['freq']['gehen VVFIN'] == 186


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
    corpus.activate_subcorpus('Horst')
    df2 = corpus.dump_from_query(
        "[lemma='Seehofer']"
    )
    assert len(df1) > len(df2)


@pytest.mark.subcorpus
def test_deactivate_subcorpus(germaparl):

    corpus = get_corpus(germaparl)

    df1 = corpus.dump_from_query(
        '[lemma="die"]',
        germaparl['s_query']
    )

    # define subcorpus
    corpus.query(
        cqp_query="[lemma='sein'] expand to s",
        name='Sein'
    )

    # activate subcorpus
    corpus.activate_subcorpus('Sein')
    df2 = corpus.dump_from_query(
        '[lemma="die"]',
        germaparl['s_query']
    )

    # deactivate subcorpus
    corpus.activate_subcorpus()
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
    corpus.query('[lemma="jetzt"]')
    # assert "Jetzt" not in corpus.show_nqr().values
    corpus.query('[lemma="jetzt"]', name='Jetzt')
    assert "Jetzt" in corpus.show_nqr().values
    corpus.activate_subcorpus("Jetzt")


@pytest.mark.subcorpus
def test_nqr_from_s_att(germaparl):

    corpus = get_corpus(germaparl)
    corpus.query_s_att("text_party", values={"CDU", "CSU"}, name="Union")
    assert "Union" in corpus.show_nqr().values
    corpus.activate_subcorpus("Union")


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
