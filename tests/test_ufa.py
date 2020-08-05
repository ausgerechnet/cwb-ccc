from pandas import read_csv
from ccc import Corpus
from ccc.ufa import UFA
import pytest


def test_keywords(sz_corpus):

    # get s_att-split
    s_att = 'month'
    meta = read_csv(sz_corpus['meta_path'], dtype=str, sep="\t").head(100000)
    ids = dict()
    for s in set(meta[s_att]):
        ids[s] = set(meta.loc[meta[s_att] == s]['id'])

    # keywords
    corpus = Corpus(sz_corpus['corpus_name'])
    ufa = UFA(corpus, ids)
    tables = ufa.keywords()
    print(tables)


@pytest.mark.now
def test_collocates(sz_corpus):

    # get s_att-split
    s_att = 'month'
    meta = read_csv(sz_corpus['meta_path'], dtype=str, sep="\t")
    ids = dict()
    s_atts = list(set(meta[s_att]))[:10]
    for s in s_atts:
        ids[s] = set(meta.loc[meta[s_att] == s]['id'])

    # keywords
    corpus = Corpus(sz_corpus['corpus_name'])
    ufa = UFA(corpus, ids)
    tables = ufa.collocates(cqp_query='"Atomkraft"', order='log_likelihood')
    # for key in tables.keys():
    #     dir_out = "/home/ausgerechnet/Downloads/"
    #     tables[key].to_csv(os.path.join(dir_out, key + ".tsv.gz"),
    #                        sep="\t", compression="gzip")
