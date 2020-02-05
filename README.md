# Collocation and Concordance Computation #

* [Introduction](#introduction)
* [Installation](#installation)
* [Usage](#usage)
	* [Initializing the engine](#cwbengine)
	* [Extracting concordance lines](#concordancing)
	* [Dealing with anchored queries](#anchored-queries)
	* [Calculating collocates](#collocation-analyses)
	* [Argument queries](#argument-queries)
* [Acknowledgements](#acknowledgements)


## Introduction ##
This module is a wrapper around the
[IMS Open Corpus Workbench (CWB)](http://cwb.sourceforge.net/).
Main purpose of the module is to extract concordance lines, calculate
collocates, and run queries with several anchor points.

If you want to extract the results of anchored queries with more than
two anchor points, the module requires CWB version 3.4.16 or later.


## Installation ##
You can install this module with pip from PyPI:

	pip3 install cwb-ccc

You can also clone the repository from
[github](https://github.com/ausgerechnet/cwb-ccc), `cd` in the
respective folder, and use `setup.py`:

	python3 setup.py install


## Usage ##

### CWBEngine
All methods rely on the `CWBEngine` from `ccc.cwb`, which you first
have to initialize with your system specific settings:
```python
from ccc.cwb import CWBEngine
engine = CWBEngine(
	corpus_name="EXAMPLE_CORPUS",
	registry_path="/path/to/your/cwb/registry/"
)
```

This will raise a `KeyError` if the named corpus is not in the
specified registry.

If you are using macros and wordlists, you have to store them in a
separate folder (with subfolders `wordlists` and `macros`).  Make sure
you specify this folder via `lib_path` when initializing the
engine.

Point your engine to meta data stored as a tab-separated (and possibly
gziped) file via the `meta_path` parameter. The first column must be a
unique identifier, and the corresponding text regions have to be
annotated in the corpus as structural attribute (whose name you can
specify via the `s_meta` parameter, e.g. "text_id").

You can use the `cqp_bin` to point the engine to a specific version of
`cqp` (this is also helpful if `cqp` is not in your `PATH`).

By default, the `cache_path` points to "/tmp/ccc-cache". Make sure
that "/tmp/" exists and the appropriate rights are granted. Otherwise,
change the parameter when envoking the engine (or set it to `None`).

### Concordancing ###

You can use the `Concordance` class from `ccc.concordances` for
concordancing. The concordancer has to be initialized with the engine:
```python
from ccc.concordances import Concordance
concordance = Concordance(engine)
```
The concordancer accepts valid CQP queries such as
```python
query = '[lemma="Angela"]? [lemma="Merkel"] [word="\\("] [lemma="CDU"] [word="\\)"]'
```

The default context window is 20 tokens to the left and 20 tokens to
the right of the query match and matchend, respectively. You can
change this via the `context` parameter.

Note that queries _may_ end on a "within" clause (`s_query`), which
will limit the matches to certain regions defined by structural
attributes . Additionally, you can specify an `s_break` parameter,
which will cut the context (defaults to "text"). NB: The
implementation assumes that `s_query` regions are confined by
`s_break` regions, and both of them are within `s_meta` regions.

After executing the query
```
concordance.query(query)
```
you can access its frequency breakdown via `concordance.breakdown`:

| *type*                 | freq |
|------------------------|------|
| Angela Merkel ( CDU )  | 2253 |
| Merkel ( CDU )         | 29   |
| Angela Merkels ( CDU ) | 2    |

All query matches and their respective `meta_s` identifiers are listed
in `concordance.meta` (if `s_meta=None`, it will use the CQP
identifiers of the `s_break` parameter as `s_id`):

| *match* | s_id      |
|---------|-----------|
| 48349   | A44847086 |
| 48856   | A44855701 |
| 52966   | A44847097 |
| 53395   | A44847526 |
| ...     | ...       |

You can use `concordance.lines()` to get concordance lines. This
method will return a dictionary with the _cpos_ of the match as keys
and the entries one concordance line each. Each concordance line is
formatted as a `pandas.DataFrame` with the _cpos_ of each token as
index:

| *cpos* | offset | word                | anchor |
|--------|--------|---------------------|--------|
| 48344  | -5     | Eine                | None   |
| 48345  | -4     | entsprechende       | None   |
| 48346  | -3     | Steuererleichterung | None   |
| 48347  | -2     | hat                 | None   |
| 48348  | -1     | Kanzlerin           | None   |
| 48349  | 0      | Angela              | None   |
| 48350  | 0      | Merkel              | None   |
| 48351  | 0      | (                   | None   |
| 48352  | 0      | CDU                 | None   |
| 48353  | 0      | )                   | None   |
| 48354  | 1      | bisher              | None   |
| 48355  | 2      | ausgeschlossen      | None   |
| 48356  | 3      | .                   | None   |


You can decide which and how many concordance lines you want to
retrieve by means of the parameters `order` ("first", "last", or
"random") and `cut_off`. You can also provide a list of `matches`
(from `concordance.meta.index`) to get a `dict` of specific
concordance lines.

You can specify a `list` of additional p-attributes besides the
primary word layer to show via the `p_show` parameter of
`concordance.lines()` (these will be added as additional columns).

### Anchored Queries ###

The concordancer detects anchored queries automatically. The following query
```python
concordance.query(
	'@0[lemma="Angela"]? @1[lemma="Merkel"] [word="\\("] @2[lemma="CDU"] [word="\\)"]'
)
```
will thus return `DataFrame`s with appropriate anchors in the anchor column:

| *cpos* | offset | word                | anchor |
|--------|--------|---------------------|--------|
| 48344  | -5     | Eine                | None   |
| 48345  | -4     | entsprechende       | None   |
| 48346  | -3     | Steuererleichterung | None   |
| 48347  | -2     | hat                 | None   |
| 48348  | -1     | Kanzlerin           | None   |
| 48349  | 0      | Angela              | 0      |
| 48350  | 0      | Merkel              | 1      |
| 48351  | 0      | (                   | None   |
| 48352  | 0      | CDU                 | 2      |
| 48353  | 0      | )                   | None   |
| 48354  | 1      | bisher              | None   |
| 48355  | 2      | ausgeschlossen      | None   |
| 48356  | 3      | .                   | None   |


### Collocation Analyses ###
You can use the `Collocates` class to extract collocates for a given
window size (symmetric windows around the corpus matches):
```python
from ccc.collocates import Collocates
collocates = Collocates(engine)
# execute a query
collocates.query('[lemma="Angela"] [lemma="Merkel"]')
```
Upon executing a query, `collocates` will create a dataframe of
the cotext of the query matches. Its size is determined by the
`max_window_size` parameter. You will only be able to score collocates
up to this parameter (defaults to 20).

By default, windows are cut at the "text" s-attribute. You can change
this using the `s_break` attribute. Just like with the concordancer,
the initial query may contain an additional "within" statement.

By default, collocates are calculated on the "lemma"-layer, assuming
that this is a valid p-attribute in the corpus. The corresponding
parameter is `p_query` (which will fall back to "word" if the
specified attribute is not annotated in the corpus).

Using the marginal frequencies of the items in the whole corpus as a
reference, you can directly annotate the co-occurrence counts in a
given window:
```python
collocates.show(window=5)
```
The result will be a `DataFrame` with lexical items (lemmas by
default) as index and frequency signatures and association measures as
columns:

| *item*          | O11  | f2       | N         | f1    | O12   | O21      | O22       | E11         | E12          | E21          | E22          | log_likelihood | ... |
|-----------------|------|----------|-----------|-------|-------|----------|-----------|-------------|--------------|--------------|--------------|----------------|-----|
| die             | 1799 | 25125329 | 300917702 | 22832 | 21033 | 25123530 | 275771340 | 1906.373430 | 20925.626570 | 2.512342e+07 | 2.757714e+08 | -2.459194      | ... |
| Bundeskanzlerin | 1491 | 8816     | 300917702 | 22832 | 21341 | 7325     | 300887545 | 0.668910    | 22831.331090 | 8.815331e+03 | 3.008861e+08 | 1822.211827    | ... |
| .               | 1123 | 13677811 | 300917702 | 22832 | 21709 | 13676688 | 287218182 | 1037.797972 | 21794.202028 | 1.367677e+07 | 2.872181e+08 | 2.644804       | ... |
| ,               | 814  | 17562059 | 300917702 | 22832 | 22018 | 17561245 | 283333625 | 1332.513602 | 21499.486398 | 1.756073e+07 | 2.833341e+08 | -14.204447     | ... |
| Kanzlerin       | 648  | 17622    | 300917702 | 22832 | 22184 | 16974    | 300877896 | 1.337062    | 22830.662938 | 1.762066e+04 | 3.008772e+08 | 559.245198     | ... |

For improved performance, all hapax legomena in the cotext are dropped
after counting the cotext size. You can change this behaviour via the
`drop_hapaxes` parameter.

By default, the dataframe is annotated with "z_score", "t_score",
"dice", "log_likelihood", and "mutual_information" (parameter `ams`).
For notation and further information regarding association measures,
see
[collocations.de](http://www.collocations.de/AM/index.html). Available
association measures depend on their implementation in the
[association-measures](https://pypi.org/project/association-measures/)
module.

By default, the dataframe is sorted by co-occurrence frequency (O11),
and only the first 100 most frequently co-occurring collocates are
retrieved. You can change this behaviour via the `order` and `cut_off`
parameters.


### Argument Queries
Argument queries are anchored queries with additional information. (1)
Each anchor can be modified by an offset (usually used to capture
underspecified tokens near an anchor point). (2) Anchors can be mapped
to external identifiers for further logical processing. (3) Anchors
may be given a clear name:

| anchor | offset | idx  | clear name |
|--------|--------|------|------------|
| 0      | 0      | None | None       |
| 1      | -1     | None | None       |
| 2      | 0      | None | None       |
| 3      | -1     | None | None       |

Furthermore, several anchor points can be combined to form regions,
which in turn can be mapped to identifiers and be given a clear name:

| start | end | idx | clear name |
|-------|-----|-----|------------|
| 0     | 1   | "0" | "person X" |
| 2     | 3   | "1" | "person Y" |

Example: Given the definition of anchors and regions above as well as
suitable wordlists, the following complex query extracts corpus
positions where there's some correlation between "person X" (the
region from anchor 0 to anchor 1) and "person Y" (anchor 2 to 3):
```python
query = (
	"<np> []* /ap[]* [lemma = $nouns_similarity] "
	"[]*</np> \"between\" @0:[::](<np>[pos_simple=\"D|A\"]* "
	"([pos_simple=\"Z|P\" | lemma = $nouns_person_common | "
	"lemma = $nouns_person_origin | lemma = $nouns_person_support | "
	"lemma = $nouns_person_negative | "
	"lemma = $nouns_person_profession] |/region[ner])+ "
	"[]*</np>)+@1:[::] \"and\" @2:[::](<np>[pos_simple=\"D|A\"]* "
	"([pos_simple=\"Z|P\" | lemma = $nouns_person_common | "
	"lemma = $nouns_person_origin | lemma = $nouns_person_support | "
	"lemma = $nouns_person_negative | "
	"lemma = $nouns_person_profession] | /region[ner])+ "
	"[]*</np>) (/region[np] | <vp>[lemma!=\"be\"]</vp> | "
	"/region[pp] |/be_ap[])* @3:[::]"
)
```

NB: the set of identifiers defined in the table of anchors and in the
table of regions, respectively, should not overlap.

It is customary to store these queries in json objects (see an
[example](tests/gold/query-example.json) in the repository). You can
process argument queries with the `ArgConcordance` class from
`ccc.argmin`. As usual, the class has to be initialized with the
engine:
```python
from ccc.argmin import ArgConcordance
# read the query file
import json
query_path = "tests/gold/query-example.json"
with open(query_path, "rt") as f:
	query = json.loads(f.read())
# query the corpus
conc = ArgConcordance(engine)
result = conc.argmin_query(
	query=query['query'],
	anchors=query['anchors'],
	regions=query['regions']
)
```
Note that the `argmin_query` method directly returns the result as
`dict` with the following keys:

- "nr_matches": the number of query matches in the corpus.
- "matches": a list of concordance lines. Each concordance line
  contains:
  - "position": the corpus position of the match
  - "df": the actual concordance line as returned from
	`Concordance().query()` (see above) converted to a `dict`
  - "holes": a mapping from the IDs specified in the anchor and region
	tables to the tokens or token sequences, respectively (default:
	lemma layer)
  - "full": a reconstruction of the concordance line as a sequence of
	tokens (word layer)
- "holes": a global list of all tokens of the entities specified in
  the "idx" columns (default: lemma layer).


## Acknowledgements ##
The module relies on
[cwb-python](https://pypi.org/project/cwb-python/), thanks to Yannick
Versley and Jorg Asmussen for the implementation. Special thanks to
Markus Opolka for the implementation of
[association-measures](https://pypi.org/project/association-measures/)
and for forcing me to write tests.

This work was supported by the [Emerging Fields Initiative
(EFI)](https://www.fau.eu/research/collaborative-research/emerging-fields-initiative/)
of Friedrich-Alexander-Universität Erlangen-Nürnberg, project title
[Exploring the *Fukushima
Effect*](https://www.linguistik.phil.fau.de/projects/efe/).

Further development of the package has been funded by the Deutsche
Forschungsgemeinschaft (DFG) within the project *Reconstructing
Arguments from Noisy Text*, grant number 377333057, as part of the
Priority Program [Robust Argumentation
Machines](http://www.spp-ratio.de/home/) (SPP-1999).
