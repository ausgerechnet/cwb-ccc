from ccc import Corpus
from .conftest import DATA_PATH


def test_alignment_attribute(holmes_de, holmes_en):

    corpus = Corpus(
        holmes_de['corpus_name'],
        registry_dir=holmes_en['registry_dir'],
        lib_dir=None,
        data_dir=DATA_PATH
    )

    assert holmes_en['corpus_name'].lower() in corpus.available_attributes()['attribute'].to_list()

    corpus = Corpus(
        holmes_en['corpus_name'],
        registry_dir=holmes_en['registry_dir'],
        lib_dir=None,
        data_dir=DATA_PATH
    )

    assert holmes_de['corpus_name'].lower() in corpus.available_attributes()['attribute'].to_list()


def test_alignment_dump2aatt(holmes_de, holmes_en):

    src = Corpus(
        holmes_de['corpus_name'],
        registry_dir=holmes_de['registry_dir'],
        lib_dir=None,
        data_dir=DATA_PATH
    )

    tgt = holmes_en['corpus_name']
    tgt_attribute = tgt.lower()

    matches = src.query('[lemma="ich"]')
    matches.cpos2alg(44, tgt_attribute)
    a = matches.dump2aatt(matches.df, tgt_attribute)
    assert len(a) == 6


def test_alignment_concordancing(holmes_de, holmes_en):

    src = Corpus(
        holmes_de['corpus_name'],
        registry_dir=holmes_de['registry_dir'],
        lib_dir=None,
        data_dir=DATA_PATH
    )

    tgt = holmes_en['corpus_name']
    tgt_attribute = tgt.lower()

    matches = src.query('[lemma="ich"]', context=5)
    result = matches.concordance(a_show=[tgt_attribute],
                                 p_show=['word', 'lemma'])

    assert 'holmes-en_word' in result.columns
    assert 'holmes-en_lemma' in result.columns
