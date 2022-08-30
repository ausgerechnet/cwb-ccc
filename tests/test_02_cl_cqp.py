from ccc.cqp import CQP
from ccc.cl import Corpus

from pandas import DataFrame
from time import sleep
# import pytest


def test_cqp_version():
    print()
    print("... you should see your CQP version below ...")
    CQP(print_version=True)


def test_cqp_kill():
    n = 10
    rate = 1000                 # per second
    print()
    print("... spawning several CQP processes ...")
    print("... check htop or equivalent ...")
    for i in range(n):
        cqp = CQP()
        print("process_id = %d, run = %d/%d" % (
            cqp.CQP_process.pid,
            i + 1, n
            ), end="\r"
        )
        cqp.__kill__()
        sleep(1/rate)
    print()


def test_cqp_query(germaparl):
    cqp = CQP(
        binary="cqp",
        options='-c -r ' + germaparl['registry_path']
    )
    cqp.Exec(germaparl['corpus_name'])
    cqp.Query('"Horst"')


def test_cqp_dump(germaparl):
    cqp = CQP(
        binary="cqp",
        options='-c -r ' + germaparl['registry_path']
    )
    cqp.Exec(germaparl['corpus_name'])
    cqp.Query('"Horst"')
    df = cqp.Dump()
    assert(len(df) == 55)
    assert(isinstance(df, DataFrame))


def test_cqp_undump(germaparl):
    cqp = CQP(
        binary="cqp",
        options='-c -r ' + germaparl['registry_path']
    )
    cqp.Exec(germaparl['corpus_name'])
    cqp.Query('"Horst"')
    df = cqp.Dump()
    cqp.Undump("Test", df)
    assert(int(cqp.Exec("size Test;")) > 0)
    assert(cqp.Exec("size Test;") == str(len(df)))


def test_cqp_group(germaparl):
    cqp = CQP(
        binary="cqp",
        options='-c -r ' + germaparl['registry_path']
    )
    cqp.Exec(germaparl['corpus_name'])
    cqp.Query('[lemma="Horst"] [lemma="Seehofer"]')
    counts = cqp.Group(spec1="match.lemma", spec2="matchend.lemma")
    assert(type(counts) == str)
    assert(int(counts.split("\t")[-1]) == 11)


def test_nqr_from_query(germaparl):
    cqp = CQP(
        binary="cqp",
        options='-c -r ' + germaparl['registry_path']
    )
    cqp.Exec(germaparl['corpus_name'])
    assert(int(cqp.Exec('size Seehofer;')) == 0)
    cqp.nqr_from_query(
        query='[lemma="Seehofer"];',
        name='Seehofer',
        return_dump=False
    )
    assert(int(cqp.Exec('size Seehofer;')) > 0)
    cqp.__kill__()


def test_nqr_from_dump(germaparl):
    cqp = CQP(
        binary="cqp",
        options='-c -r ' + germaparl['registry_path']
    )
    cqp.Exec(germaparl['corpus_name'])
    assert(int(cqp.Exec('size Seehof;')) == 0)
    df_dump = germaparl['dump']
    cqp.nqr_from_dump(df_dump, name='Seehof')
    assert(int(cqp.Exec('size Seehof;')) > 0)
    cqp.__kill__()


def test_cl(germaparl):
    corpus = Corpus(germaparl['corpus_name'],
                    registry_dir=germaparl['registry_path'])

    # get sentences, words, pos-tags
    sentences = corpus.attribute('s', 's')
    assert(len(sentences) == 11364)
    words = corpus.attribute('word', 'p')
    assert(len(words) == 149800)
    postags = corpus.attribute('pos', 'p')
    assert(len(postags) == 149800)

    # offsets of the 1235th sentence (0-based)
    s_1234 = sentences[1234]
    assert(s_1234[0] == 21678)
    assert(s_1234[1] == 21688)

    # first word of 1235th sentence
    assert(words[s_1234[0]] == "Die")


def test_nqr_from_dump_error(germaparl):
    cqp = CQP(
        binary="cqp",
        options='-c -r ' + germaparl['registry_path']
    )
    cqp.Exec(germaparl['corpus_name'])

    # valid dump:
    df_dump = DataFrame(
        data={
            'match': [0, 2],
            'matchend': [3, 4]
        }
    ).set_index(['match', 'matchend'])
    cqp.nqr_from_dump(df_dump, name='Valid')
    assert cqp.Ok()
    assert int(cqp.Exec('size Valid;')) == 2

    # error type 1: missing values
    df_dump = DataFrame(
        data={
            'match': [0, 0],
            'matchend': [10, -1]
        }
    ).set_index(['match', 'matchend'])
    cqp.nqr_from_dump(df_dump, name='Error1')
    assert not cqp.Ok()
    assert int(cqp.Exec('size Error1;')) == 0

    # error type 2: match after matchend
    df_dump = DataFrame(
        data={
            'match': [0, 10],
            'matchend': [10, 9]
        }
    ).set_index(['match', 'matchend'])
    cqp.nqr_from_dump(df_dump, name='Error2')
    assert not cqp.Ok()
    assert int(cqp.Exec('size Error2;')) == 0

    # valid dump:
    df_dump = DataFrame(
        data={
            'match': [0, 2],
            'matchend': [3, 4]
        }
    ).set_index(['match', 'matchend'])
    cqp.nqr_from_dump(df_dump, name='Valid')
    assert cqp.Ok()
    assert int(cqp.Exec('size Valid;')) == 2

    cqp.__kill__()
