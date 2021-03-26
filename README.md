# Collocation and Concordance Computation #

## Introduction ##
This module is a wrapper around the [IMS Open Corpus Workbench (CWB)](http://cwb.sourceforge.net/).  Main purpose of the module is to run queries, extract concordance lines, and calculate collocates.

* [Introduction](#introduction)
	* [Prerequisites](#prerequisites)
	* [Installation](#installation)
	* [Accessing Corpora](#accessing-corpora)
* [Usage](#usage)
	* [Queries and Dumps](#queries-and-dumps)
	* [Extracting Concordance Lines](#concordancing)
	* [Dealing with Anchored Queries](#anchored-queries)
	* [Calculating Collocates](#collocation-analyses)
	* [Defining Subcorpora](#subcorpora)
	* [Extracting Keywords](#keyword-analyses)
* [Testing](#testing)
* [Acknowledgements](#acknowledgements)


### Prerequisites ###
The module needs a working installation of the [CWB](http://cwb.sourceforge.net/) and operates on CWB-indexed corpora.

If you want to run queries with more than two anchor points, the module requires CWB version 3.4.16 or later.

### Installation ###
You can install this module with pip from PyPI:

	pip3 install cwb-ccc

You can also clone the source from [github](https://github.com/ausgerechnet/cwb-ccc), `cd` in the respective folder, and use `setup.py`:

	python3 setup.py install

### Accessing Corpora ###

To list all available corpora, you can use
```python
from ccc import Corpora
corpora = Corpora(registry_path="/usr/local/share/cwb/registry/")
print(corpora)
corpora.show()  # returns a DataFrame
```

All further methods rely on the `Corpus` class, which establishes the connection to your CWB-indexed corpus. You can activate a corpus with

```python
corpus = corpora.activate(corpus_name="GERMAPARL1386")
```

or directly use the respective class:

```python
from ccc import Corpus
corpus = Corpus(
  corpus_name="GERMAPARL1386",
  registry_path="/usr/local/share/cwb/registry/"
)
```

This will raise a `KeyError` if the named corpus is not in the specified registry.

If you are using macros and wordlists, you have to store them in a separate folder (with subfolders "wordlists/" and "macros/").  Specify this folder via `lib_path` when initializing the corpus.

You can use the `cqp_bin` to point the module to a specific version of `cqp` (this is also helpful if `cqp` is not in your `PATH`).

By default, the `data_path` points to "/tmp/ccc-data/". Make sure that "/tmp/" exists and appropriate rights are granted. Otherwise, change the parameter when initializing the corpus.

If everything is set up correctly, you can list all available attributes of the activated corpus:

<details>
<summary><code>corpus.attributes_available</code></summary>
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


## Usage ##

### Queries and Dumps ###
The usual starting point for using this module is to run a query with the `corpus.query()` method, which accepts valid CQP queries such as

```python
query = r'"\[" ([word="[A-Z0-9]+.?"%d]+ "/"?)+ "\]"'
dump = corpus.query(query)
```

The result is a `Dump` object. Its core is a pandas DataFrame (`dump.df`) similar to a CQP dump and multi-indexed by "match" and "matchend" of the query.  All entries of the DataFrame, including the index, are integers representing corpus positions:

<details>
<summary><code>dump.df</code></summary>
<p>

| *match* | *matchend* | context | contextend |
|--------:|-----------:|--------:|-----------:|
|    2313 |       2319 |    2293 |       2339 |
|    8213 |       8217 |    8193 |       8237 |
|    8438 |       8444 |    8418 |       8464 |
|   15999 |      16001 |   15979 |      16021 |
|   24282 |      24288 |   24262 |      24308 |
|     ... |        ... |     ... |        ... |

</p>
</details>
<br/>

You can provide one or more parameters to define the context around the matches: a parameter `context` specifying the context window (defaults to 20) and a parameter `context_break` naming an s-attribute to limit the context .  You can specify asymmetric windows via `context_left` and `context_right`.

When providing an s-attribute limiting the context, the module additionally retrieves the CWB-id of this attribute, the corpus positions of the respective span start and end, as well as the actual context spans:

```python
dump = corpus.query(
  cqp_query=query,
  context=20,
  context_break='s'
)
```

<details>
<summary><code>dump.df</code></summary>
<p>

| *match* | *matchend* | s_cwbid | s_span | s_spanend | contextid | context | contextend |
|--------:|-----------:|--------:|-------:|----------:|----------:|--------:|-----------:|
|    2313 |       2319 |     161 |   2304 |      2320 |       161 |    2308 |       2320 |
|    8213 |       8217 |     489 |   8187 |      8218 |       489 |    8208 |       8218 |
|    8438 |       8444 |     500 |   8425 |      8445 |       500 |    8433 |       8445 |
|   15999 |      16001 |     905 |  15992 |     16002 |       905 |   15994 |      16002 |
|   24282 |      24288 |    1407 |  24273 |     24289 |      1407 |   24277 |      24289 |
|     ... |        ... |     ... |    ... |       ... |       ... |     ... |        ... |

</p>
</details>
<br/>

There are two reasons for defining the context when running the queries:

1. If you provide a `context_break` parameter, the query will be automatically confined to spans delimited by this s-attribute; this is equivalent to formulating a query that ends on a respective "within" clause.
2. Subsequent analyses (concordancing, collocation) will all work on the same context.

Notwithstanding (1), the context can also be set after having run the query:

```python
dump.set_context(context_left=5, context_right=10, context_break='s')
```

Note that this works "inplace".

You can set CQP's matching strategy ("standard", "longest", "shortest", "traditional") via the `match_strategy` parameter.
	
By default, the result is cached: the query parameters are used to create an appropriate identifier.  This way, the result can be accessed directly by later queries with the same parameters on the same (sub)corpus, without the need for CQP to run again.

We are set up to analyze the query result. Here's the frequency breakdown:

<details>
<summary><code>dump.breakdown()</code></summary>
<p>

| *word*                      |   freq |
|:----------------------------|-------:|
| [ SPD ]                     |     18 |
| [ F. D. P. ]                |     14 |
| [ CDU / CSU ]               |     13 |
| [ BÜNDNIS 90 / DIE GRÜNEN ] |     12 |
| [ PDS ]                     |      6 |

</p>
</details>
<br/>


### Concordancing ###

You can access concordance lines via the `concordance` method of the dump.  This method returns a DataFrame with information about the query matches in context:

<details>
<summary><code>dump.concordance()</code></summary>
<p>

| *match* | *matchend* | word                                                       |
|--------:|-----------:|:-----------------------------------------------------------|
|    2313 |       2319 | Joseph Fischer [ Frankfurt ] [ BÜNDNIS 90 / DIE GRÜNEN ] ) |
|    8213 |       8217 | Widerspruch des Abg. Wolfgang Zöller [ CDU / CSU ] )       |
|    8438 |       8444 | Joseph Fischer [ Frankfurt ] [ BÜNDNIS 90 / DIE GRÜNEN ] ) |
|   15999 |      16001 | des Abg. Dr. Peter Struck [ SPD ] )                        |
|   24282 |      24288 | Joseph Fischer [ Frankfurt ] [ BÜNDNIS 90 / DIE GRÜNEN ] ) |
|     ... |        ... | ...                                                        |

</p>
</details>
<br/>

By default, the output is a "simple" format, i.e. a DataFrame indexed by "match" and "matchend" with a column "word" showing the matches in context.  You can choose which p-attributes to retrieve via the `p_show` parameter.  Similarly, you can retrieve s-attributes (at match-position):

<details>
<summary><code>dump.concordance(p_show=["word", "lemma"], s_show=["text_id"])</code></summary>
<p>

| *match* | *matchend* | word                                                       | lemma                                                      | text\_id        |
|--------:|-----------:|:-----------------------------------------------------------|:-----------------------------------------------------------|:---------------|
|    2313 |       2319 | Joseph Fischer [ Frankfurt ] [ BÜNDNIS 90 / DIE GRÜNEN ] ) | Joseph Fischer [ Frankfurt ] [ Bündnis 90 / die Grünen ] ) | i13\_86\_1\_2  |
|    8213 |       8217 | Widerspruch des Abg. Wolfgang Zöller [ CDU / CSU ] )       | Widerspruch die Abg. Wolfgang Zöller [ CDU / CSU ] )       | i13\_86\_1\_4  |
|    8438 |       8444 | Joseph Fischer [ Frankfurt ] [ BÜNDNIS 90 / DIE GRÜNEN ] ) | Joseph Fischer [ Frankfurt ] [ Bündnis 90 / die Grünen ] ) | i13\_86\_1\_4  |
|   15999 |      16001 | des Abg. Dr. Peter Struck [ SPD ] )                        | die Abg. Dr. Peter Struck [ SPD ] )                        | i13\_86\_1\_8  |
|   24282 |      24288 | Joseph Fischer [ Frankfurt ] [ BÜNDNIS 90 / DIE GRÜNEN ] ) | Joseph Fischer [ Frankfurt ] [ Bündnis 90 / die Grünen ] ) | i13\_86\_1\_24 |
|     ... |        ... | ...                                                        | ...                                                        | ...            |

</p>
</details>
<br/>

The format can be changed using the `form` parameter.  The "kwic" format e.g. returns three columns for each requested p-attribute:

<details>
<summary><code>dump.concordance(form="kwic")</code></summary>
<p>

| *match* | *matchend* | left_word                            | node_word                   | right_word |
|--------:|-----------:|:-------------------------------------|:----------------------------|:-----------|
|    2313 |       2319 | Joseph Fischer [ Frankfurt ]         | [ BÜNDNIS 90 / DIE GRÜNEN ] | )          |
|    8213 |       8217 | Widerspruch des Abg. Wolfgang Zöller | [ CDU / CSU ]               | )          |
|    8438 |       8444 | Joseph Fischer [ Frankfurt ]         | [ BÜNDNIS 90 / DIE GRÜNEN ] | )          |
|   15999 |      16001 | des Abg. Dr. Peter Struck            | [ SPD ]                     | )          |
|   24282 |      24288 | Joseph Fischer [ Frankfurt ]         | [ BÜNDNIS 90 / DIE GRÜNEN ] | )          |

</p>
</details>
<br/>

If you want to inspect each query result in detail, use `form`="dataframe"; here, every concordance line is verticalized text formated as DataFrame with the _cpos_ of each token as index:

```python
lines = dump.concordance(p_show=['word', 'pos', 'lemma'], form='dataframe')
```

<details>
<summary><code>lines.iloc[0]['dataframe']</code></summary>
<p>

|   *cpos* |   offset | word      | pos     | lemma     |
|---------:|---------:|:----------|:--------|:----------|
|     2308 |       -5 | Joseph    | NE      | Joseph    |
|     2309 |       -4 | Fischer   | NE      | Fischer   |
|     2310 |       -3 | [         | XY      | [         |
|     2311 |       -2 | Frankfurt | NE      | Frankfurt |
|     2312 |       -1 | ]         | APPRART | ]         |
|     2313 |        0 | [         | ADJA    | [         |
|     2314 |        0 | BÜNDNIS   | NN      | Bündnis   |
|     2315 |        0 | 90        | CARD    | 90        |
|     2316 |        0 | /         | $(      | /         |
|     2317 |        0 | DIE       | ART     | die       |
|     2318 |        0 | GRÜNEN    | NN      | Grünen    |
|     2319 |        0 | ]         | $.      | ]         |
|     2320 |        1 | )         | $(      | )         |

</p>
</details>
<br/>

Further `form`s are "slots" (see [below](#anchored-queries)) and "dict": In the latter case, every entry in the "dict" column is a dictionary with the following keys:
- "match" (int): the cpos of the match (serves as an identifier)
- "cpos" (list): the cpos of all tokens in the concordance line
- "offset" (list): the offset to match/matchend of all tokens 
- "word" (list): the words of all tokens
- "anchors" (dict): a dictionary of {anchor: cpos} (see [below](#anchored-queries))
  
This format is especially suitable for serialization purposes.

You can decide which and how many concordance lines you want to retrieve by means of the parameters `order` ("first", "last", or "random") and `cut_off`. You can also provide a list of `matches` to get only specific concordance lines.

### Anchored Queries ###

The concordancer detects anchored queries automatically. The following query

```python
dump = corpus.query(
  cqp_query=r'@1[pos="NE"]? @2[pos="NE"] @3"\[" ([word="[A-Z0-9]+.?"%d]+ "/"?)+ @4"\]"',
  context=None, context_break='s', match_strategy='longest'
)
lines = dump.concordance(form='dataframe')
```

thus returns DataFrames with additional columns for each anchor point:

<details>
<summary><code>lines.iloc[0]['dataframe']</code></summary>
<p>

|   *cpos* |   offset | word         | 1     | 2     | 3     | 4     |
|---------:|---------:|:-------------|:------|:------|:------|:------|
|     8187 |      -24 | (            | False | False | False | False |
|     8188 |      -23 | Anhaltender  | False | False | False | False |
|     8189 |      -22 | lebhafter    | False | False | False | False |
|     8190 |      -21 | Beifall      | False | False | False | False |
|     8191 |      -20 | bei          | False | False | False | False |
|     8192 |      -19 | der          | False | False | False | False |
|     8193 |      -18 | SPD          | False | False | False | False |
|     8194 |      -17 | --           | False | False | False | False |
|     8195 |      -16 | Beifall      | False | False | False | False |
|     8196 |      -15 | bei          | False | False | False | False |
|     8197 |      -14 | Abgeordneten | False | False | False | False |
|     8198 |      -13 | des          | False | False | False | False |
|     8199 |      -12 | BÜNDNISSES   | False | False | False | False |
|     8200 |      -11 | 90           | False | False | False | False |
|     8201 |      -10 | /            | False | False | False | False |
|     8202 |       -9 | DIE          | False | False | False | False |
|     8203 |       -8 | GRÜNEN       | False | False | False | False |
|     8204 |       -7 | und          | False | False | False | False |
|     8205 |       -6 | der          | False | False | False | False |
|     8206 |       -5 | PDS          | False | False | False | False |
|     8207 |       -4 | --           | False | False | False | False |
|     8208 |       -3 | Widerspruch  | False | False | False | False |
|     8209 |       -2 | des          | False | False | False | False |
|     8210 |       -1 | Abg.         | False | False | False | False |
|     8211 |        0 | Wolfgang     | True  | False | False | False |
|     8212 |        0 | Zöller       | False | True  | False | False |
|     8213 |        0 | [            | False | False | True  | False |
|     8214 |        0 | CDU          | False | False | False | False |
|     8215 |        0 | /            | False | False | False | False |
|     8216 |        0 | CSU          | False | False | False | False |
|     8217 |        0 | ]            | False | False | False | True  |
|     8218 |        1 | )            | False | False | False | False |

</p>
</details>
<br/>

For an analysis of certain spans of your query matches, you can use anchor points to define "slots", i.e. single anchors or spans between anchors that define sub-parts of your matches.  Use the "slots" format to extract these parts from each match:
   
```python
dump = corpus.query(
    r'@1[pos="NE"]? @2[pos="NE"] @3"\[" ([word="[A-Z0-9]+.?"%d]+ "/"?)+ @4"\]"',
    context=0, context_break='s', match_strategy='longest',
)
lines = dump.concordance(
  form='slots', p_show=['word', 'lemma'], 
  slots={"name": [1, 2], "party": [3, 4]}
)
```
<details>
<summary><code>lines</code></summary>
<p>

| *match* | *matchend* | word                          | name\_word      | party\_word   |
|--------:|-----------:|:------------------------------|:----------------|:--------------|
|    8211 |       8217 | Wolfgang Zöller [ CDU / CSU ] | Wolfgang Zöller | [ CDU / CSU ] |
|   15997 |      16001 | Peter Struck [ SPD ]          | Peter Struck    | [ SPD ]       |
|   25512 |      25516 | Jörg Tauss [ SPD ]            | Jörg Tauss      | [ SPD ]       |
|   32808 |      32814 | Ina Albowitz [ F. D. P. ]     | Ina Albowitz    | [ F. D. P. ]  |
|   36980 |      36984 | Christa Luft [ PDS ]          | Christa Luft    | [ PDS ]       |
|     ... |        ... | ...                           | ...             | ...           |

</p>
</details>
<br/>



The module allows for correction of anchor points by integer offsets.  This is especially helpful if the query contains optional parts (defined by `?`, `+` or `*`) – note that this works inplace:
   
```python
dump.correct_anchors({3: +1, 4: -1})
lines = dump.concordance(
  form='slots', p_show=['word', 'lemma'], 
  slots={"name": [1, 2], "party": [3, 4]}
)
```

<details>
<summary><code>lines</code></summary>
<p>

| *match* | *matchend* | word                          | name\_word      | party\_word |
|--------:|-----------:|:------------------------------|:----------------|:------------|
|    8211 |       8217 | Wolfgang Zöller [ CDU / CSU ] | Wolfgang Zöller | CDU / CSU   |
|   15997 |      16001 | Peter Struck [ SPD ]          | Peter Struck    | SPD         |
|   25512 |      25516 | Jörg Tauss [ SPD ]            | Jörg Tauss      | SPD         |
|   32808 |      32814 | Ina Albowitz [ F. D. P. ]     | Ina Albowitz    | F. D. P.    |
|   36980 |      36984 | Christa Luft [ PDS ]          | Christa Luft    | PDS         |
|     ... |        ... | ...                           | ...             | ...         |

</p>
</details>
<br/>


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

### Subcorpora ###

In cwb-ccc terms, every `dump` is a subcorpus. There are two
possibilities to get a dump: either by running a traditional query as
outlined [above](#queries-and-dumps); the following query e.g. defines
a subcorpus of all sentences that contain the word "SPD":

```python
dump = corpus.query('"SPD" expand to s')
```

Alternatively, you can define subcorpora via meta data stored in
s-attributes.  A subcorpus of all noun phrases (indexed as
s-attributes `np`) can e.g. be extracted using

```python
dump = corpus.query_s_att("np")
```

You can also query the respective annotations:

```python
dump = corpus.query_s_att("text_party", {"CDU", "CSU"})
```

will e.g. retrieve all `text` spans with respective constraints on the
`party`.

Note that while the CWB does allow storage of arbitrary meta data in
s-attributes, it does not index these attributes.  The method thus
creates a dataframe with the spans of the s-attribute encoded as
matches and caches the result.  Consequently, the first query of an
s-attribute will be compartively slow and subsequent queries will be
faster.

Note also that the CWB does not allow complex queries on s-attributes.
It is thus reasonable to store meta data in separate spreadsheets or
relational databases and link to text spans via simple identifiers.
This way (1) you can work with natural meta data queries and (2)
working with a small number of s-attributes also unburdens the cache.


### Keyword Analyses ###

You can retrieve keywords for a subcorpus (a `dump`) with

```python
keywords = dump.keywords()
```

Just as with collocates, the result is a `DataFrame` with lexical
items (`p_query` layer) as index and frequency signatures and
association measures as columns.


## Testing ##
The module is shipped with a small test corpus ("GERMAPARL1386"),
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

The corpus is located in this [repository](tests/test-corpora/), but
you will have to manually update the path to the binary data files
(line 10 of the [registry
file](tests/test-corpora/registry/germaparl8613)), since the CWB
requires an absolute path here.

You can test the module using pytest. Make sure you install all
development dependencies:
	
	pip install --dev

You can then simply

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

Further development of the package is funded by the Deutsche
Forschungsgemeinschaft (DFG) within the project [Reconstructing
Arguments from Noisy
Text](https://www.linguistik.phil.fau.de/projects/rant/), grant number
377333057 (2018-2023), as part of the Priority Program [Robust
Argumentation Machines](http://www.spp-ratio.de/home/) (SPP-1999).
