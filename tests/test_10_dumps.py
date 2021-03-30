from ccc.cwb import Corpus
import pytest

from .conftest import LOCAL, DATA_PATH


def get_corpus(corpus_settings, data_path=DATA_PATH):

    return Corpus(
        corpus_settings['corpus_name'],
        registry_path=corpus_settings['registry_path'],
        lib_path=corpus_settings.get('lib_path', None),
        data_path=data_path
    )


def test_query2dump(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD"')
    print(dump)


def test_query2dump_name(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD"', name="Test")
    print(dump)


def test_breakdown(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD"')
    print(dump.breakdown())


def test_dump_matches(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD"')
    print(dump.matches())


def test_dump_matches1(germaparl):
    corpus = get_corpus(germaparl)
    dump_base = corpus.query(
        r'[pos="NE"]? [pos="NE"] "\[" ".*" "]")', name="Base"
    )
    tokens_base = len(dump_base.matches())
    corpus.subcorpus = "Base"
    dump_neg = corpus.query('[pos="NE"]')
    tokens_neg = len(dump_neg.matches())
    print(tokens_base - tokens_neg)


def test_dump_context(germaparl):
    corpus = get_corpus(germaparl)

    # init topic disc
    dump = corpus.query('"SPD"')
    print(dump.context())


@pytest.mark.skipif(not LOCAL, reason='works on my machine')
@pytest.mark.brexit
def test_satt2dump(brexit):

    corpus = get_corpus(brexit)
    ids = {
        't740982320711249920',
        't731037753241112576',
        't729363812802039814',
        't733648546881277953',
        't741216447595220992',
        't705780723018539012',
        't745930343627243520',
        't730870826178904065',
        't745691821477605377',
        't730419966818783232',
        't746069538693750784'
    }
    dump = corpus.query_s_att('tweet_id', ids)
    print(dump.concordance())


def test_concordance(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD"')
    print(dump.concordance())


def test_concordance_options(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD"')
    print(dump.concordance(form='raw'))
    print(dump.concordance(form='simple'))
    print(dump.concordance(form='kwic'))
    print(dump.concordance(form='dataframes'))
    print(dump.concordance(form='extended'))


def test_concordance_set_context(germaparl):

    corpus = get_corpus(germaparl)
    dump = corpus.query('"CSU"', context_break='text')
    print(dump)
    dump.set_context(10, context_break='text', context_right=10)
    print(dump)


def test_collocates(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD"')
    print(dump.collocates())


def test_collocates_options(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD"')
    print(dump.collocates(order='log_likelihood', cut_off=200))


def test_keywords(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD" expand to s')
    print(dump.keywords())


def test_keywords_options(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD" expand to s')
    print(dump.keywords(order='log_ratio', cut_off=200))


def test_context_matches(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD"')
    print(dump.matches())
    print(dump.context())


@pytest.mark.skipif(not LOCAL, reason='works on my machine')
@pytest.mark.brexit
def test_argmin_query(brexit):
    corpus = get_corpus(brexit)

    query = brexit['query_argmin']

    dump = corpus.query(
        cqp_query=query['cqp'],
        context=query.get('context', None),
        context_break=query.get('s_context', None),
        corrections=query['corrections'],
        match_strategy=query['match_strategy']
    )

    conc = dump.concordance(
        p_show=query['p_show'],
        s_show=query['s_show'],
        slots=query['slots'],
        order='first',
        cut_off=None,
        form='slots'
    )

    print(conc)
