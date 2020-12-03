from ccc import Corpus
import pytest

from .conftest import local


@pytest.mark.skipif(not local, reason='works on my machine')
@pytest.mark.brexit
@pytest.mark.setup
def test_init_corpus(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    print(corpus)


@pytest.mark.skipif(not local, reason='works on my machine')
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
