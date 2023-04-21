import os

import pytest
from pandas import read_csv

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = os.path.join(DIR_PATH, 'data-dir')


@pytest.fixture
def ucs_counts():
    """ UCS counts """

    path_land = os.path.join(DIR_PATH, "corpora", "counts",
                             "ucs-germaparl1386-Land.ds.gz")
    path_und = os.path.join(DIR_PATH, "corpora", "counts",
                            "ucs-germaparl1386-und.ds.gz")

    # Land
    land = read_csv(path_land, sep="\t", index_col=2,
                    comment="#", quoting=3, na_filter=False)
    land.index.name = 'lemma'
    land = land.drop(['id', 'l1'], axis=1).sort_values(by='f', ascending=False)
    land.columns = [c + "_ucs" for c in land.columns]

    # und
    und = read_csv(path_und, sep="\t", index_col=2,
                   comment="#", quoting=3, na_filter=False)
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
    registry_dir = os.path.join(DIR_PATH, "corpora", "registry")
    lib_dir = os.path.join(DIR_PATH, "corpora", "library")
    freq_list = os.path.join(DIR_PATH, "corpora", "counts",
                             "germaparl1386-lemma-freq.tsv")
    dump_path = os.path.join(DIR_PATH, "corpora", "counts",
                             "germaparl1386-seehofer.tsv")

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
        'registry_dir': registry_dir,
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
        'lib_dir': lib_dir,
        'query_lib': query_lib
    }


@pytest.fixture
def germaparl_full():
    """ settings for local germaparl corpus """

    corpus_name = "GERMAPARL-1949-2021"
    registry_dir = "/usr/local/share/cwb/registry"
    lib_dir = None

    context = 50
    s_context = 'speaker_node'

    s_query = 's'

    return {
        'registry_dir': registry_dir,
        'corpus_name': corpus_name,
        'context': context,
        's_context': s_context,
        's_query': s_query,
        'lib_dir': lib_dir,
    }


@pytest.fixture
def discoursemes():
    """ discoursemes """

    return {
        'topic': ["CDU", "CSU"],
        'disc1': ["und"],
        'disc2': ["Bundesregierung"],
        'parameters': {
            'flags_query': '%cd',
            'escape_query': False,
            'p_query': 'lemma',
            's_query': 's',
            's_context': 'p',
            'context': 20
        }
    }


@pytest.fixture
def query_files():
    """ paths to query files in json and cqpy """
    return {
        'as_a_x_i_y_knowledge': os.path.join(
            DIR_PATH, "corpora", "library", "queries", "as_a_x_i_y_knowledge.cqpy"
        ),
        'jemand_sagt': os.path.join(
            DIR_PATH, "corpora", "library", "queries", "jemand_sagt.cqpy"
        ),
        'jemand_sagt_sloppy': os.path.join(
            DIR_PATH, "corpora", "library", "queries", "jemand_sagt_sloppy.cqpy"
        ),
        'jemand_sagt_display': os.path.join(
            DIR_PATH, "corpora", "library", "queries", "jemand_sagt_display.cqpy"
        )
    }


@pytest.fixture
def empirist():
    """ empirist frequency list """

    freq_list = os.path.join(DIR_PATH, "corpora", "counts",
                             "empirist-lemma-freq.tsv")

    return {
        'freq_list': freq_list
    }
