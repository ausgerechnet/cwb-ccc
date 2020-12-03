from ccc.cqp import CQP
import pandas as pd


def test_cqp_version():
    print()
    print("... you should see your CQP version below ...")
    CQP(print_version=True)


def test_cqp_kill():

    from time import sleep
    n = 100
    rate = 1000                 # per second
    print()
    print("... spawning several cqp processes ...")
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


def test_cqp_dump(germaparl):
    cqp = CQP(
        bin="cqp",
        options='-c -r ' + germaparl['registry_path']
    )
    cqp.Exec(germaparl['corpus_name'])
    cqp.Query('"Horst"')
    df = cqp.Dump()
    assert(len(df) == 55)
    assert(type(df) == pd.DataFrame)


def test_cqp_undump(germaparl):
    cqp = CQP(
        bin="cqp",
        options='-c -r ' + germaparl['registry_path']
    )
    cqp.Exec(germaparl['corpus_name'])
    cqp.Query('"Horst"')
    df = cqp.Dump()
    cqp.Undump("Test", df)
    assert(cqp.Exec("size Test;") == str(len(df)))


def test_cqp_group(germaparl):
    cqp = CQP(
        bin="cqp",
        options='-c -r ' + germaparl['registry_path']
    )
    cqp.Exec(germaparl['corpus_name'])
    cqp.Query('[lemma="Horst"] [lemma="Seehofer"]')
    counts = cqp.Group(spec1="match.lemma", spec2="matchend.lemma")
    assert(type(counts) == str)
    assert(int(counts.split("\t")[-1]) == 11)
