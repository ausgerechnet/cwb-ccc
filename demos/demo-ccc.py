import json

import pytest
from pandas import read_csv

from ccc import Corpora, Corpus

from .conftest import LOCAL

corpus = Corpus(
    corpus_name="SZ_2009_14"
)

query = r'[lemma="Angela"]? [lemma="Merkel"] [word="\("] [lemma="CDU"] [word="\)"]'
result = corpus.query(query)
concordance = corpus.concordance(result)

print(concordance.breakdown)
print(concordance.size)
print(concordance.meta.head())
print(concordance.lines([567792]))


corpus = Corpus(
    corpus_name="SZ_2009_14"
)

query = r'@0[lemma="Angela"]? @1[lemma="Merkel"] [word="\("] @2[lemma="CDU"] [word="\)"]'
result = corpus.query(query)
concordance = corpus.concordance(result)

print(concordance.breakdown)
print(concordance.size)
print(concordance.lines([567792]))


corpus = Corpus(
    corpus_name="SZ_2009_14"
)

query = '[lemma="Angela"]? [lemma="Merkel"] [word="\\("] [lemma="CDU"] [word="\\)"]'
result = corpus.query(query, s_meta=['text_id'])
collocates = corpus.collocates(result)

print(collocates.show(window=5, order="log_likelihood").head())


@pytest.mark.readme_keywords
def test_keywords_sz():
    meta = read_csv("/home/ausgerechnet/corpora/cwb/upload/efe/sz-2009-14.tsv.gz",
                    sep="\t", index_col=0, dtype=str)
    ids = set(meta.loc[
        (meta['ressort'] == "Panorama") & (meta['month'] == '201103')
    ].index.values)
    meta['s_id'] = meta.index

    corpus = Corpus(
        corpus_name="SZ_2009_14",
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


@pytest.mark.setup
@pytest.mark.now
def test_corpora(germaparl):
    corpora = Corpora(registry_path=germaparl['registry_path'])
    print(corpora)
    corpus = corpora.activate(germaparl["corpus_name"])
    print(corpus)
    print(corpus.attributes_available)


@pytest.mark.skipif(not LOCAL, reason='works on my machine')
@pytest.mark.brexit
@pytest.mark.setup
def test_init_corpus(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    print(corpus)


@pytest.mark.skipif(not LOCAL, reason='works on my machine')
@pytest.mark.brexit
@pytest.mark.setup
def test_macro(brexit):
    corpus = Corpus(brexit['corpus_name'],
                    lib_path=brexit['lib_path'],
                    registry_path=brexit['registry_path'])
    cqp = corpus.start_cqp()
    cqp.Exec("Last=/ap();")
    counts = corpus.counts.matches(cqp, name="Last")
    cqp.__kill__()
    print(counts)


@pytest.mark.queries
def test_query(germaparl):

    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    query = r'"\[" ([word="[A-Z]+"] "/"?) + "\]"'
    dump = corpus.query(cqp_query=query)
    print(dump)
    print(dump.df)


@pytest.mark.queries
def test_query_context(germaparl):

    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    query = r'"\[" ([word="[A-Z]+"] "/"?) + "\]"'
    dump = corpus.query(cqp_query=query, context=20, context_break='s')
    print(dump)
    print(dump.df)


@pytest.mark.nocache
@pytest.mark.queries
def test_query_context_nocache(germaparl):

    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    query = r'"\[" ([word="[A-Z]+"] "/"?)+ "\]"'
    dump = corpus.query(cqp_query=query, context=20, context_break='s', name='parties')
    print(dump)
    print(dump.df)


@pytest.mark.queries
def test_query_breakdown(germaparl):

    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    query = r'"\[" ([word="[A-Z]+"] "/"?)+ "\]"'
    dump = corpus.query(query)
    print(dump.breakdown())


@pytest.mark.concordancing
def test_concordancing_simple(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])

    query = r'"\[" ([word="[A-Z]+"] "/"?)+ "\]"'
    dump = corpus.query(query)
    lines = dump.concordance()
    print(lines)
    print(lines.columns)
    from pprint import pprint
    pprint(lines['raw'].iloc[0])


@pytest.mark.concordancing
def test_concordancing_dataframes(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])

    query = r'"\[" ([word="[A-Z]+"] "/"?)+ "\]"'
    dump = corpus.query(query, context_break='s')
    lines = dump.concordance(form='dataframes')
    from pprint import pprint
    pprint(lines['df'].iloc[1])


@pytest.mark.concordancing
def test_concordancing_attributes(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])

    query = r'"\[" ([word="[A-Z]+"] "/"?)+ "\]"'

    dump = corpus.query(query, context_break='s')
    lines = dump.concordance(
        form='dataframes',
        p_show=['word', 'lemma'],
        s_show=['text_role']
    )
    print(lines.iloc[1])
    print(lines['df'].iloc[1])


@pytest.mark.anchor
def test_anchor(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])

    query = r'@1[pos="NE"]? @2[pos="NE"] "\[" (@3[word="[A-Z]+"]+ "/"?)+ "\]"'
    dump = corpus.query(query, context_break='s')
    lines = dump.concordance(form='dataframes')
    print()
    print(lines['df'].iloc[1])


@pytest.mark.collocates
def test_collocates(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])

    query = '"SPD"'
    dump = corpus.query(query, context=10, context_break='s')
    collocates = dump.collocates()
    print()
    print(collocates[[
        'O11', 'O12', 'O21', 'O22', 'E11', 'E12', 'E21', 'E22', 'log_likelihood'
    ]])


# @pytest.mark.now
def test_query_satt(germaparl):

    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    dump = corpus.query_s_att('p_type', {'interjection'})
    conc = dump.concordance(form='simple')
    print(conc)


# @pytest.mark.now
def test_query_satt_easy(brexit):

    corpus = Corpus(brexit['corpus_name'],
                    registry_path=brexit['registry_path'])
    dump = corpus.query_s_att('np')
    conc = dump.concordance(form='simple')
    print(conc)


@pytest.mark.keywords
def test_keywords(germaparl):

    party = {"CDU", "CSU"}
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    dump = corpus.dump_from_s_att('text_party', party)
    keywords = dump.keywords()
    print(keywords.head(50))


@pytest.mark.keywords
def test_keywords_query(germaparl):

    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    dump = corpus.query('"SPD" expand to s')
    keywords = dump.keywords()
    print(keywords.head(50))
