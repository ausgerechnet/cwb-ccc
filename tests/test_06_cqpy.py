from ccc.cqpy import cqpy_load, cqpy_dump, load_query_json, run_query
from pprint import pprint
from ccc import Corpus
import pytest

from .conftest import LOCAL, DATA_PATH


def get_corpus(corpus_settings, data_path=DATA_PATH):

    return Corpus(
        corpus_settings['corpus_name'],
        registry_path=corpus_settings['registry_path'],
        lib_path=corpus_settings.get('lib_path', None),
        data_path=data_path
    )


def test_read_json():
    path = "tests/gold/as_a_x_i_y_knowledge.json"
    query = load_query_json(path)
    pprint(query)


def test_cqpy_load():
    path = "tests/gold/as_a_x_i_y_knowledge.manual.cqpy"
    query = cqpy_load(path)
    print()
    pprint(query)


def test_cqpy_dump():
    path = "tests/gold/as_a_x_i_y_knowledge.manual.cqpy"
    query = cqpy_load(path)
    print(cqpy_dump(query))


def test_convert():
    path = "tests/gold/as_a_x_i_y_knowledge.json"
    query = load_query_json(path)
    print(cqpy_dump(query))


@pytest.mark.skipif(not LOCAL, reason='works on my machine')
@pytest.mark.brexit
def test_run_from_cqpy(brexit):

    corpus = get_corpus(brexit)
    path = "tests/gold/as_a_x_i_y_knowledge.manual.cqpy"
    query = cqpy_load(path)
    result = run_query(corpus, query)

    # print(result)
    print(result[["lonely_anchor_lemma", "region_1_lemma", "region_2_lemma"]])

    print(result[["region_1_lemma", "region_2_lemma"]])
