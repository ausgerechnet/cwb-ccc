from ccc.cwb import Corpus
import pytest

from .conftest import local


def test_query2dump(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    dump = corpus.query('"SPD"')
    print(dump)


def test_query2dump_name(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    dump = corpus.query('"SPD"', name="Test")
    print(dump)


def test_breakdown(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    dump = corpus.query('"SPD"')
    print(dump.breakdown())


def test_concordance(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    dump = corpus.query('"SPD"')
    print(dump.concordance())


def test_concordance_options(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    dump = corpus.query('"SPD"')
    print(dump.concordance(form='raw'))
    print(dump.concordance(form='simple'))
    print(dump.concordance(form='kwic'))
    print(dump.concordance(form='dataframes'))
    print(dump.concordance(form='extended'))


def test_collocates(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    dump = corpus.query('"SPD"')
    print(dump.collocates())


def test_collocates_options(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    dump = corpus.query('"SPD"')
    print(dump.collocates(order='log_likelihood', cut_off=200))


def test_keywords(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    dump = corpus.query('"SPD" expand to s')
    print(dump.keywords())


def test_keywords_options(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    dump = corpus.query('"SPD" expand to s')
    print(dump.keywords(order='log_ratio', cut_off=200))


def test_context_matches(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    dump = corpus.query('"SPD"')
    print(dump.matches())
    print(dump.context())


@pytest.mark.skipif(not local, reason='works on my machine')
@pytest.mark.brexit
def test_argmin_query(brexit):
    corpus = Corpus(
        brexit['corpus_name'],
        lib_path=brexit['lib_path']
    )

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
        p_text=query['p_text'],
        p_slots=query['p_slots'],
        slots=query['slots'],
        order='first',
        cut_off=None,
        form='extended'
    )

    print(conc)
    print(conc['df'].iloc[0])


@pytest.mark.skipif(not local, reason='works on my machine')
@pytest.mark.brexit
def test_dumps(brexit):

    corpus = Corpus(
        brexit['corpus_name']
    )
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
    dump = corpus.dump_from_s_att('tweet_id', ids)
    print(dump.concordance())
