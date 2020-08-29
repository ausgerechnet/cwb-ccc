from ccc.cwb import Corpus
import pytest


@pytest.mark.nocache
def test_query2dump_nocache(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'], data_path=None)
    dump = corpus.query(sz_corpus['query'])
    print(dump)


def test_query2dump_diff_name(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.query(sz_corpus['query'], name="Test")
    print(dump)


def test_query2dump(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.query('"1"')
    print(dump)


def test_breakdown(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.query(sz_corpus['query'])
    print(dump.breakdown())


def test_concordance(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.query(sz_corpus['query'])
    print(dump.concordance())


def test_concordance_options(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.query(sz_corpus['query'])
    print(dump.concordance(form='raw'))
    print(dump.concordance(form='simple'))
    print(dump.concordance(form='kwic'))
    print(dump.concordance(form='dataframes'))
    print(dump.concordance(form='extended'))


def test_collocates(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.query('"Angela"')
    print(dump.collocates())


def test_collocates_options(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.query('"Angela"')
    print(dump.collocates(order='log_likelihood', cut_off=200))


def test_keywords(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.query('"Angela" expand to s')
    print(dump.keywords())


def test_keywords_options(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.query('"Angela" expand to s')
    print(dump.keywords(order='log_ratio', cut_off=200))


def test_context_matches(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.query('"Angela"')
    print(dump.matches())
    print(dump.context())


def test_argmin_query(brexit_corpus):
    corpus = Corpus(
        brexit_corpus['corpus_name'],
        lib_path=brexit_corpus['lib_path']
    )

    query = brexit_corpus['query_argmin']

    dump = corpus.query(
        cqp_query=query['query'],
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
        regions=query['regions'],
        order='first',
        cut_off=None,
        form='extended'
    )

    print(conc)
    print(conc['df'].iloc[0])


@pytest.mark.now
def test_dumps(brexit_corpus):

    corpus = Corpus(
        brexit_corpus['corpus_name']
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
