from ccc.cwb import Corpus


def test_dump():
    corpus = Corpus("BREXIT_2019")
    df_node = corpus.query('[lemma="angela"] within tweet')
    corpus.save_subcorpus('Last')
    corpus.show_subcorpora()
    corpus = Corpus("BREXIT_2019")
    corpus.activate_subcorpus('Last')
    corpus.show_subcorpora()
