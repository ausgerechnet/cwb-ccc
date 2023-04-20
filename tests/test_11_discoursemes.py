import pytest
from pandas import DataFrame

from ccc import Corpus
from ccc.discoursemes import (Constellation, TextConstellation,
                              create_constellation)
from ccc.utils import format_cqp_query

from .conftest import DATA_PATH

#######################
# ccc.discoursemes ####
#######################

# constellation_merge
# role_formatter
# calculate_collocates

# Constellation
# .__init__
# .add_discourseme: constellation_merge
# .group_lines
# .concordance: role_formatter, .group_lines
# .collocates: calculate_collocates

# create_constellation

############
# mmda.ccc #
############

# - ccc_concordance:
#   create_constellation, Constellation.concordance, role_formatter
# - ccc_collocates:
#   create_constellation, Constellation.collocates

# - ccc_constellation_concordance
#   get_constellation_df
# - ccc_constellation_association
#   get_constellation_df


def get_corpus(corpus_settings, data_path=DATA_PATH):

    return Corpus(
        corpus_settings['corpus_name'],
        registry_path=corpus_settings['registry_path'],
        lib_path=corpus_settings.get('lib_path', None),
        data_path=data_path
    )


#################
# CONSTELLATION #
#################
def test_constellation_init(germaparl, discoursemes):

    corpus = get_corpus(germaparl)

    # init constellation
    topic_query = format_cqp_query(
        discoursemes['topic'],
        p_query=discoursemes['parameters']['p_query'],
        s_query=discoursemes['parameters']['s_query'],
        flags=discoursemes['parameters']['flags_query'],
        escape=discoursemes['parameters']['escape_query']
    )
    topic_dump = corpus.query(
        topic_query,
        context=None,
        context_break=discoursemes['parameters']['s_context']
    )
    const = Constellation(topic_dump)

    assert isinstance(const.df, DataFrame)
    assert len(const.df) == 2777


def test_constellation_add(germaparl, discoursemes):

    corpus = get_corpus(germaparl)

    # init constellation
    topic_query = format_cqp_query(
        discoursemes['topic'],
        p_query=discoursemes['parameters']['p_query'],
        s_query=discoursemes['parameters']['s_query'],
        flags=discoursemes['parameters']['flags_query'],
        escape=discoursemes['parameters']['escape_query']
    )
    topic_dump = corpus.query(
        topic_query,
        context=None,
        context_break=discoursemes['parameters']['s_context']
    )
    const = Constellation(topic_dump)

    # add discourseme
    disc1_query = format_cqp_query(
        discoursemes['disc1'],
        p_query=discoursemes['parameters']['p_query'],
        s_query=discoursemes['parameters']['s_query'],
        flags=discoursemes['parameters']['flags_query'],
        escape=discoursemes['parameters']['escape_query']
    )
    disc1_dump = corpus.query(
        disc1_query,
        context=None,
        context_break=discoursemes['parameters']['s_context']
    )
    const.add_discourseme(disc1_dump)

    assert len(const.df) == 1599
    assert 'topic' in const.discoursemes
    assert len(const.discoursemes) == 2


def test_constellation_add_nodrop(germaparl, discoursemes):

    corpus = get_corpus(germaparl)

    # init constellation
    topic_query = format_cqp_query(
        discoursemes['topic'],
        p_query=discoursemes['parameters']['p_query'],
        s_query=discoursemes['parameters']['s_query'],
        flags=discoursemes['parameters']['flags_query'],
        escape=discoursemes['parameters']['escape_query']
    )
    topic_dump = corpus.query(
        topic_query,
        context=None,
        context_break=discoursemes['parameters']['s_context']
    )
    const = Constellation(topic_dump)
    assert len(const.df) == 2777

    # add discourseme
    disc1_query = format_cqp_query(
        discoursemes['disc1'],
        p_query=discoursemes['parameters']['p_query'],
        s_query=discoursemes['parameters']['s_query'],
        flags=discoursemes['parameters']['flags_query'],
        escape=discoursemes['parameters']['escape_query']
    )
    disc1_dump = corpus.query(
        disc1_query,
        context=None,
        context_break=discoursemes['parameters']['s_context']
    )
    const.add_discourseme(
        disc1_dump,
        drop=False
    )
    assert len(const.df) == 3060


def test_constellation_add2(germaparl, discoursemes):

    corpus = get_corpus(germaparl)

    # init constellation
    topic_query = format_cqp_query(
        discoursemes['topic'],
        p_query=discoursemes['parameters']['p_query'],
        s_query=discoursemes['parameters']['s_query'],
        flags=discoursemes['parameters']['flags_query'],
        escape=discoursemes['parameters']['escape_query']
    )
    topic_dump = corpus.query(
        topic_query,
        context=None,
        context_break=discoursemes['parameters']['s_context']
    )
    const = Constellation(topic_dump)

    # add discourseme 1
    disc1_query = format_cqp_query(
        discoursemes['disc1'],
        p_query=discoursemes['parameters']['p_query'],
        s_query=discoursemes['parameters']['s_query'],
        flags=discoursemes['parameters']['flags_query'],
        escape=discoursemes['parameters']['escape_query']
    )
    disc1_dump = corpus.query(
        disc1_query,
        context=None,
        context_break=discoursemes['parameters']['s_context']
    )
    const.add_discourseme(
        disc1_dump,
        name='disc1'
    )

    # add discourseme 2
    disc2_query = format_cqp_query(
        discoursemes['disc2'],
        p_query=discoursemes['parameters']['p_query'],
        s_query=discoursemes['parameters']['s_query'],
        flags=discoursemes['parameters']['flags_query'],
        escape=discoursemes['parameters']['escape_query']
    )
    disc2_dump = corpus.query(
        disc2_query,
        context=None,
        context_break=discoursemes['parameters']['s_context']
    )
    const.add_discourseme(
        disc2_dump,
        name='disc2'
    )

    assert len(const.df) == 13


########################
# CREATE_CONSTELLATION #
########################
def test_create_constellation(germaparl, discoursemes):

    corpus_name = germaparl['corpus_name']

    # parameters
    parameters = discoursemes.pop('parameters')
    flags = parameters['flags_query']
    escape = parameters['escape_query']
    p_query = parameters['p_query']
    s_query = parameters['s_query']
    s_context = parameters['s_context']
    context = parameters['context']

    # get topic and additional discoursemes
    topic_items = discoursemes.pop('topic')
    topic_discourseme = {
        'topic': topic_items
    }
    discoursemes = discoursemes

    # filter
    const = create_constellation(corpus_name,
                                 # discoursemes
                                 topic_discourseme,
                                 discoursemes,
                                 {},
                                 # context settings
                                 s_context,
                                 context,
                                 # query settings
                                 p_query,
                                 s_query,
                                 flags,
                                 escape,
                                 # CWB setttings
                                 registry_path=germaparl['registry_path'],
                                 data_path=DATA_PATH)

    assert len(const.df) == 10

    # highlight
    const = create_constellation(corpus_name,
                                 # discoursemes
                                 topic_discourseme,
                                 {},
                                 discoursemes,
                                 # context settings
                                 s_context,
                                 context,
                                 # query settings
                                 p_query,
                                 s_query,
                                 flags,
                                 escape,
                                 # CWB setttings
                                 registry_path=germaparl['registry_path'],
                                 data_path=DATA_PATH)

    assert len(const.df) == 2990


def test_create_textconstellation(germaparl, discoursemes):

    corpus_name = germaparl['corpus_name']

    # parameters
    parameters = discoursemes.pop('parameters')
    flags = parameters['flags_query']
    escape = parameters['escape_query']
    p_query = parameters['p_query']
    s_query = parameters['s_query']
    s_context = parameters['s_context']
    context = parameters['context']

    # create constellation
    const = create_constellation(corpus_name,
                                 # discoursemes
                                 {},
                                 {},
                                 discoursemes,
                                 # context settings
                                 s_context,
                                 context,
                                 # query settings
                                 p_query,
                                 s_query,
                                 flags,
                                 escape,
                                 # CWB setttings
                                 registry_path=germaparl['registry_path'],
                                 data_path=DATA_PATH)

    assert len(const.df) == 2198


###############
# CONCORDANCE #
###############
def test_constellation_conc(germaparl, discoursemes):

    # parameters
    parameters = discoursemes.pop('parameters')

    # get topic and additional discoursemes
    topic_items = discoursemes.pop('topic')
    topic_discourseme = {
        'topic': topic_items
    }
    discoursemes = discoursemes

    # filter
    const = create_constellation(germaparl['corpus_name'],
                                 # discoursemes
                                 topic_discourseme,
                                 discoursemes,
                                 {},
                                 # context settings
                                 parameters['s_context'],
                                 parameters['context'],
                                 # query settings
                                 parameters['p_query'],
                                 parameters['s_query'],
                                 parameters['flags_query'],
                                 parameters['escape_query'],
                                 # CWB setttings
                                 registry_path=germaparl['registry_path'],
                                 data_path=DATA_PATH)

    lines = const.concordance(s_show=['text_id'])

    assert len(lines) == 3
    assert isinstance(lines[0], dict)
    assert 'word' in lines[0]
    assert isinstance(lines[0]['word'], list)


def test_constellation_conc_htmlify_meta(germaparl, discoursemes):

    # parameters
    parameters = discoursemes.pop('parameters')

    # get topic and additional discoursemes
    topic_items = discoursemes.pop('topic')
    topic_discourseme = {
        'topic': topic_items
    }
    discoursemes = discoursemes

    # filter
    const = create_constellation(germaparl['corpus_name'],
                                 # discoursemes
                                 topic_discourseme,
                                 discoursemes,
                                 {},
                                 # context settings
                                 parameters['s_context'],
                                 parameters['context'],
                                 # query settings
                                 parameters['p_query'],
                                 parameters['s_query'],
                                 parameters['flags_query'],
                                 parameters['escape_query'],
                                 # CWB setttings
                                 registry_path=germaparl['registry_path'],
                                 data_path=DATA_PATH)

    lines = const.concordance(s_show=['text_id'], htmlify_meta=True)

    assert len(lines) == 3
    assert isinstance(lines[0], dict)
    assert 'word' in lines[0]
    assert isinstance(lines[0]['word'], list)
    assert isinstance(lines[0]['meta'], str)


###############
# COLLOCATION #
###############
def test_constellation_collocates(germaparl):

    topic_name = 'topic'
    topic_items = ['CDU', 'CSU']
    p_query = 'lemma'
    s_query = None
    flags_query = '%cd'
    flags_show = ''
    min_freq = 2
    s_context = 's'
    context = 20
    additional_discoursemes = {}
    windows = [3, 5, 7]
    cqp_bin = 'cqp'
    lib_path = None
    p_show = ['lemma']
    ams = None
    cut_off = 200
    min_freq = 2
    order = 'log_likelihood'
    escape = True
    match_strategy = 'longest'

    # preprocess parameters
    s_query = s_context if s_query is None else s_query
    topic_name = 'topic'

    # create constellation
    const = create_constellation(
        germaparl['corpus_name'],
        {topic_name: topic_items},
        {},
        additional_discoursemes,
        s_context,
        context,
        p_query,
        s_query,
        flags_query,
        escape,
        match_strategy,
        lib_path,
        cqp_bin,
        germaparl['registry_path'],
        DATA_PATH
    )

    collocates = const.collocates(windows=windows, p_show=p_show,
                                  flags=flags_show, ams=ams,
                                  min_freq=min_freq, order=order,
                                  cut_off=cut_off)

    assert len(collocates) == 3


def test_constellation_coll(germaparl, discoursemes):

    corpus = get_corpus(germaparl)

    # init constellation
    topic_query = format_cqp_query(
        discoursemes['topic'],
        p_query=discoursemes['parameters']['p_query'],
        s_query=discoursemes['parameters']['s_query'],
        flags=discoursemes['parameters']['flags_query'],
        escape=discoursemes['parameters']['escape_query']
    )
    topic_dump = corpus.query(
        topic_query,
        context=None,
        context_break=discoursemes['parameters']['s_context']
    )
    const = Constellation(topic_dump)

    # add discourseme 1
    disc1_query = format_cqp_query(
        discoursemes['disc1'],
        p_query=discoursemes['parameters']['p_query'],
        s_query=discoursemes['parameters']['s_query'],
        flags=discoursemes['parameters']['flags_query'],
        escape=discoursemes['parameters']['escape_query']
    )
    disc1_dump = corpus.query(
        disc1_query,
        context=None,
        context_break=discoursemes['parameters']['s_context']
    )
    const.add_discourseme(
        disc1_dump,
        name='disc1'
    )

    # add discourseme 2
    disc2_query = format_cqp_query(
        discoursemes['disc2'],
        p_query=discoursemes['parameters']['p_query'],
        s_query=discoursemes['parameters']['s_query'],
        flags=discoursemes['parameters']['flags_query'],
        escape=discoursemes['parameters']['escape_query']
    )
    disc2_dump = corpus.query(
        disc2_query,
        context=None,
        context_break=discoursemes['parameters']['s_context']
    )
    const.add_discourseme(
        disc2_dump,
        name='disc2'
    )

    dfs = const.collocates(windows=list(range(1, 21)))
    assert len(dfs) == 20
    assert len(dfs[1]) == 2
    # if approximate, i.e. nodes are not removed:
    # assert len(dfs[20]) == 8
    assert len(dfs[20]) == 5


##########################
# TEXTUAL CONSTELLATIONS #
##########################
def test_textual_constellation(germaparl, discoursemes):

    corpus = get_corpus(germaparl)

    # init constellation
    topic_query = format_cqp_query(
        discoursemes['topic'],
        p_query=discoursemes['parameters']['p_query'],
        s_query=discoursemes['parameters']['s_query'],
        flags=discoursemes['parameters']['flags_query'],
        escape=discoursemes['parameters']['escape_query']
    )
    topic_dump = corpus.query(
        topic_query,
        context=None,
        context_break=discoursemes['parameters']['s_context']
    )
    const = TextConstellation(
        topic_dump,
        s_context=discoursemes['parameters']['s_context']
    )
    assert len(const.df) == 624
    assert 'topic' in const.df.columns


def test_textual_constellation_add(germaparl, discoursemes):

    corpus = get_corpus(germaparl)

    # init constellation
    topic_query = format_cqp_query(
        discoursemes['topic'],
        p_query=discoursemes['parameters']['p_query'],
        s_query=discoursemes['parameters']['s_query'],
        flags=discoursemes['parameters']['flags_query'],
        escape=discoursemes['parameters']['escape_query']
    )
    topic_dump = corpus.query(
        topic_query,
        context=None,
        context_break=discoursemes['parameters']['s_context']
    )
    const = TextConstellation(
        topic_dump,
        s_context=discoursemes['parameters']['s_context']
    )

    # add discourseme
    disc1_query = format_cqp_query(
        discoursemes['disc1'],
        p_query=discoursemes['parameters']['p_query'],
        s_query=discoursemes['parameters']['s_query'],
        flags=discoursemes['parameters']['flags_query'],
        escape=discoursemes['parameters']['escape_query']
    )
    disc1_dump = corpus.query(
        disc1_query,
        context=None,
        context_break=discoursemes['parameters']['s_context']
    )
    const.add_discourseme(
        disc1_dump
    )

    assert len(const.df) == 2156
    assert 'discourseme' in const.df.columns


def test_textual_constellation_association(germaparl, discoursemes):

    corpus_name = germaparl['corpus_name']

    # parameters
    parameters = discoursemes.pop('parameters')
    flags = parameters['flags_query']
    escape = parameters['escape_query']
    p_query = parameters['p_query']
    s_query = parameters['s_query']
    s_context = parameters['s_context']
    context = parameters['context']

    const = create_constellation(corpus_name,
                                 # discoursemes
                                 {},
                                 discoursemes,
                                 {},
                                 # context settings
                                 s_context,
                                 context,
                                 # query settings
                                 p_query,
                                 s_query,
                                 flags,
                                 escape,
                                 # CWB setttings
                                 registry_path=germaparl['registry_path'],
                                 data_path=DATA_PATH)

    assoc = const.associations()
    assert len(assoc) == 6
    assert 'candidate' in assoc.columns


def test_textual_constellation_association_approximate(germaparl, discoursemes):

    corpus_name = germaparl['corpus_name']

    # parameters
    parameters = discoursemes.pop('parameters')
    flags = parameters['flags_query']
    escape = parameters['escape_query']
    p_query = parameters['p_query']
    s_query = parameters['s_query']
    s_context = parameters['s_context']
    context = parameters['context']

    const = create_constellation(corpus_name,
                                 # discoursemes
                                 {},
                                 discoursemes,
                                 {},
                                 # context settings
                                 s_context,
                                 context,
                                 # query settings
                                 p_query,
                                 s_query,
                                 flags,
                                 escape,
                                 # CWB setttings
                                 registry_path=germaparl['registry_path'],
                                 data_path=DATA_PATH,
                                 approximate=True)

    assoc = const.associations()
    assert len(assoc) == 6
    assert 'candidate' in assoc.columns


def test_textual_constellation_association_empty(germaparl, discoursemes):

    corpus_name = germaparl['corpus_name']

    # parameters
    parameters = discoursemes.pop('parameters')
    flags = parameters['flags_query']
    escape = parameters['escape_query']
    p_query = parameters['p_query']
    s_query = parameters['s_query']
    s_context = parameters['s_context']
    context = parameters['context']
    discoursemes2 = discoursemes.copy()
    discoursemes2['fail'] = ["fail"]
    discoursemes2['fail2'] = ["fail2"]

    const = create_constellation(corpus_name,
                                 # discoursemes
                                 {},
                                 discoursemes2,
                                 {},
                                 # context settings
                                 s_context,
                                 context,
                                 # query settings
                                 p_query,
                                 s_query,
                                 flags,
                                 escape,
                                 # CWB setttings
                                 registry_path=germaparl['registry_path'],
                                 data_path=DATA_PATH,
                                 approximate=True)

    assoc = const.associations()
    assert len(assoc) == 6
    assert 'candidate' in assoc.columns


def test_textual_constellation_concordance(germaparl, discoursemes):

    corpus_name = germaparl['corpus_name']

    # parameters
    parameters = discoursemes.pop('parameters')
    flags = parameters['flags_query']
    escape = parameters['escape_query']
    p_query = parameters['p_query']
    s_query = parameters['s_query']
    s_context = parameters['s_context']
    context = parameters['context']

    # create constellation
    const = create_constellation(corpus_name,
                                 # discoursemes
                                 {},
                                 discoursemes,
                                 {},
                                 # context settings
                                 s_context,
                                 context,
                                 # query settings
                                 p_query,
                                 s_query,
                                 flags,
                                 escape,
                                 # CWB setttings
                                 registry_path=germaparl['registry_path'],
                                 data_path=DATA_PATH)

    # retrieve lines
    lines = const.concordance(cut_off=None)

    assert len(lines) == 2198


def test_textual_constellation_breakdown(germaparl, discoursemes):

    corpus_name = germaparl['corpus_name']

    # parameters
    parameters = discoursemes.pop('parameters')
    flags = parameters['flags_query']
    escape = parameters['escape_query']
    p_query = parameters['p_query']
    s_query = parameters['s_query']
    s_context = parameters['s_context']
    context = parameters['context']

    # create constellation
    const = create_constellation(corpus_name,
                                 # discoursemes
                                 {},
                                 discoursemes,
                                 {},
                                 # context settings
                                 s_context,
                                 context,
                                 # query settings
                                 p_query,
                                 s_query,
                                 flags,
                                 escape,
                                 # CWB setttings
                                 registry_path=germaparl['registry_path'],
                                 data_path=DATA_PATH)

    assert len(const.breakdown()) == 5
