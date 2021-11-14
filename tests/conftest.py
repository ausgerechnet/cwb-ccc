import os
import pytest
from pandas import read_csv
from pathlib import Path


LOCAL = str(Path.home()) == "/home/ausgerechnet"
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = os.path.join(DIR_PATH, 'data-dir')


@pytest.fixture
def ucs_counts():
    """ UCS counts """
    land = read_csv("tests/counts/ucs-germaparl1386-Land.ds.gz",
                    sep="\t", index_col=2, comment="#", quoting=3, na_filter=False)
    land.index.name = 'lemma'
    land = land.drop(['id', 'l1'], axis=1).sort_values(by='f', ascending=False)
    land.columns = [c + "_ucs" for c in land.columns]

    und = read_csv("tests/counts/ucs-germaparl1386-und.ds.gz",
                   sep="\t", index_col=2, comment="#", quoting=3, na_filter=False)
    und.index.name = 'lemma'
    und = und.drop(['id', 'l1'], axis=1).sort_values(by='f', ascending=False)
    und.columns = [c + "_ucs" for c in und.columns]

    return {
        'Land': land,
        'und': und
    }


@pytest.fixture
def germaparl():
    """ settings for small germaparl testing corpus """

    corpus_name = 'GERMAPARL1386'
    registry_path = os.path.join(DIR_PATH, "corpora/registry/")
    lib_path = os.path.join(DIR_PATH, "corpora", "library")
    freq_list = os.path.join(DIR_PATH, "corpora", "germaparl1386-lemma-freq.tsv")
    dump_path = os.path.join(DIR_PATH, "counts", "germaparl-seehofer.tsv")

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

    query_lib = '/np[] [lemma="zeigen"]'

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
        'dump': seehofer_dump,
        'freq_list': freq_list,
        'lib_path': lib_path,
        'query_lib': query_lib
    }


@pytest.fixture
def discoursemes():
    """ discourseme settings """

    return {
        'items_topic': ["CDU", "CSU"],
        'items_1': ["und"],
        'items_2': ["Bundesregierung"],
        'parameters': {
            'flags_query': '%cd',
            'escape_query': False,
            'p_query': 'lemma',
            's_query': 's',
            's_context': 'p',
            'context': 20,
        }
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

    query_path = (os.path.join(DIR_PATH, "query-files", "as_a_x_i_y_knowledge.json"))

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


@pytest.fixture
def empirist():
    """ settings for empirist corpus """

    freq_list = os.path.join(DIR_PATH, "corpora", "empirist-lemma-freq.tsv")

    return {
        'freq_list': freq_list
    }
