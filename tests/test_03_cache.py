from ccc.cache import Cache
from pandas import DataFrame
from random import randint
import os

from .conftest import DATA_PATH


def test_generate_idx():

    parameters = {'query': "test", 's_break': "test"}
    cache = Cache()
    s = cache.generate_idx(parameters)
    assert(type(s) == str)


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
