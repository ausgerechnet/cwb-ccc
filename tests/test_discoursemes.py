from ccc import Corpus
from ccc.discoursemes import Disc, DiscCon
import pytest


@pytest.mark.discourseme
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


@pytest.mark.discourseme
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
    print(topic.dump.matches())


@pytest.mark.discourseme
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
    print(topic.dump.context())


@pytest.mark.discourseme
def test_disc_concordance():

    topic = Disc(
        Corpus('GERMAPARL_1114'),
        ["Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's'
    )
    print(topic.concordance(20))
    print(topic.concordance(10))
    print(topic.concordance(30))


@pytest.mark.discourseme
def test_disc_concordance_form():

    topic = Disc(
        Corpus('GERMAPARL_1114'),
        ["Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's'
    )
    print(topic.concordance(cut_off=None, form='kwic'))
    print(topic.concordance(matches=[11057], cut_off=None, form='extended'))


@pytest.mark.discourseme
def test_disc_collocates():

    corpus = Corpus('GERMAPARL_1114')
    topic = Disc(
        corpus,
        ["Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's'
    )
    print(topic.collocates())


@pytest.mark.disccon
def test_disccon():

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
    discpos = DiscCon(topic, [disc1, disc2])
    discpos.slice_discs()
    print(discpos.df_nodes.keys())
    print(discpos.df_nodes[discpos.parameters['context']])


@pytest.mark.disccon
def test_disccon_2():

    # init topic disc
    topic = Disc(
        Corpus('GERMAPARL_1114'),
        ["Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's'
    )
    dp = DiscCon(topic)
    # two floating discoursemes
    dp.add_items(["Streit", "Verhandlung", "Regierung"])
    dp.add_items(["Angela"])

    dp.slice_discs()
    print(dp.df_nodes.keys())
    print(dp.df_nodes)


@pytest.mark.disccon
def test_disccon_concordance():
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
    disccon = DiscCon(topic, [disc1, disc2])
    # show concordance
    print(disccon.concordance())
    print(disccon.concordance(p_show=['word', 'lemma'])['df'].iloc[0])


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
    discpos = DiscCon(topic, [disc1, disc2])
    # show collocates
    print(discpos.collocates())


@pytest.mark.disccon
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
    disccon = DiscCon(topic, [disc1, disc2])
    # show collocates
    print(disccon.collocates())


@pytest.mark.disccon
def test_disccon_collocates_empty():
    # three discoursemes
    topic = Disc(
        Corpus('GERMAPARL_1114'),
        ["Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's'
    )
    # init discursive position
    disccon = DiscCon(topic)
    disccon.add_items(["Verhandlung"])
    # show collocates
    assert(disccon.collocates(window=5).empty)
