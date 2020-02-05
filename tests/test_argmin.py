from ccc.cwb import CWBEngine
from ccc.argmin import ArgConcordance, process_argmin_file
import pytest
import gzip
import json


registry_path = "/home/ausgerechnet/corpora/cwb/registry/"
lib_path = "/home/ausgerechnet/projects/spheroscope/app/instance-stable/lib/"
corpus_name = "BREXIT_V20190522"
subcorpus_query = "/region[tweet,a] :: (a.tweet_duplicate_status!='1') within tweet"
subcorpus_name = "DEDUP"
match_strategy = 'longest'

query_path = "/home/ausgerechnet/projects/cwb-ccc/tests/gold/query-example.json"
result_path = "/home/ausgerechnet/projects/cwb-ccc/tests/gold/query-example-result.ldjson.gz"


@pytest.mark.argconc
def test_argconc():

    engine = CWBEngine(corpus_name=corpus_name,
                       registry_path=registry_path, lib_path=lib_path,
                       meta_s="tweet_id", meta_path=None)

    with open(query_path, "rt") as f:
        try:
            query = json.loads(f.read())
        except json.JSONDecodeError:
            print("WARNING: not a valid json file")
            return

    argconc = ArgConcordance(engine)
    result = argconc.argmin_query(query['query'], query['anchors'], query['regions'])
    assert('test' in result['holes'].keys())
    assert(type(result['matches']) == list)


@pytest.mark.argmin_file
def test_process_argmin_file():

    engine = CWBEngine(corpus_name=corpus_name,
                       registry_path=registry_path, lib_path=lib_path,
                       meta_s="tweet_id")
    engine.subcorpus_from_query(subcorpus_query, subcorpus_name)
    result = process_argmin_file(engine, query_path)
    assert(all(x in result.keys() for x in ['corpus_name',
                                            'subcorpus',
                                            'query',
                                            'pattern',
                                            'name',
                                            'anchors',
                                            'regions',
                                            'query_path',
                                            'result']))
    assert(all(x in result['result'].keys() for x in ['matches',
                                                      'holes',
                                                      'nr_matches']))
    with gzip.open(result_path, 'wt') as f_out:
        json.dump(result, f_out, indent=4)
