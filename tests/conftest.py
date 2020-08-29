import pytest


@pytest.fixture(scope='function')
def brexit_corpus():
    """ settings for BREXIT_V20190522_DEDUP """

    registry_path = "/home/ausgerechnet/corpora/cwb/registry/"
    context = 50

    corpus_name = "BREXIT_V20190522_DEDUP"
    lib_path = "/home/ausgerechnet/repositories/spheroscope/library/BREXIT_V20190522_DEDUP/"
    meta_path = (
        "/home/ausgerechnet/corpora/cwb/upload/"
        "brexit/brexit-preref-rant/brexit_v20190522_dedup.tsv.gz"
    )

    s_break = 'tweet'
    s_query = 'tweet'

    query = '[lemma="test"]'
    query_lib = (
        '<np>[pos_simple!="P"] []*</np> [lemma = $verbs_cause] [pos_simple="R"]? '
        '<np>[]*</np> (<np>[]*</np> | <vp>[]*</vp> | <pp>[]*</pp>)+'
    )

    query_argmin = {
        'query': '("according" "to" | "as" [lemma = $verbs_communication] "by") <np> @0:[::][word != "(http.|www|t\\.co).+"]* (/name_any[] | [lemma = $nouns_experts | lemma = $nouns_person_profession]) [word != "(http.|www|t\\.co).+"]* </np>@1:[::] ","? <np>@2:[::][word != "(http.|www|t\\.co).+"]*</np> (<vp>[]*</vp>)+ (<np>[word != "(http.|www|t\\.co).+"]*</np> | <vp>[]*</vp> |<pp>[]*</pp> | [pos_simple = "I|R"])+ @3:[::]',
        'anchors': [
            [0, 0, None, None],
            [1, -1, None, None],
            [2, 0, None, None],
            [3, -1, None, None]
        ],
        'corrections': {0: 0, 1: -1, 2: 0, 3: -1},
        'regions': {'region_1': [0, 1], 'region_2': [2, 3]},
        'match_strategy': 'longest',
        's_query': 'tweet',
        's_context': 'tweet',
        's_show': ['tweet_id'],
        'p_text': 'word',
        'p_slots': 'lemma',
        'p_show': ['word', 'pos_ner', 'lemma', 'pos_ark']
    }

    return {
        'registry_path': registry_path,
        'context': context,
        'corpus_name': corpus_name,
        'lib_path': lib_path,
        's_break': s_break,
        's_query': s_query,
        'query': query,
        'query_lib': query_lib,
        'meta_path': meta_path,
        'query_argmin': query_argmin
    }


@pytest.fixture(scope='function')
def sz_corpus():
    """ settings for SZ_2009_14 """

    registry_path = "/home/ausgerechnet/corpora/cwb/registry/"
    context = 50

    meta_path = (
        "/home/ausgerechnet/corpora/cwb/upload/efe/sz-2009-14.tsv.gz"
    )

    corpus_name = 'SZ_2009_14'

    s_query = 's'
    s_break = 'text'

    query = '[lemma="Angela"] [lemma="Merkel"] | [lemma="CDU"]'
    anchor_query = (
        r'@0[lemma="Angela"]? @1[lemma="Merkel"] '
        r'[word="\("] @2[lemma="CDU"] [word="\)"]'
    )
    anchors = [0, 1, 2]

    query_full = anchor_query + " within " + s_query + ";"

    return {
        'registry_path': registry_path,
        'context': context,
        'corpus_name': corpus_name,
        's_break': s_break,
        's_query': s_query,
        'query': query,
        'anchor_query': anchor_query,
        'anchors': anchors,
        'query_full': query_full,
        'meta_path': meta_path
    }
