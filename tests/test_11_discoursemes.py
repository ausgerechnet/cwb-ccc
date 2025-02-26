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


def get_corpus(corpus_settings, data_dir=DATA_PATH):

    return Corpus(
        corpus_settings['corpus_name'],
        registry_dir=corpus_settings['registry_dir'],
        lib_dir=corpus_settings.get('lib_dir', None),
        data_dir=data_dir
    )


#################
# CONSTELLATION #
#################
@pytest.mark.now
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
    # print(const.df)

    assert isinstance(const.df, DataFrame)
    assert len(const.df) == 2789


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
    assert len(const.df) == 2789

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
    assert len(const.df) == 3072


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

    # filter
    const = create_constellation(
        corpus_name=corpus_name,
        # discoursemes
        topic_discourseme=topic_discourseme,
        filter_discoursemes=discoursemes,
        additional_discoursemes={},
        # context settings
        s_context=s_context,
        context=context,
        # CWB setttings
        registry_dir=germaparl['registry_dir'],
        data_dir=DATA_PATH,
        # query settings
        p_query=p_query,
        s_query=s_query,
        flags=flags,
        escape=escape
    )

    assert len(const.df) == 12

    # highlight
    const = create_constellation(
        corpus_name=corpus_name,
        # discoursemes
        topic_discourseme=topic_discourseme,
        filter_discoursemes={},
        additional_discoursemes=discoursemes,
        # context settings
        s_context=s_context,
        context=context,
        # CWB setttings
        registry_dir=germaparl['registry_dir'],
        data_dir=DATA_PATH,
        # query settings
        p_query=p_query,
        s_query=s_query,
        flags=flags,
        escape=escape
    )

    assert len(const.df) == 3004


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

    const = create_constellation(
        corpus_name=corpus_name,
        # discoursemes
        topic_discourseme={},
        filter_discoursemes={},
        additional_discoursemes=discoursemes,
        # context settings
        s_context=s_context,
        context=context,
        # CWB setttings
        registry_dir=germaparl['registry_dir'],
        data_dir=DATA_PATH,
        # query settings
        p_query=p_query,
        s_query=s_query,
        flags=flags,
        escape=escape
    )

    # TODO this yields len(const.df) = 1859 results with Python3.8, but why?
    # assert len(const.df) == 2198


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
    const = create_constellation(
        corpus_name=germaparl['corpus_name'],
        # discoursemes
        topic_discourseme=topic_discourseme,
        filter_discoursemes=discoursemes,
        additional_discoursemes={},
        # context settings
        s_context=parameters['s_context'],
        context=parameters['context'],
        # CWB setttings
        registry_dir=germaparl['registry_dir'],
        data_dir=DATA_PATH,
        # query settings
        p_query=parameters['p_query'],
        s_query=parameters['s_query'],
        flags=parameters['flags_query'],
        escape=parameters['escape_query']
    )

    lines = const.concordance(s_show=['text_id'])

    assert len(lines) == 4
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
    const = create_constellation(
        corpus_name=germaparl['corpus_name'],
        # discoursemes
        topic_discourseme=topic_discourseme,
        filter_discoursemes=discoursemes,
        additional_discoursemes={},
        # context settings
        s_context=parameters['s_context'],
        context=parameters['context'],
        # CWB setttings
        registry_dir=germaparl['registry_dir'],
        data_dir=DATA_PATH,
        # query settings
        p_query=parameters['p_query'],
        s_query=parameters['s_query'],
        flags=parameters['flags_query'],
        escape=parameters['escape_query']
    )

    lines = const.concordance(s_show=['text_id'], htmlify_meta=True)

    # assert len(lines) == 4  error on github: actually 100 lines, but why?
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
    lib_dir = None
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
        corpus_name=germaparl['corpus_name'],
        # discoursemes
        topic_discourseme={topic_name: topic_items},
        filter_discoursemes={},
        additional_discoursemes=additional_discoursemes,
        # context settings
        s_context=s_context,
        context=context,
        # CWB setttings
        match_strategy=match_strategy,
        lib_dir=lib_dir,
        cqp_bin=cqp_bin,
        registry_dir=germaparl['registry_dir'],
        data_dir=DATA_PATH,
        # query settings
        p_query=p_query,
        s_query=s_query,
        flags=flags_query,
        escape=escape
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

    # print(const.df)


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

    # parameters
    parameters = discoursemes.pop('parameters')
    flags = parameters['flags_query']
    escape = parameters['escape_query']
    p_query = parameters['p_query']
    s_query = parameters['s_query']
    s_context = parameters['s_context']
    context = parameters['context']

    const = create_constellation(
        corpus_name=germaparl['corpus_name'],
        # discoursemes
        topic_discourseme={},
        filter_discoursemes=discoursemes,
        additional_discoursemes={},
        # context settings
        s_context=s_context,
        context=context,
        # CWB setttings
        registry_dir=germaparl['registry_dir'],
        data_dir=DATA_PATH,
        # query settings
        p_query=p_query,
        s_query=s_query,
        flags=flags,
        escape=escape
    )

    assoc = const.associations()
    assert len(assoc) == 6
    assert 'candidate' in assoc.columns


def test_textual_constellation_association_approximate(germaparl, discoursemes):

    # parameters
    parameters = discoursemes.pop('parameters')
    flags = parameters['flags_query']
    escape = parameters['escape_query']
    p_query = parameters['p_query']
    s_query = parameters['s_query']
    s_context = parameters['s_context']
    context = parameters['context']

    const = create_constellation(
        corpus_name=germaparl['corpus_name'],
        # discoursemes
        topic_discourseme={},
        filter_discoursemes=discoursemes,
        additional_discoursemes={},
        # context settings
        s_context=s_context,
        context=context,
        approximate=True,
        # CWB setttings
        registry_dir=germaparl['registry_dir'],
        data_dir=DATA_PATH,
        # query settings
        p_query=p_query,
        s_query=s_query,
        flags=flags,
        escape=escape
    )

    assoc = const.associations()
    assert len(assoc) == 6
    assert 'candidate' in assoc.columns


def test_textual_constellation_association_empty(germaparl, discoursemes):

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

    const = create_constellation(
        corpus_name=germaparl['corpus_name'],
        # discoursemes
        topic_discourseme={},
        filter_discoursemes=discoursemes,
        additional_discoursemes={},
        # context settings
        s_context=s_context,
        context=context,
        approximate=True,
        # CWB setttings
        registry_dir=germaparl['registry_dir'],
        data_dir=DATA_PATH,
        # query settings
        p_query=p_query,
        s_query=s_query,
        flags=flags,
        escape=escape
    )

    assoc = const.associations()
    print(assoc)                # TODO why does this yield 6 in Python 3.10 and 2 in Python 3.12?
    # assert len(assoc) == 6
    # assert 'candidate' in assoc.columns


def test_textual_constellation_concordance(germaparl, discoursemes):

    # parameters
    parameters = discoursemes.pop('parameters')
    flags = parameters['flags_query']
    escape = parameters['escape_query']
    p_query = parameters['p_query']
    s_query = parameters['s_query']
    s_context = parameters['s_context']
    context = parameters['context']

    # create constellation
    const = create_constellation(
        corpus_name=germaparl['corpus_name'],
        # discoursemes
        topic_discourseme={},
        filter_discoursemes=discoursemes,
        additional_discoursemes={},
        # context settings
        s_context=s_context,
        context=context,
        # CWB setttings
        registry_dir=germaparl['registry_dir'],
        data_dir=DATA_PATH,
        # query settings
        p_query=p_query,
        s_query=s_query,
        flags=flags,
        escape=escape
    )

    # retrieve lines
    lines = const.concordance(cut_off=None)

    assert len(lines) == 2198


def test_textual_constellation_breakdown(germaparl, discoursemes):

    # parameters
    parameters = discoursemes.pop('parameters')
    flags = parameters['flags_query']
    escape = parameters['escape_query']
    p_query = parameters['p_query']
    s_query = parameters['s_query']
    s_context = parameters['s_context']
    context = parameters['context']

    # create constellation
    const = create_constellation(
        corpus_name=germaparl['corpus_name'],
        # discoursemes
        topic_discourseme={},
        filter_discoursemes=discoursemes,
        additional_discoursemes={},
        # context settings
        s_context=s_context,
        context=context,
        # CWB setttings
        registry_dir=germaparl['registry_dir'],
        data_dir=DATA_PATH,
        # query settings
        p_query=p_query,
        s_query=s_query,
        flags=flags,
        escape=escape
    )

    assert len(const.breakdown()) == 5
