from ccc import Corpus
from ccc import Corpora
import pandas as pd
import pytest

from .conftest import local


def get_corpus(corpus_settings):
    return Corpus(
        corpus_settings['corpus_name'],
        registry_path=corpus_settings['registry_path'],
        lib_path=corpus_settings.get('lib_path', None)
    )


###############################################
# INIT ########################################
###############################################

@pytest.mark.corpus_init
def test_corpora(germaparl):
    corpora = Corpora(registry_path=germaparl['registry_path'])
    assert(type(corpora.show()) == pd.DataFrame)
    assert("GERMAPARL1386" in corpora.show().index)


@pytest.mark.corpus_init
def test_corpus(germaparl):
    corpus = get_corpus(germaparl)
    assert(corpus.corpus_size > 1000)


@pytest.mark.corpus_init
def test_get_corpus(germaparl):
    corpus = get_corpus(germaparl)
    assert(corpus.corpus_size > 1000)


@pytest.mark.corpus_init
def test_corpus_descriptor(germaparl):
    corpus = get_corpus(germaparl)
    assert(type(corpus.attributes_available) == pd.DataFrame)


@pytest.mark.skipif(not local, reason='works on my machine')
@pytest.mark.brexit
@pytest.mark.corpus_init
def test_corpus_lib(brexit):
    corpus = get_corpus(brexit)
    assert(corpus.corpus_size > 1000)


################################################
# DUMPS ########################################
################################################


@pytest.mark.dump
def test_dump_from_query(germaparl):
    corpus = get_corpus(germaparl)
    df_dump = corpus.dump_from_query(
        query=germaparl['query'],
        s_query=germaparl['s_query'],
        match_strategy='standard'
    )
    assert(type(df_dump) == pd.DataFrame)
    assert(df_dump.shape[0] == 1)


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


@pytest.mark.skipif(not local, reason='works on my machine')
@pytest.mark.brexit
@pytest.mark.dump
def test_dump_from_query_lib(brexit):
    corpus = Corpus(
        brexit['corpus_name'],
        lib_path=brexit['lib_path']
    )
    df_dump = corpus.dump_from_query(
        query=brexit['query_lib'],
        s_query=brexit['s_query'],
        match_strategy='longest'
    )
    assert(type(df_dump) == pd.DataFrame)
    assert(df_dump.shape[0] > 99)


@pytest.mark.skipif(not local, reason='works on my machine')
@pytest.mark.brexit
@pytest.mark.dump
def test_dump_from_query_1(brexit):
    corpus = Corpus(
        brexit['corpus_name']
    )
    df_dump = corpus.dump_from_query(
        query='[lemma="angela"] @1[lemma="merkel"]',
        anchors=[1],
        match_strategy='longest'
    )
    assert(type(df_dump) == pd.DataFrame)
    assert(df_dump.shape[0] > 99)


#####################################################
# SUBCORPORA ########################################
#####################################################


@pytest.mark.subcorpus
def test_subcorpus_from_query(germaparl):
    corpus = get_corpus(germaparl)
    assert(int(corpus.start_cqp().Exec('size SBCRPS1')) == 0)
    cqp = corpus.start_cqp()
    cqp.nqr_from_query(
        query="[lemma='Seehofer']",
        name='SBCRPS1',
        return_dump=False
    )
    assert(int(cqp.Exec('size SBCRPS1')) > 0)
    cqp.__kill__()


@pytest.mark.subcorpus
def test_subcorpus_from_df(germaparl):
    corpus = get_corpus(germaparl)
    cqp = corpus.start_cqp()
    assert(int(cqp.Exec('size SBCRPS2')) == 0)
    df = corpus.dump_from_query(
        query=germaparl['query']
    )
    cqp.nqr_from_dump(
        df_dump=df,
        name='SBCRPS2',
    )
    assert(int(cqp.Exec('size SBCRPS2')) > 0)
    cqp.__kill__()


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
        name='SBCRPS3',
        save=True
    )

    # activate subcorpus
    corpus.subcorpus = 'SBCRPS3'
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


@pytest.mark.subcorpus
def test_subcorpus_anchor(germaparl):
    corpus = get_corpus(germaparl)

    df1 = corpus.dump_from_query(
        "[lemma='Horst']",
        s_query=germaparl['s_context']
    )
    df_anchor = corpus.query(
        germaparl['query_anchor'],
        name='SBCRPS5',
        save=True
    ).df
    corpus.subcorpus = 'SBCRPS5'
    df2 = corpus.dump_from_query(
        "[lemma='Horst']", None
    )
    assert(len(df1) > len(df_anchor) > len(df2))


@pytest.mark.subcorpus
def test_dump_from_s_att(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.dump_from_s_att(
        'text_id', ['i13_86_1_1']
    )
    assert(dump.df.shape[0] == 1)


@pytest.mark.subcorpus
def test_dump_from_s_att_wo(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.dump_from_s_att('p', [True])
    assert(dump.df.shape[0] == 7332)


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
def test_get_s_extents(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.get_s_extents('text_id')
    print(df)


@pytest.mark.skipif(not local, reason='works on my machine')
@pytest.mark.brexit
@pytest.mark.attributes
def test_get_s_extents_2(brexit):
    corpus = Corpus(brexit['corpus_name'])
    df = corpus.get_s_extents('ner_type')
    print(df)


#################################################
# .query ########################################
#################################################


@pytest.mark.query
def test_query_context_1(germaparl):
    corpus = get_corpus(germaparl)
    df = corpus.query(
        cqp_query=germaparl['query_anchor'],
        context=None,
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
        context=15,
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
    columns = germaparl['anchors'] + ['context_id', 'context', 'contextend']
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
    columns = germaparl['anchors'] + ['context_id', 'context', 'contextend']
    assert(all(elem in df.columns for elem in columns))


@pytest.mark.skipif(not local, reason='works on my machine')
@pytest.mark.brexit
@pytest.mark.query
def test_query_s_atts_brexit(brexit):
    corpus = Corpus(brexit['corpus_name'])
    df_dump = corpus.query(
        cqp_query='[lemma="nigel"]',
        context=10,
        context_break='tweet'
    ).df
    df = corpus.get_s_annotations(df_dump, ['ner_type', 'tweet_id', 'tweet'])
    assert(type(df) == pd.DataFrame)
    columns = [a + '_CWBID' for a in ['ner_type', 'tweet_id', 'tweet']]
    columns += ['ner_type', 'tweet_id']
    print(df['ner_type'].value_counts())
    assert(all(elem in df.columns for elem in columns))

