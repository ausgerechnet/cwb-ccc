#! /usr/bin/env python
# -*- coding: utf-8 -*-

from random import sample
# part of module
from .utils import node2cooc
# requirements
from pandas import DataFrame
# logging
import logging
logger = logging.getLogger(__name__)


class Concordance:
    """ concordancing """

    def __init__(self, corpus, df_dump):

        # bind corpus
        self.corpus = corpus

        # what's in the dump?
        self.df_dump = df_dump
        self.size = len(df_dump)
        anchors = [i for i in range(10) if i in df_dump.columns]
        anchors += ['match', 'matchend', 'context', 'contextend']
        self.anchors = anchors

        if len(df_dump) == 0:
            logger.warning('empty dump')

    def text_line(self, index, columns, p_show=['word']):
        """Translates one row of self.df_dump into a concordance_line.

        :return: dictionary of [match, cpos, offset, anchors] + p_show
        :rtype: dict

        """

        # pack values
        match, matchend = index
        row = dict(columns)
        row['match'] = match
        row['matchend'] = matchend

        # create cotext
        cotext = node2cooc(row)
        cpos = cotext['cpos_list']

        # init output dictionary
        out = {
            'cpos': cpos,
            'offset': cotext['offset_list'],
            'match': match
        }
        assert(match == cotext['match_list'][0])

        # lexicalize positions
        attribute_lists = zip(
            *list(map(lambda x: self.corpus.cpos2patts(x, p_show), cpos))
        )
        for a, p in zip(p_show, attribute_lists):
            out[a] = list(p)

        # process anchors
        out['anchors'] = dict()
        for a in self.anchors:
            out['anchors'][a] = row[a]

        return out

    def lines(self, matches=None, p_show=['word'], s_show=[],
              p_text=None, p_slots=None, slots=[], order='first',
              cut_off=100, form='raw'):
        """ creates concordance lines from self.df_dump

        :param str form: raw / simple / kwic / dataframes / extended

        """

        # check parameter consistency
        if len(self.df_dump) == 0:
            logger.error("no concordance lines to show")
            return
        if p_text is not None and p_text not in p_show:
            logger.error('p_text not in p_show')
            return
        if p_slots is not None and p_slots not in p_show:
            logger.error('p_slots not in p_show')
            return

        # select appropriate subset of matches
        logger.info('lines: selecting matches')
        if matches is None:
            matches = set(self.df_dump.index.droplevel('matchend'))
        # pre-process cut_off if necessary
        if (cut_off is None) or (len(matches) < cut_off):
            cut_off = len(matches)

        # order
        if order == 'random':
            matches = sample(matches, cut_off)
        elif order == 'first':
            matches = sorted(list(matches))[:cut_off]
        elif order == 'last':
            matches = sorted(list(matches))[-cut_off:]
        else:
            raise NotImplementedError('concordance order not implemented')

        logger.info("lines: retrieving %d concordance line(s)" % len(matches))
        df = self.df_dump.loc[matches, :]

        # texts
        if len(p_show) > 0:

            # retrieve lines as Series
            # - index: match, matchend
            # - values: dictionaries
            df_lines = df.apply(
                lambda row: self.text_line(row.name, row, p_show),
                axis=1,
            )
            df_lines.name = 'raw'

            # format text
            if form == 'raw':
                concordance = df_lines
            else:
                concordance = format_lines(
                    df_lines, p_show, p_text,
                    p_slots, slots, form=form
                )
            df = df.join(DataFrame(concordance))

        # meta data
        for s in s_show:
            df = self.corpus.dump2satt(df, s)

        return df


##########################
# CONCORDANCE FORMATTING #
##########################
def format_lines(df_lines,
                 p_show=['word'],
                 p_text=None,   # only for form == 'extended'
                 p_slots=None,  # only for form == 'extended'
                 slots=[],      # only for form == 'extended'
                 form='dataframes'):

    # select p-attribute for simple and kwic
    if form == 'simple' or form == 'kwic':
        if len(p_show) > 1:
            logger.warning(
                'cannot show more than one p-attribute in simple/kwic format'
            )
            logger.info(
                'showing p-attribute "%s"' % p_show[0]
            )
        p_show = p_show[0]

    if form == 'simple':
        df = DataFrame.from_records(
            index=df_lines.index,
            data=df_lines.apply(
                lambda row: line2simple(row, p_show, kwic=False)
            ).values
        )

    elif form == 'kwic':
        df = DataFrame.from_records(
            index=df_lines.index,
            data=df_lines.apply(
                lambda row: line2simple(row, p_show, kwic=True)
            ).values
        )

    elif form == 'dataframes':
        df = DataFrame.from_records(
            index=df_lines.index,
            data=df_lines.apply(
                lambda row: line2df(row)
            ).values
        )

    elif form == 'extended':
        df = DataFrame.from_records(
            index=df_lines.index,
            data=df_lines.apply(
                lambda row: line2extended(row, p_text, p_slots, slots)
            ).values
        )
    else:
        raise NotImplementedError('no support for format "%s"' % form)

    return df


def line2simple(line, p_show='word', kwic=False):
    """transforms one text_line to dictionary to
    {"text": str} (kwic=False) or
    {"left": str, "node": str, "right": str} (kwic=True)
    input is a dictionary {p_show: list, ("offset": list)}

    :param dict line: dicionary with "p_show": list(), "offset": list()
    :param str p_show: what layer to show
    :param bool kwic: kwic view?

    :return: dictionary with "text" or "left", "node", "right"
    :rtype: dict

    """

    if not kwic:
        return {
            'text': " ".join(line[p_show])
        }

    # get and append left / node / right
    left = list()
    node = list()
    right = list()
    for offset, word in zip(line['offset'], line[p_show]):
        if offset < 0:
            left.append(word)
        elif offset == 0:
            node.append(word)
        else:
            right.append(word)

    return {
        'left': " ".join(left),
        'node': " ".join(node),
        'right': " ".join(right),
    }


def line2df(line):
    """transforms one text_line to dictionary of {"df": DataFrame}. Pops
    "anchors", "match"; everything else must be aligned.

    :param dict line: dictionary

    :return: {'df': DataFrame}
    :rtype: dict

    """

    # pop non-lists
    anchors = []
    if 'anchors' in line.keys():
        anchors = line.pop('anchors')
    if 'match' in line:
        line.pop('match')       # not needed

    # transform to df
    df = DataFrame.from_records(line).set_index('cpos')

    # append anchors
    for a in anchors:
        df[a] = False
        if anchors[a] in df.index:
            df.at[anchors[a], a] = True

    return {
        'df': df
    }


def line2extended(line, p_text=None, p_slots=None, slots=dict()):
    """transforms one text_line to dictionary of {"df": DataFrame,
    "match_p_slots": str, ...}.

    :param dict line: dictionary

    :return: {'df': DataFrame, ...}
    :rtype: dict

    """

    # init dataframe
    out = line2df(line)

    # get full text
    if p_text is None:
        p_text = 'word'
    out['text'] = " ".join(out['df'][p_text].to_list())

    # process slots
    if p_slots:
        for slot in slots.keys():

            region = slots[slot]

            if type(region) == int:
                region = [region, region]

            anchor_left = True in out['df'][region[0]].values
            anchor_right = True in out['df'][region[1]].values

            if not anchor_left and not anchor_right:
                slots_p = None
            elif anchor_left and anchor_right:
                start = out['df'].index[out['df'][region[0]]].tolist()[0]
                end = out['df'].index[out['df'][region[1]]].tolist()[0]
                slots_p = " ".join(out['df'][p_slots].loc[start: end].to_list())
            elif anchor_right:
                end = out['df'].index[out['df'][region[1]]].tolist()[0]
                slots_p = out['df'][p_slots].loc[end]
            elif anchor_left:
                start = out['df'].index[out['df'][region[0]]].tolist()[0]
                slots_p = out['df'][p_slots][start]

            out["_".join([str(slot), p_slots])] = slots_p

    return out
