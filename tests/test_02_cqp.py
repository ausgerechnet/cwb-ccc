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
        binary="cqp",
        options='-c -r ' + germaparl['registry_path']
    )
    cqp.Exec(germaparl['corpus_name'])
    cqp.Query('"Horst"')
    df = cqp.Dump()
    assert(len(df) == 55)
    assert(isinstance(df, pd.DataFrame))


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
