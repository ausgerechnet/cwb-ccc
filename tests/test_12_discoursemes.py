from ccc import Corpus
from ccc.utils import format_cqp_query
from ccc.discoursemes import Constellation
from .conftest import DATA_PATH

import pytest

#######################
# ccc.discoursemes ####
#######################

# create_constellation
# constellation_merge
# role_formatter
# calculate_collocates

# Constellation
# - __init__
# - add_discourseme: constellation_merge
# - group_lines
# - concordance: role_formatter, group_lines
# - collocates: calculate_collocates

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


@pytest.mark.discourseme
def test_constellation_init(germaparl, discoursemes):

    corpus = get_corpus(germaparl)

    # init constellation
    topic_query = format_cqp_query(discoursemes['items_topic'],
                                   p_query=discoursemes['p_query'],
                                   s_query=discoursemes['s_query'],
                                   flags="%cd", escape=False)
    topic_dump = corpus.query(
        topic_query, context=None, context_break=discoursemes['s_context']
    )

    const = Constellation(topic_dump)

    print(const.df)


@pytest.mark.discourseme
def test_constellation_add(germaparl, discoursemes):

    corpus = get_corpus(germaparl)

    # init constellation
    topic_query = format_cqp_query(discoursemes['items_topic'],
                                   p_query=discoursemes['p_query'],
                                   s_query=discoursemes['s_query'],
                                   flags="%cd",
                                   escape=False)
    topic_dump = corpus.query(
        topic_query, context=None, context_break=discoursemes['s_context']
    )
    const = Constellation(topic_dump)

    # add discourseme
    disc1_query = format_cqp_query(
        discoursemes['items_1'],
        p_query=discoursemes['p_query'],
        s_query=discoursemes['s_query'],
        flags="%cd",
        escape=False
    )
    disc1_dump = corpus.query(
        disc1_query,
        context=None,
        context_break=discoursemes['s_context']
    )
    const.add_discourseme(disc1_dump)

    print(const.df)
    print(const.discoursemes.keys())


@pytest.mark.discourseme
def test_constellation_add2(germaparl, discoursemes):

    corpus = get_corpus(germaparl)

    # init constellation
    topic_query = format_cqp_query(discoursemes['items_topic'],
                                   p_query=discoursemes['p_query'],
                                   s_query=discoursemes['s_query'],
                                   flags="%cd",
                                   escape=False)
    topic_dump = corpus.query(
        topic_query, context=None, context_break=discoursemes['s_context']
    )
    const = Constellation(topic_dump)

    # add discourseme 1
    disc1_query = format_cqp_query(
        discoursemes['items_1'],
        p_query=discoursemes['p_query'],
        s_query=discoursemes['s_query'],
        flags="%cd",
        escape=False
    )
    disc1_dump = corpus.query(
        disc1_query,
        context=None,
        context_break=discoursemes['s_context']
    )
    const.add_discourseme(disc1_dump, name='disc1')

    # add discourseme 2
    disc2_query = format_cqp_query(
        discoursemes['items_2'],
        p_query=discoursemes['p_query'],
        s_query=discoursemes['s_query'],
        flags="%cd",
        escape=False
    )
    disc2_dump = corpus.query(
        disc2_query,
        context=None,
        context_break=discoursemes['s_context']
    )
    const.add_discourseme(disc2_dump, name='disc2')

    print(const.df)
    print(const.discoursemes.keys())


@pytest.mark.discourseme
def test_constellation_conc(germaparl, discoursemes):

    corpus = get_corpus(germaparl)

    # init constellation
    topic_query = format_cqp_query(discoursemes['items_topic'],
                                   p_query=discoursemes['p_query'],
                                   s_query=discoursemes['s_query'],
                                   flags="%cd",
                                   escape=False)
    topic_dump = corpus.query(
        topic_query, context=None, context_break=discoursemes['s_context']
    )
    const = Constellation(topic_dump)

    # add discourseme 1
    disc1_query = format_cqp_query(
        discoursemes['items_1'],
        p_query=discoursemes['p_query'],
        s_query=discoursemes['s_query'],
        flags="%cd",
        escape=False
    )
    disc1_dump = corpus.query(
        disc1_query,
        context=None,
        context_break=discoursemes['s_context']
    )
    const.add_discourseme(disc1_dump, name='disc1')

    # add discourseme 2
    disc2_query = format_cqp_query(
        discoursemes['items_2'],
        p_query=discoursemes['p_query'],
        s_query=discoursemes['s_query'],
        flags="%cd",
        escape=False
    )
    disc2_dump = corpus.query(
        disc2_query,
        context=None,
        context_break=discoursemes['s_context']
    )
    const.add_discourseme(disc2_dump, name='disc2')

    lines = const.concordance(s_show=['text_id'])
    print(lines)


@pytest.mark.discourseme
def test_constellation_coll(germaparl, discoursemes):

    corpus = get_corpus(germaparl)

    # init constellation
    topic_query = format_cqp_query(discoursemes['items_topic'],
                                   p_query=discoursemes['p_query'],
                                   s_query=discoursemes['s_query'],
                                   flags="%cd",
                                   escape=False)
    topic_dump = corpus.query(
        topic_query, context=None, context_break=discoursemes['s_context']
    )
    const = Constellation(topic_dump)

    # add discourseme 1
    disc1_query = format_cqp_query(
        discoursemes['items_1'],
        p_query=discoursemes['p_query'],
        s_query=discoursemes['s_query'],
        flags="%cd",
        escape=False
    )
    disc1_dump = corpus.query(
        disc1_query,
        context=None,
        context_break=discoursemes['s_context']
    )
    const.add_discourseme(disc1_dump, name='disc1')

    # add discourseme 2
    disc2_query = format_cqp_query(
        discoursemes['items_2'],
        p_query=discoursemes['p_query'],
        s_query=discoursemes['s_query'],
        flags="%cd",
        escape=False
    )
    disc2_dump = corpus.query(
        disc2_query,
        context=None,
        context_break=discoursemes['s_context']
    )
    const.add_discourseme(disc2_dump, name='disc2')

    lines = const.collocates(windows=list(range(1, 20)))
    print(lines)
