from ccc.queries import cqpy_load, cqpy_dump, load_query_json, run_query
from pprint import pprint
from ccc import Corpus
import pytest

from .conftest import local


def test_read_json():
    path = "tests/as_a_x_i_y_knowledge.json"
    query = load_query_json(path)
    pprint(query)


def test_cqpy_load():
    path = "tests/as_a_x_i_y_knowledge.manual.cqpy"
    query = cqpy_load(path)
    print()
    pprint(query)


def test_cqpy_dump():
    path = "tests/as_a_x_i_y_knowledge.manual.cqpy"
    query = cqpy_load(path)
    print(cqpy_dump(query))


def test_convert():
    path = "tests/as_a_x_i_y_knowledge.json"
    query = load_query_json(path)
    print(cqpy_dump(query))


@pytest.mark.skipif(not local, reason='works on my machine')
@pytest.mark.brexit
def test_run_from_cqpy(brexit):

    corpus = Corpus(brexit['corpus_name'],
                    brexit['lib_path'])

    path = "tests/as_a_x_i_y_knowledge.manual.cqpy"
    query = cqpy_load(path)
    result = run_query(corpus, query)

    print(result[["lonely_anchor_lemma", "region_1_lemma", "region_2_lemma"]])

    print(result[["region_1_lemma", "region_2_lemma"]])
