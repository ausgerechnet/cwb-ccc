from ccc import Corpus
from .conftest import DATA_PATH


def test_alignment(holmes_en):

    corpus = Corpus(
        holmes_en['corpus_name'],
        registry_dir=holmes_en['registry_dir'],
        lib_dir=None,
        data_dir=DATA_PATH
    )

    print(corpus.available_attributes())
