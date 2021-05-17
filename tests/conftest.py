import os
import pytest
from pandas import read_csv


LOCAL = True
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = os.path.join(DIR_PATH, 'data-dir')
# DATA_PATH = "/tmp/ccc-data"


@pytest.fixture
def germaparl():
    """ settings for small germaparl testing corpus """

    registry_path = os.path.join(DIR_PATH, "corpora/registry/")
    dump_path = os.path.join(DIR_PATH, "gold", "germaparl-seehofer.tsv")
    corpus_name = 'GERMAPARL1386'

    context = 50
    s_context = 'text'
    s_meta = 'text_id'

    s_query = 's'
    query = '[lemma="Seehofer"]'
    query_anchor = (
        r'@0[lemma="Horst"]? @1[lemma="Seehofer"] @2:[::]'
    )
    anchors = [0, 1, 2]
    query_within = query_anchor + " within " + s_query + ";"
    seehofer_dump = read_csv(dump_path, sep="\t", header=None, dtype=int,
                             index_col=[0, 1], names=['match', 'matchend'])

    return {
        'registry_path': registry_path,
        'corpus_name': corpus_name,
        'context': context,
        's_context': s_context,
        's_query': s_query,
        's_meta': s_meta,
        'query': query,
        'query_anchor': query_anchor,
        'anchors': anchors,
        'query_full': query_within,
        'dump': seehofer_dump
    }


@pytest.fixture
def brexit():
    """ settings for brexit tweet corpus """

    registry_path = (
        "/home/ausgerechnet/corpora/cwb/registry/"
    )
    corpus_name = "BREXIT_V20190522_DEDUP"
    lib_path = (
        "/home/ausgerechnet/implementation/spheroscope/library/BREXIT_V20190522_DEDUP/"
    )
    meta_path = (
        "/home/ausgerechnet/corpora/cwb/upload/"
        "brexit/brexit-preref-rant/brexit_v20190522_dedup.tsv.gz"
    )

    query_path = (os.path.join(DIR_PATH, "gold", "as_a_x_i_y_knowledge.json"))

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
