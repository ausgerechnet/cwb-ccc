from ccc import Corpus
from ccc.discoursemes import Disc, DiscPos
# import pytest


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
        's',
        name='topic'
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
        's',
        name='topic'
    )
    print(topic.context())


def test_disc_concordance():

    corpus = Corpus('GERMAPARL_1114')
    topic = Disc(
        corpus,
        ["Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's'
    )
    print(topic.show_concordance(20))
    print(topic.show_concordance(10))
    print(topic.show_concordance(30))


def test_disc_concordance_form():

    corpus = Corpus('GERMAPARL_1114')
    topic = Disc(
        corpus,
        ["Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's'
    )
    # print(topic.show_concordance(cut_off=None, form='kwic'))
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

    corpus = Corpus('GERMAPARL_1114')

    # init topic disc
    topic = Disc(
        corpus,
        ["Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's',
        name='topic'
    )

    # switch to subcorpus for improved performance
    corpus.subcorpus_from_dump(
        topic.context(),
        topic.idx + '_context'
    )
    corpus.activate_subcorpus(topic.idx + '_context')

    # two discoursemes
    disc1 = Disc(
        corpus,
        ["Streit", "Verhandlung", "Regierung"],
        'lemma',
        's',
        's',
        name='disc1'
    )
    disc2 = Disc(
        corpus,
        ["Angela"],
        'lemma',
        's',
        's',
        name='disc2'
    )
    discpos = DiscPos(topic, corpus, [disc1, disc2])
    discpos.slice_discs()
    print(discpos.df_nodes.columns)
    print(discpos.df_nodes)
    print(discpos.df_nodes['offset_disc1'])
    print(discpos.df_nodes['offset_disc2'])


def test_discpos_concordance():
    corpus = Corpus('GERMAPARL_1114')

    # three discoursemes
    topic = Disc(
        corpus,
        ["Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's',
        name='topic'
    )
    disc1 = Disc(
        corpus,
        ["Angela", "Streit", "Verhandlung", "Regierung"],
        'lemma',
        's',
        's',
        name='disc1'
    )
    disc2 = Disc(
        corpus,
        ["die"],
        'lemma',
        's',
        's',
        name='disc2'
    )

    # init discursive position
    discpos = DiscPos(topic, corpus, [disc1, disc2])
    # show collocates
    print(discpos.show_concordance())
    print(discpos.show_concordance(p_show=['word', 'lemma'])['df'].iloc[0])


def test_discpos_collocates():
    corpus = Corpus('GERMAPARL_1114')

    # three discoursemes
    topic = Disc(
        corpus,
        ["Merkel", "Seehofer", "Steinmeier"],
        'lemma',
        's',
        's',
        name='topic'
    )
    disc1 = Disc(
        corpus,
        ["Angela", "Streit", "Verhandlung", "Regierung"],
        'lemma',
        's',
        's',
        name='disc1'
    )
    disc2 = Disc(
        corpus,
        ["die"],
        'lemma',
        's',
        's',
        name='disc2'
    )

    # init discursive position
    discpos = DiscPos(topic, corpus, [disc1, disc2])
    # show collocates
    print(discpos.show_collocates())
