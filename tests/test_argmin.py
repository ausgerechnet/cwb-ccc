from ccc.cwb import CWBEngine
from ccc.argmin import process_argmin_file, argmin_query, get_holes
import pytest
import gzip
import json
import pandas as pd


registry_path = "/home/ausgerechnet/corpora/cwb/registry/"
lib_path = "/home/ausgerechnet/projects/spheroscope/app/instance-stable/lib/"
corpus_name = "BREXIT_V20190522"
subcorpus_query = "/region[tweet,a] :: (a.tweet_duplicate_status!='1') within tweet"
subcorpus_name = "DEDUP"
match_strategy = 'longest'


query_path = "/home/ausgerechnet/projects/ccc/tests/gold/query-example.json"
result_path = "/home/ausgerechnet/projects/ccc/tests/gold/query-example-result.ldjson.gz"

# set concordance settings
concordance_settings = {
    'order': 'first',
    'cut_off': None,
    'p_show': ['lemma'],
    's_break': 'tweet',
    'context': 50
}


@pytest.mark.holes
def test_get_holes():

    query_path = "/home/ausgerechnet/projects/ccc/tests/gold/query-example-2.json"
    # result_path = "/home/ausgerechnet/projects/ccc/tests/gold/query-example-2-result.ldjson.gz"

    with open(query_path, "rt") as f:
        try:
            query = json.loads(f.read())
        except json.JSONDecodeError:
            print("WARNING: not a valid json file")
            return

    engine = CWBEngine(corpus_name=corpus_name,
                       registry_path=registry_path, lib_path=lib_path,
                       meta_s="tweet_id", meta_path=None)

    result = argmin_query(engine,
                          query['query'],
                          query['anchors'],
                          query['regions'],
                          concordance_settings['s_break'],
                          concordance_settings['context'],
                          concordance_settings['p_show'])

    df = pd.DataFrame(result['matches'][0]['df'])
    get_holes(df, query['anchors'], query['regions'])


@pytest.mark.argmin_query
def test_argmin_query():

    with open(query_path, "rt") as f:
        try:
            query = json.loads(f.read())
        except json.JSONDecodeError:
            print("WARNING: not a valid json file")
            return

    engine = CWBEngine(corpus_name=corpus_name,
                       registry_path=registry_path, lib_path=lib_path,
                       meta_s="tweet_id", meta_path=None)

    result = argmin_query(engine,
                          query['query'],
                          query['anchors'],
                          query['regions'],
                          concordance_settings['s_break'],
                          concordance_settings['context'],
                          concordance_settings['p_show'])

    assert(all(x in result.keys() for x in ['matches',
                                            'holes',
                                            'nr_matches']))


@pytest.mark.argmin_file
def test_process_argmin_file():

    engine = CWBEngine(corpus_name=corpus_name,
                       registry_path=registry_path, lib_path=lib_path,
                       meta_s="tweet_id")
    engine.subcorpus_from_query(subcorpus_query, subcorpus_name)
    result = process_argmin_file(engine, query_path, concordance_settings)
    assert(all(x in result.keys() for x in ['query',
                                            'pattern',
                                            'name',
                                            'anchors',
                                            'regions',
                                            'concordance_settings',
                                            'query_path',
                                            'result']))
    assert(all(x in result['result'].keys() for x in ['matches',
                                                      'holes',
                                                      'nr_matches']))
    with gzip.open(result_path, 'wt') as f_out:
        json.dump(result, f_out, indent=4)
