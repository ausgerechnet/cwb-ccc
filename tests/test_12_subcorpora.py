from ccc import Corpus
from ccc.cwb import SubCorpora
from .conftest import DATA_PATH
import pytest


def test_subcorpora_from_dataframe(germaparl):

    corpus = Corpus(
        germaparl['corpus_name'],
        registry_dir=germaparl['registry_dir'],
        lib_dir=None,
        data_dir=DATA_PATH
    )

    factions = corpus.query_s_att('text_parliamentary_group').df.drop('text_parliamentary_group_cwbid', axis=1)
    factions.columns = ['subcorpus']

    subcorpora = SubCorpora(
        germaparl['corpus_name'],
        factions,
        registry_dir=germaparl['registry_dir'],
        lib_dir=None,
        data_dir=DATA_PATH
    )

    assert isinstance(subcorpora, SubCorpora)


@pytest.mark.now
def test_subcorpora_query(germaparl):

    corpus = Corpus(
        germaparl['corpus_name'],
        registry_dir=germaparl['registry_dir'],
        lib_dir=None,
        data_dir=DATA_PATH
    )

    factions = corpus.query_s_att('text_parliamentary_group').df.drop('text_parliamentary_group_cwbid', axis=1)
    factions.columns = ['subcorpus']

    subcorpora = SubCorpora(
        germaparl['corpus_name'],
        factions,
        registry_dir=germaparl['registry_dir'],
        lib_dir=None,
        data_dir=DATA_PATH
    )

    subcorpora.query('[lemma="und"]')

    print(subcorpora.nodes)


@pytest.mark.now
def test_subcorpora_collocates(germaparl):

    corpus = Corpus(
        germaparl['corpus_name'],
        registry_dir=germaparl['registry_dir'],
        lib_dir=None,
        data_dir=DATA_PATH
    )

    factions = corpus.query_s_att('text_parliamentary_group').df.drop('text_parliamentary_group_cwbid', axis=1)
    factions.columns = ['subcorpus']

    subcorpora = SubCorpora(
        germaparl['corpus_name'],
        factions,
        registry_dir=germaparl['registry_dir'],
        lib_dir=None,
        data_dir=DATA_PATH
    )

    subcorpora.query('[lemma="und"]')

    print(subcorpora.collocates())


@pytest.mark.now
def test_subcorpora_concordance(germaparl):

    corpus = Corpus(
        germaparl['corpus_name'],
        registry_dir=germaparl['registry_dir'],
        lib_dir=None,
        data_dir=DATA_PATH
    )

    factions = corpus.query_s_att('text_parliamentary_group').df.drop('text_parliamentary_group_cwbid', axis=1)
    factions.columns = ['subcorpus']

    subcorpora = SubCorpora(
        germaparl['corpus_name'],
        factions,
        registry_dir=germaparl['registry_dir'],
        lib_dir=None,
        data_dir=DATA_PATH
    )

    subcorpora.query('[lemma="und"]')

    print(subcorpora.concordance())
