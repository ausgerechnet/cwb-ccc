cwb-ccc demo
================
Philipp Heinrich
March 23, 2021

-   [Setup](#setup)

## Setup

``` python
import os
import sys
sys.path.append("/home/ausgerechnet/implementation/cwb-ccc/")
import ccc
print(ccc.__version__)
```

    ## 0.9.14dev

``` python
from ccc import Corpora
corpora = Corpora()
print(corpora)
```

``` python
corpora.show()  # returns a dataframe
```

``` python
corpus = corpora.activate(corpus_name="GERMAPARL8613")
# select corpus
from ccc import Corpus
corpus = Corpus("GERMAPARL8613")
# print(corpus)
df = corpus.attributes_available
print(df.to_markdown())
```

|     | type  | attribute                  | annotation | active |
|----:|:------|:---------------------------|:-----------|:-------|
|   0 | p-Att | word                       | False      | True   |
|   1 | p-Att | pos                        | False      | False  |
|   2 | p-Att | lemma                      | False      | False  |
|   3 | s-Att | corpus                     | False      | False  |
|   4 | s-Att | corpus\_name               | True       | False  |
|   5 | s-Att | sitzung                    | False      | False  |
|   6 | s-Att | sitzung\_date              | True       | False  |
|   7 | s-Att | sitzung\_period            | True       | False  |
|   8 | s-Att | sitzung\_session           | True       | False  |
|   9 | s-Att | div                        | False      | False  |
|  10 | s-Att | div\_desc                  | True       | False  |
|  11 | s-Att | div\_n                     | True       | False  |
|  12 | s-Att | div\_type                  | True       | False  |
|  13 | s-Att | div\_what                  | True       | False  |
|  14 | s-Att | text                       | False      | False  |
|  15 | s-Att | text\_id                   | True       | False  |
|  16 | s-Att | text\_name                 | True       | False  |
|  17 | s-Att | text\_parliamentary\_group | True       | False  |
|  18 | s-Att | text\_party                | True       | False  |
|  19 | s-Att | text\_position             | True       | False  |
|  20 | s-Att | text\_role                 | True       | False  |
|  21 | s-Att | text\_who                  | True       | False  |
|  22 | s-Att | p                          | False      | False  |
|  23 | s-Att | p\_type                    | True       | False  |
|  24 | s-Att | s                          | False      | False  |

``` python
query = r'"\[" ([pos="NE"] "/"?)+ "\]"'
dump = corpus.query(query)
print(dump.df.head())
```

                context  contextend

match matchend  
580 582 560 602 649 651 629 671 2310 2312 2290 2332 2475 2477 2455 2497
2561 2563 2541 2583

``` python
print(dump.df.head().to_markdown())
```

|              | context | contextend |
|:-------------|--------:|-----------:|
| (580, 582)   |     560 |        602 |
| (649, 651)   |     629 |        671 |
| (2310, 2312) |    2290 |       2332 |
| (2475, 2477) |    2455 |       2497 |
| (2561, 2563) |    2541 |       2583 |
