# Collocation and Concordance Computation #

## Introduction ##
This module is a wrapper around the
[IMS Open Corpus Workbench (CWB)](http://cwb.sourceforge.net/).
Main purpose of the module is to extract concordance lines, calculate
collocates, and run queries with several anchor points.

If you want to extract the results of anchored queries with more than
two anchor points, the module requires CWB version 3.4.16 or newer.


## Installation ##
You can install this module with pip from PyPI:

	pip3 install cwb-ccc

You can also clone the repository from
[github](https://github.com/ausgerechnet/cwb-ccc) and use `setup.py`:

    python3 setup.py install

You can also just install all requirements specified in `setup.py` and
make sure the `ccc` subfolder can be found by Python by including it
in your `PYTHONPATH`.


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
specify via the `meta_s` parameter, e.g. "text_id").

You can use the `cqp_bin` to point the engine to a specific version of
`cqp` (this is also helpful if `cqp` is not in your `PATH`).

By default, the `cache_path` points to "/tmp/ccc-cache". Make sure
that "/tmp/" exists and the appropriate rights are granted. Otherwise,
change the parameter when envoking the engine (or set it to `None`).

### Concordancing ###

You can use the `Concordance` class from `ccc.concordances` for
concordancing. The concordancer has to be initialized with the engine
and accepts valid CQP queries:
	
```python
from ccc.concordances import Concordance
# initialize the concordancer with the engine
concordance = Concordance(engine)
# extract concordance lines
concordance.query('[lemma="Angela"] [lemma="Merkel"]')
```

The result will be a dictionary with the _cpos_ of the match as keys
and the entries one concordance line each. Each concordance line is
formatted as a `pandas.DataFrame` with the _cpos_ of each token as
index:

| *cpos*    | word    | match | offset |
|-----------|---------|-------|--------|
| 188530363 | ,       | False | -5     |
| 188530364 | dass    | False | -4     |
| 188530365 | die     | False | -3     |
| 188530366 | Tage    | False | -2     |
| 188530367 | von     | False | -1     |
| 188530368 | Angela  | True  | 0      |
| 188530369 | Merkel  | True  | 0      |
| 188530370 | gezählt | False | 1      |
| 188530371 | sind    | False | 2      |
| 188530372 | .       | False | 3      |

The queries _must not_ end on a "within" clause.  If you want to
restrict your concordance lines by a structural attribute, use the
`s_break` parameter (defaults to "text"). The default context window
is 20 tokens to the left and 20 tokens to the right of the query match
and matchend, respectively.

Further parameters for the `Concordance` class are `order` (one of
"random", "first", or "last"), `cut_off` (for the number of
concordance lines to extract), and `p_show` (a `list` of additional
p-attributes besides the primary word layer to show, e.g. "lemma" or
"pos"; these will be added as additional columns).

### Collocation Analyses ###
You can use the `Collocates` class to extract collocates for a given
window size (symmetric windows around the corpus matches):
```python
from ccc.collocates import Collocates
# initialize the collocation calculator with the engine
collocates = Collocates(engine)
# extract collocates
collocates.query('[lemma="Angela"] [lemma="Merkel"]', window=5)
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

By default, the dataframe is sorted by co-occurrence frequency (O11),
and only the first 100 most frequently co-occurring collocates are
retrieved. You can change the `order` and `cut_off` parameters when
envoking the `Collocates` class.

By default, collocates are calculated on the "lemma"-layer (assuming
that this is a valid p-attribute in the corpus) and windows are cut at
the "text" s-attribute. The corresponding parameters are `s_break` and
`p_query`.

By default, the dataframe is annotated with "z_score", "t_score",
"dice", "log_likelihood", and "mutual_information" (parameter `ams`).
For notation and further information regarding association measures,
see
[collocations.de](http://www.collocations.de/AM/index.html). Available
association measures depend on their implementation in the
[association-measures](https://pypi.org/project/association-measures/)
module.

A further parameter of the `Collocates` class is the
`max_window_size`. This is an internal parameter that determines the
result of the initial query via the `CWBEngine`. The result of the
initial query and its co-occurrence dataframe are cached (assuming the
engine was not initialized with `cache_path=None`), which means that
you can extract collocates for windows from 0 to `max_window_size`
quickly after the first run.


### Anchored Queries ###

The `Concordance` class detects anchored queries by default. The following query
```python
concordance.query(
	'@0[lemma="Angela"]? @1[lemma="Merkel"] [word="\\("] @2[lemma="CDU"] [word="\\)"]'
)
```
will thus return `DataFrame`s with an additional column indicating the
anchor positions:

| *cpos*    | word       | match | offset | anchor |
|-----------|------------|-------|--------|--------|
| 298906425 | auch       | False | -5     | None   |
| 298906426 | das        | False | -4     | None   |
| 298906427 | Handy      | False | -3     | None   |
| 298906428 | von        | False | -2     | None   |
| 298906429 | Kanzlerin  | False | -1     | None   |
| 298906430 | Angela     | True  | 0      | 0      |
| 298906431 | Merkel     | True  | 0      | 1      |
| 298906432 | (          | True  | 0      | None   |
| 298906433 | CDU        | True  | 0      | 2      |
| 298906434 | )          | True  | 0      | None   |
| 298906435 | sowie      | False | 1      | None   |
| 298906436 | ihres      | False | 2      | None   |
| 298906437 | Vorgängers | False | 3      | None   |
| 298906438 | Gerhard    | False | 4      | None   |
| 298906439 | Schröder   | False | 5      | None   |


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
process argument queries with the `argmin_query` method from
`ccc.argmin`:

```python
import json
from ccc.argmin import argmin_query
# read the query file
query_path = "tests/gold/query-example.json"
with open(query_path, "rt") as f:
	query = json.loads(f.read())
# query the corpus
result = argmin_query(
	engine,
	query=query['query'],
	anchors=query['anchors'],
	regions=query['regions']
)
```
Further parameters for `argmin_query` are `s_break`, `context`,
`p_show`, and `match_strategy` (one of "longest" or "standard", see
documentation of CQP).

The result is a `dict` with the following keys:

- "nr_matches": the number of query matches in the corpus.
- "matches": a list of concordance lines. Each concordance line
  contains 
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
[cwb-python](https://pypi.org/project/cwb-python/), special thanks to
Yannick Versley and Jorg Asmussen for the implementation. Thanks to
Markus Opolka for the implementation of
[association-measures](https://pypi.org/project/association-measures/)
and for forcing me to write tests.

This work was supported by the
[https://www.fau.eu/research/collaborative-research/emerging-fields-initiative/](Emerging Fields Initiative (EFI)) of Friedrich-Alexander-Universität
Erlangen-Nürnberg. project title 
[https://www.linguistik.phil.fau.de/projects/efe/](Exploring the 'Fukushima Effect').

Further development of the package has been funded by the Deutsche
Forschungsgemeinschaft (DFG) within the project "Reconstructing
Arguments from Noisy Text", grant number 377333057, as part of the
Priority Program [http://www.spp-ratio.de/home/](Robust Argumentation Machines) (SPP-1999).
