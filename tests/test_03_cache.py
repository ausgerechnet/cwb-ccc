import os
from random import randint

from pandas import DataFrame

from ccc.cache import Cache, generate_idx, generate_library_idx

from .conftest import DATA_PATH


def test_set_get_empty():

    parameters = {'query': "test", 's_break': "test"}
    cache = Cache()
    s = generate_idx(parameters)
    assert(cache.get(s) is None)
    cache.set(s, parameters)
    assert(cache.get(s) is None)


def test_set_get():

    cache = Cache(os.path.join(DATA_PATH, 'test-cache'))
    parameters = {'query': "test", 's_break': "test", 'key': randint(0, 9e+9)}
    dump = DataFrame()
    r = cache.get(parameters.values())
    assert(r is None)

    cache.set(parameters, dump)
    r = cache.get(parameters)
    assert(r.empty)

    cache.set('testtest', dump)
    r = cache.get('testtest')
    assert(r.empty)


def test_generate_library_idx(germaparl):
    assert isinstance(generate_library_idx(germaparl['lib_path']), str)
