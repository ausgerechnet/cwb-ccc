# gold standard for context counts 
- compare context counts with UCS toolkit
- test corpus: GERMAPARL1386

## Land
- context counts for 'Land'
- window size: L10, R10
- restricted to <s> regions
- query level: lemma (node and collocates)
- cut-off: none

```bash
ucs-tool surface-from-cwb-query -ca lemma -w 10 -S s GERMAPARL1386 ucs-germaparl1386-Land.ds.gz '[lemma="Land"]' "match .. matchend lemma"
```

## und
- context counts for 'und'
- window size: L5, R5
- restricted to <s> regions
- query level: lemma (node and collocates)
- cut-off: >=2 (drop hapaxes)

```bash
ucs-tool surface-from-cwb-query -f 2 -ca lemma -w 5 -S s GERMAPARL1386 ucs-germaparl1386-und.ds.gz '[lemma="und"]' "match .. matchend lemma"
```
