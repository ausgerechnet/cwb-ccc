import os
from pprint import pprint

from ccc.argmin import read_query_json, run_query
from ccc.cwb import Corpus

import pytest


@pytest.mark.now
def test_read_query_json():
    query_path = (
        "/home/ausgerechnet/repositories/cwb-ccc/tests/argmin_queries/"
        "query-example.json"
    )
    query = read_query_json(query_path)
    pprint(query)


@pytest.mark.now
def test_run_query(brexit_corpus):
    query_path = (
        "/home/ausgerechnet/repositories/cwb-ccc/tests/argmin_queries/"
        "query-example.json"
    )
    data_path = (
        "/home/ausgerechnet/repositories/cwb-ccc/tests/argmin_queries/"
        "argmin_queries"
    )
    corpus = Corpus(brexit_corpus['corpus_name'],
                    brexit_corpus['lib_path'],
                    data_path=data_path)
    query = read_query_json(query_path)
    result = run_query(corpus, query)
    pprint(result)


@pytest.mark.files
def test_argmin(brexit_corpus):
    query_path = (
        "/home/ausgerechnet/repositories/cwb-ccc/tests/argmin_queries/"
        "query-example.json"
    )
    data_path = (
        "/home/ausgerechnet/repositories/cwb-ccc/tests/"
        "argmin_queries"
    )

    # read file
    query = read_query_json(query_path)

    # patch path to query
    query['query_path'] = query_path

    # run query
    corpus = Corpus(brexit_corpus['corpus_name'],
                    brexit_corpus['lib_path'],
                    data_path=data_path)
    result = run_query(corpus, query)

    # get path for output
    path_out = os.path.join(data_path, query['name']) + ".tsv"
    result['df'] = result['df'].apply(lambda row: row.to_json())
    result.to_csv(path_out, sep="\t")
