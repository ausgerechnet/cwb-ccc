from ccc import Corpus
from ccc.discoursemes import Discourseme, DiscoursemeConstellation
from collections import defaultdict
import pytest


from .conftest import DATA_PATH


# backend.analysis.ccc methods ####################################
def get_concordance(corpus_name, topic_items, topic_name, s_context,
                    window_size, context=20,
                    additional_discoursemes={}, p_query='lemma',
                    p_show=['word', 'lemma'], s_show=['text_id'],
                    s_query=None, order='random', cut_off=100,
                    form='dataframe'):

    if s_query is None:
        s_query = s_context

    # init corpus
    corpus = Corpus(corpus_name)

    # init topic discourseme
    topic_disc = Discourseme(
        corpus,
        items=topic_items,
        p_query=p_query,
        s_query=s_query
    )

    # init discourseme constellation
    dp = DiscoursemeConstellation(topic_disc)

    # id2name: mapper from ccc cache names to discourseme names
    id2name = {
        topic_disc.idx: topic_name
    }

    # add discoursemes to discourseme constellation
    for key in additional_discoursemes.keys():
        idx = dp.add_items(additional_discoursemes[key])
        id2name[idx] = key

    # extract concordance
    concordance = dp.concordance(
        window=window_size,
        matches=None,
        p_show=p_show,
        s_show=s_show,
        order=order,
        cut_off=cut_off,
        form=form
    )

    if concordance.empty:
        return None

    # convert each concordance line to dictionary, create roles
    # TODO: implement as form='json' in cwb-ccc
    concordance = concordance.reset_index()
    ret = dict()
    for idx, df in zip(concordance['match'], concordance['dataframe']):

        # rename columns according to given names for discoursemes
        df = df.rename(columns=id2name)

        # get roles as dict
        roles = defaultdict(list)
        for cpos, row in df.iterrows():
            for col_name in id2name.values():
                if row[col_name]:
                    # TODO: propagate proper info about discourseme names
                    if col_name == topic_name:
                        roles[cpos].append('topic')
                    else:
                        roles[cpos].append('collocate')
                else:
                    roles[cpos].append(None)

        ret[idx] = {
            'word': list(df['word']),    # list of words
            p_query: list(df[p_query]),  # secondary p-att
            'role': list(roles.values())  # roles
        }

    return ret


def get_collocates(corpus_name, topic_items, s_context, window_sizes,
                   context=20, additional_discoursemes=[],
                   p_query='lemma', s_query=None, ams=None,
                   cut_off=200, order='log_likelihood'):

    if s_query is None:
        s_query = s_context

    corpus = Corpus(corpus_name)

    topic_disc = Discourseme(
        corpus,
        items=topic_items,
        p_query=p_query,
        s_query=s_query
    )

    # TODO speed up in backend
    collocates = dict()
    for window in window_sizes:

        if not additional_discoursemes:
            # single discourseme
            coll_window = topic_disc.collocates(
                window_sizes=window,
                order=order,
                cut_off=cut_off,
                p_query=p_query,
                ams=ams,
                min_freq=2,
                frequencies=False,
                flags=None
            )
        else:
            # discursive position
            dp = DiscoursemeConstellation(topic_disc)
            for key in additional_discoursemes.keys():
                dp.add_items(additional_discoursemes[key])

            coll_window = dp.collocates(
                window=window,
                order=order,
                cut_off=cut_off,
                p_query=p_query,
                ams=ams,
                min_freq=2,
                frequencies=False,
                flags=None
            )

        # drop superfluous columns and sort
        coll_window = coll_window[[
            'log_likelihood',
            'log_ratio',
            'f',
            'f2',
            'mutual_information',
            'z_score',
            't_score'
        ]]

        # rename AMs
        am_dict = {
            'log_likelihood': 'log-likelihood',
            'f': 'co-oc. freq.',
            'mutual_information': 'mutual information',
            'log_ratio': 'log-ratio',
            'f2': 'marginal freq.',
            't_score': 't-score',
            'z_score': 'z-score'
        }
        collocates[window] = coll_window.rename(am_dict, axis=1)

    return collocates


def get_corpus(corpus_settings, data_path=DATA_PATH):

    return Corpus(
        corpus_settings['corpus_name'],
        registry_path=corpus_settings['registry_path'],
        lib_path=corpus_settings.get('lib_path', None),
        data_path=data_path
    )


@pytest.mark.discourseme
def test_init(germaparl):
    corpus = get_corpus(germaparl)
    topic = Discourseme(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma', 's',
    )
    assert(len(topic.dump.df) == 1640)


@pytest.mark.discourseme
def test_concordance(germaparl):
    corpus = get_corpus(germaparl)
    topic = Discourseme(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma', 's'
    )
    print(topic.concordance())
    print(topic.concordance(10))
    print(topic.concordance(30))


@pytest.mark.discourseme
def test_disc_concordance_form(germaparl):

    corpus = get_corpus(germaparl)
    # init topic disc
    topic = Discourseme(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's'
    )
    print(topic.concordance(cut_off=None, form='kwic'))
    print(topic.concordance(matches=[148430], cut_off=None, form='slots'))


@pytest.mark.discourseme
def test_disc_collocates(germaparl):

    corpus = get_corpus(germaparl)

    # init topic disc
    topic = Discourseme(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's'
    )
    print(topic.collocates())


# constellations
@pytest.mark.disccon
def test_disccon(germaparl):

    corpus = get_corpus(germaparl)

    # init topic disc
    topic = Discourseme(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's'
    )

    # two floating discoursemes
    disc1 = Discourseme(
        corpus,
        ["sollen", "müssen"],
        'lemma',
        's'
    )
    disc2 = Discourseme(
        corpus,
        ["und"],
        'lemma',
        's'
    )
    discon = DiscoursemeConstellation(topic, [disc1, disc2])
    discon.slice_discs(10)
    print(discon.df_nodes[10])
    print(discon.df_nodes[10].columns)
    print(discon.discoursemes)


@pytest.mark.disccon
def test_disccon_2(germaparl):

    corpus = get_corpus(germaparl)

    # init topic disc
    topic = Discourseme(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's',
    )
    discon = DiscoursemeConstellation(topic)
    # two floating discoursemes
    discon.add_items(["sollen", "müssen"])
    discon.add_items(["und"])
    discon.slice_discs(10)
    print(discon.df_nodes[10].keys())
    print(discon.df_nodes[10])


@pytest.mark.disccon
def test_disccon_concordance(germaparl):

    corpus = get_corpus(germaparl)

    # three discoursemes
    topic = Discourseme(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's'
    )
    disc1 = Discourseme(
        corpus,
        ["sollen", "müssen"],
        'lemma',
        's'
    )
    disc2 = Discourseme(
        corpus,
        ["und"],
        'lemma',
        's'
    )

    # init discursive position
    disccon = DiscoursemeConstellation(topic, [disc1, disc2])
    # show concordance
    print(disccon.concordance())
    print(disccon.concordance(p_show=['word', 'lemma'])['dataframe'].iloc[0])


@pytest.mark.disccon
def test_disccon_collocates(germaparl):

    corpus = get_corpus(germaparl)

    # three discoursemes
    topic = Discourseme(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's',
        's'
    )
    disc1 = Discourseme(
        corpus,
        ["sollen", "müssen", "machen"],
        'lemma',
        's',
        's'
    )
    disc2 = Discourseme(
        corpus,
        ["und"],
        'lemma',
        's',
        's'
    )

    # init discursive position
    discpos = DiscoursemeConstellation(topic, [disc1, disc2])
    # show collocates
    print(discpos.collocates())


@pytest.mark.disccon
def test_disccon_collocates_empty(germaparl):

    corpus = get_corpus(germaparl)
    # three discoursemes
    topic = Discourseme(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's'
    )
    # init discursive position
    disccon = DiscoursemeConstellation(topic)
    disccon.add_items(["Verhandlung"])
    # show collocates
    assert(disccon.collocates(window=5).empty)


@pytest.mark.disccon
def test_disccon_collocates_nodes(germaparl):
    corpus = get_corpus(germaparl)
    topic = Discourseme(
        corpus,
        [",", ".", ")", "("],
        'lemma',
        's',
        escape=True
    )
    df = topic.collocates(cut_off=None)[5]
    assert("," not in df.index)
    assert("(" not in df.index)

    topic2 = DiscoursemeConstellation(topic)
    df2 = topic2.collocates(cut_off=None)
    assert(df2.equals(df))


@pytest.mark.disccon
def test_disccon_collocates_range(germaparl):

    corpus = get_corpus(germaparl)

    # three discoursemes
    topic = Discourseme(
        corpus,
        [",", ".", ")", "("],
        'lemma',
        's',
        's',
        escape=True
    )
    disc1 = Discourseme(
        corpus,
        ["die", "sie", "und"],
        'lemma',
        's',
        's'
    )
    disc2 = Discourseme(
        corpus,
        ["sein", "in", "eine", "zu", "haben"],
        'lemma',
        's',
        's'
    )
    disccon = DiscoursemeConstellation(topic, [disc1, disc2])
    df = disccon.collocates(cut_off=None)
    print(df)


# @pytest.mark.mmda
def test_get_concordance_simple():

    # init corpus
    corpus_name = "GERMAPARL1318"

    # request parameters
    topic_items = ['Atomkraft', 'Nuklearnergie', 'Atomenergie']
    topic_name = "Atomkraft"
    s_context = "s"
    window_size = 3
    context = 15
    additional_discoursemes = {}
    p_query = 'lemma'
    p_show = ['word', 'lemma']
    s_show = ['s']
    s_query = s_context
    order = 'random'
    cut_off = 100
    form = 'dataframe'

    conc = get_concordance(
        corpus_name,
        topic_items,
        topic_name,
        s_context,
        window_size,
        context,
        additional_discoursemes,
        p_query,
        p_show,
        s_show,
        s_query,
        order,
        cut_off,
        form
    )
    from pprint import pprint
    pprint(conc[list(conc.keys())[0]])


@pytest.mark.mmda
def test_get_collocates_simple():

    # init corpus
    corpus_name = "GERMAPARL1318"

    # request parameters
    topic_items = ['Atomkraft', 'Nuklearnergie', 'Atomenergie']
    s_context = "s"
    window_size = 3
    context = 15
    additional_discoursemes = {}
    p_query = 'lemma'
    s_query = s_context
    order = 'log_likelihood'
    cut_off = 100

    coll = get_collocates(
        corpus_name,
        topic_items,
        s_context,
        [window_size],
        context,
        additional_discoursemes,
        p_query,
        s_query,
        None,
        cut_off,
        order
    )
    from pprint import pprint
    pprint(coll[list(coll.keys())[0]])
