# query parameters
- context counts for 'Atomkraft'
- window size: L5, R5
- restricted to <s> regions
- query level: lemma (node and collocates)

# polmineR
```R
library(polmineR)
library(readr)
cooc <- cooccurrences("GERMAPARL_1114", query='[lemma="Atomkraft"]', left=5, right=5, p_attribute='lemma', s_attribute='s')
write_tsv(format(cooc), path="polmineR-germaparl1114-atomkraft.tsv")
```
