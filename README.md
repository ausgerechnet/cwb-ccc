# Collocation and Concordance Computation #

## Introduction ##
This module is a wrapper around the [IMS Open Corpus Workbench
(CWB)](http://cwb.sourceforge.net/).  Main purpose of the module is to
run queries, extract concordance lines, and calculate collocates.

* [Introduction](#introduction)
	* [Prerequisites](#prerequisites)
	* [Installation](#installation)
	* [Defining your corpus](#corpus-setup)
* [Usage](#usage)
	* [Queries and Dumps](#queries-and-dumps)
	* [Extracting concordance lines](#concordancing)
	* [Dealing with anchored queries](#anchored-queries)
	* [Calculating collocates](#collocation-analyses)
	* [Extracting keywords](#keyword-analyses)
* [Acknowledgements](#acknowledgements)


### Prerequisites ###
The module needs a working installation of the CWB and operates on
CWB-indexed corpora.

If you want to run queries with more than two anchor points, the
module requires CWB version 3.4.16 or later.

The module requires the
[association-measures](https://github.com/fau-klue/pandas-association-measures)
module in version 0.1.4, which currently can only be installed
directly from github.

### Installation ###
You can install this module with pip from PyPI:

	pip3 install cwb-ccc

You can also clone the repository from
[github](https://github.com/ausgerechnet/cwb-ccc), `cd` in the
respective folder, and use `setup.py`:

	python3 setup.py install

### Corpus Setup
All methods rely on the `Corpus` class, which establishes the
connection to your CWB-indexed corpus:

```python
from ccc import Corpus
corpus = Corpus(
	corpus_name="EXAMPLE_CORPUS",
	registry_path='/usr/local/share/cwb/registry/'
)
print(corpus)
```

This will raise a `KeyError` if the named corpus is not in the
specified registry.

If you are using macros and wordlists, you have to store them in a
separate folder (with subfolders `wordlists` and `macros`).  Make sure
you specify this folder via `lib_path` when initializing the
corpus.

You can use the `cqp_bin` to point the module to a specific version of
`cqp` (this is also helpful if `cqp` is not in your `PATH`).

By default, the `data_path` points to "/tmp/ccc-data". Make sure
that "/tmp/" exists and appropriate rights are granted. Otherwise,
change the parameter when initializing the corpus.

## Usage ##

### Queries and Dumps
Before you can display anything, you have to run a query with the
`corpus.query()` method, which accepts valid CQP queries such as
```python
query = '[lemma="Angela"]? [lemma="Merkel"] [word="\("] [lemma="CDU"] [word="\)"]'
dump = corpus.query(
	cqp_query=query
)
print(dump)
```
The result is a `Dump` object. Its core is a pandas DataFrame
multi-indexed by CQP's "match" and "matchend" (similar to a
CQP dump). All entries of the DataFrame, including the index, are
integers representing corpus positions:

```
print(dump.df)
```

You can provide one or more parameters to define the context around
the matches: a parameter `context` specifying the context window
(defaults to 20) and an s-attribute defining the context
(`context_break`). You can specify asymmetric windows via
`context_left` and `context_right`.
```python
dump = corpus.query(
	cqp_query=query,
	context=20,
	context_break='s'
)
```
In this case, the `dump.df` will contain two further columns,
specifying the context: "context" and "contextend".

Note that queries _may_ end on a "within" clause, which will limit the
matches to regions defined by this structural attribute. If you
provide a `context_break` parameter, the query will be automatically
confined by this s-attribute.

You can set CQP's matching strategy ("standard", "longest",
"shortest") via the `match_strategy` parameter.
	
By default, the result is cached: the query parameters will be used to
create an identifier. The resulting `Dump` object contains the
appropriate identifier as attribute `name_cache`. The resulting
subcorpus will be saved to disk by CQP, and the extended dump
containing the context put into a cache. This way, the result can be
accessed directly by later queries with the same parameters on the
same (sub)corpus, without the need for CQP to run again.  You can
disable caching by providing a `name` other than "mnemosyne".

Now you are set up to analyze your query result. Let's start with the
frequency breakdown:
```
print(dump.breakdown())
```
| *word*                 | freq |
|------------------------|------|
| Angela Merkel ( CDU )  | 2253 |
| Merkel ( CDU )         | 29   |
| Angela Merkels ( CDU ) | 2    |


### Concordancing ###

You can directly access concordance lines via the `concordance` method
of the dump. This method returns a dataframe with information about
the query matches in context:

```
lines = dump.concordance()
print(lines)
```
| *match* | *matchend* | context | contextend | raw                                               |
|---------|------------|---------|------------|---------------------------------------------------|
| 676     | 680        | 656     | 700        | {'cpos': [656, 657, 658, 659, 660, 661, 662, 6... |
| 1190    | 1194       | 1170    | 1214       | {'cpos': [1170, 1171, 1172, 1173, 1174, 1175, ... |
| 543640  | 543644     | 543620  | 543664     | {'cpos': [543620, 543621, 543622, 543623, 5436... |
| ...     | ...        | ...     | ...        | ...                                               |

Column `raw` contains a dictionary with the following keys:
- "match" (int)
- "cpos" (list)
- "offset" (list)
- "word" (list)
- "anchors" (dict) 

You can create your own formatting from this, or use the `form`
parameter to define how your lines should be formatted ("raw",
"simple", "kwic", "dataframes" or "extended"). If `form="dataframes"`
or `form="extended"`, the dataframe contains a column `df` with each
concordance line being formatted as a `DataFrame` with the _cpos_ of
each token as index:

```
lines = dump.concordance(form="dataframes")
print(lines['df'].iloc[0])
```

| *cpos* | offset | word                | match | matchend | context | contextend |
|--------|--------|---------------------|-------|----------|---------|------------|
| 48344  | -5     | Eine                | False | False    | True    | False      |
| 48345  | -4     | entsprechende       | False | False    | False   | False      |
| 48346  | -3     | Steuererleichterung | False | False    | False   | False      |
| 48347  | -2     | hat                 | False | False    | False   | False      |
| 48348  | -1     | Kanzlerin           | False | False    | False   | False      |
| 48349  | 0      | Angela              | True  | False    | False   | False      |
| 48350  | 0      | Merkel              | False | False    | False   | False      |
| 48351  | 0      | (                   | False | False    | False   | False      |
| 48352  | 0      | CDU                 | False | False    | False   | False      |
| 48353  | 0      | )                   | False | True     | False   | False      |
| 48354  | 1      | bisher              | False | False    | False   | False      |
| 48355  | 2      | ausgeschlossen      | False | False    | False   | False      |
| 48356  | 3      | .                   | False | False    | False   | True       |


Attribute selection is controlled via the `p_show` and `s_show`
parameters (lists of p-attributes and s-attributes, respectively):
```
lines = dump.concordance(
	form="dataframes",
	p_show=['word', 'lemma'],
	s_show=['text_id']
)
print(lines)
```
| *match* | *matchend* | context | contextend | df  | text_id |
|---------|------------|---------|------------|-----|---------|
| 676     | 680        | 656     | 700        | ... | A113224 |
| 1190    | 1194       | 1170    | 1214       | ... | A124124 |
| 543640  | 543644     | 543620  | 543664     | ... | A423523 |
| ...     | ...        | ...     | ...        | ... | ...     |

```
print(lines['df'].iloc[0])
```
| *cpos* | offset | word                | lemma               | match | matchend | context | contextend |
|--------|--------|---------------------|---------------------|-------|----------|---------|------------|
| 48344  | -5     | Eine                | eine                | False | False    | True    | False      |
| 48345  | -4     | entsprechende       | entsprechende       | False | False    | False   | False      |
| 48346  | -3     | Steuererleichterung | Steuererleichterung | False | False    | False   | False      |
| 48347  | -2     | hat                 | haben               | False | False    | False   | False      |
| 48348  | -1     | Kanzlerin           | Kanzlerin           | False | False    | False   | False      |
| 48349  | 0      | Angela              | Angela              | True  | False    | False   | False      |
| 48350  | 0      | Merkel              | Merkel              | False | False    | False   | False      |
| 48351  | 0      | (                   | (                   | False | False    | False   | False      |
| 48352  | 0      | CDU                 | CDU                 | False | False    | False   | False      |
| 48353  | 0      | )                   | )                   | False | True     | False   | False      |
| 48354  | 1      | bisher              | bisher              | False | False    | False   | False      |
| 48355  | 2      | ausgeschlossen      | ausschließen        | False | False    | False   | False      |
| 48356  | 3      | .                   | .                   | False | False    | False   | True       |


You can decide which and how many concordance lines you want to
retrieve by means of the parameters `order` ("first", "last", or
"random") and `cut_off`. You can also provide a list of `matches` to
get only specific concordance lines.


### Anchored Queries ###

The concordancer detects anchored queries automatically. The following
query

```python
dump = corpus.query(
	'@0[lemma="Angela"]? @1[lemma="Merkel"] [word="\("] @2[lemma="CDU"] [word="\)"]',
)
dump.concordance(form='dataframes')
```

thus returns `DataFrame`s with additional columns for each anchor point.

| *cpos* | offset | word                | match | matchend | context | contextend | 0     | 1     | 2     |
|--------|--------|---------------------|-------|----------|---------|------------|-------|-------|-------|
| 48344  | -5     | Eine                | False | False    | True    | False      | False | False | False |
| 48345  | -4     | entsprechende       | False | False    | False   | False      | False | False | False |
| 48346  | -3     | Steuererleichterung | False | False    | False   | False      | False | False | False |
| 48347  | -2     | hat                 | False | False    | False   | False      | False | False | False |
| 48348  | -1     | Kanzlerin           | False | False    | False   | False      | False | False | False |
| 48349  | 0      | Angela              | True  | False    | False   | False      | True  | False | False |
| 48350  | 0      | Merkel              | False | False    | False   | False      | False | True  | False |
| 48351  | 0      | (                   | False | False    | False   | False      | False | False | False |
| 48352  | 0      | CDU                 | False | False    | False   | False      | False | False | True  |
| 48353  | 0      | )                   | False | True     | False   | False      | False | False | False |
| 48354  | 1      | bisher              | False | False    | False   | False      | False | False | False |
| 48355  | 2      | ausgeschlossen      | False | False    | False   | False      | False | False | False |
| 48356  | 3      | .                   | False | False    | False   | True       | False | False | False |


### Collocation Analyses ###
After executing a query, you can use the `dump.collocates()` method to
extract collocates for a given window size (symmetric windows around
the corpus matches). The result will be a `DataFrame` with lexical
items as index and frequency signatures and association measures as
columns.

```python
dump = corpus.query(
    '[lemma="Angela"] [lemma="Merkel"]',
	context=10, context_break='s'
)
collocates = dump.collocates()
print(collocates)
```

| *item*          | O11  | O12   | O21      | O22       | E11         | E12          | E21          | E22          | log_likelihood | ... |
|-----------------|------|-------|----------|-----------|-------------|--------------|--------------|--------------|----------------|-----|
| die             | 1799 | 21033 | 25123530 | 275771340 | 1906.373430 | 20925.626570 | 2.512342e+07 | 2.757714e+08 | -2.459194      | ... |
| Bundeskanzlerin | 1491 | 21341 | 7325     | 300887545 | 0.668910    | 22831.331090 | 8.815331e+03 | 3.008861e+08 | 1822.211827    | ... |
| .               | 1123 | 21709 | 13676688 | 287218182 | 1037.797972 | 21794.202028 | 1.367677e+07 | 2.872181e+08 | 2.644804       | ... |
| ,               | 814  | 22018 | 17561245 | 283333625 | 1332.513602 | 21499.486398 | 1.756073e+07 | 2.833341e+08 | -14.204447     | ... |
| Kanzlerin       | 648  | 22184 | 16974    | 300877896 | 1.337062    | 22830.662938 | 1.762066e+04 | 3.008772e+08 | 559.245198     | ... |


By default, collocates are calculated on the "lemma"-layer, assuming
that this is a valid p-attribute in the corpus. The corresponding
parameter is `p_query` (which will fall back to "word" if the
specified attribute is not annotated in the corpus).

For improved performance, all hapax legomena in the context are
dropped after calculating the context size. You can change this
behaviour via the `min_freq` parameter.

By default, the dataframe is annotated with "z_score", "t_score",
"dice", "log_likelihood", and "mutual_information" (parameter `ams`).
For notation and further information regarding association measures,
see
[collocations.de](http://www.collocations.de/AM/index.html). Available
association measures depend on their implementation in the
[association-measures](https://pypi.org/project/association-measures/)
module.

The dataframe is sorted by co-occurrence frequency (column "f"), and
only the first 100 most frequently co-occurring collocates are
retrieved. You can change this behaviour via the `order` and `cut_off`
parameters.

### Keyword Analyses

For keyword analyses, you will have to define a subcorpus. The natural
way of doing so is by selecting text identifiers via spreadsheets or
relational databases. If you have collected an appropriate set of
identifiers, you can use `corpus.dump_from_s_att()` method:

```python
dump = corpus.subcorpus_from_s_att('text_id', ids)
keywords = dump.keywords()
```

Just as with collocates, the result is a `DataFrame` with lexical
items (`p_query` layer) as index and frequency signatures and
association measures as columns.

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
