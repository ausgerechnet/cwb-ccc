import pytest


@pytest.fixture(scope='function')
def brexit_corpus():
    """ settings for BREXIT_V20190522_DEDUP """

    registry_path = "/home/ausgerechnet/corpora/cwb/registry/"
    context = 50

    corpus_name = "BREXIT_V20190522_DEDUP"
    lib_path = "/home/ausgerechnet/repositories/spheroscope/instance-stable/lib/"

    s_break = 'tweet'
    s_query = 'tweet'

    query = '[lemma="test"]'
    query_lib = (
        '<np>[pos_simple!="P"] []*</np> [lemma = $verbs_cause] [pos_simple="R"]? '
        '<np>[]*</np> (<np>[]*</np> | <vp>[]*</vp> | <pp>[]*</pp>)+'
    )

    return {
        'registry_path': registry_path,
        'context': context,
        'corpus_name': corpus_name,
        'lib_path': lib_path,
        's_break': s_break,
        's_query': s_query,
        'query': query,
        'query_lib': query_lib
    }


@pytest.fixture(scope='function')
def sz_corpus():
    """ settings for SZ_2009_14 """

    registry_path = "/home/ausgerechnet/corpora/cwb/registry/"
    context = 50

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
        'query_full': query_full
    }
