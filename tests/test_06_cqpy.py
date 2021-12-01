from ccc.cqpy import cqpy_load, cqpy_loads, cqpy_dumps, run_query
from ccc import Corpus
import pytest

from .conftest import DATA_PATH


def get_corpus(corpus_settings, data_path=DATA_PATH):

    return Corpus(
        corpus_settings['corpus_name'],
        registry_path=corpus_settings['registry_path'],
        lib_path=corpus_settings.get('lib_path', None),
        data_path=data_path
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
