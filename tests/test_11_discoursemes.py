from ccc import Corpus
from ccc.utils import format_cqp_query
from ccc.discoursemes import Constellation, create_constellation
from ccc.discoursemes import TextConstellation
from .conftest import DATA_PATH

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

    print(const.df)


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

    print(const.df)
    print(const.discoursemes.keys())


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

    print(const.df)
    print(const.discoursemes.keys())


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

    print(const.df)
    print(const.discoursemes.keys())


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

    print("return constellation" + "-" * 120)
    const = create_constellation(corpus_name, topic_name, topic_items,
                                 p_query, s_query, flags, escape,
                                 s_context, context,
                                 additional_discoursemes,
                                 registry_path=germaparl['registry_path'],
                                 data_path=DATA_PATH)

    print(const)

    print("return dataframe" + "-" * 120)
    df = create_constellation(corpus_name, topic_name, topic_items,
                              p_query, s_query, flags, escape,
                              s_context, context,
                              additional_discoursemes,
                              dataframe=True,
                              registry_path=germaparl['registry_path'],
                              data_path=DATA_PATH)

    print(df)

    print("return dataframe without drop" + "-" * 120)
    df = create_constellation(corpus_name, topic_name, topic_items,
                              p_query, s_query, flags, escape,
                              s_context, context,
                              additional_discoursemes,
                              registry_path=germaparl['registry_path'],
                              data_path=DATA_PATH,
                              dataframe=True, drop=False)

    print(df)


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
    print(lines)


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

    lines = const.collocates(windows=list(range(1, 21)))
    print(lines)


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
    print(const.df)


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

    print(const.df)


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

    print(const.associations())
