from ccc import Corpus
from ccc import Corpora
import pandas as pd
import pytest

from .conftest import LOCAL, DATA_PATH


def get_corpus(corpus_settings, data_path=DATA_PATH):

    return Corpus(
        corpus_settings['corpus_name'],
        registry_path=corpus_settings['registry_path'],
        lib_path=corpus_settings.get('lib_path', None),
        data_path=data_path
    )


###############################################
# INIT ########################################
###############################################

@pytest.mark.init
def test_corpora(germaparl):
    corpora = Corpora(registry_path=germaparl['registry_path'])
    assert(type(corpora.show()) == pd.DataFrame)
    assert("GERMAPARL1386" in corpora.show().index)


@pytest.mark.init
def test_corpus(germaparl):
    corpus = get_corpus(germaparl)
    assert(corpus.corpus_size > 1000)


@pytest.mark.init
def test_get_corpus(germaparl):
    corpus = get_corpus(germaparl)
    assert(corpus.corpus_size > 1000)


@pytest.mark.init
def test_corpus_descriptor(germaparl):
    corpus = get_corpus(germaparl)
    assert(type(corpus.attributes_available) == pd.DataFrame)


@pytest.mark.skipif(not LOCAL, reason='works on my machine')
@pytest.mark.brexit
@pytest.mark.init
def test_corpus_lib(brexit):
    corpus = get_corpus(brexit)
    assert(corpus.corpus_size > 1000)


#####################################################
# ATTRIBUTES ########################################
#####################################################

@pytest.mark.attributes
def test_cpos2patt(germaparl):
    corpus = get_corpus(germaparl)
    token = corpus.cpos2patts(124345)
    assert(type(token) == tuple)
    assert(token[0] == 'gilt')


@pytest.mark.attributes
def test_cpos2patts(germaparl):
    corpus = get_corpus(germaparl)
    token = corpus.cpos2patts(124345, ['word', 'pos'])
    assert(type(token) == tuple)


@pytest.mark.attributes
def test_marginals(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.marginals(["Merkel", "Seehofer", "gehen"], p_att='lemma')
    assert(df.loc['gehen']['freq'] == 224)


@pytest.mark.attributes
def test_marginals_pattern(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.marginals(["Merkel", "Seehofer", "geh.*"], pattern=True)
    assert(df.loc['geh.*']['freq'] == 310)


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
    corpus.subcorpus = 'Horst'
    df2 = corpus.dump_from_query(
        "[lemma='Seehofer']"
    )
    assert(len(df1) > len(df2))


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
    corpus.subcorpus = 'Sein'
    df2 = corpus.dump_from_query(
        '[lemma="die"]',
        germaparl['s_query']
    )

    # deactivate subcorpus
    corpus.subcorpus = corpus.corpus_name
    df3 = corpus.dump_from_query(
        '[lemma="die"]',
        germaparl['s_query']
    )

    assert(len(df1) == len(df3))
    assert(len(df1) > len(df2))


################################################
# CREATING DUMPS ###############################
################################################


@pytest.mark.dump
def test_dump_from_s_att(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.dump_from_s_att('text_id')
    assert(df.iloc[0]['text_id'] == "i13_86_1_1")


@pytest.mark.dump
def test_dump_from_s_att_wo(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.dump_from_s_att('p')
    assert(df.shape[0] == 7332)


@pytest.mark.skipif(not LOCAL, reason='works on my machine')
@pytest.mark.brexit
@pytest.mark.dump
def test_dump_from_s_att_with(brexit):
    corpus = get_corpus(brexit)
    df = corpus.dump_from_s_att('ner_type')
    assert(len(df) == 1212944)


@pytest.mark.dump
def test_dump_from_query(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.dump_from_query(
        query=germaparl['query'],
        s_query=germaparl['s_query'],
        match_strategy='standard'
    )
    assert(type(df_dump) == pd.DataFrame)
    assert(df_dump.shape[0] == 30)


@pytest.mark.skipif(not LOCAL, reason='works on my machine')
@pytest.mark.brexit
@pytest.mark.dump
def test_dump_from_query_1(brexit):
    corpus = get_corpus(brexit)
    df_dump = corpus.dump_from_query(
        query='[lemma="angela"] @1[lemma="merkel"]',
        anchors=[1],
        match_strategy='longest'
    )
    assert(type(df_dump) == pd.DataFrame)
    assert(df_dump.shape[0] > 99)


@pytest.mark.dump
def test_dump_from_query_anchors(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.dump_from_query(
        query=germaparl['query_anchor'],
        s_query=germaparl['s_query'],
        anchors=germaparl['anchors'],
        match_strategy='standard'
    )
    assert(type(df_dump) == pd.DataFrame)
    assert(df_dump.shape[0] == 30)
    assert(all(elem in df_dump.columns for elem in germaparl['anchors']))


@pytest.mark.skipif(not LOCAL, reason='works on my machine')
@pytest.mark.brexit
@pytest.mark.dump
def test_dump_from_query_lib(brexit):
    corpus = get_corpus(brexit)
    df_dump = corpus.dump_from_query(
        query=brexit['query_lib'],
        s_query=brexit['s_query'],
        match_strategy='longest'
    )
    assert(type(df_dump) == pd.DataFrame)
    assert(df_dump.shape[0] > 99)


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
    assert('test' in df.columns)
    assert(len(df) == 30)
    assert(df.iloc[0]['text_id_span'] == 10628)


@pytest.mark.skipif(not LOCAL, reason='works on my machine')
@pytest.mark.brexit
@pytest.mark.dumpp
def test_dump2satt_2(brexit):
    corpus = get_corpus(brexit)
    df_dump = corpus.dump_from_query(
        query=brexit['query'],
        s_query=brexit['s_query'],
        match_strategy='longest'
    )
    df = corpus.dump2satt(df_dump, 'vp')
    assert(df.iloc[0]['vp_cwbid'] == 112)


@pytest.mark.dumpp
def test_dump2context(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.dump_from_query(
        query=germaparl['query'],
        s_query=germaparl['s_query'],
        match_strategy='standard'
    )
    df_dump = corpus.dump2context(df_dump, 20, 20, 's')
    assert(all(
        elem in df_dump.columns for elem in ['context', 'contextid', 'contextend']
    ))


@pytest.mark.dumpp
def test_dump2context2(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.dump_from_query(
        query=germaparl['query'],
        s_query=germaparl['s_query'],
        match_strategy='standard'
    )
    df_dump = corpus.dump2context(df_dump, 20, 20, 'text_id')
    assert(all(elem in df_dump.columns for elem in [
        'context', 'contextid', 'contextend', 'text_id_cwbid', 'text_id'
    ]))


@pytest.mark.skipif(not LOCAL, reason='works on my machine')
@pytest.mark.brexit
@pytest.mark.dumpp
def test_dump2context3(brexit):
    corpus = get_corpus(brexit)
    df_dump = corpus.dump_from_query(
        query=brexit['query'],
        s_query=brexit['s_query'],
        match_strategy='longest'
    )
    df_dump = corpus.dump2context(df_dump, 20, 20, 'np')
    assert(all(elem in df_dump.columns for elem in [
        'context', 'contextid', 'contextend', 'np_cwbid'
    ]))


@pytest.mark.skipif(not LOCAL, reason='works on my machine')
@pytest.mark.brexit
@pytest.mark.dumpp
def test_dump2context4(brexit):
    corpus = get_corpus(brexit)
    df_dump = corpus.dump_from_query(
        query=brexit['query'],
        s_query=brexit['s_query'],
        match_strategy='longest'
    )
    df_dump = corpus.dump2context(df_dump, None, 5, 'tweet_id')
    assert(all(elem in df_dump.columns for elem in [
        'context', 'contextid', 'contextend', 'tweet_id_cwbid', 'tweet_id'
    ]))


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
    assert('word' in df_dump.columns)


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
    assert('word' in df_dump.columns)


#################################################
# QUERY ALIASES #################################
#################################################

@pytest.mark.query
def test_query_context_1(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.query(
        cqp_query=germaparl['query_anchor'],
        context=None
    ).df
    assert(type(df) == pd.DataFrame)
    columns = germaparl['anchors'] + ['context', 'contextend']
    assert(all(elem in df.columns for elem in columns))


@pytest.mark.query
def test_query_context_2(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.query(
        cqp_query=germaparl['query_anchor'],
        context_left=10,
        context=15
    ).df
    assert(type(df) == pd.DataFrame)
    columns = germaparl['anchors'] + ['context', 'contextend']
    assert(all(elem in df.columns for elem in columns))


@pytest.mark.query
def test_query_context_3(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.query(
        cqp_query=germaparl['query_anchor'],
        context=None,
        context_break='s'
    ).df
    assert(type(df) == pd.DataFrame)
    columns = germaparl['anchors'] + ['contextid', 'context', 'contextend']
    assert(all(elem in df.columns for elem in columns))


@pytest.mark.query
def test_query_context_4(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.query(
        cqp_query=germaparl['query_anchor'],
        context=10,
        context_break='s'
    ).df
    assert(type(df) == pd.DataFrame)
    columns = germaparl['anchors'] + ['contextid', 'context', 'contextend']
    assert(all(elem in df.columns for elem in columns))


@pytest.mark.query
def test_query_context_5(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.query(
        cqp_query='[lemma="Horst"]',
        context=10,
        context_break='s'
    ).df
    assert(type(df) == pd.DataFrame)
