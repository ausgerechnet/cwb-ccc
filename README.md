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

### Installation ###
You can install this module with pip from PyPI:

	pip3 install cwb-ccc

You can also clone the source from
[github](https://github.com/ausgerechnet/cwb-ccc), `cd` in the
respective folder, and use `setup.py`:

	python3 setup.py install

### Corpus Setup
All methods rely on the `Corpus` class, which establishes the
connection to your CWB-indexed corpus:

```python
from ccc import Corpus
corpus = Corpus(
  corpus_name="GERMAPARL1386",
  registry_path='/usr/local/share/cwb/registry/'
)
```

This will raise a `KeyError` if the named corpus is not in the
specified registry.

If you are using macros and wordlists, you have to store them in a
separate folder (with subfolders "wordlists/" and "macros/").  Make
sure you specify this folder via `lib_path` when initializing the
corpus.

You can use the `cqp_bin` to point the module to a specific version of
`cqp` (this is also helpful if `cqp` is not in your `PATH`).

By default, the `data_path` points to "/tmp/ccc-data/". Make sure that
"/tmp/" exists and appropriate rights are granted. Otherwise, change
the parameter when initializing the corpus.

## Usage ##

### Queries and Dumps
The normal starting point for analyzing a corpus is to run a query
with the `corpus.query()` method, which accepts valid CQP queries such
as

```python
query = r'"\[" ([pos="NE"] "/"?)+ "\]"'
dump = corpus.query(cqp_query=query)
```

The result is a `Dump` object. Its core is a pandas DataFrame
(`dump.df`) multi-indexed by CQP's "match" and "matchend" (similar to
a CQP dump). All entries of the DataFrame, including the index, are
integers representing corpus positions.

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

We are set up to analyze your query result. Let's start with the
frequency breakdown:

```
print(dump.breakdown())
```

| *word*        | freq |
|---------------|------|
| [ SPD ]       | 18   |
| [ CDU / CSU ] | 13   |
| [ PDS ]       | 6    |


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
| 8213    | 8217       | 8193    | 8237       | {'cpos': [8193, 8194, 8195, 8196, 8197, 8198, ... |
| 15999   | 16001      | 15979   | 16021      | {'cpos': [15979, 15980, 15981, 15982, 15983, 1... |
| 25471   | 25473      | 25451   | 25493      | {'cpos': [25451, 25452, 25453, 25454, 25455, 2... |
| ...     | ...        | ...     | ...        | ...                                               |

Column `raw` contains a dictionary with the following keys:
- "match" (int): the cpos of the match
- "cpos" (list): the cpos of all tokens in the concordance line
- "offset" (list): the offset to match/matchend of all tokens 
- "word" (list): the words of all tokens
- "anchors" (dict): a dictionary of {anchor: cpos} (see
  [below](#anchored-queries))

You can create your own formatting from this, or use the `form`
parameter to define how your lines should be formatted ("raw",
"simple", "kwic", "dataframes" or "extended"). If `form="dataframes"`
or `form="extended"`, the dataframe contains a column `df` with each
concordance line being formatted as a `DataFrame` with the _cpos_ of
each token as index:

```
lines = dump.concordance(form="dataframes")
print(lines['df'].iloc[1])
```

| *cpos* | offset | word    | match | matchend | context | contextend |
|--------|--------|---------|-------|----------|---------|------------|
| 15992  | -7     | (       | False | False    | True    | False      |
| 15993  | -6     | Beifall | False | False    | False   | False      |
| 15994  | -5     | des     | False | False    | False   | False      |
| 15995  | -4     | Abg.    | False | False    | False   | False      |
| 15996  | -3     | Dr.     | False | False    | False   | False      |
| 15997  | -2     | Peter   | False | False    | False   | False      |
| 15998  | -1     | Struck  | False | False    | False   | False      |
| 15999  | 0      | [       | True  | False    | False   | False      |
| 16000  | 0      | SPD     | False | False    | False   | False      |
| 16001  | 0      | ]       | False | True     | False   | False      |
| 16002  | 1      | )       | False | False    | False   | True       |


Attribute selection is controlled via the `p_show` and `s_show`
parameters (lists of p-attributes and s-attributes, respectively):

```
lines = dump.concordance(
  form="dataframes",
  p_show=['word', 'lemma'],
  s_show=['text_id']
)
```

|                   |                       |
|-------------------|-----------------------|
| context\_id       | 905                   |
| context           | 15992                 |
| contextend        | 16002                 |
| df                | lemma offset word ... |
| text\_role\_CWBID | 7                     |
| text\_role        | mp                    |

```
print(lines['df'].iloc[1])
```

| *cpos* | lemma   | offset | word    | match | matchend | context | contextend |
|--------|---------|--------|---------|-------|----------|---------|------------|
| 15992  | (       | -7     | (       | False | False    | True    | False      |
| 15993  | Beifall | -6     | Beifall | False | False    | False   | False      |
| 15994  | die     | -5     | des     | False | False    | False   | False      |
| 15995  | Abg.    | -4     | Abg.    | False | False    | False   | False      |
| 15996  | Dr.     | -3     | Dr.     | False | False    | False   | False      |
| 15997  | Peter   | -2     | Peter   | False | False    | False   | False      |
| 15998  | Struck  | -1     | Struck  | False | False    | False   | False      |
| 15999  | [       | 0      | [       | True  | False    | False   | False      |
| 16000  | SPD     | 0      | SPD     | False | False    | False   | False      |
| 16001  | ]       | 0      | ]       | False | True     | False   | False      |
| 16002  | )       | 1      | )       | False | False    | False   | True       |

You can decide which and how many concordance lines you want to
retrieve by means of the parameters `order` ("first", "last", or
"random") and `cut_off`. You can also provide a list of `matches` to
get only specific concordance lines.


### Anchored Queries ###

The concordancer detects anchored queries automatically. The following
query
```python
dump = corpus.query(
  query = r'@1[pos="NE"]? @2[pos="NE"] "\[" (@3[word="[A-Z]+"]+ "/"?)+ "\]"'
)
lines = dump.concordance(form='dataframes')
print(lines['df'].iloc[1])
```
thus returns `DataFrame`s with additional columns for each anchor point.

| *cpos* | offset | word    | 1     | 2     | 3     | match | matchend | context | contextend |
|--------|--------|---------|-------|-------|-------|-------|----------|---------|------------|
| 15992  | -5     | (       | False | False | False | False | False    | True    | False      |
| 15993  | -4     | Beifall | False | False | False | False | False    | False   | False      |
| 15994  | -3     | des     | False | False | False | False | False    | False   | False      |
| 15995  | -2     | Abg.    | False | False | False | False | False    | False   | False      |
| 15996  | -1     | Dr.     | False | False | False | False | False    | False   | False      |
| 15997  | 0      | Peter   | True  | False | False | True  | False    | False   | False      |
| 15998  | 0      | Struck  | False | True  | False | False | False    | False   | False      |
| 15999  | 0      | [       | False | False | False | False | False    | False   | False      |
| 16000  | 0      | SPD     | False | False | True  | False | False    | False   | False      |
| 16001  | 0      | ]       | False | False | False | False | True     | False   | False      |
| 16002  | 1      | )       | False | False | False | False | False    | False   | True       |


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

| *item* | O11 | O12  | O21   | O22    | E11        | E12         | E21          | E22           | log_likelihood | ... |
|--------|-----|------|-------|--------|------------|-------------|--------------|---------------|----------------|-----|
| die    | 813 | 4373 | 12952 | 131030 | 478.556326 | 4707.443674 | 13286.443674 | 130695.556326 | 226.512603     | ... |
| bei    | 366 | 4820 | 991   | 142991 | 47.177692  | 5138.822308 | 1309.822308  | 142672.177692 | 967.728153     | ... |
| (      | 314 | 4872 | 1444  | 142538 | 61.118926  | 5124.881074 | 1696.881074  | 142285.118926 | 574.853985     | ... |
| [      | 221 | 4965 | 477   | 143505 | 24.266786  | 5161.733214 | 673.733214   | 143308.266786 | 654.834131     | ... |
| )      | 207 | 4979 | 1620  | 142362 | 63.517792  | 5122.482208 | 1763.482208  | 142218.517792 | 218.340710     | ... |
| ...    | ... | ...  | ...   | ...    | ...        | ...         | ...          | ...           | ...            | ... |


By default, collocates are calculated on the "lemma"-layer, assuming
that this is an available p-attribute in the corpus. The corresponding
parameter is `p_query` (which will fall back to "word" if the
specified attribute is not annotated in the corpus).

For improved performance, all hapax legomena in the context are
dropped after calculating the context size. You can change this
behaviour via the `min_freq` parameter.

By default, the dataframe is annotated with "z\_score", "t\_score",
"dice", "log\_likelihood", and "mutual\_information" (parameter
`ams`).  For notation and further information regarding association
measures, see
[collocations.de](http://www.collocations.de/AM/index.html). Availability
of association measures depends on their implementation in the
[pandas-association-measures](https://pypi.org/project/association-measures/)
package.

The dataframe is sorted by co-occurrence frequency (column "O11"), and
only the first 100 most frequently co-occurring collocates are
retrieved. You can (and should) change this behaviour via the `order`
and `cut_off` parameters.

### Keyword Analyses

For keyword analyses, you have to define a subcorpus. The natural way
of doing so is by selecting text identifiers via spreadsheets or
relational databases, or by directly using the annotated
s-attributes. If you have collected an appropriate set of attribute
values, you can use the `corpus.dump_from_s_att()` method:

```python
party = {"CDU", "CSU"}
dump = corpus.dump_from_s_att('text_party', party)
keywords = dump.keywords()
```

Just as with collocates, the result is a `DataFrame` with lexical
items (`p_query` layer) as index and frequency signatures and
association measures as columns.

You can of course also define a subcorpus via a corpus query,
e.g.
```python
dump = corpus.query('"SPD" expand to s')
keywords = dump.keywords()
```

## Testing ##
The module is shipped with a small test corpus ("GERMAPARL8613"),
which contains all speeches of the 86th session of the 13th German
Bundestag on Feburary 8, 1996. The corpus consists of 149,800 tokens
in 7332 paragraphs (s-attribute `p` with annotation _type_ ("regular"
or "interjection")) split into 11,364 sentences (s-attribute `s`).
The p-attributes are `pos` and `lemma`. The s-attributes are 1
`sitzung` (with annotations _date_, _period_, _session_), 10 `div`s
corresponding to different agenda items (annotations _desc_, _n_,
_type_, _what_), and 346 `text`s corresponding to all speeches
(annotations _name_, _parliamentary\_group_, _party_, _position_,
_role_, _who_).

The module is tested using pytest. Make sure you install all
development dependencies:
	
	pip install --dev

You can then

	make test
	
and

	make coverage

## Acknowledgements ##
The module relies on
[cwb-python](https://pypi.org/project/cwb-python/), thanks to **Yannick
Versley** and **Jorg Asmussen** for the implementation. Special thanks to
**Markus Opolka** for the implementation of
[association-measures](https://pypi.org/project/association-measures/)
and for forcing me to write tests.

The test corpus was extracted from the
[GermaParl](https://github.com/PolMine/GermaParlTEI) corpus (see the
[PolMine Project](https://polmine.github.io/)); many thanks to **Andreas
Blätte**.

This work was supported by the [Emerging Fields Initiative
(EFI)](https://www.fau.eu/research/collaborative-research/emerging-fields-initiative/)
of Friedrich-Alexander-Universität Erlangen-Nürnberg, project title
[Exploring the *Fukushima
Effect*](https://www.linguistik.phil.fau.de/projects/efe/)
(2017-2020).

Further development of the package has been funded by the Deutsche
Forschungsgemeinschaft (DFG) within the project [Reconstructing
Arguments from Noisy
Text](https://www.linguistik.phil.fau.de/projects/rant/), grant number
377333057, as part of the Priority Program [Robust Argumentation
Machines](http://www.spp-ratio.de/home/) (SPP-1999).
