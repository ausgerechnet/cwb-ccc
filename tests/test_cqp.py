from ccc.cqp import CQP
import pandas as pd
import pytest

registry_path = "/home/ausgerechnet/corpora/cwb/registry/"
corpus_name = "BREXIT_V20190522"


def test_cqp_dump():
    cqp = CQP(
        bin="cqp",
        options='-c -r ' + registry_path
    )
    cqp.Exec(corpus_name)
    cqp.Query('"test"')
    df = cqp.Dump()
    assert(len(df) > 1000)
    assert(type(df) == pd.DataFrame)


def test_cqp_undump():
    cqp = CQP(
        bin="cqp",
        options='-c -r ' + registry_path
    )
    cqp.Exec(corpus_name)
    cqp.Query('"test"')
    df = cqp.Dump()
    cqp.Undump("test", df)
    assert(cqp.Exec("size test;") == str(len(df)))


def test_cqp_group():
    cqp = CQP(
        bin="cqp",
        options='-c -r ' + registry_path
    )
    cqp.Exec(corpus_name)
    cqp.Query('[lemma="angela"] [lemma="merkel"]')
    counts = cqp.Group(spec1="match.lemma", spec2="matchend.lemma")
    assert(type(counts) == str)


def test_cqp_many():

    from time import sleep
    for i in range(10):
        cqp = CQP(
            bin="cqp",
            options='-c -r ' + registry_path
        )
        print(i, cqp.CQP_process.pid)
        cqp.__kill__()
        sleep(.1)
