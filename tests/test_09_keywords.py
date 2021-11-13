from ccc import Corpus
from ccc.keywords import Keywords
from ccc.counts import read_freq_list, score_counts
import pytest

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
    assert lines.index[1] == "die ART"


def test_score_counts(germaparl, empirist):

    df1, R1 = read_freq_list(germaparl['freq_list'])
    df2, R2 = read_freq_list(empirist['freq_list'])

    kw = score_counts(df1[['freq']], df2[['freq']], R1, R2, cut_off=None)
    assert kw['log_likelihood']['die'] == 4087.28
