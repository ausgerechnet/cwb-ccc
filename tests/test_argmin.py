from ccc.cwb import Corpus
from ccc.concordances import process_argmin_file
import gzip
import pytest
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

    corpus = Corpus(corpus_name=corpus_name,
                    registry_path=registry_path, lib_path=lib_path,
                    s_meta="tweet_id")

    with open(query_path, "rt") as f:
        try:
            query = json.loads(f.read())
        except json.JSONDecodeError:
            print("WARNING: not a valid json file")
            return

    corpus.query(query['query'], context=None, s_break='tweet',
                 match_strategy='longest')
    conc = corpus.concordance()
    result = conc.show_argmin(query['anchors'], query['regions'])
    assert('test' in result['holes'].keys())
    assert(type(result['matches']) == list)


@pytest.mark.argmin_file
def test_process_argmin_file():

    corpus = Corpus(corpus_name=corpus_name,
                    registry_path=registry_path, lib_path=lib_path,
                    s_meta="tweet_id")
    corpus.define_subcorpus(query=subcorpus_query,
                            name=subcorpus_name, activate=True)
    result = process_argmin_file(corpus, query_path)
    assert(all(x in result.keys() for x in ['query',
                                            'pattern',
                                            'name',
                                            'query_path',
                                            'result']))
    assert(all(x in result['result'].keys() for x in ['matches',
                                                      'holes',
                                                      'nr_matches']))
    with gzip.open(result_path, 'wt') as f_out:
        json.dump(result, f_out, indent=4)
