from ccc import Corpus
from ccc.discoursemes import Disc, DiscPos
import pytest


def test_disc():
    corpus = Corpus('GERMAPARL_1114')
    topic = Disc(
        corpus,
        ["Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's'
    )
    print(topic.dump)
    print(topic.idx)


def test_disc_matches():
    corpus = Corpus('GERMAPARL_1114')

    # init topic disc
    topic = Disc(
        corpus,
        ["Angela Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's'
    )
    print(topic.matches())


def test_disc_context():
    corpus = Corpus('GERMAPARL_1114')

    # init topic disc
    topic = Disc(
        corpus,
        ["Angela Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's'
    )
    print(topic.context())


def test_disc_concordance():

    topic = Disc(
        Corpus('GERMAPARL_1114'),
        ["Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's'
    )
    print(topic.show_concordance(20))
    print(topic.show_concordance(10))
    print(topic.show_concordance(30))


def test_disc_concordance_form():

    topic = Disc(
        Corpus('GERMAPARL_1114'),
        ["Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's'
    )
    print(topic.show_concordance(cut_off=None, form='kwic'))
    print(topic.show_concordance(matches=[11057], cut_off=None, form='extended'))


def test_disc_collocates():

    corpus = Corpus('GERMAPARL_1114')
    topic = Disc(
        corpus,
        ["Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's'
    )
    print(topic.show_collocates())


def test_discpos():

    # init topic disc
    topic = Disc(
        Corpus('GERMAPARL_1114'),
        ["Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's'
    )

    # two floating discoursemes
    disc1 = Disc(
        Corpus('GERMAPARL_1114'),
        ["Streit", "Verhandlung", "Regierung"],
        'lemma',
        's',
        's'
    )
    disc2 = Disc(
        Corpus('GERMAPARL_1114'),
        ["Angela"],
        'lemma',
        's',
        's'
    )
    discpos = DiscPos(topic, [disc1, disc2])
    discpos.slice_discs()
    print(discpos.df_nodes.keys())
    print(discpos.df_nodes[discpos.parameters['context']])


def test_discpos_2():

    # init topic disc
    topic = Disc(
        Corpus('GERMAPARL_1114'),
        ["Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's'
    )
    dp = DiscPos(topic)
    # two floating discoursemes
    dp.add_items(["Streit", "Verhandlung", "Regierung"])
    dp.add_items(["Angela"])

    dp.slice_discs()
    print(dp.df_nodes.keys())
    print(dp.df_nodes)


def test_discpos_concordance():
    corpus = Corpus('GERMAPARL_1114')

    # three discoursemes
    topic = Disc(
        corpus,
        ["Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's'
    )
    disc1 = Disc(
        corpus,
        ["Angela", "Streit", "Verhandlung", "Regierung"],
        'lemma',
        's',
        's'
    )
    disc2 = Disc(
        corpus,
        ["die"],
        'lemma',
        's',
        's'
    )

    # init discursive position
    dp = DiscPos(topic, [disc1, disc2])
    # show collocates
    print(dp.show_concordance())
    print(dp.show_concordance(p_show=['word', 'lemma'])['df'].iloc[0])


@pytest.mark.skip
def test_discpos_collocates():
    # three discoursemes
    topic = Disc(
        Corpus('GERMAPARL_1114'),
        ["Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's'
    )
    disc1 = Disc(
        Corpus('GERMAPARL_1114'),
        ["Angela", "Streit", "Verhandlung", "Regierung"],
        'lemma',
        's',
        's'
    )
    disc2 = Disc(
        Corpus('GERMAPARL_1114'),
        ["die"],
        'lemma',
        's',
        's'
    )

    # init discursive position
    discpos = DiscPos(topic, [disc1, disc2])
    # show collocates
    print(discpos.show_collocates())


def test_discpos_collocates_small():
    # three discoursemes
    topic = Disc(
        Corpus('GERMAPARL_1114'),
        ["Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's'
    )
    disc1 = Disc(
        Corpus('GERMAPARL_1114'),
        ["Angela", "Streit", "Verhandlung"],
        'lemma',
        's',
        's'
    )
    disc2 = Disc(
        Corpus('GERMAPARL_1114'),
        ["Regierung"],
        'lemma',
        's',
        's'
    )

    # init discursive position
    discpos = DiscPos(topic, [disc1, disc2])
    # show collocates
    print(discpos.show_collocates())


@pytest.mark.now
def test_discpos_collocates_empty():
    # three discoursemes
    topic = Disc(
        Corpus('GERMAPARL_1114'),
        ["Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's'
    )
    # init discursive position
    discpos = DiscPos(topic)
    discpos.add_items(["Verhandlung"])
    # show collocates
    print(discpos.show_collocates(window=5))
