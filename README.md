# Collocation and Concordance Computation #
[![Build](https://github.com/ausgerechnet/cwb-ccc/actions/workflows/build-test.yml/badge.svg?branch=master)](https://github.com/ausgerechnet/cwb-ccc/actions/workflows/build-test.yml?query=branch%3Amaster)
[![PyPI version](https://badge.fury.io/py/cwb-ccc.svg)](https://badge.fury.io/py/cwb-ccc)
[![PyPI Downloads](https://img.shields.io/pypi/dm/cwb-ccc)](https://img.shields.io/pypi/dm/cwb-ccc)
[![License](https://img.shields.io/pypi/l/cwb-ccc.svg)](https://github.com/ausgerechnet/cwb-ccc/blob/master/LICENSE)
[![Imports: association-measures](https://img.shields.io/badge/%20imports-association--measures-%231674b1?style=flat&labelColor=gray)](https://github.com/fau-klue/pandas-association-measures)

**cwb-ccc** is a Python 3 wrapper around the [IMS Open Corpus Workbench (CWB)](http://cwb.sourceforge.net/).  Main purpose of the module is to run queries (including queries with more than two anchor points), extract concordance lines, and score frequency lists (particularly to extract collocates and keywords).

The [Quickstart](#quickstart) here gives a rough overview.  For a more detailed dive into the functionality, see the [Vignette](demos/vignette.md).

* [Installation](#installation)
* [Quickstart](#quickstart)
  * [Accessing Corpora](#accessing-corpora)
  * [Queries and SubCorpora](#queries-and-subcorpus)
  * [Concordancing](#concordancing)
  * [Collocates](#collocation-analyses)
  * [Keywords](#keyword-analyses)
* [Testing](#testing)
* [Acknowledgements](#acknowledgements)


## Installation ##

**System requirements**:  The module is developed for Ubuntu (currently 24.04 LTS) but also runs on other Debian-based systems and MacOS.  On a fresh install of Ubuntu, you will need to install the following packages:
```
sudo apt install libncurses5-dev libglib2.0-dev libpcre3 libpcre3-dev
```

**CWB**:  The module needs a working installation of [CWB](http://cwb.sourceforge.io/) and operates on CWB-indexed corpora.  If you want to run queries with more than two anchor points, you will need CWB version 3.4.16 or later.  We recommend installing the [3.5.x package](https://cwb.sourceforge.io/install.php).  You will also need to install the corresponding `cwb-dev` package. On Ubuntu, you can e.g. run
```
wget https://kumisystems.dl.sourceforge.net/project/cwb/cwb/cwb-3.5/deb/cwb_3.5.0-1_amd64.deb
wget https://master.dl.sourceforge.net/project/cwb/cwb/cwb-3.5/deb/cwb-dev_3.5.0-1_amd64.deb
sudo apt install ./cwb_3.5.0-1_amd64.deb
sudo apt install ./cwb-dev_3.5.0-1_amd64.deb
```

**Python dependencies**:  Python dependencies are specified in [requirements.txt](requirements.txt) and will be installed automatically if you follow the instructions below.  We recommend installing dependencies in a [virtual environment](https://docs.python.org/3/library/venv.html) to avoid conflicts with other installs on your machine.  Note that since version v0.13.0, `cwb-ccc` uses `pandas2` and `numpy2`, which requires Python 3.9 or above.

**Installation using pip**:  You can install cwb-ccc with pip from [PyPI](https://pypi.org/project/cwb-ccc/):
```
python3 -m pip install cwb-ccc
```

**Installation from source**:  You can also clone the source from [github](https://github.com/ausgerechnet/cwb-ccc), `cd` in the respective folder, and e.g. build your own wheel:
```
python3 -m venv venv
. venv/bin/activate
pip3 install -U pip setuptools wheel twine
pip3 install -r requirements.txt
pip3 install -r requirements-dev.txt
python3 -m cython -2 ccc/cl.pyx
python3 setup.py bdist_wheel
```

## Quickstart ##

### Accessing Corpora ###

To list all available corpora, you can use
```python
from ccc import Corpora
corpora = Corpora(registry_dir="/usr/local/share/cwb/registry/")
```

Most functionality is tied to the `Corpus` class, which establishes the connection to your CWB-indexed corpus:
```python
from ccc import Corpus
corpus = Corpus(corpus_name="GERMAPARL1386", registry_dir="tests/corpora/registry/")
```
This will raise a `KeyError` if the named corpus is not in the specified registry.


### Queries and SubCorpora ###

The usual starting point is to run a query with `corpus.query()`.  This method accepts valid CQP queries such as
```python
subcorpus = corpus.query('[lemma="Arbeit"]', context_break='s')
```

The result is a `SubCorpus`; at its core this is a pandas `DataFrame` with corpus positions (similar to CWB dumps of NQRs).

You can also query structural attributes, e.g.
```python
corpus.query(s_query='text_party', s_values={'CDU', 'CSU'})
```

### Concordancing ###

You can access concordance lines via the `concordance()` method of subcorpora.  This method returns a DataFrame with information about the query matches in context:

<details>
<summary><code>subcorpus.concordance()</code></summary>
<p>

| *match* | *matchend* | word                                                                                                                                                    |
|--------:|-----------:|:--------------------------------------------------------------------------------------------------------------------------------------------------------|
|     151 |        151 | Er brachte diese Erfahrung in seine Arbeit im Ausschuß für Familie , Senioren , Frauen und Jugend sowie im Petitionsausschuß ein , wo er sich vor allem |
|     227 |        227 | Seine Arbeit und sein Rat werden uns fehlen .                                                                                                           |
|    1493 |       1493 | Ausschuß für Arbeit und Sozialordnung                                                                                                                   |
|    1555 |       1555 | Ausschuß für Arbeit und Sozialordnung                                                                                                                   |
|    1598 |       1598 | Ausschuß für Arbeit und Sozialordnung                                                                                                                   |
|     ... |        ... | ...                                                                                                                                                     |
|         |            |                                                                                                                                                         |

</p>
</details>

By default, it retrieves concordance lines in `simple` format in the order in which they appear in the corpus.  In most situations it is more useful to get `random` concordance lines in KWIC formatting:

<details>
<summary><code>subcorpus.concordance(form='kwic', order='random')</code></summary>
<p>

| *match* | *matchend* | left\_word                                                                                                                                    | node\_word | right\_word                                                                                                                                        |
|--------:|-----------:|:----------------------------------------------------------------------------------------------------------------------------------------------|:-----------|:---------------------------------------------------------------------------------------------------------------------------------------------------|
|   81769 |      81769 | Ich unterstütze daher nachträglich die Forderung , daß die Durchführung des Gesetzes auch künftig durch die Bundesanstalt für                 | Arbeit     | vorgenommen wird ; denn beim Bund gibt es die entsprechend ausgebildeten Sachbearbeiter .                                                          |
|    8774 |       8774 | Glauben Sie im Ernst , Sie könnten am Ende ein Bündnis für                                                                                    | Arbeit     | , eine Wende in der deutschen Politik , die Bekämpfung der Arbeitslosigkeit erreichen , wenn Sie nicht die Länder ,                                |
|    8994 |       8994 | alle Entscheidungen gemeinsam zu treffen , die sich gegen Schwarzarbeit und illegale                                                          | Arbeit     | wenden , und gemeinsam nach einem Weg zu suchen ,                                                                                                  |
|   80098 |      80098 | : Was der Vermittlungsausschuß mit Mehrheit zum Meister-BAföG beschlossen hat , heißt , daß die bewährten Institutionen der Bundesanstalt für | Arbeit     | , die die Ausbildungsförderung für Meister bis zum Jahr 1993 durchgeführt haben , die darin große Erfahrung haben , die                            |
|   61056 |      61056 | Selbst wenn Sie ein Konstrukt anbieten , das tendenziell die zusätzliche Belastung der Bundesanstalt für                                      | Arbeit     | etwas geringer hielte als die Entlastung bei der gesetzlichen Rentenversicherung , so wäre dies bei einem deutlichen Aufwuchs der Arbeitslosigkeit |
|     ... |        ... | ...                                                                                                                                           | ...        | ...                                                                                                                                                |
|         |            |                                                                                                                                               |            |                                                                                                                                                    |

</p>
</details>

Use `cut_off` to specify the maximum number of lines.


### Collocation Analyses ###

After executing a query, you can use `subcorpus.collocates()` to extract collocates (see the vignette for parameter settings).  The result is a `DataFrame` with lemmata as index and frequency signatures and association measures as columns:

<details>
<summary><code>subcorpus.collocates()</code></summary>
<p>

| *item* | O11 | O12 |  O21 |    O22 |  R1 |     R2 |   C1 |     C2 |      N |     E11 |     E12 |     E21 |    E22 | z\_score | t\_score | log\_likelihood | simple\_ll | min\_sensitivity |  liddell |     dice | log\_ratio | conservative\_log\_ratio | mutual\_information | local\_mutual\_information |     ipm | ipm\_reference | ipm\_expected | in\_nodes | marginal |
|:-------|----:|----:|-----:|-------:|----:|-------:|-----:|-------:|-------:|--------:|--------:|--------:|-------:|---------:|---------:|----------------:|-----------:|-----------------:|---------:|---------:|-----------:|-------------------------:|--------------------:|---------------------------:|--------:|---------------:|--------------:|----------:|---------:|
| für    |  46 | 730 |  831 | 148102 | 776 | 148933 |  877 | 148832 | 149709 | 4.54583 | 771.454 | 872.454 | 148061 |  19.4429 |  6.11208 |         134.301 |    130.019 |         0.052452 | 0.047547 | 0.055656 |    3.40925 |                  2.26335 |             1.00514 |                    46.2366 | 59278.4 |        5579.69 |       5858.03 |         0 |      877 |
| ,      |  43 | 733 | 7827 | 141106 | 776 | 148933 | 7870 | 141839 | 149709 | 40.7933 | 735.207 | 7829.21 | 141104 | 0.345505 | 0.336523 |        0.124564 |   0.117278 |         0.005464 | 0.000296 | 0.009947 |   0.076412 |                        0 |             0.02288 |                   0.983836 | 55412.4 |        52553.8 |       52568.6 |         0 |     7870 |
| .      |  33 | 743 | 5626 | 143307 | 776 | 148933 | 5659 | 144050 | 149709 | 29.3328 | 746.667 | 5629.67 | 143303 | 0.677108 | 0.638378 |        0.461005 |   0.440481 |         0.005831 | 0.000673 | 0.010256 |   0.170891 |                        0 |             0.05116 |                    1.68829 | 42525.8 |        37775.4 |         37800 |         0 |     5659 |
| und    |  32 | 744 | 2848 | 146085 | 776 | 148933 | 2880 | 146829 | 149709 | 14.9282 | 761.072 | 2865.07 | 146068 |  4.41852 |   3.0179 |         15.1452 |    14.6555 |         0.011111 | 0.006044 | 0.017505 |    1.10866 |                        0 |            0.331144 |                    10.5966 | 41237.1 |        19122.7 |       19237.3 |         0 |     2880 |
| in     |  24 | 752 | 2474 | 146459 | 776 | 148933 | 2498 | 147211 | 149709 | 12.9481 | 763.052 | 2485.05 | 146448 |  3.07138 |  2.25596 |         7.72813 |    7.51722 |         0.009608 | 0.004499 | 0.014661 |   0.896724 |                        0 |            0.268005 |                    6.43212 | 30927.8 |        16611.5 |       16685.7 |         0 |     2498 |
| ...    | ... | ... |  ... |    ... | ... |    ... |  ... |    ... |    ... |     ... |     ... |     ... |    ... |      ... |      ... |             ... |        ... |              ... |      ... |      ... |        ... |                      ... |                 ... |                        ... |     ... |            ... |           ... |       ... |      ... |

</p>
</details>

Setting `p_query` allows calculating scores for arbitrary combinations of positional attributes, e.g. `p_query=['lemma', 'pos']`.  The dataframe contains the observed counts in contingency notation and is annotated with all available association measures from the [pandas-association-measures](https://pypi.org/project/association-measures/) package (parameter `ams`).


### Keyword Analyses ###

Having created a subcorpus
```python
subcorpus = corpus.query(s_query='text_party', s_values={'CDU', 'CSU'})
```
you can use its `keywords()` method for retrieving keywords:

<details>
<summary><code>subcorpus.keywords(order='conservative_log_ratio')</code></summary>
<p>

| *item*     | O11 |   O12 |  O21 |    O22 |    R1 |     R2 |   C1 |     C2 |      N |     E11 |     E12 |     E21 |    E22 | z\_score | t\_score | log\_likelihood | simple\_ll | min\_sensitivity |  liddell |     dice | log\_ratio | conservative\_log\_ratio | mutual\_information | local\_mutual\_information |     ipm | ipm\_reference | ipm\_expected |
|:-----------|----:|------:|-----:|-------:|------:|-------:|-----:|-------:|-------:|--------:|--------:|--------:|-------:|---------:|---------:|----------------:|-----------:|-----------------:|---------:|---------:|-----------:|-------------------------:|--------------------:|---------------------------:|--------:|---------------:|--------------:|
| deswegen   |  55 | 41296 |   37 | 108412 | 41351 | 108449 |   92 | 149708 | 149800 | 25.3958 | 41325.6 | 66.6042 | 108382 |  5.87452 |  3.99183 |         41.5308 |     25.794 |          0.00133 | 0.321982 | 0.002654 |    1.96293 |                 0.404166 |            0.335601 |                     18.458 | 1330.08 |        341.174 |       614.152 |
| CSU        | 255 | 41096 |  380 | 108069 | 41351 | 108449 |  635 | 149165 | 149800 | 175.286 | 41175.7 | 459.714 | 107989 |  6.02087 |  4.99187 |         46.6543 |    31.7425 |         0.006167 | 0.126068 | 0.012147 |    0.81552 |                 0.212301 |            0.162792 |                     41.512 | 6166.72 |        3503.95 |       4238.99 |
| CDU        | 260 | 41091 |  390 | 108059 | 41351 | 108449 |  650 | 149150 | 149800 | 179.427 | 41171.6 | 470.573 | 107978 |  6.01515 |  4.99693 |         46.6055 |    31.7289 |         0.006288 | 0.124499 | 0.012381 |    0.80606 |                 0.209511 |            0.161086 |                    41.8823 | 6287.64 |        3596.16 |       4339.12 |
| in         | 867 | 40484 | 1631 | 106818 | 41351 | 108449 | 2498 | 147302 | 149800 | 689.551 | 40661.4 | 1808.45 | 106641 |  6.75755 |  6.02647 |         61.2663 |    42.1849 |         0.020967 | 0.072241 | 0.039545 |    0.47937 |                 0.168901 |            0.099452 |                    86.2253 | 20966.8 |        15039.3 |       16675.6 |
| Wirtschaft |  39 | 41312 |   25 | 108424 | 41351 | 108449 |   64 | 149736 | 149800 | 17.6666 | 41333.3 | 46.3334 | 108403 |  5.07554 |  3.41607 |         30.9328 |    19.1002 |         0.000943 | 0.333476 | 0.001883 |    2.03257 |                 0.150982 |             0.34391 |                    13.4125 | 943.145 |        230.523 |       427.236 |
| ...        | ... |   ... |  ... |    ... |   ... |    ... |  ... |    ... |    ... |     ... |     ... |     ... |    ... |      ... |      ... |             ... |        ... |              ... |      ... |      ... |        ... |                      ... |                 ... |                        ... |     ... |            ... |           ... |

</p>
</details>

Just as with collocates, the result is a `DataFrame` with lemmata as index and frequency signatures and association measures as columns.

## Testing ##

The module ships with a small test corpus ("GERMAPARL1386"), which contains all speeches of the 86th session of the 13th German Bundestag on Feburary 8, 1996.
```python
corpus = Corpus("GERMAPARL1386", registry_dir="tests/corpora/registry/")
```
This corpus consists of 149,800 tokens in 7332 paragraphs (s-attribute "p" with annotation "type" ("regular" or "interjection")) split into 11,364 sentences (s-attribute "s").  The p-attributes are "pos" and "lemma":

<details>
<summary><code>corpus.available_attributes()</code></summary>
<p>

| type   | attribute                  | annotation   | active   |
|:-------|:---------------------------|:-------------|:---------|
| p-Att  | word                       | False        | True     |
| p-Att  | pos                        | False        | False    |
| p-Att  | lemma                      | False        | False    |
| s-Att  | corpus                     | False        | False    |
| s-Att  | corpus\_name               | True         | False    |
| s-Att  | sitzung                    | False        | False    |
| s-Att  | sitzung\_date              | True         | False    |
| s-Att  | sitzung\_period            | True         | False    |
| s-Att  | sitzung\_session           | True         | False    |
| s-Att  | div                        | False        | False    |
| s-Att  | div\_desc                  | True         | False    |
| s-Att  | div\_n                     | True         | False    |
| s-Att  | div\_type                  | True         | False    |
| s-Att  | div\_what                  | True         | False    |
| s-Att  | text                       | False        | False    |
| s-Att  | text\_id                   | True         | False    |
| s-Att  | text\_name                 | True         | False    |
| s-Att  | text\_parliamentary\_group | True         | False    |
| s-Att  | text\_party                | True         | False    |
| s-Att  | text\_position             | True         | False    |
| s-Att  | text\_role                 | True         | False    |
| s-Att  | text\_who                  | True         | False    |
| s-Att  | p                          | False        | False    |
| s-Att  | p\_type                    | True         | False    |
| s-Att  | s                          | False        | False    |

</p>
</details>

The corpus is located in this [repository](tests/corpora/).  All tests are written using this corpus as well as some reference counts and scores obtained from the [UCS toolkit](http://www.collocations.de/software.html) and some additional frequency lists.  Make sure you install all development dependencies (especially [pytest](https://pytest.org/)).  You can then
```
pytest -m "not benchmark"
pytest -m benchmark
pytest --cov-report term-missing -v --cov=ccc/
```

## Acknowledgements ##

- The module includes a slight adaptation of [cwb-python](https://github.com/fau-klue/cwb-python), a Python port of Perl's CWB::CL; thanks to **Yannick Versley** for the implementation.
- Special thanks to **Markus Opolka** for the original implementation of [association-measures](https://github.com/fau-klue/pandas-association-measures) and for forcing me to write tests.
- The test corpus was extracted from the [GermaParl](https://github.com/PolMine/GermaParlTEI) corpus (see the [PolMine Project](https://polmine.github.io/)); many thanks to **Andreas Blätte**.
- This work was supported by the [Emerging Fields Initiative (EFI)](https://www.fau.eu/research/collaborative-research/emerging-fields-initiative/) of [**Friedrich-Alexander-Universität Erlangen-Nürnberg**](https://www.fau.eu/), project title [Exploring the *Fukushima Effect*](https://www.linguistik.phil.fau.de/projects/efe/) (2017-2020).
- Further development of the package was funded by the Deutsche Forschungsgemeinschaft (DFG) within the projects [Reconstructing Arguments from Noisy Text (2018-2021) and Newsworthy Debates (2021-2024)](https://www.linguistik.phil.fau.de/projects/rant/), grant number 377333057, as part of the Priority Program [**Robust Argumentation Machines**](http://www.spp-ratio.de/) (SPP-1999).
