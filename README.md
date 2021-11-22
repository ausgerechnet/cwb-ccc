# Collocation and Concordance Computation #

[![PyPI Latest Release](https://img.shields.io/pypi/v/cwb-ccc.svg)](https://pypi.org/project/cwb-ccc/)
[![Build](https://github.com/ausgerechnet/cwb-ccc/actions/workflows/build-test.yml/badge.svg?branch=master)](https://github.com/ausgerechnet/cwb-ccc/actions/workflows/build-test.yml?query=branch%3Amaster)


## Introduction ##
**cwb-ccc** is a Python wrapper around the [IMS Open Corpus Workbench (CWB)](http://cwb.sourceforge.net/).  Main purpose of the module is to run queries, extract concordance lines, and score frequency lists (particularly to extract collocates and keywords).

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

If you want to run queries with more than two anchor points, you will need CWB version 3.4.16 or later.


### Installation ###
You can install this module with pip from PyPI:

    pip3 install cwb-ccc

You can also clone the source from [github](https://github.com/ausgerechnet/cwb-ccc), `cd` in the respective folder, and build your own wheel:

    python -m pip install pipenv
    pipenv install --dev
    pipenv run python3 setup.py bdist_wheel


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

By default, the `data_path` points to "/tmp/ccc-{version}/". Make sure that "/tmp/" exists and appropriate rights are granted. Otherwise, change the parameter when initializing the corpus. Note that each corpus will have its own subdirectory for each library.

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
The usual starting point for using this module is to run a query with `corpus.query()`, which accepts valid CQP queries such as

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

There are two reasons for defining the context when running a query:

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

You can access concordance lines via the `concordance()` method of the dump.  This method returns a DataFrame with information about the query matches in context:

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

|   *match* |   *matchend* | word                          | lemma                         | name\_word      | name\_lemma     | party\_word   | party\_lemma   |
|----------:|-------------:|:------------------------------|:------------------------------|:----------------|:----------------|:--------------|:---------------|
|      8211 |         8217 | Wolfgang Zöller [ CDU / CSU ] | Wolfgang Zöller [ CDU / CSU ] | Wolfgang Zöller | Wolfgang Zöller | CDU / CSU     | CDU / CSU      |
|     15997 |        16001 | Peter Struck [ SPD ]          | Peter Struck [ SPD ]          | Peter Struck    | Peter Struck    | SPD           | SPD            |
|     25512 |        25516 | Jörg Tauss [ SPD ]            | Jörg Tauss [ SPD ]            | Jörg Tauss      | Jörg Tauss      | SPD           | SPD            |
|     32808 |        32814 | Ina Albowitz [ F. D. P. ]     | Ina Albowitz [ F. D. P. ]     | Ina Albowitz    | Ina Albowitz    | F. D. P.      | F. D. P.       |
|     36980 |        36984 | Christa Luft [ PDS ]          | Christa Luft [ PDS ]          | Christa Luft    | Christa Luft    | PDS           | PDS            |
|...|...|...|...|...|...|...|...|

</p>
</details>
<br/>

The module allows for correction of anchor points by integer offsets.  This is especially helpful if the query contains optional parts (defined by `?`, `+` or `*`) – note that this works inplace:

```python
dump.correct_anchors({3: +1, 4: -1})
lines = dump.concordance(
  form='slots', slots={"name": [1, 2], "party": [3, 4]}
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
After executing a query, you can use `dump.collocates()` to extract collocates for a given window size (symmetric windows around the corpus matches). The result will be a `DataFrame` with lexical items (e.g. lemmata) as index and frequency signatures and association measures as columns.

```python
dump = corpus.query('[lemma="SPD"]', context=10, context_break='s')
```

<details>
<summary><code>dump.collocates()</code></summary>
<p>

| *item*   |   O11 |   O12 |   O21 |    O22 |      E11 |     E12 |       E21 |    E22 |   z\_score |   t\_score |   log\_likelihood |   simple\_ll |     dice |   log\_ratio |   mutual\_information |   local\_mutual\_information |   conservative\_log\_ratio |      ipm |   ipm\_expected |   ipm\_reference |   ipm\_reference\_expected |   in\_nodes |   marginal |
|:---------|------:|------:|------:|-------:|---------:|--------:|----------:|-------:|-----------:|-----------:|------------------:|-------------:|---------:|-------------:|----------------------:|-----------------------------:|---------------------------:|---------:|----------------:|-----------------:|---------------------------:|------------:|-----------:|
| die      |   813 |  4373 | 12952 | 131030 | 478.556  | 4707.44 | 13286.4   | 130696 |    15.2882 |    11.7295 |           226.513 |      192.823 | 0.0858   |     0.801347 |              0.230157 |                      187.118 |                   0.605981 | 156768   |        92278.5  |         89955.7  |                   92278.5  |           0 |      13765 |
| bei      |   366 |  4820 |   991 | 142991 |  47.1777 | 5138.82 |  1309.82  | 142672 |    46.4174 |    16.6651 |           967.728 |      862.013 | 0.111875 |     3.35808  |              0.889744 |                      325.646 |                   3.00871  |  70574.6 |         9097.13 |          6882.8  |                    9097.13 |           0 |       1357 |
| (        |   314 |  4872 |  1444 | 142538 |  61.1189 | 5124.88 |  1696.88  | 142285 |    32.3466 |    14.2709 |           574.854 |      522.005 | 0.090438 |     2.59389  |              0.710754 |                      223.177 |                   2.23788  |  60547.6 |        11785.4  |         10029    |                   11785.4  |           0 |       1758 |
| [        |   221 |  4965 |   477 | 143505 |  24.2668 | 5161.73 |   673.733 | 143308 |    39.9366 |    13.2337 |           654.834 |      582.935 | 0.075119 |     3.68518  |              0.95938  |                      212.023 |                   3.21474  |  42614.7 |         4679.29 |          3312.91 |                    4679.29 |           0 |        698 |
| )        |   207 |  4979 |  1620 | 142362 |  63.5178 | 5122.48 |  1763.48  | 142219 |    18.0032 |     9.9727 |           218.341 |      202.135 | 0.059033 |     1.82683  |              0.513075 |                      106.207 |                   1.40153  |  39915.2 |        12247.9  |         11251.4  |                   12247.9  |           0 |       1827 |
|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|

</p>
</details>
<br/>

By default, collocates are calculated on the "lemma"-layer, assuming that this is an available p-attribute in the corpus. The corresponding parameter is `p_query` (which will fall back to "word" if the specified attribute is not annotated in the corpus).

**New in version 0.9.14**: You can now perform collocation analyses on combinations of p-attribute layers, the most prominent use case being POS-disambiguated lemmata:
<details>
<summary><code>dump.collocates(['lemma', 'pos'], order='log_likelihood')</code></summary>
<p>

| *item*     | O11 |  O12 |  O21 |    O22 |     E11 |     E12 |     E21 |    E22 | z\_score | t\_score | log\_likelihood | simple\_ll |     dice | log\_ratio | mutual\_information | local\_mutual\_information | conservative\_log\_ratio |     ipm | ipm\_expected | ipm\_reference | ipm\_reference\_expected | in\_nodes | marginal |
|:-----------|----:|-----:|-----:|-------:|--------:|--------:|--------:|-------:|---------:|---------:|----------------:|-----------:|---------:|-----------:|--------------------:|---------------------------:|-------------------------:|--------:|--------------:|---------------:|-------------------------:|----------:|---------:|
| bei APPR   | 360 | 4826 |  869 | 143113 | 42.7276 | 5143.27 | 1186.27 | 142796 |  48.5376 |  16.7217 |         1014.28 |    899.961 | 0.112237 |    3.52376 |            0.925594 |                    333.214 |                  3.16388 | 69417.7 |       8239.03 |        6035.48 |                  8239.03 |         0 |     1229 |
| ( $(       | 314 | 4872 | 1444 | 142538 | 61.1189 | 5124.88 | 1696.88 | 142285 |  32.3466 |  14.2709 |         574.854 |    522.005 | 0.090438 |    2.59389 |            0.710754 |                    223.177 |                  2.23649 | 60547.6 |       11785.4 |          10029 |                  11785.4 |         0 |     1758 |
| Beifall NN | 199 | 4987 |  471 | 143511 | 23.2933 | 5162.71 | 646.707 | 143335 |   36.406 |  12.4555 |         561.382 |    502.351 | 0.067964 |    3.55216 |            0.931621 |                    185.393 |                  3.06089 | 38372.5 |       4491.58 |        3271.24 |                  4491.58 |         0 |      670 |
| [ $(       | 161 | 5025 |  259 | 143723 | 14.6018 |  5171.4 | 405.398 | 143577 |  38.3118 |  11.5378 |         545.131 |    480.087 | 0.057438 |    4.10923 |             1.04242 |                     167.83 |                  3.52364 | 31045.1 |       2815.62 |        1798.84 |                  2815.62 |         0 |      420 |
| ]: $(      | 139 | 5047 |  340 | 143642 |  16.653 | 5169.35 | 462.347 | 143520 |  29.9811 |  10.3773 |         383.895 |     345.19 | 0.049073 |    3.50467 |            0.921522 |                    128.092 |                  2.91721 | 26802.9 |       3211.14 |        2361.41 |                  3211.14 |         0 |      479 |
| ...        | ... |  ... |  ... |    ... |     ... |     ... |     ... |    ... |      ... |      ... |             ... |        ... |      ... |        ... |                 ... |                        ... |                      ... |     ... |           ... |            ... |                      ... |       ... |      ... |

</p>
</details>
<br/>

For improved performance, all hapax legomena in the context are dropped after calculating the context size. You can change this behaviour via the `min_freq` parameter.

By default, the dataframe contains the counts, namely
- observed and expected absolute frequencies (columns O11, ..., E22),
- observed and expected relative frequencies (instances per million, IPM), 
- marginal frequencies, and 
- instances within nodes.

You can drop the counts by specifying `freq=False`. By default, the dataframe is annotated with all available association measures in the [pandas-association-measures](https://pypi.org/project/association-measures/) package (parameter `ams`). For notation and further information regarding association measures, see [collocations.de](http://www.collocations.de/AM/index.html).

The dataframe is sorted by co-occurrence frequency (column "O11"), and only the first 100 most frequently co-occurring collocates are retrieved. You can (and should) change this behaviour via the `order` and `cut_off` parameters.

### Subcorpora ###

In **cwb-ccc terms**, every instance of a `Dump` is a subcorpus.  There are two possibilities to get a `dump`: either by running a traditional query as outlined [above](#queries-and-dumps); the following query e.g. defines a subcorpus of all sentences that contain "SPD":

```python
dump = corpus.query('"SPD" expand to s')
```

Alternatively, you can define subcorpora via values stored in s-attributes.  A subcorpus of all noun phrases (assuming they are indexed as structural attribute `np`) can e.g. be extracted using

```python
dump = corpus.query_s_att("np")
```

You can also query the respective annotations:

```python
dump = corpus.query_s_att("text_party", {"CDU", "CSU"})
```

will e.g. retrieve all `text` spans with respective constraints on the `party` annotation.

Implementation note: While the CWB does allow storage of arbitrary meta data in s-attributes, it does not index these attributes.  `corpus.query_s_att()` thus creates a dataframe with the spans of the s-attribute encoded as matches and caches the result.  Consequently, the first query of an s-attribute will be compartively slow and subsequent queries will be faster.

Note also that the CWB does not allow complex queries on s-attributes.  It is thus reasonable to store meta data in separate spreadsheets or relational databases and link to text spans via simple identifiers.  This way (1) you can work with natural meta data queries and (2) working with a small number of s-attributes also unburdens the cache.

In **CWB terms**, subcorpora are _named query results_ (NQRs), which consist of the corpus positions of match and matchend (and optional anchor points called _anchor_ and _keyword_).  If you give a `name` when using `corpus.query()` or `corpus.query_s_att()`, the respective matches of the dump will also be available as NQRs in CQP.

This way you can run queries on NQRs in CQP (a.k.a. *subqueries*).  Compare e.g. the frequency breakdown for a query on the whole corpus

<details>
<summary><code>corpus.query('[lemma="sagen"]').breakdown()</code></summary>
<p>

| *word*   |   freq |
|:---------|-------:|
| sagen    |    234 |
| gesagt   |    131 |
| sage     |     69 |
| sagt     |     39 |
| Sagen    |     12 |
| sagte    |      6 |

</p>
</details>
<br/>

with the one a subcorpus:

```python
corpus.query_s_att("text_party", values={"CDU", "CSU"}, name="Union")
corpus.activate_subcorpus("Union")
print(corpus.subcorpus)
> 'Union'
```

<details>
<summary><code>corpus.query('[lemma="sagen"]').breakdown()</code></summary>
<p>

| *word*   |   freq |
|:---------|-------:|
| sagen    |     64 |
| gesagt   |     45 |
| sage     |     30 |
| sagt     |     12 |
| Sagen    |      6 |
| sagte    |      3 |

</p>
</details>
<br/>

Don't forget to switch back to the main corpus when you are done with the analysis on the activated NQR:

```python
corpus.activate_subcorpus()  # switches to main corpus when given no name
print(corpus.subcorpus)
> None
```

You can access all available NQRs via

<details>
<summary><code>corpus.show_nqr()</code></summary>
<p>

| corpus        | subcorpus   |   size | storage   |
|:--------------|:------------|-------:|:----------|
| GERMAPARL1386 | Union       |     82 | md-       |

</p>
</details>
<br/>


### Keyword Analyses ###

Having created a subcorpus (a `dump`)
```python
dump = corpus.query_s_att("text_party", values={"CDU", "CSU"})
```

you can use its `keywords()` method for retrieving keywords:

<details>
<summary><code>dump.keywords()</code></summary>
<p>

| *item*   |   O11 |   O12 |   O21 |    O22 |       E11 |     E12 |       E21 |    E22 |   z\_score |   t\_score |   log\_likelihood |   simple\_ll |     dice |   log\_ratio |   mutual\_information |   local\_mutual\_information |   conservative\_log\_ratio |      ipm |   ipm\_expected |   ipm\_reference |   ipm\_reference\_expected |
|:---------|------:|------:|------:|-------:|----------:|--------:|----------:|-------:|-----------:|-----------:|------------------:|-------------:|---------:|-------------:|----------------------:|-----------------------------:|---------------------------:|---------:|----------------:|-----------------:|---------------------------:|
| ,        |  2499 | 38852 |  5371 | 103078 | 2172.45   | 39178.6 | 5697.55   | 102751 |    7.00617 |    6.53239 |           69.6474 |      46.7967 | 0.101542 |     0.287183 |              0.060817 |                     151.982  |                   0.131751 | 60433.8  |       52536.7   |        49525.6   |                  52536.7   |
| in       |   867 | 40484 |  1631 | 106818 |  689.551  | 40661.4 | 1808.45   | 106641 |    6.75755 |    6.02647 |           61.2663 |      42.1849 | 0.039545 |     0.47937  |              0.099452 |                      86.2253 |                   0.204192 | 20966.8  |       16675.6   |        15039.3   |                  16675.6   |
| CSU      |   255 | 41096 |   380 | 108069 |  175.286  | 41175.7 |  459.714  | 107989 |    6.02087 |    4.99187 |           46.6543 |      31.7425 | 0.012147 |     0.81552  |              0.162792 |                      41.512  |                   0.281799 |  6166.72 |        4238.99  |         3503.95  |                   4238.99  |
| CDU      |   260 | 41091 |   390 | 108059 |  179.427  | 41171.6 |  470.573  | 107978 |    6.01515 |    4.99693 |           46.6055 |      31.7289 | 0.012381 |     0.80606  |              0.161086 |                      41.8823 |                   0.27822  |  6287.64 |        4339.12  |         3596.16  |                   4339.12  |
| deswegen |    55 | 41296 |    37 | 108412 |   25.3958 | 41325.6 |   66.6042 | 108382 |    5.87452 |    3.99183 |           41.5308 |      25.794  | 0.002654 |     1.96293  |              0.335601 |                      18.458  |                   0.558012 |  1330.08 |         614.152 |          341.174 |                    614.152 |
|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|

</p>
</details>
<br/>

Just as with collocates, the result is a `DataFrame` with lexical items (`p_query` layer) as index and frequency signatures and association measures as columns.

**New in version 0.9.14**: Keywords for p-attribute combinations:

<details>
<summary><code>dump.keywords(["lemma", "pos"], order="log_likelihood")</code></summary>
<p>

| *item*   |   O11 |   O12 |   O21 |    O22 |       E11 |     E12 |      E21 |    E22 |   z\_score |   t\_score |   log\_likelihood |   simple\_ll |     dice |   log\_ratio |   mutual\_information |   local\_mutual\_information |   conservative\_log\_ratio |      ipm |   ipm\_expected |   ipm\_reference |   ipm\_reference\_expected |
|:---------|------:|------:|------:|-------:|----------:|--------:|---------:|-------:|-----------:|-----------:|------------------:|-------------:|---------:|-------------:|----------------------:|-----------------------------:|---------------------------:|---------:|----------------:|-----------------:|---------------------------:|
| , $,     |  2499 | 38288 |  5371 | 103642 | 2142.82   | 38644.2 | 5727.18  | 103286 |    7.69455 |    7.12512 |           83.3197 |      56.1738 | 0.102719 |     0.314479 |              0.066782 |                     166.887  |                   0.158575 | 61269.5  |        52536.7  |         49269.4  |                   52536.7  |
| F. NN    |   161 | 40626 |   192 | 108821 |   96.1136 | 40690.9 |  256.886 | 108756 |    6.61853 |    5.11377 |           54.4564 |      36.3385 | 0.007827 |     1.16427  |              0.224041 |                      36.0706 |                   0.456631 |  3947.34 |         2356.48 |          1761.26 |                    2356.48 |
| CSU NE   |   255 | 40532 |   380 | 108633 |  172.895  | 40614.1 |  462.105 | 108551 |    6.24418 |    5.14158 |           49.731  |      33.9649 | 0.012312 |     0.842817 |              0.168757 |                      43.0329 |                   0.307344 |  6251.99 |         4238.99 |          3485.82 |                    4238.99 |
| CDU NE   |   260 | 40527 |   390 | 108623 |  176.98   | 40610   |  473.02  | 108540 |    6.24055 |    5.1487  |           49.7162 |      33.9757 | 0.012549 |     0.833356 |              0.16705  |                      43.433  |                   0.303785 |  6374.58 |         4339.12 |          3577.55 |                    4339.12 |
| die ART  |  3443 | 37344 |  8026 | 100987 | 3122.74   | 37664.3 | 8346.26  | 100667 |    5.7311  |    5.45805 |           47.9751 |      31.7769 | 0.131774 |     0.197304 |              0.042402 |                     145.988  |                   0.067797 | 84414.2  |        76562.1  |         73624.2  |                   76562.1  |
|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|...|

</p>
</details>
<br/>

Implementation note: `dump.keywords()` looks at all unigrams at the corpus positions in match..matchend, and compares the frequencies of their surface realizations with their marginal frequencies.  Similarly, `dump.collocates()` uses the the union of the corpus positions in context..contextend, excluding all corpus positions containted in any match..matchend.

## Testing ##
The module ships with a small test corpus ("GERMAPARL1386"), which contains all speeches of the 86th session of the 13th German Bundestag on Feburary 8, 1996.

The corpus consists of 149,800 tokens in 7332 paragraphs (s-attribute "p" with annotation "type" ("regular" or "interjection")) split into 11,364 sentences (s-attribute "s").  The p-attributes are "pos" and "lemma":

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
<br/>

The corpus is located in this [repository](tests/test-corpora/).  All tests are written using this corpus as a reference.  Make sure you install all development dependencies:

    pip install pipenv
    pipenv install --dev

You can then simply

    make test

and

    make coverage

which uses [pytest](https://pytest.org/) to check that all methods work reliably.

Note that the make commands above update the path to the binary data files (line 10 of the [registry file](tests/test-corpora/registry/germaparl1386)) in order to make the tests, since the CWB requires an absolute path here.


## Acknowledgements ##

- The module includes a slight adaptation of [cwb-python](https://github.com/fau-klue/cwb-python), a Python port of Perl's CWB::CL; thanks to **Yannick Versley** for the implementation.
- Special thanks to **Markus Opolka** for the original implementation of [association-measures](https://github.com/fau-klue/pandas-association-measures) and for forcing me to write tests.
- The test corpus was extracted from the [GermaParl](https://github.com/PolMine/GermaParlTEI) corpus (see the [PolMine Project](https://polmine.github.io/)); many thanks to **Andreas Blätte**.
- This work was supported by the [Emerging Fields Initiative (EFI)](https://www.fau.eu/research/collaborative-research/emerging-fields-initiative/) of [**Friedrich-Alexander-Universität Erlangen-Nürnberg**](https://www.fau.eu/), project title [Exploring the *Fukushima Effect*](https://www.linguistik.phil.fau.de/projects/efe/) (2017-2020).
- Further development of the package is funded by the Deutsche Forschungsgemeinschaft (DFG) within the project [Reconstructing Arguments from Noisy Text](https://www.linguistik.phil.fau.de/projects/rant/), grant number 377333057 (2018-2023), as part of the Priority Program [**Robust Argumentation Machines**](http://www.spp-ratio.de/) (SPP-1999).
