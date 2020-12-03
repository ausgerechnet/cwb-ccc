from ccc import Corpus
from ccc.discoursemes import Disc, DiscCon
import pytest


@pytest.mark.discourseme
def test_disc(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])
    topic = Disc(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's',
        's'
    )
    print(topic.dump)


@pytest.mark.discourseme
def test_disc_matches(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])

    # init topic disc
    topic = Disc(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's',
        's'
    )
    print(topic.dump.matches())


@pytest.mark.discourseme
def test_disc_context(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])

    # init topic disc
    topic = Disc(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's',
        's'
    )
    print(topic.dump.context())


@pytest.mark.discourseme
def test_disc_concordance(germaparl):

    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])

    # init topic disc
    topic = Disc(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's',
        's'
    )
    print(topic.concordance(20))
    print(topic.concordance(10))
    print(topic.concordance(30))


@pytest.mark.discourseme
def test_disc_concordance_form(germaparl):

    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])

    # init topic disc
    topic = Disc(
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
    topic = Disc(
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
    topic = Disc(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's',
        's'
    )

    # two floating discoursemes
    disc1 = Disc(
        corpus,
        ["sollen", "müssen"],
        'lemma',
        's',
        's'
    )
    disc2 = Disc(
        corpus,
        ["und"],
        'lemma',
        's',
        's'
    )
    discon = DiscCon(topic, [disc1, disc2])
    discon.slice_discs()
    print(discon.df_nodes.keys())
    print(discon.df_nodes[discon.parameters['context']])


@pytest.mark.disccon
def test_disccon_2(germaparl):

    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])

    # init topic disc
    topic = Disc(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's',
        's'
    )
    discon = DiscCon(topic)
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
    topic = Disc(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's',
        's'
    )
    disc1 = Disc(
        corpus,
        ["sollen", "müssen"],
        'lemma',
        's',
        's'
    )
    disc2 = Disc(
        corpus,
        ["und"],
        'lemma',
        's',
        's'
    )

    # init discursive position
    disccon = DiscCon(topic, [disc1, disc2])
    # show concordance
    print(disccon.concordance())
    print(disccon.concordance(p_show=['word', 'lemma'])['df'].iloc[0]['word'])


@pytest.mark.disccon
def test_discpos_collocates(germaparl):

    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])

    # three discoursemes
    topic = Disc(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's',
        's'
    )
    disc1 = Disc(
        corpus,
        ["sollen", "müssen", "machen"],
        'lemma',
        's',
        's'
    )
    disc2 = Disc(
        corpus,
        ["und"],
        'lemma',
        's',
        's'
    )

    # init discursive position
    discpos = DiscCon(topic, [disc1, disc2])
    # show collocates
    print(discpos.collocates())


@pytest.mark.disccon
def test_disccon_collocates_empty(germaparl):

    corpus = Corpus(germaparl['corpus_name'],
                    registry_path=germaparl['registry_path'])

    # three discoursemes
    topic = Disc(
        corpus,
        ["SPD", "CSU", "Grünen"],
        'lemma',
        's',
        's'
    )
    # init discursive position
    disccon = DiscCon(topic)
    disccon.add_items(["Verhandlung"])
    # show collocates
    assert(disccon.collocates(window=5).empty)
