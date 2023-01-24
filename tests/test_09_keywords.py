import pytest

from ccc import Corpus
from ccc.counts import score_counts
from ccc.keywords import Keywords, keywords

from .conftest import DATA_PATH


def get_corpus(corpus_settings, data_path=DATA_PATH):

    return Corpus(
        corpus_settings['corpus_name'],
        registry_path=corpus_settings['registry_path'],
        lib_path=corpus_settings.get('lib_path', None),
        data_path=data_path
    )


@pytest.mark.meta
def test_keywords_from_satt_values(germaparl):

    corpus = get_corpus(germaparl)
    df_dump = corpus.query_s_att(
        "text_party", {"GRUENE", "Bündnis 90/Die Grünen"}
    ).df

    # keywords
    keywords = Keywords(corpus, df_dump, p_query='lemma')
    lines = keywords.show(order='log_ratio', cut_off=None)
    assert lines.index[0] == "Oppositionsfraktion"


@pytest.mark.query
def test_keywords_from_query(germaparl):

    # get subcorpus as dump
    corpus = get_corpus(germaparl)
    df_dump = corpus.query('"Seehofer" expand to s').df

    # keywords
    keywords = Keywords(corpus, df_dump)
    lines = keywords.show(order='log_ratio')
    assert lines.index[1] == "Gesundheitsreform"


@pytest.mark.query
def test_keywords_from_dump(germaparl):

    # get subcorpus as dump
    corpus = get_corpus(germaparl)
    df_dump = corpus.dump_from_query('"und" expand to s')

    # keywords
    keywords = Keywords(corpus, df_dump)
    lines = keywords.show(order='log_likelihood', min_freq=10)
    assert lines.index[1] == "Dame"


@pytest.mark.subcorpus
def test_keywords_switch(germaparl):

    # get some regions
    corpus = get_corpus(germaparl)
    df_all = corpus.query('"und" expand to s', name='Und_all').df

    df_head = df_all.head(500)
    df_tail = df_all.tail(500)

    # will show keywords for head
    keywords = Keywords(corpus, df_dump=df_head, p_query="lemma")
    lines_head = keywords.show(order='log_likelihood')

    # will show keywords for tail
    keywords = Keywords(corpus, df_dump=df_tail, p_query="lemma")
    lines_tail = keywords.show(order='log_likelihood')

    assert not lines_head.equals(lines_tail)


@pytest.mark.query
def test_keywords_combo(germaparl):

    # get subcorpus as dump
    corpus = get_corpus(germaparl)
    dump = corpus.query('"und" expand to s')

    # keywords
    lines = dump.keywords(["lemma", "pos"], order='log_likelihood', min_freq=10)
    assert lines.index[0] == "und KON"


def test_keywords(germaparl):

    corpus = get_corpus(germaparl)

    left = corpus.marginals(p_atts=['lemma', 'pos'])[['freq']].rename(
        columns={'freq': 'f1'}
    )
    right = corpus.marginals(p_atts=['lemma', 'pos'])[['freq']].rename(
        columns={'freq': 'f2'}
    )

    df = left.join(right).fillna(0, downcast='infer')
    df['N1'] = df['f1'].sum()
    df['N2'] = df['f2'].sum()
    kw = score_counts(df, order='O11')
    assert kw.iloc[0]['O11'] == 11469
    assert kw.iloc[0]['conservative_log_ratio'] == 0


@pytest.mark.subcorpus
def test_keywords_func(germaparl):

    corpus = get_corpus(germaparl)
    green = corpus.query_s_att("text_party", {"GRUENE", "Bündnis 90/Die Grünen"})
    red = corpus.query_s_att("text_party", {"SPD", "S.P.D."})
    kw = keywords(green, red, ['lemma'], ['lemma'], 'conservative_log_ratio')
    assert kw.index[0] == 'Dr.'


@pytest.mark.subcorpus
def test_keywords_func_corpora(germaparl):

    corpus = get_corpus(germaparl)
    kw = keywords(corpus, corpus, ['lemma'], ['word'], 'conservative_log_ratio')
    assert kw.index[0] == 'sie'
