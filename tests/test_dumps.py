from ccc.cwb import Corpus


def test_query2dump_nocache(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'], data_path=None)
    dump = corpus.query(sz_corpus['query'])
    print(dump)


def test_query2dump_diff_name(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.query(sz_corpus['query'], name="Test")
    print(dump)


def test_query2dump(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.query('"1"')
    print(dump)


def test_breakdown(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.query(sz_corpus['query'])
    print(dump.breakdown())


def test_concordance(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.query(sz_corpus['query'])
    print(dump.concordance())


def test_concordance_options(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.query(sz_corpus['query'])
    print(dump.concordance(form='raw'))
    print(dump.concordance(form='simple'))
    print(dump.concordance(form='kwic'))
    print(dump.concordance(form='dataframes'))
    print(dump.concordance(form='extended'))


def test_collocates(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.query('"Angela"')
    print(dump.collocates())


def test_collocates_options(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.query('"Angela"')
    print(dump.collocates(order='log_likelihood', cut_off=200))


def test_keywords(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.query('"Angela" expand to s')
    print(dump.keywords())


def test_keywords_options(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.query('"Angela" expand to s')
    print(dump.keywords(order='log_ratio', cut_off=200))


def test_context_matches(sz_corpus):
    corpus = Corpus(sz_corpus['corpus_name'])
    dump = corpus.query('"Angela"')
    print(dump.matches())
    print(dump.context())
