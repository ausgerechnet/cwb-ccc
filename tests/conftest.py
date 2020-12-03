import os
import pytest


local = False


@pytest.fixture
def germaparl():
    """ settings for small germaparl testing corpus """

    dir_path = os.path.dirname(os.path.realpath(__file__))
    registry_path = os.path.join(dir_path, "test-corpora/registry/")
    corpus_name = 'GERMAPARL1386'

    context = 50
    s_context = 'text'

    s_query = 's'
    query = (
        r'[lemma="Horst"]? [lemma="Seehofer"]'
        r'"\[" "CDU" "/" "CSU" "\]"'
    )
    query_anchor = (
        r'@0[lemma="Horst"]? @1[lemma="Seehofer"] @2:[::]'
    )
    anchors = [0, 1, 2]
    query_within = query_anchor + " within " + s_query + ";"

    return {
        'registry_path': registry_path,
        'corpus_name': corpus_name,
        'context': context,
        's_context': s_context,
        's_query': s_query,
        'query': query,
        'query_anchor': query_anchor,
        'anchors': anchors,
        'query_full': query_within
    }


@pytest.fixture
def brexit():
    """ settings for brexit tweet corpus """

    registry_path = (
        "/home/ausgerechnet/corpora/cwb/registry/"
    )
    corpus_name = "BREXIT_V20190522_DEDUP"
    lib_path = (
        "/home/ausgerechnet/repositories/spheroscope/library/BREXIT_V20190522_DEDUP/"
    )
    meta_path = (
        "/home/ausgerechnet/corpora/cwb/upload/"
        "brexit/brexit-preref-rant/brexit_v20190522_dedup.tsv.gz"
    )

    dir_path = os.path.dirname(os.path.realpath(__file__))
    query_path = (
        os.path.join(dir_path, "as_a_x_i_y_knowledge.json")
    )

    context = 50
    s_context = 'tweet'

    s_query = 'tweet'
    query = '[lemma="test"]'
    query_wordlist = (
        '[lemma = $verbs_cause]'
    )

    # according to experts ...
    query_argmin = {
        'cqp': (
            '("according" "to" | "as" [lemma = $verbs_communication] "by")'
            '<np> @0:[::][word != "(http.|www|t\\.co).+"]*'
            '(/name_any[] | [lemma = $nouns_experts |'
            'lemma = $nouns_person_profession]) [word != "(http.|www|t\\.co).+"]* </np>'
            '@1:[::] ","? <np>@2:[::][word != "(http.|www|t\\.co).+"]*</np>'
            '(<vp>[]*</vp>)+ (<np>[word != "(http.|www|t\\.co).+"]*</np>'
            ' | <vp>[]*</vp> |<pp>[]*</pp> | [pos_simple = "I|R"])+ @3:[::]'
        ),
        'corrections': {
            0: 0,
            1: -1,
            2: 0,
            3: -1
        },
        'slots': {
            'slot_single': 0,
            'slot_1': [0, 1],
            'slot_2': [2, 3]
        },
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
        'corpus_name': corpus_name,
        'lib_path': lib_path,
        'meta_path': meta_path,
        'context': context,
        's_context': s_context,
        's_query': s_query,
        'query': query,
        'query_lib': query_wordlist,
        'query_argmin': query_argmin,
        'query_path': query_path
    }
