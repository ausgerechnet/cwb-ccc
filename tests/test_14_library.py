import os

import pytest

from ccc import Corpus
from ccc.library import Library, parse_macro_signature

from .conftest import DATA_PATH


def get_corpus(corpus_settings, lib=True, **kwargs):

    return Corpus(
        corpus_settings['corpus_name'],
        registry_dir=corpus_settings['registry_dir'],
        lib_dir=corpus_settings['lib_dir'] if lib else None,
        data_dir=DATA_PATH,
        **kwargs
    )


def test_parse_macro_signature():

    assert parse_macro_signature('np') == ('np', 0, 'np(0)')
    assert parse_macro_signature('/np', 2) == ('np', 2, 'np(2)')
    assert parse_macro_signature('np(1)') == ('np', 1, 'np(1)')
    assert parse_macro_signature('ap($0=Adj)') == ('ap', 1, 'ap($0=Adj)')
    with pytest.raises(ValueError):
        parse_macro_signature('np(1)', 1)
    with pytest.raises(ValueError):
        parse_macro_signature('n p')


def test_library_validation():

    library = Library()
    with pytest.raises(ValueError):
        library.add_wordlist('my-list', ['a'])
    with pytest.raises(TypeError):
        library.add_wordlist('items', 'abc')
    with pytest.raises(ValueError):
        library.add_wordlist('items', ['a\nb'])


def test_library_idx():

    library = Library()
    assert library.idx() is None
    library.add_wordlist('$parties', ['CDU', 'CSU'])
    idx = library.idx()
    assert idx is not None

    copied = library.copy()
    assert copied.idx() == idx
    copied.add_macro('np', '[pos="NN"]')
    assert copied.idx() != idx
    assert library.idx() == idx


def test_library_cqp_commands(germaparl):

    directory = os.path.join(DATA_PATH, 'library-test')
    library = Library(germaparl['lib_dir'], wordlists={'parties': ['CDU']})
    commands = library.cqp_commands(directory)

    # in-memory wordlist overrides the one in lib_dir
    wordlist_cmds = [c for c in commands if c.startswith('define $parties')]
    assert len(wordlist_cmds) == 1
    assert directory in wordlist_cmds[0]

    # content-addressed: same content, same file
    assert library.cqp_commands(directory) == commands


def test_define_wordlist(germaparl):

    corpus = get_corpus(germaparl, lib=False, wordlists={'greens': ['GRÜNEN', 'Grünen']})
    assert '$greens' in corpus.available_wordlists()

    corpus.define_wordlist('$union', ['CDU', 'CSU'])
    assert '$union' in corpus.available_wordlists()

    union = corpus.query('[word=$union]', context=0).df
    cdu = corpus.query('[word="CDU|CSU"]', context=0).df
    assert len(union) == len(cdu) > 0


def test_define_wordlist_overrides_lib(germaparl):

    corpus = get_corpus(germaparl)
    n_lib = len(corpus.query('$parties', context=0).df)

    corpus.define_wordlist('parties', ['CDU'])
    n_mem = len(corpus.query('$parties', context=0).df)
    assert 0 < n_mem < n_lib


def test_define_macro(germaparl):

    corpus = get_corpus(germaparl, lib=False, macros={'name(0)': '[lemma="Horst"] [lemma="Seehofer"]'})
    assert '/name(0)' in corpus.available_macros()
    assert len(corpus.query('/name[]', context=0).df) > 0

    corpus.define_macro('lemma_pos', '[lemma="$0" & pos="$1"]', n_args=2)
    assert '/lemma_pos(2)' in corpus.available_macros()
    df = corpus.query('/lemma_pos["Seehofer", "NE"]', context=0).df
    assert len(df) == len(corpus.query('[lemma="Seehofer" & pos="NE"]', context=0).df)


def test_define_macro_with_wordlist(germaparl):

    corpus = get_corpus(germaparl, lib=False)
    corpus.define_wordlist('union', ['CDU', 'CSU'])
    corpus.define_macro('union', '[word=$union]')
    assert len(corpus.query('/union[]', context=0).df) == len(corpus.query('[word="CDU|CSU"]', context=0).df)


def test_cache_invalidation(germaparl):

    corpus = get_corpus(germaparl, lib=False)
    corpus.define_wordlist('test', ['CDU'])
    n_cdu = len(corpus.query('[word=$test]', context=0).df)

    # same query, different definition: must not use cached result
    corpus.define_wordlist('test', ['CDU', 'CSU'])
    n_both = len(corpus.query('[word=$test]', context=0).df)
    assert n_both > n_cdu

    # back to old definition: cached result is valid again
    corpus.define_wordlist('test', ['CDU'])
    assert len(corpus.query('[word=$test]', context=0).df) == n_cdu


def test_propagation(germaparl):

    corpus = get_corpus(germaparl, lib=False, wordlists={'union': ['CDU', 'CSU']})

    assert '$union' in corpus.copy().available_wordlists()

    subcorpus = corpus.query('[word=$union]', context=10)
    assert '$union' in subcorpus.available_wordlists()

    # definitions on derived corpora do not affect the original
    subcorpus.define_wordlist('spd', ['SPD'])
    assert '$spd' not in corpus.available_wordlists()
