from pandas import read_csv, cut
from ccc import Corpus
import pytest


@pytest.mark.now
def test_ufa(sz_corpus):

    s_att = 'month'

    corpus = Corpus(sz_corpus['corpus_name'])

    # get s_att-split
    meta = read_csv(sz_corpus['meta_path'], dtype=str, sep="\t").head(1000)
    print(meta)

    # get bin positions
    ids = dict()
    for s in set(meta[s_att]):
        ids[s] = set(meta.loc[meta[s_att] == s]['id'])

    corpus.ufa(ids, 'lemma', )
