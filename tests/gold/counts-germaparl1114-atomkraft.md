# query parameters
- context counts for 'Atomkraft'
- window size: L5, R5
- restricted to <s> regions
- query level: lemma (node and collocates)

# UCS
```bash
ucs-tool surface-from-cwb-query -h
ucs-tool surface-from-cwb-query -ca lemma -w 5 -S s GERMAPARL_1114 ucs-germaparl1114-Atomkraft.ds.gz '[lemma="Atomkraft"]' "match .. matchend lemma"
```

# ccc
```python
from ccc.cwb import CWBEngine
from ccc.collocates import Collocates
engine = CWBEngine("GERMAPARL_1114", registry_path)
collocates = Collocates(engine, max_window_size=5, s_break='p', p_query='lemma', cut_off=None)
c = collocates.query('[lemma="Atomkraft"]', window=5)
c.to_csv("tests/gold/ccc-germaparl1114-atomkraft.tsv.gz", compression="gzip", sep="\t")
```

# polmineR
```R
library(polmineR)
library(readr)
cooc <- cooccurrences("GERMAPARL_1114", query='[lemma="Atomkraft"]', left=5, right=5, p_attribute='lemma', s_attribute='s')
write_tsv(format(cooc), path="polmineR-germaparl1114-atomkraft.tsv")
```
