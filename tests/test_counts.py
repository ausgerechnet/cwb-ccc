from ccc.cwb import Corpus
from ccc.counts import Counts
from ccc.counts import cwb_scan_corpus
from ccc.utils import formulate_cqp_query
import pandas as pd
import pytest


@pytest.mark.cwb_counts
def test_cwb_scan_corpus(brexit_corpus):
    from tempfile import NamedTemporaryFile
    corpus = Corpus(brexit_corpus['corpus_name'])
    corpus.query('[lemma="test"]', name='tmp')

    with NamedTemporaryFile(mode="wt") as f:
        corpus.cqp.Exec('dump tmp > "%s"' % f.name)
        df1 = cwb_scan_corpus(f.name, brexit_corpus['corpus_name'])

    corpus.subcorpus_from_query(query='[lemma="farage"] expand to tweet',
                                name='farage')
    corpus.activate_subcorpus('farage')
    corpus.query('[lemma="test"]', name='tmp')

    with NamedTemporaryFile(mode="wt") as f:
        corpus.cqp.Exec('dump tmp > "%s"' % f.name)
        df2 = cwb_scan_corpus(f.name, brexit_corpus['corpus_name'])

    assert(sum(df2['freq']) != sum(df1['freq']))


@pytest.mark.cwb_counts
def test_count_cpos(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    counts = corpus.counts.cpos(list(range(1, 1000)), p_atts=['word'])
    assert(type(counts) == pd.DataFrame)


@pytest.mark.cwb_counts
def test_count_cpos_combo(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    counts = corpus.counts.cpos(list(range(1, 1000)), p_atts=['lemma', 'pos'])
    assert(type(counts) == pd.DataFrame)
    assert(counts.index.names == ['lemma', 'pos'])


@pytest.mark.cwb_counts
def test_marginals(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    counts = corpus.counts.marginals(["Angela", "Merkel", "CDU"])
    assert(len(counts) == 3)


@pytest.mark.cwb_counts
def test_marginals_patterns(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    counts = corpus.counts.marginals(["Ang*", "Merkel", "CDU"])
    assert(len(counts) == 3)
    counts = corpus.counts.marginals(["Angel*", "Merkel", "CDU"], pattern=True)
    assert(len(counts) == 3)


@pytest.mark.cwb_counts
def test_count_items(sz_corpus):

    corpus = Corpus(sz_corpus['corpus_name'])

    # whole corpus
    counts1 = corpus.counts.marginals(["Angela", "Merkel", "CDU"])
    counts2 = corpus.counts.mwus(corpus.cqp, ['"Angela"', '"Merkel"', '"CDU"'])
    assert(list(counts1["freq"]) == list(counts2["freq"]))

    # subcorpus
    corpus.subcorpus_from_query(query='[lemma="Bundesregierung"] expand to s',
                                name='Bundesregierung')
    corpus.activate_subcorpus('Bundesregierung')

    counts1 = corpus.counts.marginals(["Angela", "Merkel", "CDU"])
    counts2 = corpus.counts.mwus(corpus.cqp, ['"Angela"', '"Merkel"', '"CDU"'])
    assert(counts1.loc['Angela', 'freq'] > counts2.loc['"Angela"', 'freq'])

    # whole corpus
    corpus.activate_subcorpus()
    counts1 = corpus.counts.marginals(["Angela", "Merkel", "CDU"])
    counts2 = corpus.counts.mwus(corpus.cqp, ['"Angela"', '"Merkel"', '"CDU"'])
    assert(list(counts1["freq"]) == list(counts2["freq"]))


@pytest.mark.cwb_counts
def test_count_matches(brexit_corpus):
    corpus = Corpus(brexit_corpus['corpus_name'])
    corpus.query(
        query='[lemma="nigel"]',
        context=10,
        s_context='tweet',
        name='Test'
    )
    counts = corpus.counts.matches(corpus.cqp, 'Test')
    assert("Nigel" in counts.index)


@pytest.mark.mwus
def test_count_mwus_3(sz_corpus):

    # whole corpus
    corpus = Corpus(sz_corpus['corpus_name'])
    items = ["Horst Seehofer", r"( CSU )", "CSU", "WES324", "CSU"]
    queries = [
        formulate_cqp_query([item]) for item in items
    ]

    counts3 = corpus.counts.mwus(
        corpus.cqp,
        queries,
        strategy=3,
        fill_missing=False
    )

    print(counts3)


@pytest.mark.mwus
@pytest.mark.cwb_counts
def test_count_mwus_strategies(sz_corpus):

    # whole corpus
    corpus = Corpus(sz_corpus['corpus_name'])
    items = ["Horst Seehofer", r"( CSU )", "CSU", "WES324", "CSU"]
    queries = [
        formulate_cqp_query([item]) for item in items
    ]

    counts1 = corpus.counts.mwus(
        corpus.cqp,
        queries,
        strategy=1,
        fill_missing=False
    )
    assert('([word="CSU"])' in counts1.index)

    counts2 = corpus.counts.mwus(
        corpus.cqp,
        queries,
        strategy=2,
        fill_missing=False
    )

    counts3 = corpus.counts.mwus(
        corpus.cqp,
        queries,
        strategy=3,
        fill_missing=False
    )

    assert(counts2.equals(counts3))
    assert(sum(counts1['freq']) == sum(counts2['freq']))


@pytest.mark.cwb_counts
def test_count_items_subcorpora(sz_corpus):

    # subcorpus
    corpus = Corpus(sz_corpus['corpus_name'])
    corpus.subcorpus_from_s_att("text_year", ["2011"], name='c2011')
    corpus.activate_subcorpus('c2011')
    items = ["Horst Seehofer", r"( CSU )", "CSU", "WES324", "CSU"]
    queries = [formulate_cqp_query([item]) for item in items]

    counts1 = corpus.counts.mwus(
        corpus.cqp,
        queries,
        strategy=1,
        fill_missing=False
    )
    assert(sum(counts1['freq']) > 0)

    counts2 = corpus.counts.mwus(
        corpus.cqp,
        queries,
        strategy=2,
        fill_missing=False
    )

    counts3 = corpus.counts.mwus(
        corpus.cqp,
        queries,
        strategy=3,
        fill_missing=False
    )
    print(counts2.equals(counts3))


# @pytest.mark.now
# @pytest.mark.cwb_counts
# def test_count_dump_1(sz_corpus):

#     strategy = 1
#     corpus = Corpus(sz_corpus['corpus_name'])
#     df_dump = corpus.dump_from_query(
#         query=sz_corpus['query'],
#         s_query=sz_corpus['s_query'],
#         match_strategy='standard'
#     )

#     # no split
#     # - easy
#     counts_ns_e = corpus.count_dump(df_dump,
#                                     strategy=strategy,
#                                     split=False,
#                                     p_atts=['word'])
#     # - combo
#     counts_ns_c = corpus.count_dump(df_dump,
#                                     strategy=strategy,
#                                     split=False,
#                                     p_atts=['word', 'pos'])

#     # split
#     # - easy
#     counts_s_e = corpus.count_dump(df_dump,
#                                    strategy=strategy,
#                                    split=True,
#                                    p_atts=['word'])
#     # - combo
#     counts_s_c = corpus.count_dump(df_dump,
#                                    strategy=strategy,
#                                    split=True,
#                                    p_atts=['word', 'pos'])

#     print(counts_ns_e)
#     print(counts_ns_c)
#     print(counts_s_e)
#     print(counts_s_c)


# def test_count_dump_2(sz_corpus):

#     strategy = 2
#     corpus = Corpus(sz_corpus['corpus_name'])
#     df_dump = corpus.dump_from_query(
#         query=sz_corpus['query'],
#         s_query=sz_corpus['s_query'],
#         match_strategy='standard'
#     )

#     # no split
#     # - easy
#     counts_ns_e = corpus.count_dump(df_dump,
#                                     strategy=strategy,
#                                     split=False,
#                                     p_atts=['word'])
#     # - combo
#     counts_ns_c = corpus.count_dump(df_dump,
#                                     strategy=strategy,
#                                     split=False,
#                                     p_atts=['word', 'pos'])

#     # split
#     # - easy
#     counts_s_e = corpus.count_dump(df_dump,
#                                    strategy=strategy,
#                                    split=True,
#                                    p_atts=['word'])
#     # - combo
#     counts_s_c = corpus.count_dump(df_dump,
#                                    strategy=strategy,
#                                    split=True,
#                                    p_atts=['word', 'pos'])

#     print(counts_ns_e)
#     print(counts_ns_c)
#     print(counts_s_e)
#     print(counts_s_c)


@pytest.mark.cwb_counts
def test_counts_dump_1_split(brexit_corpus):
    strategy = 1

    corpus = Corpus(brexit_corpus['corpus_name'])
    dump = corpus.dump_from_query('[lemma="Angela"%cd] [lemma="Merkel"%cd]')

    df = corpus.counts.dump(dump, p_atts=['word'], split=True, strategy=strategy)
    print(df)

    df = corpus.counts.dump(dump, p_atts=['word', 'lemma'], split=True, strategy=strategy)
    print(df)


@pytest.mark.cwb_counts
def test_counts_dump_1_no_split(sz_corpus):
    strategy = 1

    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.dump_from_query('[lemma="Angela"%cd] [lemma="Merkel"%cd]')

    # no split
    df = corpus.counts.dump(dump, p_atts=['word'], split=False, strategy=strategy)
    print(df)

    df = corpus.counts.dump(dump, p_atts=['word', 'pos'], split=False, strategy=strategy)
    print(df)


@pytest.mark.count_class
def test_counts_dump_2(sz_corpus):
    strategy = 2

    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.dump_from_query('[lemma="Angela"%cd] [lemma="Merkel"%cd]')

    print("\n\n\nsplit\n")
    df = corpus.counts.dump(dump, p_atts=['word'], split=True, strategy=strategy)
    print(df)

    df = corpus.counts.dump(dump, p_atts=['word', 'pos'], split=True, strategy=strategy)
    print(df)

    print("\n\n\nno split\n")
    df = corpus.counts.dump(dump, p_atts=['word'], split=False, strategy=strategy)
    print(df)

    df = corpus.counts.dump(dump, p_atts=['word', 'pos'], split=False, strategy=strategy)
    print(df)


@pytest.mark.cwb_counts
def test_counts_matches_1(sz_corpus):
    strategy = 1

    corpus = Corpus(sz_corpus['corpus_name'])
    corpus.subcorpus_from_query('[lemma="Angela"%cd] [lemma="Merkel"%cd]', name='Last')

    print("\n\n\nno split\n")
    df = corpus.counts.matches(corpus.cqp, 'Last', p_atts=['word'], split=False,
                               flags="%cd", strategy=strategy)
    print(df)

    df = corpus.counts.matches(corpus.cqp, 'Last', p_atts=['word'], split=False,
                               strategy=strategy)
    print(df)

    print("\n\n\n split\n")
    df = corpus.counts.matches(corpus.cqp, 'Last', p_atts=['word'], split=True,
                               flags="%cd", strategy=strategy)
    print(df)

    df = corpus.counts.matches(corpus.cqp, 'Last', p_atts=['word'], split=True,
                               strategy=strategy)
    print(df)


@pytest.mark.cwb_counts
def test_counts_matches_2(sz_corpus):
    strategy = 2

    corpus = Corpus(sz_corpus['corpus_name'])
    corpus.subcorpus_from_query('[lemma="Angela"%cd] [lemma="Merkel"%cd]', name='Last')

    print("\n\n\nno split\n")
    df = corpus.counts.matches(corpus.cqp, 'Last', p_atts=['word'], split=False,
                               flags="%cd", strategy=strategy)
    print(df)

    df = corpus.counts.matches(corpus.cqp, 'Last', p_atts=['word'], split=False,
                               strategy=strategy)
    print(df)

    print("\n\n\n split\n")
    df = corpus.counts.matches(corpus.cqp, 'Last', p_atts=['word'], split=True,
                               flags="%cd", strategy=strategy)
    print(df)

    df = corpus.counts.matches(corpus.cqp, 'Last', p_atts=['word'], split=True,
                               strategy=strategy)
    print(df)


@pytest.mark.cwb_counts
def test_counts_matches_3(sz_corpus):
    strategy = 3

    corpus = Corpus(sz_corpus['corpus_name'])
    corpus.subcorpus_from_query('[lemma="Angela"%cd] [lemma="Merkel"%cd]', name='Last')

    df = corpus.counts.matches(corpus.cqp, 'Last', p_atts=['word'], split=True,
                               flags="%cd", strategy=strategy)
    print(df)

    df = corpus.counts.matches(corpus.cqp, 'Last', p_atts=['word'], split=True,
                               strategy=strategy)
    print(df)

    df = corpus.counts.matches(corpus.cqp, 'Last', p_atts=['word', 'pos'], split=True,
                               strategy=strategy)
    print(df)


@pytest.mark.cwb_counts
def test_counts_marginals(sz_corpus):
    counter = Counts(sz_corpus['corpus_name'])
    df = counter.marginals(['angela', 'merkel'], flags=3)
    print(df)


@pytest.mark.cwb_counts
def test_counts_mwus(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    df = corpus.counts.mwus(corpus.cqp,
                            ['[lemma="Angela"%cd & pos="NE"] [lemma="Merkel"]',
                             '[lemma="Horst"]'],
                            strategy=1)
    print(df)

    df = corpus.counts.mwus(corpus.cqp,
                            ['[lemma="Angela"%cd & pos="NE"] [lemma="Merkel"]',
                             '[lemma="Horst"]'],
                            strategy=3,
                            p_atts=['lemma', 'pos'])
    print(df)

    df = corpus.counts.mwus(corpus.cqp,
                            ['[lemma="Angela"%cd & pos="NE"] [lemma="Merkel"]',
                             '[lemma="Horst"]'],
                            strategy=3,
                            p_atts=['lemma'])

    print(df)


@pytest.mark.cwb_counts
def test_cwb_counts(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    df = corpus.counts.mwus(corpus.cqp,
                            ['[lemma="Angela"%cd & pos="NE"] [lemma="Merkel"]',
                             '[lemma="Horst"]'])
    print(df)
