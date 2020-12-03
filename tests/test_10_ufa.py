from pandas import read_csv
from ccc import Corpus
from ccc.ufa import UFA
import pytest

from .conftest import local


@pytest.mark.skipif(not local, reason='works on my machine')
@pytest.mark.brexit
def test_keywords(brexit):

    # get s_att-split
    meta = read_csv(brexit['meta_path'], dtype=str, sep="\t", nrows=100000)
    s_values = list(meta['ymd'].value_counts().head(5).index)
    ids = dict()
    for s in s_values:
        ids[s] = set(meta.loc[meta['ymd'] == s]['id'])

    # keywords
    corpus = Corpus(brexit['corpus_name'])
    ufa = UFA(corpus, ids, s_att='tweet_id')
    tables = ufa.keywords()
    print(tables)


@pytest.mark.skipif(not local, reason='works on my machine')
@pytest.mark.brexit
def test_collocates(brexit):

    # get s_att-split
    meta = read_csv(brexit['meta_path'], dtype=str, sep="\t", nrows=100000)
    s_values = list(meta['ymd'].value_counts().head(5).index)
    ids = dict()
    for s in s_values:
        ids[s] = set(meta.loc[meta['ymd'] == s]['id'])

    # keywords
    corpus = Corpus(brexit['corpus_name'])
    ufa = UFA(corpus, ids, s_att='tweet_id')
    tables = ufa.collocates(cqp_query='[lemma="johnson"]', order='log_likelihood')
    print(tables)
    # for key in tables.keys():
    #     dir_out = "/home/ausgerechnet/Downloads/"
    #     tables[key].to_csv(os.path.join(dir_out, key + ".tsv.gz"),
    #                        sep="\t", compression="gzip")
