from pandas import read_csv
from ccc import Corpus
from ccc.ufa import UFA
import pytest

from .conftest import LOCAL, DATA_PATH


def get_corpus(corpus_settings, data_path=DATA_PATH):

    return Corpus(
        corpus_settings['corpus_name'],
        registry_path=corpus_settings['registry_path'],
        lib_path=corpus_settings.get('lib_path', None),
        data_path=data_path
    )


@pytest.mark.skipif(not LOCAL, reason='works on my machine')
@pytest.mark.brexit
def test_keywords(brexit):

    # get s_att-split
    meta = read_csv(brexit['meta_path'], dtype=str, sep="\t", nrows=100000)
    s_values = list(meta['ymd'].value_counts().head(5).index)
    ids = dict()
    for s in s_values:
        ids[s] = set(meta.loc[meta['ymd'] == s]['id'])

    # keywords
    corpus = get_corpus(brexit)
    ufa = UFA(corpus, ids, s_att='tweet_id')
    tables = ufa.keywords(order='log_likelihood')
    print(tables)


@pytest.mark.skipif(not LOCAL, reason='works on my machine')
@pytest.mark.brexit
def test_collocates(brexit):

    # get s_att-split
    meta = read_csv(brexit['meta_path'], dtype=str, sep="\t", nrows=100000)
    s_values = list(meta['ymd'].value_counts().head(5).index)
    ids = dict()
    for s in s_values:
        ids[s] = set(meta.loc[meta['ymd'] == s]['id'])

    # collocates
    corpus = get_corpus(brexit)
    ufa = UFA(corpus, ids, s_att='tweet_id')
    tables = ufa.collocates(cqp_query='[lemma="i"]',
                            order='log_likelihood',
                            context_break='tweet_id',
                            window=20)
    print(tables)
