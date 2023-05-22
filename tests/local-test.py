from pandas import concat, read_csv

from ccc import Corpus
from ccc.discoursemes import create_constellation
from ccc.dumps import Dumps
from ccc.keywords import keywords

from .conftest import DATA_PATH

import pytest


#########
# LOCAL #
#########
def test_textual_constellation_breakdown_local():

    covcorp = Corpus("COV_PRESSE_DE")

    # get discoursemes
    df_discoursemes = read_csv("tests/covcorp-discoursemes.tsv", sep="\t")
    df_discoursemes['cqp'] = df_discoursemes['item'].apply(
        lambda x: '[smorlemma="%s" & sttspos="%s"]' % tuple(x.split(" "))
    )
    print(df_discoursemes['cat'].value_counts())
    discourseme_queries = dict()
    for cat in ['maßnahmen', 'erreger']:
        discourseme_queries[cat] = "( " + " | ".join(
            list(df_discoursemes.loc[df_discoursemes['cat'] == cat]['cqp'].values)
        ) + " )"

    # run queries
    dumps = dict()
    for name, query in discourseme_queries.items():
        dumps[name] = covcorp.query(
            discourseme_queries[name], context_break='text', context=None
        )

    # create constellation
    # topic = dumps.pop('maßnahmen')
    # const = TextConstellation(topic, s_context='text', name='maßnahmen')
    # for name, dump in dumps.items():
    #     const.add_discourseme(dump, name)

    print('A')
    dfs = list()
    for name, dump in dumps.items():
        print(name)
        b = dump.breakdown()
        b['discourseme'] = name
        dfs.append(b)

    print('B')
    breakdown = concat(dfs)
    print(breakdown)


def test_textual_constellation_creation_local():

    covcorp = Corpus("COV_PRESSE_DE")

    # get discoursemes
    df_discoursemes = read_csv("tests/covcorp-discoursemes.tsv", sep="\t").sample(20, random_state=42)
    df_discoursemes['cqp'] = df_discoursemes['item'].apply(
        lambda x: '[smorlemma="%s" & sttspos="%s"]' % tuple(x.split(" "))
    )
    print(df_discoursemes['cat'].value_counts())

    # queries
    discourseme_queries = dict()
    for cat in ['maßnahmen', 'erreger']:
        discourseme_queries[cat] = "( " + " | ".join(
            list(df_discoursemes.loc[df_discoursemes['cat'] == cat]['cqp'].values)
        ) + " )"

    # run queries
    dumps = dict()
    for name, query in discourseme_queries.items():
        dumps[name] = covcorp.query(
            discourseme_queries[name], context_break='text', context=None
        )

    # create constellation
    from ccc.discoursemes import TextConstellation
    const = TextConstellation(dumps, s_context='text')
    print(const.N)
    # topic = dumps.pop('maßnahmen')
    # const = TextConstellation(topic, s_context='text', name='maßnahmen')
    # for name, dump in dumps.items():
    #     const.add_discourseme(dump, name)

    # print('A')
    # dfs = list()
    # for name, dump in dumps.items():
    #     print(name)
    #     b = dump.breakdown()
    #     b['discourseme'] = name
    #     dfs.append(b)

    # print('B')
    # breakdown = concat(dfs)
    # print(breakdown)


def test_constellation_concordance():

    corpus_name = "GEREDE_V2_DEV0"
    topic_discourseme = {
        'topic': ['(Pseudo|Fake|Lügen)-?pandemie', 'Virentheorie', 'Maskenzwang',
                  'Gesichtslappen', 'Gesichtswindel', 'Corona-?(wahnsinn|lüge|fake|schwindel)']
    }
    filter_discoursemes = {
    }

    additional_discoursemes = {
        '28': ['Henrion-Caude', 'Allianz', 'Fraktion', 'Bevölkerung', 'uns', 'mich', 'Kind'],
        '27': ['news', 'News', 'verbreiten', 'warnen', 'sprechen', 'erreichen', 'erklären', 'reden'],
        '26': ['Lockdown', 'Lockdowns', 'Verordnung', 'Maulkorb', 'aufsetzen', '😷', 'staatlich', 'tragen'],
        '25': ['⚔', 'gegen', 'stoppen', 'wehren', 'beenden', 'schwachsinnig',
               'satt', 'Gegner', 'aufhören', 'angeblich', 'Sinn'],
        '24': ['Impf-?(betrug|experiment|schwindel|wahnsinn|zwang)', 'Shedding', 'Zwangsimpfung']
    }

    # parameters
    flags = "%cd"
    escape = False
    p_query = "lemma"
    s_query = "s"
    s_context = "s"
    context = 10

    cut_off = 100
    windows = list(range(1, 10))
    p_show = ["lemma"]
    flags_show = ""
    ams = None
    frequencies = True
    min_freq = 2
    order = 'log_likelihood'

    # create constellation
    const = create_constellation(corpus_name,
                                 # discoursemes
                                 topic_discourseme,
                                 filter_discoursemes,
                                 additional_discoursemes,
                                 # context settings
                                 s_context,
                                 context,
                                 # query settings
                                 p_query,
                                 s_query,
                                 flags,
                                 escape,
                                 # CWB setttings
                                 data_dir=DATA_PATH,
                                 approximate=True)

    # retrieve lines
    lines = const.concordance()
    # print(lines)

    collocates = const.collocates(
        windows=windows,
        p_show=p_show,
        flags=flags_show,
        ams=ams,
        frequencies=frequencies,
        min_freq=min_freq,
        order=order,
        cut_off=cut_off
    )
    print(collocates)


def test_dumps_collocates_slow():

    # subcorpora via s-attribute values
    parties = {
        # 'green': {"GRUENE", "Bündnis 90/Die Grünen"},
        'red': {'SPD'},
        # 'black': {'CDU', 'CSU'},
        'yellow': {'FDP'},
        # 'purple': {'PDS'}
    }

    # collocates
    corpus = Corpus("GERMAPARL-1949-2021")
    dumps = Dumps(corpus, parties, s_att='parliamentary_group')
    tables = dumps.collocates(
        cqp_query='"Atomkraft"',
        order='log_ratio',
        context_break='s',
        window=20
    )
    assert len(tables) == len(parties)
    # assert tables['yellow'].index[0] == 'Grad'


def test_keywords():
    germaparl = Corpus("GERMAPARL-1949-2021")
    sz = Corpus("SZ-2009-2014")
    print(keywords(germaparl, sz, cut_off=None))


@pytest.mark.now
def test_keywords_NA():

    corpus = Corpus("GERMAPARL-1949-2021")
    parties = {
        'green': {"GRUENE", "Bündnis 90/Die Grünen"},
        'red': {'SPD'},
        'black': {'CDU', 'CSU'},
        'yellow': {'FDP'},
        'purple': {'PDS'}
    }
    factions = Dumps(corpus, s_dict=parties, s_att='parliamentary_group')
    collocates = factions.collocates(cqp_query='[lemma="Klimawandel"]', cut_off=None)
    print(collocates)
