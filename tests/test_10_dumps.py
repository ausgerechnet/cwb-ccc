import pytest
from pandas import DataFrame

from ccc.cwb import Corpus
from ccc.dumps import Dumps

from .conftest import DATA_PATH


def get_corpus(corpus_settings, data_path=DATA_PATH):

    return Corpus(
        corpus_settings['corpus_name'],
        registry_path=corpus_settings['registry_path'],
        lib_path=corpus_settings.get('lib_path', None),
        data_path=data_path
    )


########
# DUMP #
########
def test_query(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD"')
    assert dump.name_cqp == 'Last'
    assert dump.size == 632
    assert (dump.df.columns == ['context', 'contextend']).all()


def test_query_name(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD"', name="SPD")
    assert dump.name_cqp == "SPD"
    assert dump.size == 632
    assert (dump.df.columns == ['context', 'contextend']).all()


def test_breakdown(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD"')
    breakdown = dump.breakdown()
    assert isinstance(breakdown, DataFrame)
    assert breakdown.loc['SPD']['freq'] == 632


def test_breakdown_p_att(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('[lemma="gehen"]')
    breakdown = dump.breakdown()
    assert isinstance(breakdown, DataFrame)
    assert breakdown.loc['geht']['freq'] == 150
    breakdown = dump.breakdown(p_atts=['lemma'])
    assert isinstance(breakdown, DataFrame)
    assert breakdown.loc['gehen']['freq'] == 224


def test_matches(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD"')
    matches = dump.matches()
    assert isinstance(matches, set)
    assert 8193 in matches


def test_matches_subcorpus(germaparl):
    corpus = get_corpus(germaparl)
    dump_base = corpus.query(r'[pos="NE"]? [pos="NE"] "\[" ".*" "\]"', name="Base")
    tokens_base = len(dump_base.matches())
    corpus.subcorpus = "Base"
    dump_neg = corpus.query('[pos="NE"]')
    tokens_neg = len(dump_neg.matches())
    assert (tokens_base - tokens_neg) == 350


def test_context(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD"')
    context = dump.context()
    assert isinstance(context, DataFrame)
    assert context['context'][0] == 76


def test_set_context(germaparl):

    corpus = get_corpus(germaparl)
    dump = corpus.query('"CSU"', context_break='text')
    assert dump.df['context'].iloc[0] == 620
    dump = dump.set_context(10, context_break='text', context_right=10)
    assert dump.df['context'].iloc[0] == 630


def test_query_s_satt(germaparl):
    corpus = get_corpus(germaparl)
    parties = {"GRUENE", "Bündnis 90/Die Grünen"}
    dump = corpus.query_s_att('text_party', parties)
    assert dump.name_cqp is None
    assert dump.size == 87
    assert (dump.df.columns == ['text_party_cwbid', 'text_party']).all()


def test_concordance(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD"')
    conc = dump.concordance()
    assert isinstance(conc, DataFrame)
    assert conc['word'].iloc[0].startswith("früh")


def test_concordance_options(germaparl):

    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD"')

    conc = dump.concordance(form='simple')
    assert isinstance(conc, DataFrame)
    assert len(conc) == 100
    assert 'word' in conc.columns
    conc = dump.concordance(form='kwic')
    assert isinstance(conc, DataFrame)
    assert len(conc) == 100
    assert 'node_word' in conc.columns
    conc = dump.concordance(form='dict')
    assert isinstance(conc, DataFrame)
    assert len(conc) == 100
    assert 'dict' in conc.columns
    conc = dump.concordance(form='slots')
    assert isinstance(conc, DataFrame)
    assert len(conc) == 100
    assert 'match..matchend_word' in conc.columns
    conc = dump.concordance(form='dataframe')
    assert isinstance(conc, DataFrame)
    assert len(conc) == 100
    assert 'dataframe' in conc.columns


def test_collocates(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD"')
    coll = dump.collocates()
    assert coll.index[0] == 'die'


def test_collocates_options(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD"')
    coll = dump.collocates(order='log_likelihood', cut_off=70)
    assert coll.index[0] == 'bei'
    assert len(coll) == 70


def test_keywords(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD" expand to s')
    kw = dump.keywords()
    assert kw.index[0] == 'die'


def test_keywords_options(germaparl):
    corpus = get_corpus(germaparl)
    dump = corpus.query('"SPD" expand to s')
    kw = dump.keywords(order='log_ratio', cut_off=200)
    assert kw.index[0] == 'SPD'


#########
# DUMPS #
#########
@pytest.mark.dumps
def test_dumps_keywords(germaparl):

    # subcorpora via s-attribute values
    parties = {
        'green': {"GRUENE", "Bündnis 90/Die Grünen"},
        'red': {'SPD'},
        'black': {'CDU', 'CSU'},
        'yellow': {'FDP'},
        'purple': {'PDS'}
    }

    # keywords
    corpus = get_corpus(germaparl)
    dumps = Dumps(corpus, parties, s_att='text_party')
    tables = dumps.keywords(order='log_ratio')
    assert tables['green'].index[0] == "Oppositionsfraktion"
    assert tables['red'].index[0] == "Bereicherung"
    assert tables['black'].index[0] == "Abgabenquote"
    assert tables['yellow'].index[0] == "Wirtschafts-"
    assert tables['purple'].index[0] == "ÖPNV-Gesetz"


@pytest.mark.dumps
def test_dumps_collocates(germaparl):

    # subcorpora via s-attribute values
    parties = {
        'green': {"GRUENE", "Bündnis 90/Die Grünen"},
        'red': {'SPD'},
        'black': {'CDU', 'CSU'},
        'yellow': {'FDP'},
        'purple': {'PDS'}
    }

    # collocates
    corpus = get_corpus(germaparl)
    dumps = Dumps(corpus, parties, s_att='text_party')
    tables = dumps.collocates(
        cqp_query='"Wirtschaft"',
        order='log_ratio',
        context_break='s',
        window=20
    )
    assert len(tables) == len(parties)
    assert tables['yellow'].index[0] == 'Grad'


def test_dumps_collocates_global(germaparl):

    # subcorpora via s-attribute values
    parties = {
        'green': {"GRUENE", "Bündnis 90/Die Grünen"},
        'red': {'SPD'},
        'black': {'CDU', 'CSU'},
        'yellow': {'FDP'},
        'purple': {'PDS'}
    }

    # collocates
    corpus = get_corpus(germaparl)
    dumps = Dumps(corpus, parties, s_att='text_party')
    tables = dumps.collocates(
        cqp_query='"Wirtschaft"',
        order='log_ratio',
        context_break='s',
        window=20,
        reference='global'
    )
    assert len(tables) == len(parties)
    assert tables['yellow'].index[0] == 'Grad'


@pytest.mark.benchmark
def test_perf_dumps(benchmark, germaparl):
    benchmark.pedantic(test_dumps_collocates, kwargs={'germaparl': germaparl}, rounds=5, iterations=2)
