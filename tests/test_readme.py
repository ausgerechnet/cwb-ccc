from ccc import Corpus
from pandas import read_csv
import json
import pytest


@pytest.mark.v1
@pytest.mark.setup
def test_init_corpus(brexit_corpus):
    corpus = Corpus(brexit_corpus['corpus_name'],
                    lib_path=brexit_corpus['lib_path'],
                    registry_path=brexit_corpus['registry_path'])
    print(corpus)


@pytest.mark.v1
@pytest.mark.setup
def test_macro(brexit_corpus):
    corpus = Corpus(brexit_corpus['corpus_name'],
                    lib_path=brexit_corpus['lib_path'],
                    registry_path=brexit_corpus['registry_path'])
    corpus.cqp.Exec("Last=/ap();")
    counts = corpus.counts.matches(corpus.cqp, name="Last")
    print(counts)


@pytest.mark.v1
@pytest.mark.queries
def test_query_no_cache(sz_corpus):

    corpus = Corpus(
        corpus_name=sz_corpus['corpus_name']
    )
    query = r'[lemma="Angela"]? [lemma="Merkel"]'
    dump = corpus.query(query, name='Merkel')
    print(dump)
    print(dump.df)


@pytest.mark.v1
@pytest.mark.queries
def test_query(sz_corpus):

    corpus = Corpus(
        corpus_name=sz_corpus['corpus_name']
    )
    query = r'[lemma="Angela"]? [lemma="Merkel"] [word="\("] [lemma="CDU"] [word="\)"]'
    dump = corpus.query(query)
    print(dump)
    print(dump.df)
    print(dump.breakdown())


@pytest.mark.v1
@pytest.mark.concordancing
def test_concordancing_simple():
    corpus = Corpus(
        corpus_name="SZ_2009_14"
    )

    query = r'[lemma="Angela"]? [lemma="Merkel"] [word="\("] [lemma="CDU"] [word="\)"]'
    dump = corpus.query(query)
    lines = dump.concordance()
    print(lines)
    print(lines.columns)
    from pprint import pprint
    pprint(lines['raw'].iloc[0])


@pytest.mark.v1
@pytest.mark.concordancing
def test_concordancing():
    corpus = Corpus(
        corpus_name="SZ_2009_14"
    )

    query = r'[lemma="Angela"]? [lemma="Merkel"] [word="\("] [lemma="CDU"] [word="\)"]'
    result = corpus.query(query, context_break='s')
    lines = result.concordance(form='dataframes')
    from pprint import pprint
    pprint(lines['df'].iloc[0])


@pytest.mark.v1
@pytest.mark.concordancing
def test_concordancing_attributes():
    corpus = Corpus(
        corpus_name="SZ_2009_14"
    )

    query = r'[lemma="Angela"]? [lemma="Merkel"] [word="\("] [lemma="CDU"] [word="\)"]'
    result = corpus.query(query, context_break='s')
    lines = result.concordance(
        form='dataframes',
        p_show=['word', 'lemma'],
        s_show=['text_id']
    )
    print(lines['df'].iloc[0])
    print(lines)


@pytest.mark.v1
@pytest.mark.anchor
def test_anchor():
    corpus = Corpus(
        corpus_name="SZ_2009_14"
    )

    query = r'@0[lemma="Angela"]? @1[lemma="Merkel"] [word="\("] @2[lemma="CDU"] [word="\)"]'
    result = corpus.query(query, context_break='s')
    concordance = result.concordance(matches=[18640085],
                                     form='dataframes')['df'][0]
    print(concordance)


@pytest.mark.collocates
def test_collocates():
    corpus = Corpus(
        corpus_name="SZ_2009_14"
    )

    query = '[lemma="Angela"]? [lemma="Merkel"] [word="\\("] [lemma="CDU"] [word="\\)"]'
    result = corpus.query(query, context=10, context_break='s')
    collocates = result.collocates()
    print(collocates)


@pytest.mark.now
@pytest.mark.v1
@pytest.mark.keywords
def test_keywords():
    meta = read_csv("/home/ausgerechnet/corpora/cwb/upload/efe/sz-2009-14.tsv.gz",
                    sep="\t", index_col=0, dtype=str)
    ids = set(meta.loc[
        (meta['ressort'] == "Panorama") & (meta['month'] == '201103')
    ].index.values)
    meta['s_id'] = meta.index

    corpus = Corpus(
        corpus_name="SZ_2009_14"
    )
    dump = corpus.dump_from_s_att('text_id', ids)
    keywords = dump.keywords()
    print(keywords.head(50))


@pytest.mark.skip
@pytest.mark.argmin
def test_argmin():
    corpus = Corpus(
        corpus_name="BREXIT_V20190522",
        registry_path="/home/ausgerechnet/corpora/cwb/registry/",
        lib_path="/home/ausgerechnet/projects/spheroscope/app/instance-stable/lib/",
        s_meta="tweet_id"
    )

    query_path = "/home/ausgerechnet/projects/cwb-ccc/tests/gold/query-example.json"
    with open(query_path, "rt") as f:
        query = json.loads(f.read())
    query_result = corpus.query(query['query'], context=None, s_break='tweet',
                                match_strategy='longest')
    concordance = corpus.concordance(query_result)

    result = concordance.show_argmin(query['anchors'], query['regions'])
    print(result.keys())
    print(result['nr_matches'])
    from pandas import DataFrame
    print(DataFrame(result['matches'][0]['df']))
