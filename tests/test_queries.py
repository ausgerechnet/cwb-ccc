from ccc.queries import cqpy_load, cqpy_dump, load_query_json, run_query
from pprint import pprint
import pytest
from ccc import Corpus


def test_read_json():
    path = "tests/according_to_experts_x.query"
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
    path = "tests/according_to_experts_x.query"
    query = load_query_json(path)
    print(cqpy_dump(query))


@pytest.mark.now
def test_run_query():
    lib_path = (
        "/home/ausgerechnet/repositories/spheroscope/library/BREXIT_V20190522_DEDUP/"
    )
    corpus_name = "BREXIT_V20190522_DEDUP"

    corpus = Corpus(corpus_name, lib_path)

    path = "tests/as_a_x_i_y_knowledge.manual.cqpy"
    query = cqpy_load(path)
    result = run_query(corpus, query)
    print(result[["lonely_anchor_lemma", "region_1_lemma", "region_2_lemma"]])

    path = "tests/according_to_experts_x.query"
    query = load_query_json(path)
    corpus = Corpus(query['corpus']['corpus_name'], lib_path)
    result = run_query(corpus, query)
    print(result[["0_lemma", "1_lemma"]])
