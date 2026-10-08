#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""cache.py

simple caching using shelve/pickle.

"""
import logging
import os
import shelve
from hashlib import sha256

logger = logging.getLogger(__name__)


def generate_idx(identifiers, prefix='', length=10):
    """generate an ID from an iterable

    """
    string = ''.join([str(idx) for idx in identifiers])
    identifier = sha256(str(string).encode()).hexdigest()
    return prefix + identifier[:length]


def generate_library_idx(lib_dir, prefix='', length=10):
    """generate an ID for a library (deprecated: use ccc.library.generate_library_idx)

    """
    from .library import generate_library_idx
    return generate_library_idx(lib_dir, prefix, length)


class Cache:

    def __init__(self, path=None, salt=None):
        """
        :param str path: path of shelve
        :param str salt: prepended to all keys (e.g. to identify in-memory library)

        """

        self.path = path
        self.salt = salt

        if path:
            directory = os.path.dirname(path)
            os.makedirs(directory, exist_ok=True)

    def key(self, identifier):

        if isinstance(identifier, str):
            key = identifier
        else:
            key = generate_idx(identifier)

        if self.salt is not None:
            key = f"{self.salt}:{key}"

        return key

    def delete(self, identifier):

        if self.path is None:
            logger.info('no cache path')
            return

        key = self.key(identifier)

        with shelve.open(self.path) as shelf:
            if key in shelf.keys():
                logger.info(f'deleting object "{key}" from cache')
                del shelf[key]

    def get(self, identifier):

        if self.path is None:
            logger.info('no cache path')
            return

        key = self.key(identifier)

        with shelve.open(self.path) as shelf:
            if key in shelf.keys():
                logger.info(f'retrieving object "{key}" from cache')
                return shelf[key]

    def set(self, identifier, value):

        if self.path is None:
            logger.error('no cache path')
            return

        key = self.key(identifier)

        with shelve.open(self.path) as shelf:
            logger.info(f'saving object "{key}" to cache')
            shelf[key] = value
