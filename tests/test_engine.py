from ccc.cwb import Engine


def test_engine():
    engine = Engine("/home/ausgerechnet/corpora/cwb/registry/")
    corpora = engine.show_corpora()
    print(corpora)
