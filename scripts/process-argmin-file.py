#! /usr/bin/env python
# -*- coding: utf-8 -*-


from ccc.cwb import Corpus
from ccc.concordances import read_query_json, run_query
from argparse import ArgumentParser
import os
import logging
logger = logging.getLogger(__name__)


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('query_path')
    parser.add_argument('corpus')
    parser.add_argument('data_path')
    args = parser.parse_args()

    # read file
    query = read_query_json(args.query_path)

    # patch path to query
    query['query_path'] = args.query_path

    # run query
    corpus = Corpus(args.corpus,
                    query['lib_path'],
                    data_path=args.data_path)
    query, result = run_query(corpus, query)

    # get path for output
    path_out = os.path.join(args.data_path, query['name']) + ".tsv"
    result['df'] = result['df'].apply(lambda row: row.to_json())
    result.to_csv(path_out, sep="\t")
