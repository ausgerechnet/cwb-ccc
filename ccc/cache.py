#! /usr/bin/env python
# -*- coding: utf-8 -*-

import shelve
import os
from hashlib import sha256
# logging
import logging
logger = logging.getLogger(__name__)


class Cache:

    def __init__(self, path=None):

        self.path = path

        if path:
            directory = os.path.dirname(path)
            os.makedirs(directory, exist_ok=True)

    def generate_idx(self, identifiers, prefix='', length=10):
        string = ''.join([str(idx) for idx in identifiers])
        h = sha256(str(string).encode()).hexdigest()
        return prefix + h[:length]

    def get(self, identifier):

        if self.path is None:
            logger.info('cache: no path')
            return None

        if isinstance(identifier, str):
            key = identifier
        else:
            key = self.generate_idx(identifier)

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
            key = self.generate_idx(identifier)

        with shelve.open(self.path) as db:
            logger.info('cache: saving object "%s"' % key)
            db[key] = value
