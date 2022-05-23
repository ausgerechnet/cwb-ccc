import pytest
from ccc.discoursemes import create_constellation
from .conftest import DATA_PATH


@pytest.mark.now
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
                                 data_path=DATA_PATH,
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
