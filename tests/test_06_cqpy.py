import pytest

from ccc import Corpus
from ccc.cqpy import cqpy_dumps, cqpy_load, cqpy_loads, run_query

from .conftest import DATA_PATH


def get_corpus(corpus_settings, data_dir=DATA_PATH):

    return Corpus(
        corpus_settings['corpus_name'],
        registry_dir=corpus_settings['registry_dir'],
        lib_dir=corpus_settings.get('lib_dir', None),
        data_dir=data_dir
    )


def test_cqpy_load(query_files):
    query = cqpy_load(query_files['as_a_x_i_y_knowledge'])
    assert 'meta' in query
    assert 'cqp' in query
    assert query['anchors']['corrections'][1] == -1
    assert query['query']['context'] is None


def test_cqpy_dump(query_files):
    query_load = cqpy_load(query_files['as_a_x_i_y_knowledge'])
    query_reload = cqpy_loads(cqpy_dumps(query_load))
    assert query_load == query_reload


def test_run_from_cqpy(germaparl, query_files):

    corpus = get_corpus(germaparl)
    query = cqpy_load(query_files['jemand_sagt'])
    lines = run_query(corpus, query)
    assert all([v in lines.columns for v in ['word', 'entity_lemma', 'vp_lemma']])


def test_run_from_cqpy_sloppy(germaparl, query_files):

    corpus = get_corpus(germaparl)
    query = cqpy_load(query_files['jemand_sagt_sloppy'])
    lines = run_query(corpus, query)
    assert lines[['five_word']].value_counts()[''] == 440
    assert lines[['five_word']].value_counts()['nichts'] == 3
    assert lines[['entity_lemma']].value_counts()['sie'] == 273


def test_run_from_cqpy_display(germaparl, query_files):

    corpus = get_corpus(germaparl)
    query = cqpy_load(query_files['jemand_sagt_display'])
    lines = run_query(corpus, query)

    assert 'word' in lines.columns
    assert 'lemma' not in lines.columns
    assert 'entity_word' not in lines.columns
    assert 'entity_lemma' in lines.columns
    assert lines[['entity_lemma']].value_counts()['sie'] == 273
