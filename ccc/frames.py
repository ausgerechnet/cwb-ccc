#! /usr/bin/env python
# -*- coding: utf-8 -*-

""" frames.py: classes for dataframe types

- FreqFrame
- DumpFrame
- CoocFrame
- CollFrame
- ConcFrame

"""

import pandas as pd


@pd.api.extensions.register_dataframe_accessor("freq")
class FreqFrame:
    """A DataFrame for Frequencies:
    == (p_atts) freq ==
    MultiIndex, even if single p-att

    examples:
    == (word, ) freq ==
    == (lemma, pos) freq ==
    == (query, ) freq ==

    for MWUs, each p-att-layer is " ".joined
    """

    def __init__(self, pandas_obj):
        self._validate(pandas_obj)
        self._obj = pandas_obj

    @staticmethod
    def _validate(obj):
        # verify there is a column "freq" and a named MultiIndex
        if "freq" not in obj.columns or not isinstance(obj.index, pd.MultiIndex):
            raise AttributeError("wrong format")

    def test(self):
        print(self)
