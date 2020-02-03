import json

from ccc.cwb import CWBEngine
from ccc.argmin import anchor_query


query_path = "app/instance-stable/queries/verbal_classification.query"
with open(query_path, "rt") as f:
    query = json.load(f)


##################
concordance_settings = {
    'order': 'first',
    'cut_off': 10,
    'context': 100,
    'p_show': ['lemma'],
    's_break': 'tweet'
}
match_strategy = 'longest'


engine = CWBEngine(
    corpus_name="BREXIT_V20190522",
    registry_path="/home/ausgerechnet/corpora/cwb/registry/",
    lib_path="app/instance-stable/lib/",
    cache_path="/tmp/test-cache"
)
engine.cqp.Exec("/person_any[];")


conc = anchor_query(
    engine,
    query_str=query['query'],
    anchors=query['anchors'],
    regions=query['regions'],
    s_break=concordance_settings['s_break'],
    p_show=concordance_settings['p_show'],
    match_strategy=match_strategy
)
