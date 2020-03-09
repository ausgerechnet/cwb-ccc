from ccc import Corpus
from pandas import read_csv
import json
import pytest


@pytest.mark.readme_concordancing
def test_concordancing():
    corpus = Corpus(
        corpus_name="SZ_FULL",
        registry_path="/home/ausgerechnet/corpora/cwb/registry/",
        s_meta="text_id"
    )

    query = r'[lemma="Angela"]? [lemma="Merkel"] [word="\("] [lemma="CDU"] [word="\)"]'
    result = corpus.query(query, s_break='s')
    concordance = corpus.concordance(result)

    print(concordance.breakdown)
    print(concordance.size)
    print(concordance.meta.head())
    print(concordance.lines([48349]))


@pytest.mark.readme_anchor
def test_anchor():
    corpus = Corpus(
        corpus_name="SZ_FULL",
        registry_path="/home/ausgerechnet/corpora/cwb/registry/",
        s_meta="text_id"
    )

    query = r'@0[lemma="Angela"]? @1[lemma="Merkel"] [word="\("] @2[lemma="CDU"] [word="\)"]'
    result = corpus.query(query, s_break='s')
    concordance = corpus.concordance(result)

    print(concordance.breakdown)
    print(concordance.size)
    print(concordance.meta.head())
    print(concordance.lines([48349]))


@pytest.mark.readme_collocates
def test_collocates():
    corpus = Corpus(
        corpus_name="SZ_FULL",
        registry_path="/home/ausgerechnet/corpora/cwb/registry/",
        s_meta="text_id"
    )

    query = '[lemma="Angela"]? [lemma="Merkel"] [word="\\("] [lemma="CDU"] [word="\\)"]'
    result = corpus.query(query, s_break='s')
    collocates = corpus.collocates(result)

    print(collocates.show(window=5).head())


@pytest.mark.readme_keywords
def test_keywords():
    meta = read_csv("/home/ausgerechnet/corpora/cwb/upload/efe/sz-full.tsv.gz",
                    sep="\t", index_col=0, dtype=str)
    ids = set(meta.loc[
        (meta['ressort'] == "Panorama") & (meta['month'] == '032011')
    ].index.values)

    corpus = Corpus(
        corpus_name="SZ_FULL",
        registry_path="/home/ausgerechnet/corpora/cwb/registry/",
        s_meta="text_id"
    )
    corpus.subcorpus_from_ids(ids, name='tmp_keywords')
    keywords = corpus.keywords('tmp_keywords')
    print(keywords.show(order='dice').head(50))


@pytest.mark.skip
@pytest.mark.readme_argmin
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
