from ccc import Corpus
from ccc.utils import format_cqp_query
from ccc.discoursemes import Constellation, create_constellation
from ccc.discoursemes import TextConstellation
from .conftest import DATA_PATH, LOCAL
from pandas import DataFrame

import pytest

# from pandas import set_option
# set_option('display.max_rows', 10000)

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

############
# CREATION #
############
@pytest.mark.discourseme
def test_constellation_init(germaparl, discoursemes):

    corpus = get_corpus(germaparl)

    # init constellation
    topic_query = format_cqp_query(
        discoursemes['items_topic'],
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


@pytest.mark.discourseme
def test_constellation_add(germaparl, discoursemes):

    corpus = get_corpus(germaparl)

    # init constellation
    topic_query = format_cqp_query(
        discoursemes['items_topic'],
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
        discoursemes['items_1'],
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


@pytest.mark.discourseme
def test_constellation_add_nodrop(germaparl, discoursemes):

    corpus = get_corpus(germaparl)

    # init constellation
    topic_query = format_cqp_query(
        discoursemes['items_topic'],
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
        discoursemes['items_1'],
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


@pytest.mark.discourseme
def test_constellation_add2(germaparl, discoursemes):

    corpus = get_corpus(germaparl)

    # init constellation
    topic_query = format_cqp_query(
        discoursemes['items_topic'],
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
        discoursemes['items_1'],
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
        discoursemes['items_2'],
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
    names = list(discoursemes.keys())
    topic_name = names[0]
    topic_items = discoursemes.pop(topic_name)
    additional_discoursemes = discoursemes

    const = create_constellation(corpus_name, topic_name, topic_items,
                                 p_query, s_query, flags, escape,
                                 s_context, context,
                                 additional_discoursemes,
                                 registry_path=germaparl['registry_path'],
                                 data_path=DATA_PATH)

    assert len(const.df) == 10

    df = create_constellation(corpus_name, topic_name, topic_items,
                              p_query, s_query, flags, escape,
                              s_context, context,
                              additional_discoursemes,
                              dataframe=True,
                              registry_path=germaparl['registry_path'],
                              data_path=DATA_PATH)

    assert len(df) == 10

    df = create_constellation(corpus_name, topic_name, topic_items,
                              p_query, s_query, flags, escape,
                              s_context, context,
                              additional_discoursemes,
                              registry_path=germaparl['registry_path'],
                              data_path=DATA_PATH,
                              dataframe=True, drop=False)

    assert len(df) == 2990


@pytest.mark.skipif(not LOCAL, reason='works on my machine')
def test_mmda_1():

    corpus_name = "GERMAPARL1318"
    topic_name = 'topic'
    topic_items = ['Atomkraft', 'Atomenergie', 'Kernkraft']
    p_query = 'lemma'
    s_query = None
    flags_query = '%cd'
    flags_show = ''
    min_freq = 2
    s_context = 's'
    context = 20
    additional_discoursemes = {}
    data_path = '/tmp/mmda-ccc/'
    windows = [3, 5, 7]
    cqp_bin = 'cqp'
    lib_path = None
    p_show = ['lemma']
    ams = None
    cut_off = 200
    min_freq = 2
    order = 'log_likelihood'
    escape = True
    frequencies = True
    registry_path = '/usr/local/share/cwb/registry/'

    # preprocess parameters
    s_query = s_context if s_query is None else s_query
    topic_name = 'topic'

    # create constellation
    const = create_constellation(corpus_name,
                                 topic_name, topic_items,
                                 p_query, s_query, flags_query, escape,
                                 s_context, context,
                                 additional_discoursemes,
                                 lib_path, cqp_bin, registry_path, data_path)

    collocates = const.collocates(windows=windows,
                                  p_show=p_show, flags=flags_show,
                                  ams=ams, frequencies=frequencies, min_freq=min_freq,
                                  order=order, cut_off=cut_off)

    assert len(collocates) == 3


###############
# CONCORDANCE #
###############
@pytest.mark.discourseme
def test_constellation_conc(germaparl, discoursemes):

    corpus = get_corpus(germaparl)

    # init constellation
    topic_query = format_cqp_query(
        discoursemes['items_topic'],
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
        discoursemes['items_1'],
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
        discoursemes['items_2'],
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

    lines = const.concordance(s_show=['text_id'])

    assert len(lines) == 5
    assert isinstance(lines[0], dict)
    assert 'word' in lines[0]
    assert isinstance(lines[0]['word'], list)


###############
# COLLOCATION #
###############
@pytest.mark.discourseme
def test_constellation_coll(germaparl, discoursemes):

    corpus = get_corpus(germaparl)

    # init constellation
    topic_query = format_cqp_query(
        discoursemes['items_topic'],
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
        discoursemes['items_1'],
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
        discoursemes['items_2'],
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
    assert len(dfs[20]) == 5


##########################
# TEXTUAL CONSTELLATIONS #
##########################
def test_textual_constellation(germaparl, discoursemes):

    corpus = get_corpus(germaparl)

    # init constellation
    topic_query = format_cqp_query(
        discoursemes['items_topic'],
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
        discoursemes['items_topic'],
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
        discoursemes['items_1'],
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

    corpus = get_corpus(germaparl)

    # init constellation
    topic_query = format_cqp_query(
        discoursemes['items_topic'],
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
        discoursemes['items_1'],
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
        discoursemes['items_2'],
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

    assoc = const.associations()
    assert len(assoc) == 6
    assert 'candidate' in assoc.columns
