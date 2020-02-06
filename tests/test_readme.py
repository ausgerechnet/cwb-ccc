from ccc.cwb import CWBEngine
from ccc.concordances import Concordance
from ccc.collocates import Collocates
import json
import pytest


def test_concordancing():
    engine = CWBEngine(
        corpus_name="SZ_FULL",
        registry_path="/home/ausgerechnet/corpora/cwb/registry/",
        s_meta="text_id",
        cache_path=None
    )

    query = '[lemma="Angela"]? [lemma="Merkel"] [word="\\("] [lemma="CDU"] [word="\\)"]'
    concordance = Concordance(engine, query, s_break='s')

    print(concordance.breakdown)
    print(concordance.size)
    print(concordance.meta)
    print(concordance.lines([48349]))


def test_collocates():
    engine = CWBEngine(
        corpus_name="SZ_FULL",
        registry_path="/home/ausgerechnet/corpora/cwb/registry/",
        s_meta="text_id",
        cache_path=None
    )
    query = '[lemma="Angela"]? [lemma="Merkel"] [word="\\("] [lemma="CDU"] [word="\\)"]'
    collocates = Collocates(engine, query)
    collocates.show(window=5)


def test_argmin():
    engine = CWBEngine(
        corpus_name="BREXIT_V20190522",
        registry_path="/home/ausgerechnet/corpora/cwb/registry/",
        lib_path="/home/ausgerechnet/projects/spheroscope/app/instance-stable/lib/",
        s_meta="tweet_id",
        cache_path=None
    )

    query_path = "/home/ausgerechnet/projects/cwb-ccc/tests/gold/query-example.json"
    with open(query_path, "rt") as f:
        query = json.loads(f.read())

    concordance = Concordance(engine, query['query'], context=None,
                              s_break='tweet', match_strategy='longest')
    result = concordance.show_argmin(query['anchors'], query['regions'])
    result.keys()
    result['nr_matches']
    len(result['matches'])
