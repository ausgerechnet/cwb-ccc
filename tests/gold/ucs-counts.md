# gold standard from UCS toolkit

## Atomkraft
- context counts for 'Atomkraft'
- window size: L5, R5
- restricted to <s> regions
- query level: lemma (node and collocates)

```bash
ucs-tool surface-from-cwb-query -ca lemma -w 5 -S s GERMAPARL_1114 ucs-germaparl1114-Atomkraft.ds.gz '[lemma="Atomkraft"]' "match .. matchend lemma"
```

## Angela
- context counts for Atomkraft
- window size: L5, R5
- restricted to <s> regions
- query level: lemma (node and collocates)

```bash
ucs-tool surface-from-cwb-query -ca lemma -w 5 -S s GERMAPARL_1114 ucs-germaparl1114-Angela.ds.gz '[lemma="Angela"]' "match .. matchend lemma"
```

## Angela
- context counts for Atomkraft
- window size: L2, R2
- restricted to <s> regions
- query level: lemma (node and collocates)
- cut-off: >=2 (drop hapaxes)

```bash
ucs-tool surface-from-cwb-query -f 2 -ca lemma -w 2 -S s GERMAPARL_1114 ucs-germaparl1114-und.ds.gz '[lemma="und"]' "match .. matchend lemma"
```
