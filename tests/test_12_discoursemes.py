from ccc import Corpus
# from ccc.discoursemes import Discourseme, DiscoursemeConstellation
import pytest
from ccc.utils import formulate_cqp_query
from ccc.discoursemes import Constellation
from ccc.discoursemes import get_concordance, get_collocates


# set CCC PATHS
CORPUS_NAME = "GERMAPARL1318"
LIB_PATH = None
REGISTRY_PATH = "/usr/local/share/cwb/registry/"
CQP_BIN = "cqp"
DATA_PATH = "/tmp/mmda-ccc-data/"

S_QUERY = 's'
S_CONTEXT = 'p'
P_QUERY = 'lemma'

TOPIC_ITEMS = ["Atomkraft", "Atomenergie", "Atomkraftwerk",
               "Nuklearenergie",
               "Kernkraft", "Kernenergie"]

# DISC1_ITEMS = ["Fukushima", "Störfall", "Tschernobyl", "Unfall"]
DISC1_ITEMS = ["Deutschland", "deutsch"]
DISC2_ITEMS = ["Stilllegung", "Stillegung",
               "Auslaufbetrieb",
               "Laufzeitverlängerung", "Weiterbetrieb"]


CORPUS = Corpus(
    CORPUS_NAME,
    lib_path=LIB_PATH,
    registry_path=REGISTRY_PATH,
    cqp_bin=CQP_BIN,
    data_path=DATA_PATH
)


@pytest.mark.discourseme
def test_constellation_init():

    # init constellation
    topic_query = formulate_cqp_query(TOPIC_ITEMS,
                                      p_query=P_QUERY, s_query=S_QUERY,
                                      flags="%cd", escape=False)

    topic_dump = CORPUS.query(topic_query, context=None, context_break=S_CONTEXT)

    const = Constellation(topic_dump)

    print(const.df)


@pytest.mark.discourseme
def test_constellation_add():

    topic_query = formulate_cqp_query(TOPIC_ITEMS,
                                      p_query=P_QUERY, s_query=S_QUERY,
                                      flags="%cd", escape=False)

    # init constellation
    topic_dump = CORPUS.query(topic_query,
                              context=None, context_break=S_CONTEXT)

    const = Constellation(topic_dump)

    # add discourseme
    disc1_query = formulate_cqp_query(DISC1_ITEMS,
                                      p_query=P_QUERY, s_query=S_QUERY,
                                      flags="%cd", escape=False)

    disc1_dump = CORPUS.query(disc1_query,
                              context=None, context_break=S_CONTEXT)

    const.add_discourseme(disc1_dump)

    print(const.df)
    print(const.discoursemes.keys())


@pytest.mark.discourseme
def test_constellation_add2():

    topic_query = formulate_cqp_query(TOPIC_ITEMS,
                                      p_query=P_QUERY, s_query=S_QUERY,
                                      flags="%cd", escape=False)

    # init constellation
    topic_dump = CORPUS.query(topic_query,
                              context=None, context_break=S_CONTEXT)

    const = Constellation(topic_dump)

    # add discourseme 1
    disc1_query = formulate_cqp_query(DISC1_ITEMS,
                                      p_query=P_QUERY, s_query=S_QUERY,
                                      flags="%cd", escape=False)
    disc1_dump = CORPUS.query(disc1_query,
                              context=None, context_break=S_CONTEXT)

    const.add_discourseme(disc1_dump, name='disc1')

    # add discourseme 2
    disc2_query = formulate_cqp_query(DISC2_ITEMS,
                                      p_query=P_QUERY, s_query=S_QUERY,
                                      flags="%cd", escape=False)
    disc2_dump = CORPUS.query(disc2_query,
                              context=None, context_break=S_CONTEXT)

    const.add_discourseme(disc2_dump, name='disc2')

    print(const.df)
    print(const.discoursemes.keys())


@pytest.mark.discourseme
def test_constellation_conc():

    topic_query = formulate_cqp_query(TOPIC_ITEMS,
                                      p_query=P_QUERY, s_query=S_QUERY,
                                      flags="%cd", escape=False)

    # init constellation
    topic_dump = CORPUS.query(topic_query,
                              context=None, context_break=S_CONTEXT)

    const = Constellation(topic_dump)

    # add discourseme 1
    disc1_query = formulate_cqp_query(DISC1_ITEMS,
                                      p_query=P_QUERY, s_query=S_QUERY,
                                      flags="%cd", escape=False)
    disc1_dump = CORPUS.query(disc1_query,
                              context=None, context_break=S_CONTEXT)

    const.add_discourseme(disc1_dump, name='disc1')

    # add discourseme 2
    disc2_query = formulate_cqp_query(DISC2_ITEMS,
                                      p_query=P_QUERY, s_query=S_QUERY,
                                      flags="%cd", escape=False)
    disc2_dump = CORPUS.query(disc2_query,
                              context=None, context_break=S_CONTEXT)

    const.add_discourseme(disc2_dump, name='disc2')

    lines = const.concordance(s_show=['text_id'])
    print(lines)
    # from pprint import pprint
    # pprint(lines)


@pytest.mark.discourseme
def test_constellation_coll():

    topic_query = formulate_cqp_query(TOPIC_ITEMS,
                                      p_query=P_QUERY, s_query=S_QUERY,
                                      flags="%cd", escape=False)

    # init constellation
    topic_dump = CORPUS.query(topic_query,
                              context=None, context_break=S_CONTEXT)
    const = Constellation(topic_dump)

    # add discourseme 1
    disc1_query = formulate_cqp_query(DISC1_ITEMS,
                                      p_query=P_QUERY, s_query=S_QUERY,
                                      flags="%cd", escape=False)
    disc1_dump = CORPUS.query(disc1_query,
                              context=None, context_break=S_CONTEXT)

    const.add_discourseme(disc1_dump, name='disc1')

    # add discourseme 2
    disc2_query = formulate_cqp_query(DISC2_ITEMS,
                                      p_query=P_QUERY, s_query=S_QUERY,
                                      flags="%cd", escape=False)
    disc2_dump = CORPUS.query(disc2_query,
                              context=None, context_break=S_CONTEXT)

    const.add_discourseme(disc2_dump, name='disc2')

    lines = const.collocates(windows=list(range(1, 20)))
    print(lines)


@pytest.mark.mmda
def test_get_concordance_simple():

    # init corpus
    corpus_name = "GERMAPARL1318"

    # request parameters
    topic_items = ['Atomkraft', 'Nuklearnergie', 'Atomenergie']
    topic_name = "Atomkraft"
    s_context = "s"
    window = 3
    context = 30
    additional_discoursemes = {}
    p_query = 'lemma'
    p_show = ['word', 'lemma']
    s_show = ['text_id']
    s_query = s_context
    order = 'random'
    cut_off = 100

    conc = get_concordance(
        corpus_name=corpus_name,
        topic_name=topic_name,
        topic_items=topic_items,
        p_query=p_query,
        s_query=s_query,
        s_context=s_context,
        window=window,
        context=context,
        additional_discoursemes=additional_discoursemes,
        p_show=p_show,
        s_show=s_show,
        order=order,
        cut_off=cut_off
    )
    from pprint import pprint
    pprint(conc[list(conc.keys())[1]])


@pytest.mark.mmda
def test_get_collocates_simple():

    # init corpus
    corpus_name = "GERMAPARL1318"

    # request parameters
    topic_items = ['Atomkraft', 'Nuklearnergie', 'Atomenergie']
    s_context = "s"
    windows = list(range(1, 10))
    print(windows)
    additional_discoursemes = {}
    p_query = 'lemma'
    p_show = ['lemma']
    s_query = s_context
    order = 'log_likelihood'
    cut_off = 100

    coll = get_collocates(
        corpus_name=corpus_name,
        topic_items=topic_items,
        s_context=s_context,
        windows=windows,
        additional_discoursemes=additional_discoursemes,
        p_query=p_query,
        p_show=p_show,
        s_query=s_query,
        cut_off=cut_off,
        order=order
    )
    from pprint import pprint
    pprint(coll[list(coll.keys())[0]])


@pytest.mark.mmda
def test_get_concordance_constellation():

    # init corpus
    corpus_name = "GERMAPARL1318"

    # request parameters
    topic_items = TOPIC_ITEMS
    topic_name = "Atomkraft"
    s_context = "s"
    window = 3
    context = None
    additional_discoursemes = {'Deutschland': DISC1_ITEMS, 'Stillegung': DISC2_ITEMS}
    p_query = 'lemma'
    p_show = ['word', 'lemma']
    s_show = ['text_id']
    s_query = s_context
    order = 'random'
    cut_off = 100

    conc = get_concordance(
        corpus_name=corpus_name,
        topic_name=topic_name,
        topic_items=topic_items,
        p_query=p_query,
        s_query=s_query,
        s_context=s_context,
        window=window,
        context=context,
        additional_discoursemes=additional_discoursemes,
        p_show=p_show,
        s_show=s_show,
        order=order,
        cut_off=cut_off
    )
    from pprint import pprint
    pprint(conc[list(conc.keys())[0]])


@pytest.mark.mmda
def test_get_collocates_constellation():

    # init corpus
    corpus_name = "GERMAPARL1318"

    # request parameters
    topic_items = TOPIC_ITEMS
    s_context = "s"
    windows = list(range(1, 10))
    additional_discoursemes = {'Deutschland': DISC1_ITEMS, 'Stillegung': DISC2_ITEMS}
    p_query = 'lemma'
    p_show = ['lemma']
    s_query = s_context
    order = 'log_likelihood'
    cut_off = 100

    coll = get_collocates(
        corpus_name=corpus_name,
        topic_items=topic_items,
        s_context=s_context,
        windows=windows,
        additional_discoursemes=additional_discoursemes,
        p_query=p_query,
        p_show=p_show,
        s_query=s_query,
        cut_off=cut_off,
        order=order
    )
    from pprint import pprint
    pprint(coll[5])
