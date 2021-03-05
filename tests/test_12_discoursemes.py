from ccc import Corpus
from ccc.discoursemes import Discourseme, DiscoursemeConstellation
import pytest


@pytest.mark.discourseme
def test_init(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    topic = Discourseme(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma', 's',
    )
    print(topic.dump)


@pytest.mark.discourseme1
def test_concordance(germaparl):

    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])

    topic = Discourseme(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma', 's',
    )
    print(topic.concordance(20))
    print(topic.concordance(10))
    print(topic.concordance(30))


@pytest.mark.discourseme
def test_disc_concordance_form(germaparl):

    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])

    # init topic disc
    topic = Discourseme(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's',
        's'
    )
    print(topic.concordance(cut_off=None, form='kwic'))
    print(topic.concordance(matches=[148430], cut_off=None, form='extended'))


@pytest.mark.discourseme
def test_disc_collocates(germaparl):

    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])

    # init topic disc
    topic = Discourseme(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's',
        's'
    )
    print(topic.collocates())


@pytest.mark.disccon
def test_disccon(germaparl):

    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])

    # init topic disc
    topic = Discourseme(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's',
        's'
    )

    # two floating discoursemes
    disc1 = Discourseme(
        corpus,
        ["sollen", "müssen"],
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
    discon = DiscoursemeConstellation(topic, [disc1, disc2])
    discon.slice_discs()
    print(discon.df_nodes.keys())
    print(discon.df_nodes[discon.parameters['context']])


@pytest.mark.disccon
def test_disccon_2(germaparl):

    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])

    # init topic disc
    topic = Discourseme(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's',
        's'
    )
    discon = DiscoursemeConstellation(topic)
    # two floating discoursemes
    discon.add_items(["sollen", "müssen"])
    discon.add_items(["und"])
    discon.slice_discs()
    print(discon.df_nodes.keys())
    print(discon.df_nodes)


@pytest.mark.disccon
def test_disccon_concordance(germaparl):

    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])

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
        ["sollen", "müssen"],
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
    disccon = DiscoursemeConstellation(topic, [disc1, disc2])
    # show concordance
    print(disccon.concordance())
    print(disccon.concordance(p_show=['word', 'lemma'])['df'].iloc[0]['word'])


@pytest.mark.disccon
def test_disccon_collocates(germaparl):

    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])

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

    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])

    # three discoursemes
    topic = Discourseme(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's',
        's'
    )
    # init discursive position
    disccon = DiscoursemeConstellation(topic)
    disccon.add_items(["Verhandlung"])
    # show collocates
    assert(disccon.collocates(window=5).empty)


def test_disccon_collocates_nodes(germaparl):
    corpus = Corpus(
        germaparl['corpus_name'],
        registry_path=germaparl['registry_path'],
        # data_path=None
    )
    topic = Discourseme(
        corpus,
        [",", ".", ")", "("],
        'lemma',
        's',
        's',
        escape=True
    )
    df = topic.collocates(cut_off=None)
    assert("," not in df.index)
    assert("(" not in df.index)

    topic2 = DiscoursemeConstellation(topic)
    df2 = topic2.collocates(cut_off=None)
    assert(df2.equals(df))


@pytest.mark.disccon
def test_disccon_collocates_range(germaparl):

    corpus = Corpus(
        germaparl['corpus_name'],
        registry_path=germaparl['registry_path'],
        # data_path=None
    )

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
