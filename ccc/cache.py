#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import shelve
from glob import glob
from hashlib import sha256

logger = logging.getLogger(__name__)


def generate_idx(identifiers, prefix='', length=10):

    string = ''.join([str(idx) for idx in identifiers])
    identifier = sha256(str(string).encode()).hexdigest()
    return prefix + identifier[:length]


def generate_library_idx(lib_path, prefix='', length=10):

    wordlists = glob(os.path.join(lib_path, 'wordlists', '*.txt'))
    macros = glob(os.path.join(lib_path, 'macros', '*.txt'))
    paths = macros + wordlists
    identifiers = [
        generate_idx(open(p, 'rt')) for p in sorted(paths)
    ]
    return generate_idx(identifiers, prefix, length)


class Cache:

    def __init__(self, path=None):

        self.path = path

        if path:
            directory = os.path.dirname(path)
            os.makedirs(directory, exist_ok=True)

    def delete(self, identifier):

        if self.path is None:
            logger.info('cache: no path')
            return

        if isinstance(identifier, str):
            key = identifier
        else:
            key = generate_idx(identifier)

        with shelve.open(self.path) as db:
            if key in db.keys():
                logger.info('cache: deleting object "%s"' % key)
                del db[key]

    def get(self, identifier):

        if self.path is None:
            logger.info('cache: no path')
            return

        if isinstance(identifier, str):
            key = identifier
        else:
            key = generate_idx(identifier)

        with shelve.open(self.path) as db:
            if key in db.keys():
                logger.info('cache: retrieving object "%s"' % key)
                return db[key]
            else:
                return None

    def set(self, identifier, value):

        if self.path is None:
            logger.info('cache: no path')
            return

        if isinstance(identifier, str):
            key = identifier
        else:
            key = generate_idx(identifier)

        with shelve.open(self.path) as db:
            logger.info('cache: saving object "%s"' % key)
            db[key] = value
