from ccc import Corpus

# Test = [lemma="haben"] @0[xpos="P.*"] @1[lemma=".*"];
# group Test target lemma by keyword lemma
# NB: target = 0; keyword = 1

query = '@0[pos="N.*"] [lemma="sein"] [pos="ART.*"]? @1[pos="N.*"];'
germaparl = Corpus("GERMAPARL1386", registry_path="tests/corpora/registry/")

dump = germaparl.query(query)
conc = dump.concordance(p_show=['lemma'], form='slots', cut_off=None)
conc.groupby(['1_lemma', '0_lemma']).size().sort_values(ascending=False)

cqp = germaparl.start_cqp()
cqp.Query(f'Test={query}')
print(cqp.Group("Test target lemma by keyword lemma;"))
