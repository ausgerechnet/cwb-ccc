from ccc import Corpus
from ccc.utils import (filter_df, fold_item, intersect_intervals,
                       merge_intervals, preprocess_query)

from .conftest import DATA_PATH


def test_preprocess_query():
    query = (
        "/nobody[] <vp>[]*@0:[lemma = $verbs_cog_positive] "
        "[]* @1:[]</vp> <np>@2:[::][]* [lemma = $adj_cog_negative]* "
        "[lemma = $nouns_person_negative][]* @3:[]</np> "
        "within tweet;"
    )
    query = preprocess_query(query)
    assert query['anchors'] == [0, 1, 2, 3]
    assert query['s_query'] == 'tweet'
    assert query['wordlists'] == ["$verbs_cog_positive", "$adj_cog_negative",
                                  "$nouns_person_negative"]
    assert query['macros'] == ['/nobody[]']

    query = (
        "<vp>[]*@0:[lemma = $verbs_cog_positive] "
        "[]* @1:[]</vp> <np>@2:[::][]* [lemma = $adj_cog_negative]* "
        "[lemma = $nouns_person_negative][]* @3:[]</np>;"
    )
    query = preprocess_query(query)
    assert query['s_query'] is None
    assert query['macros'] == []


def test_preprocess_anchor_query():
    query = (
        '@0[lemma="Angela"]? @1[lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"]'
    )
    query_1 = preprocess_query(query)

    query = (
        '@0[lemma="Angela"]? @1[lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"];'
    )
    query_2 = preprocess_query(query)

    query = (
        '@0[lemma="Angela"]? @1[lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"] within tweet;'
    )
    query_3 = preprocess_query(query)

    query = (
        '@0[lemma="Angela"]? @1[lemma="Merkel"] '
        '[word="\\("] @2[lemma="CDU"] [word="\\)"] within s'
    )
    query_4 = preprocess_query(query)

    assert query_1['s_query'] == query_2['s_query'] is None
    assert query_3['s_query'] == 'tweet'
    assert query_4['s_query'] == 's'
    assert query_1['query'] == query_2['query'] == query_3['query'] == query_4['query']
    assert query_1['anchors'] == query_2['anchors'] == query_3['anchors'] == query_4['anchors']


def test_fold_items():
    items_aber = ['aber', 'äber', 'AbEr', 'ÄBER']
    items_francais = ['français', 'Fráncàis']
    assert len(set([fold_item(item) for item in items_aber])) == 1
    assert len(set([fold_item(item) for item in items_francais])) == 1


def test_filter_df(germaparl):
    c = Corpus(germaparl['corpus_name'], registry_dir=germaparl['registry_dir'], data_dir=DATA_PATH)
    subcorpus = c.query(germaparl['query'])
    coll = subcorpus.collocates()
    assert ',' in coll.index
    coll_filtered = filter_df(coll, 'resources/stopwords-de.txt')
    assert ',' not in coll_filtered.index


def test_merge_intervals():

    intervals = [[1, 3], [2, 4], [5, 9], [6, 10]]
    merge = merge_intervals(intervals)
    assert merge == [[1, 4], [5, 10]]

    intervals = [[0, 5], [2, 4], [6, 9], [6, 10]]
    merge = merge_intervals(intervals)
    assert merge == [[0, 5], [6, 10]]


def test_intersect_intervals():

    intervals_left = [[0, 1801], [7438, 7449]]
    intervals_right = [[458, 463], [548, 553], [1025, 1500], [2540, 2670], [7438, 7439], [7440, 7449], [8500, 8600]]
    merge = intersect_intervals(intervals_left, intervals_right)
    assert merge == [[458, 463], [548, 553], [1025, 1500], [7438, 7439], [7440, 7449]]

    intervals_left = [[0, 1801], [7438, 7449]]
    intervals_right = [[458, 463], [548, 553], [1025, 1500], [1800, 1802], [7438, 7439], [7440, 7449], [8500, 8600]]
    merge = intersect_intervals(intervals_left, intervals_right)
    assert merge == [[458, 463], [548, 553], [1025, 1500], [1800, 1801], [7438, 7439], [7440, 7449]]
