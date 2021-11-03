from ccc.cwb import Corpus
from ccc.counts import cwb_scan_corpus, read_freq_list, cwb_lexdecode
from ccc.utils import format_cqp_query
import pandas as pd
import pytest
from tempfile import NamedTemporaryFile

from .conftest import LOCAL, DATA_PATH


def get_corpus(corpus_settings, data_path=DATA_PATH):

    return Corpus(
        corpus_settings['corpus_name'],
        registry_path=corpus_settings['registry_path'],
        lib_path=corpus_settings.get('lib_path', None),
        data_path=data_path
    )


@pytest.mark.cwb_counts
def test_cwb_scan_corpus_subcorpora(germaparl):

    corpus = get_corpus(germaparl)
    cqp = corpus.start_cqp()

    # get a DumpFrame
    cqp.nqr_from_query('[lemma="Helmut"]', name='Tmp')

    # run cwb-scan-corpus on dump
    with NamedTemporaryFile(mode="wt") as f:
        cqp.Exec('dump Tmp > "%s"' % f.name)
        df1 = cwb_scan_corpus(f.name, germaparl['corpus_name'],
                              germaparl['registry_path'])

    # activate a sub-corpus
    cqp.nqr_from_query(query='[lemma="und"] expand to s', name='und')
    cqp.nqr_activate(corpus.corpus_name, 'und')

    # run same query on sub-corpus
    cqp.nqr_from_query('[lemma="Helmut"]', name='Tmp')

    # run cwb-scan-corpus on dump
    with NamedTemporaryFile(mode="wt") as f:
        cqp.Exec('dump Tmp > "%s"' % f.name)
        df2 = cwb_scan_corpus(f.name, germaparl['corpus_name'],
                              germaparl['registry_path'])

    # check that results are different
    assert(sum(df2['freq']) != sum(df1['freq']))

    cqp.__kill__()


@pytest.mark.marginals
@pytest.mark.cwb_counts
def test_cwb_scan_corpus_marginal(germaparl):

    df1 = cwb_scan_corpus(
        None,
        germaparl['corpus_name'],
        germaparl['registry_path']
    )
    df2 = cwb_scan_corpus(
        None,
        germaparl['corpus_name'],
        germaparl['registry_path'],
        p_atts=['lemma', 'pos']
    )
    assert(isinstance(df1.index, pd.MultiIndex))
    assert(isinstance(df2.index, pd.MultiIndex))
    assert(df1.index.names == ['word'])
    assert(df2.index.names == ['lemma', 'pos'])
    assert(df1.columns == df2.columns)


@pytest.mark.marginals
@pytest.mark.cwb_counts
def test_marginals(germaparl):
    corpus = get_corpus(germaparl)
    freqframe = corpus.marginals(["Helmut", "Kohl", "CDU"])
    assert(len(freqframe) == 3)
    assert(isinstance(freqframe, pd.DataFrame))
    print(freqframe.index)


@pytest.mark.marginals
@pytest.mark.cwb_counts
def test_marginals_patterns(germaparl):
    corpus = get_corpus(germaparl)
    freqframe = corpus.marginals(["H.*", "Kohl", "CDU"])
    assert(len(freqframe) == 3)
    assert(isinstance(freqframe, pd.DataFrame))
    assert(freqframe.loc['H.*']['freq'] == 0)
    freqframe = corpus.marginals(["H.*", "Kohl", "CDU"], pattern=True)
    assert(len(freqframe) == 3)
    assert(isinstance(freqframe, pd.DataFrame))
    assert(freqframe.loc['H.*']['freq'] == 2466)


@pytest.mark.cwb_counts
def test_count_cpos(germaparl):
    corpus = get_corpus(germaparl)
    freqframe = corpus.counts.cpos(list(range(1, 1000)), p_atts=['word'])
    assert(isinstance(freqframe, pd.DataFrame))
    assert(isinstance(freqframe.index, pd.MultiIndex))


@pytest.mark.cwb_counts
def test_count_cpos_combo(germaparl):
    corpus = get_corpus(germaparl)
    freqframe = corpus.counts.cpos(list(range(1, 1000)), p_atts=['lemma', 'pos'])
    assert(isinstance(freqframe, pd.DataFrame))
    assert(isinstance(freqframe.index, pd.MultiIndex))


@pytest.mark.cwb_counts
def test_count_items(germaparl):

    corpus = get_corpus(germaparl)
    cqp = corpus.start_cqp()

    items = ["Helmut", "Kohl", "CDU"]
    queries = [
        format_cqp_query([item]) for item in items
    ]

    # whole corpus
    counts1 = corpus.marginals(items)
    counts2 = corpus.counts.mwus(cqp, queries)
    print(counts1, counts2)
    assert(list(counts1["freq"]) == list(counts2["freq"]))

    # subcorpus
    cqp.nqr_from_query(query='[lemma="und"] expand to s', name='und')
    cqp.nqr_activate(corpus.corpus_name, 'und')
    counts1 = corpus.marginals(items)
    counts2 = corpus.counts.mwus(cqp, queries)
    assert(counts1.loc[items[0], 'freq'] > counts2.loc[queries[0], 'freq'])

    # whole corpus
    cqp.nqr_activate(corpus.corpus_name)
    counts1 = corpus.marginals(items)
    counts2 = corpus.counts.mwus(cqp, queries)
    assert(list(counts1["freq"]) == list(counts2["freq"]))

    cqp.__kill__()


@pytest.mark.skipif(not LOCAL, reason='works on my machine')
@pytest.mark.brexit
@pytest.mark.cwb_counts
def test_count_matches(brexit):
    corpus = get_corpus(brexit)
    corpus.query(
        cqp_query='[lemma="nigel"]',
        context=10,
        context_break='tweet',
        name='Nigel'
    )
    cqp = corpus.start_cqp()
    counts = corpus.counts.matches(cqp, 'Nigel')
    cqp.__kill__()
    assert("Nigel" in counts.index)


@pytest.mark.mwus
def test_count_mwus_3(germaparl):

    # whole corpus
    corpus = get_corpus(germaparl)
    items = ["Horst Seehofer", r"( CSU )", "CSU", "WES324", "CSU"]
    queries = [
        format_cqp_query([item]) for item in items
    ]

    cqp = corpus.start_cqp()
    counts3 = corpus.counts.mwus(
        cqp,
        queries,
        strategy=3,
        fill_missing=False
    )
    cqp.__kill__()

    assert(counts3['freq']['CSU'] == 635)


@pytest.mark.mwus
@pytest.mark.cwb_counts
def test_count_mwus_strategies(germaparl):

    # whole corpus
    corpus = get_corpus(germaparl)
    items = ["Horst Seehofer", r"( CSU )", "CSU", "WES324"]
    queries = [
        format_cqp_query([item]) for item in items
    ]

    cqp = corpus.start_cqp()
    counts1 = corpus.counts.mwus(
        cqp,
        queries,
        strategy=1,
        fill_missing=False
    )
    assert('([word="CSU"])' in counts1.index)

    counts2 = corpus.counts.mwus(
        cqp,
        queries,
        strategy=2,
        fill_missing=False
    )

    counts3 = corpus.counts.mwus(
        cqp,
        queries,
        strategy=3,
        fill_missing=False
    )

    cqp.__kill__()
    assert(counts2.equals(counts3))
    assert(sum(counts1['freq']) == sum(counts2['freq']))


@pytest.mark.cwb_counts
def test_count_items_subcorpora(germaparl):

    # subcorpus
    corpus = get_corpus(germaparl)
    cqp = corpus.start_cqp()
    dump = corpus.dump_from_s_att("text_role", ["presidency"])
    cqp.nqr_from_dump(dump, 'Presidency')
    cqp.nqr_activate(corpus.corpus_name, 'Presidency')
    items = ["Horst Seehofer", r"( CSU )", "CSU", "WES324", "CSU"]
    queries = [format_cqp_query([item]) for item in items]

    counts1 = corpus.counts.mwus(
        cqp,
        queries,
        strategy=1,
        fill_missing=False
    )
    assert(sum(counts1['freq']) > 0)

    counts2 = corpus.counts.mwus(
        cqp,
        queries,
        strategy=2,
        fill_missing=False
    )

    counts3 = corpus.counts.mwus(
        cqp,
        queries,
        strategy=3,
        fill_missing=False
    )
    assert(counts2.equals(counts3))
    cqp.__kill__()


# def test_count_dump_1(germaparl):

#     strategy = 1
#     corpus = get_corpus(germaparl)
#     df_dump = corpus.dump_from_query(
#         query=germaparl['query'],
#         s_query=germaparl['s_query'],
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


# def test_count_dump_2(germaparl):

#     strategy = 2
#     corpus = get_corpus(germaparl)
#     df_dump = corpus.dump_from_query(
#         query=germaparl['query'],
#         s_query=germaparl['s_query'],
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
def test_counts_dump_1_split(germaparl):
    strategy = 1

    corpus = get_corpus(germaparl)
    dump = corpus.dump_from_query('[lemma="die" %cd] [pos="N.*"]')

    df = corpus.counts.dump(dump, p_atts=['word'], split=True, strategy=strategy)
    assert(int(df["freq"]["der"]) == 3775)

    df = corpus.counts.dump(dump, p_atts=['word', 'lemma'], split=True, strategy=strategy)
    assert(int(df["freq"][("der", "die")]) == 3775)


@pytest.mark.cwb_counts
def test_counts_dump_1_no_split(germaparl):
    strategy = 1

    corpus = get_corpus(germaparl)
    dump = corpus.dump_from_query('[lemma="Helmut"%cd] [lemma="Kohl"%cd]')

    # no split
    df = corpus.counts.dump(dump, p_atts=['word'], split=False, strategy=strategy)
    assert("Helmut Kohl" in df.index)

    df = corpus.counts.dump(dump, p_atts=['word', 'pos'], split=False, strategy=strategy)
    assert(("Helmut Kohl", "NE NE") in df.index)


@pytest.mark.cwb_counts
def test_counts_dump_2(germaparl):
    strategy = 2

    corpus = get_corpus(germaparl)
    dump = corpus.dump_from_query('[lemma="Helmut"%cd] [lemma="Kohl"%cd]')

    df = corpus.counts.dump(dump, p_atts=['word'], split=True, strategy=strategy)
    assert(df["freq"]["Helmut"] == 6)

    df = corpus.counts.dump(dump, p_atts=['word', 'pos'], split=True, strategy=strategy)
    assert(df["freq"][("Helmut", "NE")] == 6)

    df = corpus.counts.dump(dump, p_atts=['word'], split=False, strategy=strategy)
    assert("Helmut Kohl" in df.index)
    assert(df["freq"].iloc[0] == 6)

    df = corpus.counts.dump(dump, p_atts=['word', 'pos'], split=False, strategy=strategy)
    assert(("Helmut Kohl", "NE NE") in df.index)
    assert(df["freq"].iloc[0] == 6)


@pytest.mark.cwb_counts
def test_counts_matches_1(germaparl):
    strategy = 1

    corpus = get_corpus(germaparl)
    cqp = corpus.start_cqp()
    cqp.nqr_from_query('[lemma="Helmut"%cd] [lemma="Kohl"%cd]', name='Last')
    cqp.nqr_activate(corpus.corpus_name, 'Last')

    df = corpus.counts.matches(cqp, 'Last', p_atts=['word'], split=False,
                               flags="%cd", strategy=strategy)
    assert("helmut kohl" in df.index)
    df = corpus.counts.matches(cqp, 'Last', p_atts=['word'], split=False,
                               strategy=strategy)
    assert("Helmut Kohl" in df.index)

    df = corpus.counts.matches(cqp, 'Last', p_atts=['word'], split=True,
                               flags="%cd", strategy=strategy)
    assert("helmut" in df.index)

    df = corpus.counts.matches(cqp, 'Last', p_atts=['word'], split=True,
                               strategy=strategy)
    assert("Helmut" in df.index)

    cqp.__kill__()


@pytest.mark.cwb_counts
def test_counts_matches_2(germaparl):
    strategy = 2

    corpus = get_corpus(germaparl)

    cqp = corpus.start_cqp()
    cqp.nqr_from_query('[lemma="Helmut"%cd] [lemma="Kohl"%cd]', name='Last')
    cqp.nqr_activate(corpus.corpus_name, 'Last')
    df = corpus.counts.matches(cqp, 'Last', p_atts=['word'], split=False,
                               flags="%cd", strategy=strategy)
    assert("helmut kohl" in df.index)

    df = corpus.counts.matches(cqp, 'Last', p_atts=['word'], split=False,
                               strategy=strategy)
    assert("Helmut Kohl" in df.index)

    df = corpus.counts.matches(cqp, 'Last', p_atts=['word'], split=True,
                               flags="%cd", strategy=strategy)
    assert("helmut" in df.index)

    df = corpus.counts.matches(cqp, 'Last', p_atts=['word'], split=True,
                               strategy=strategy)
    assert("Helmut" in df.index)
    cqp.__kill__()


@pytest.mark.cwb_counts
def test_counts_matches_3(germaparl):
    strategy = 3

    corpus = get_corpus(germaparl)
    cqp = corpus.start_cqp()
    cqp.nqr_from_query('[lemma="Helmut"%cd] [lemma="Kohl"%cd]', name='Last')
    df = corpus.counts.matches(cqp, 'Last', p_atts=['word'], split=True,
                               flags="%cd", strategy=strategy)
    assert("helmut" in df.index)

    df = corpus.counts.matches(cqp, 'Last', p_atts=['word'], split=True,
                               strategy=strategy)
    assert("Helmut" in df.index)

    df = corpus.counts.matches(cqp, 'Last', p_atts=['word', 'pos'], split=True,
                               strategy=strategy)
    assert(("Helmut", "NE") in df.index)
    cqp.__kill__()


@pytest.mark.cwb_counts
def test_counts_mwus(germaparl):
    corpus = get_corpus(germaparl)
    cqp = corpus.start_cqp()
    queries = ['[lemma="Helmut"%cd & pos="NE"] [lemma="Kohl"]', '[lemma="Horst"]']
    df = corpus.counts.mwus(cqp,
                            queries,
                            strategy=1)
    assert(df['freq'][queries[0]] == 6)

    df = corpus.counts.mwus(cqp,
                            queries,
                            strategy=3,
                            p_atts=['lemma', 'pos'])
    assert(df['freq'][('Horst', 'NE')] == 55)

    df = corpus.counts.mwus(cqp,
                            queries,
                            strategy=3,
                            p_atts=['lemma'])

    assert(df['freq']['Horst'] == 55)
    cqp.__kill__()


@pytest.mark.cwb_counts
def test_cwb_counts(germaparl):
    corpus = get_corpus(germaparl)
    cqp = corpus.start_cqp()
    queries = ['[lemma="Helmut"%cd & pos="NE"] [lemma="Kohl"]', '[lemma="Horst"]']
    df = corpus.counts.mwus(cqp,
                            queries)
    assert(df['freq'][queries[1]] == 55)
    cqp.__kill__()


@pytest.mark.cwb_counts
def test_read_and_lexdecode(germaparl):

    df1, R1 = read_freq_list(germaparl['freq_list'])
    df2, R2 = cwb_lexdecode(germaparl['corpus_name'],
                            germaparl['registry_path'],
                            'lemma')

    assert(R1 == R2)
    assert(df1.equals(df2))
