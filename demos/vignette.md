cwb-ccc Vignette
================
Philipp Heinrich
(October 16, 2022)

-   <a href="#accessing-corpora" id="toc-accessing-corpora">Accessing
    Corpora</a>
-   <a href="#queries-and-dumps" id="toc-queries-and-dumps">Queries and
    Dumps</a>
-   <a href="#concordancing" id="toc-concordancing">Concordancing</a>
-   <a href="#anchored-queries" id="toc-anchored-queries">Anchored
    Queries</a>
-   <a href="#collocation-analyses"
    id="toc-collocation-analyses">Collocation Analyses</a>
-   <a href="#subcorpora" id="toc-subcorpora">Subcorpora</a>
-   <a href="#keyword-analyses" id="toc-keyword-analyses">Keyword
    Analyses</a>

``` python
import ccc
ccc.__version__
```

    '0.11.0'

## Accessing Corpora

To list all CWB corpora defined in the registry, you can use

``` python
from ccc import Corpora

corpora = Corpora(registry_path="/usr/local/share/cwb/registry/")
```

``` python
corpora.show()  # returns a pd.DataFrame
print(corpora)  # returns a str
```

All further methods rely on the `Corpus` class, which establishes the
connection to your CWB-indexed corpus. You can activate a corpus with

``` python
corpus = corpora.activate(corpus_name="GERMAPARL1386")
```

or directly use the respective class:

``` python
from ccc import Corpus

corpus = Corpus(
  corpus_name="GERMAPARL1386",
  registry_path="/usr/local/share/cwb/registry/"
)
```

This will raise a `KeyError` if the named corpus is not in the specified
registry.

If you are using macros and wordlists, you have to store them in a
separate folder (with subfolders “wordlists/” and “macros/”). Specify
this folder via `lib_path` when initializing the corpus.

You can use the `cqp_bin` to point the module to a specific version of
`cqp` (this is also helpful if `cqp` is not in your `PATH`).

By default, the `data_path` points to “/tmp/ccc-{version}/”. Make sure
that “/tmp/” exists and appropriate rights are granted. Otherwise,
change the parameter when initializing the corpus. Note that each corpus
will have its own subdirectory for each library.

If everything is set up correctly, you can list all available attributes
of the activated corpus:

``` python
corpus.attributes_available
```

| type  | attribute                | annotation | active |
|:------|:-------------------------|:-----------|:-------|
| p-Att | word                     | False      | True   |
| p-Att | pos                      | False      | False  |
| p-Att | lemma                    | False      | False  |
| s-Att | corpus                   | False      | False  |
| s-Att | corpus_name              | True       | False  |
| s-Att | sitzung                  | False      | False  |
| s-Att | sitzung_date             | True       | False  |
| s-Att | sitzung_period           | True       | False  |
| s-Att | sitzung_session          | True       | False  |
| s-Att | div                      | False      | False  |
| s-Att | div_desc                 | True       | False  |
| s-Att | div_n                    | True       | False  |
| s-Att | div_type                 | True       | False  |
| s-Att | div_what                 | True       | False  |
| s-Att | text                     | False      | False  |
| s-Att | text_id                  | True       | False  |
| s-Att | text_name                | True       | False  |
| s-Att | text_parliamentary_group | True       | False  |
| s-Att | text_party               | True       | False  |
| s-Att | text_position            | True       | False  |
| s-Att | text_role                | True       | False  |
| s-Att | text_who                 | True       | False  |
| s-Att | p                        | False      | False  |
| s-Att | p_type                   | True       | False  |
| s-Att | s                        | False      | False  |

## Queries and Dumps

The usual starting point for using this module is to run a query with
`corpus.query()`, which accepts valid CQP queries such as

``` python
query = r'"\[" ([word="[A-Z0-9]+.?"%d]+ "/"?)+ "\]"'
dump = corpus.query(query)
```

The result is a `Dump` object. Its core is a pandas DataFrame
(`dump.df`) similar to a CQP dump and multi-indexed by “match” and
“matchend” of the query. All entries of the DataFrame, including the
index, are integers representing corpus positions:

``` python
dump.df
```

| *match* | *matchend* | context | contextend |
|--------:|-----------:|--------:|-----------:|
|    2313 |       2319 |    2293 |       2339 |
|    8213 |       8217 |    8193 |       8237 |
|    8438 |       8444 |    8418 |       8464 |
|   15999 |      16001 |   15979 |      16021 |
|   24282 |      24288 |   24262 |      24308 |
|       … |          … |       … |          … |

You can provide one or more parameters to define the context around the
matches: a parameter `context` specifying the context window (defaults
to 20) and a parameter `context_break` naming an s-attribute to limit
the context . You can specify asymmetric windows via `context_left` and
`context_right`.

When providing an s-attribute limiting the context, the module
additionally retrieves the CWB-id of this attribute, the corpus
positions of the respective span start and end, as well as the actual
context spans:

``` python
dump = corpus.query(
  cqp_query=query,
  context=20,
  context_break='s'
)
```

``` python
dump.df
```

| *match* | *matchend* | s_cwbid | s_span | s_spanend | contextid | context | contextend |
|--------:|-----------:|--------:|-------:|----------:|----------:|--------:|-----------:|
|    2313 |       2319 |     161 |   2304 |      2320 |       161 |    2304 |       2320 |
|    8213 |       8217 |     489 |   8187 |      8218 |       489 |    8193 |       8218 |
|    8438 |       8444 |     500 |   8425 |      8445 |       500 |    8425 |       8445 |
|   15999 |      16001 |     905 |  15992 |     16002 |       905 |   15992 |      16002 |
|   24282 |      24288 |    1407 |  24273 |     24289 |      1407 |   24273 |      24289 |
|       … |          … |       … |      … |         … |         … |       … |          … |

There are two reasons for defining the context when running a query:

1.  If you provide a `context_break` parameter, the query will be
    automatically confined to spans delimited by this s-attribute; this
    is equivalent to formulating a query that ends on a respective
    “within” clause.
2.  Subsequent analyses (concordancing, collocation) will all work on
    the same context.

Notwithstanding (1), the context can also be set after having run the
query:

``` python
dump = dump.set_context(
    context_left=5,
    context_right=10,
    context_break='s'
)
```

You can set CQP’s matching strategy (“standard”, “longest”, “shortest”,
“traditional”) via the `match_strategy` parameter.

By default, the result is cached: the query parameters are used to
create an appropriate identifier. This way, the result can be accessed
directly by later queries with the same parameters on the same
(sub)corpus, without the need for CQP to run again.

We are set up to analyze the query result. Here’s the frequency
breakdown:

``` python
dump.breakdown()
```

| *item*                        | freq |
|:------------------------------|-----:|
| \[ BÜNDNIS 90 / DIE GRÜNEN \] |   12 |
| \[ CDU / CSU \]               |   13 |
| \[ F. D. P. \]                |   14 |
| \[ PDS \]                     |    6 |
| \[ SPD \]                     |   18 |

## Concordancing

You can access concordance lines via the `concordance()` method of the
dump. This method returns a DataFrame with information about the query
matches in context:

``` python
dump.concordance()
```

| *match* | *matchend* | word                                                           |
|--------:|-----------:|:---------------------------------------------------------------|
|    2313 |       2319 | Joseph Fischer \[ Frankfurt \] \[ BÜNDNIS 90 / DIE GRÜNEN \] ) |
|    8213 |       8217 | Widerspruch des Abg. Wolfgang Zöller \[ CDU / CSU \] )         |
|    8438 |       8444 | Joseph Fischer \[ Frankfurt \] \[ BÜNDNIS 90 / DIE GRÜNEN \] ) |
|   15999 |      16001 | des Abg. Dr. Peter Struck \[ SPD \] )                          |
|   24282 |      24288 | Joseph Fischer \[ Frankfurt \] \[ BÜNDNIS 90 / DIE GRÜNEN \] ) |
|       … |          … | …                                                              |

By default, the output is a “simple” format, i.e. a DataFrame indexed by
“match” and “matchend” with a column “word” showing the matches in
context. You can choose which p-attributes to retrieve via the `p_show`
parameter. Similarly, you can retrieve s-attributes (at match-position):

``` python
dump.concordance(p_show=["word", "lemma"], s_show=["text_id"])
```

| *match* | *matchend* | word                                                           | lemma                                                          | text_id      |
|--------:|-----------:|:---------------------------------------------------------------|:---------------------------------------------------------------|:-------------|
|    2313 |       2319 | Joseph Fischer \[ Frankfurt \] \[ BÜNDNIS 90 / DIE GRÜNEN \] ) | Joseph Fischer \[ Frankfurt \] \[ Bündnis 90 / die Grünen \] ) | i13_86_1\_2  |
|    8213 |       8217 | Widerspruch des Abg. Wolfgang Zöller \[ CDU / CSU \] )         | Widerspruch die Abg. Wolfgang Zöller \[ CDU / CSU \] )         | i13_86_1\_4  |
|    8438 |       8444 | Joseph Fischer \[ Frankfurt \] \[ BÜNDNIS 90 / DIE GRÜNEN \] ) | Joseph Fischer \[ Frankfurt \] \[ Bündnis 90 / die Grünen \] ) | i13_86_1\_4  |
|   15999 |      16001 | des Abg. Dr. Peter Struck \[ SPD \] )                          | die Abg. Dr. Peter Struck \[ SPD \] )                          | i13_86_1\_8  |
|   24282 |      24288 | Joseph Fischer \[ Frankfurt \] \[ BÜNDNIS 90 / DIE GRÜNEN \] ) | Joseph Fischer \[ Frankfurt \] \[ Bündnis 90 / die Grünen \] ) | i13_86_1\_24 |
|       … |          … | …                                                              | …                                                              | …            |

The format can be changed using the `form` parameter. The “kwic” format
e.g. returns three columns for each requested p-attribute:

``` python
dump.concordance(form="kwic")
```

| *match* | *matchend* | left_word                            | node_word                     | right_word |
|--------:|-----------:|:-------------------------------------|:------------------------------|:-----------|
|    2313 |       2319 | Joseph Fischer \[ Frankfurt \]       | \[ BÜNDNIS 90 / DIE GRÜNEN \] | )          |
|    8213 |       8217 | Widerspruch des Abg. Wolfgang Zöller | \[ CDU / CSU \]               | )          |
|    8438 |       8444 | Joseph Fischer \[ Frankfurt \]       | \[ BÜNDNIS 90 / DIE GRÜNEN \] | )          |
|   15999 |      16001 | des Abg. Dr. Peter Struck            | \[ SPD \]                     | )          |
|   24282 |      24288 | Joseph Fischer \[ Frankfurt \]       | \[ BÜNDNIS 90 / DIE GRÜNEN \] | )          |
|       … |          … | …                                    | …                             | …          |

If you want to inspect each query result in detail, use
`form`=“dataframe”; here, every concordance line is verticalized text
formated as DataFrame with the *cpos* of each token as index:

``` python
lines = dump.concordance(
    p_show=['word', 'pos', 'lemma'],
    form='dataframe'
)
```

``` python
lines.iloc[0]['dataframe']
```

| *cpos* | offset | word      | pos     | lemma     |
|-------:|-------:|:----------|:--------|:----------|
|   2308 |     -5 | Joseph    | NE      | Joseph    |
|   2309 |     -4 | Fischer   | NE      | Fischer   |
|   2310 |     -3 | \[        | XY      | \[        |
|   2311 |     -2 | Frankfurt | NE      | Frankfurt |
|   2312 |     -1 | \]        | APPRART | \]        |
|   2313 |      0 | \[        | ADJA    | \[        |
|   2314 |      0 | BÜNDNIS   | NN      | Bündnis   |
|   2315 |      0 | 90        | CARD    | 90        |
|   2316 |      0 | /         | \$(     | /         |
|   2317 |      0 | DIE       | ART     | die       |
|   2318 |      0 | GRÜNEN    | NN      | Grünen    |
|   2319 |      0 | \]        | \$.     | \]        |
|   2320 |      1 | )         | \$(     | )         |

Further `form`s are “slots” (see [below](#anchored-queries)) and “dict”:
In the latter case, every entry in the “dict” column is a dictionary
with the following keys:

-   “match” (int): the cpos of the match (serves as an identifier)
-   “cpos” (list): the cpos of all tokens in the concordance line
-   “offset” (list): the offset to match/matchend of all tokens
-   “word” (list): the words of all tokens
-   “anchors” (dict): a dictionary of {anchor: cpos} (see
    [below](#anchored-queries))

This format is especially suitable for serialization purposes.

You can decide which and how many concordance lines you want to retrieve
by means of the parameters `order` (“first”, “last”, or “random”) and
`cut_off`. You can also provide a list of `matches` to get only specific
concordance lines.

## Anchored Queries

The concordancer detects anchored queries automatically. The following
query

``` python
dump = corpus.query(
  cqp_query=r'@1[pos="NE"]? @2[pos="NE"] @3"\[" ([word="[A-Z0-9]+.?"%d]+ "/"?)+ @4"\]"',
  context=None, 
  context_break='s', 
  match_strategy='longest'
)
lines = dump.concordance(form='dataframe')
```

thus returns DataFrames with additional columns for each anchor point:

``` python
lines.iloc[0]['dataframe']
```

| *cpos* | offset | word         | 1     | 2     | 3     | 4     |
|-------:|-------:|:-------------|:------|:------|:------|:------|
|   8187 |    -24 | (            | False | False | False | False |
|   8188 |    -23 | Anhaltender  | False | False | False | False |
|   8189 |    -22 | lebhafter    | False | False | False | False |
|   8190 |    -21 | Beifall      | False | False | False | False |
|   8191 |    -20 | bei          | False | False | False | False |
|   8192 |    -19 | der          | False | False | False | False |
|   8193 |    -18 | SPD          | False | False | False | False |
|   8194 |    -17 | –            | False | False | False | False |
|   8195 |    -16 | Beifall      | False | False | False | False |
|   8196 |    -15 | bei          | False | False | False | False |
|   8197 |    -14 | Abgeordneten | False | False | False | False |
|   8198 |    -13 | des          | False | False | False | False |
|   8199 |    -12 | BÜNDNISSES   | False | False | False | False |
|   8200 |    -11 | 90           | False | False | False | False |
|   8201 |    -10 | /            | False | False | False | False |
|   8202 |     -9 | DIE          | False | False | False | False |
|   8203 |     -8 | GRÜNEN       | False | False | False | False |
|   8204 |     -7 | und          | False | False | False | False |
|   8205 |     -6 | der          | False | False | False | False |
|   8206 |     -5 | PDS          | False | False | False | False |
|   8207 |     -4 | –            | False | False | False | False |
|   8208 |     -3 | Widerspruch  | False | False | False | False |
|   8209 |     -2 | des          | False | False | False | False |
|   8210 |     -1 | Abg.         | False | False | False | False |
|   8211 |      0 | Wolfgang     | True  | False | False | False |
|   8212 |      0 | Zöller       | False | True  | False | False |
|   8213 |      0 | \[           | False | False | True  | False |
|   8214 |      0 | CDU          | False | False | False | False |
|   8215 |      0 | /            | False | False | False | False |
|   8216 |      0 | CSU          | False | False | False | False |
|   8217 |      0 | \]           | False | False | False | True  |
|   8218 |      1 | )            | False | False | False | False |

For an analysis of certain spans of your query matches, you can use
anchor points to define “slots”, i.e. single anchors or spans between
anchors that define sub-parts of your matches. Use the “slots” format to
extract these parts from each match:

``` python
dump = corpus.query(
    r'@1[pos="NE"]? @2[pos="NE"] @3"\[" ([word="[A-Z0-9]+.?"%d]+ "/"?)+ @4"\]"',
    context=0,
    context_break='s',
    match_strategy='longest',
)
lines = dump.concordance(
  form='slots', 
  p_show=['word', 'lemma'],
  slots={"name": [1, 2], "party": [3, 4]}
)
```

``` python
lines
```

| *match* | *matchend* | word                            | lemma                           | name_word       | name_lemma      | party_word      | party_lemma     |
|--------:|-----------:|:--------------------------------|:--------------------------------|:----------------|:----------------|:----------------|:----------------|
|    8211 |       8217 | Wolfgang Zöller \[ CDU / CSU \] | Wolfgang Zöller \[ CDU / CSU \] | Wolfgang Zöller | Wolfgang Zöller | \[ CDU / CSU \] | \[ CDU / CSU \] |
|   15997 |      16001 | Peter Struck \[ SPD \]          | Peter Struck \[ SPD \]          | Peter Struck    | Peter Struck    | \[ SPD \]       | \[ SPD \]       |
|   25512 |      25516 | Jörg Tauss \[ SPD \]            | Jörg Tauss \[ SPD \]            | Jörg Tauss      | Jörg Tauss      | \[ SPD \]       | \[ SPD \]       |
|   32808 |      32814 | Ina Albowitz \[ F. D. P. \]     | Ina Albowitz \[ F. D. P. \]     | Ina Albowitz    | Ina Albowitz    | \[ F. D. P. \]  | \[ F. D. P. \]  |
|   36980 |      36984 | Christa Luft \[ PDS \]          | Christa Luft \[ PDS \]          | Christa Luft    | Christa Luft    | \[ PDS \]       | \[ PDS \]       |
|       … |          … | …                               | …                               | …               | …               | …               | …               |

The module allows for correction of anchor points by integer offsets.
This is especially helpful if the query contains optional parts (defined
by `?`, `+` or `*`) – note that this works inplace:

``` python
dump.correct_anchors({3: +1, 4: -1})
lines = dump.concordance(
  form='slots',
  slots={"name": [1, 2],
  "party": [3, 4]}
)
```

``` python
lines
```

| *match* | *matchend* | word                            | name_word       | party_word |
|--------:|-----------:|:--------------------------------|:----------------|:-----------|
|    8211 |       8217 | Wolfgang Zöller \[ CDU / CSU \] | Wolfgang Zöller | CDU / CSU  |
|   15997 |      16001 | Peter Struck \[ SPD \]          | Peter Struck    | SPD        |
|   25512 |      25516 | Jörg Tauss \[ SPD \]            | Jörg Tauss      | SPD        |
|   32808 |      32814 | Ina Albowitz \[ F. D. P. \]     | Ina Albowitz    | F. D. P.   |
|   36980 |      36984 | Christa Luft \[ PDS \]          | Christa Luft    | PDS        |
|       … |          … | …                               | …               | …          |

## Collocation Analyses

After executing a query, you can use `dump.collocates()` to extract
collocates for a given window size (symmetric windows around the corpus
matches). The result will be a `DataFrame` with lexical items
(e.g. lemmata) as index and frequency signatures and association
measures as columns.

``` python
dump = corpus.query(
    '[lemma="SPD"]', 
    context=10, 
    context_break='s'
)
```

``` python
dump.collocates()
```

| *item* | O11 |  O12 |   O21 |    O22 |   R1 |     R2 |    C1 |     C2 |      N |     E11 |     E12 |     E21 |    E22 | z_score | t_score | log_likelihood | simple_ll | min_sensitivity |  liddell |     dice | log_ratio | conservative_log_ratio | mutual_information | local_mutual_information |     ipm | ipm_reference | ipm_expected | in_nodes | marginal |
|:-------|----:|-----:|------:|-------:|-----:|-------:|------:|-------:|-------:|--------:|--------:|--------:|-------:|--------:|--------:|---------------:|----------:|----------------:|---------:|---------:|----------:|-----------------------:|-------------------:|-------------------------:|--------:|--------------:|-------------:|---------:|---------:|
| die    | 813 | 4373 | 12952 | 131030 | 5186 | 143982 | 13765 | 135403 | 149168 | 478.556 | 4707.44 | 13286.4 | 130696 | 15.2882 | 11.7295 |        226.513 |   192.823 |        0.059063 | 0.026767 |   0.0858 |  0.801347 |               0.545843 |           0.230157 |                  187.118 |  156768 |       89955.7 |      92278.5 |        0 |    13765 |
| bei    | 366 | 4820 |   991 | 142991 | 5186 | 143982 |  1357 | 147811 | 149168 | 47.1777 | 5138.82 | 1309.82 | 142672 | 46.4174 | 16.6651 |        967.728 |   862.013 |        0.070575 | 0.237103 | 0.111875 |   3.35808 |                2.92542 |           0.889744 |                  325.646 | 70574.6 |        6882.8 |      9097.13 |        0 |     1357 |
| (      | 314 | 4872 |  1444 | 142538 | 5186 | 143982 |  1758 | 147410 | 149168 | 61.1189 | 5124.88 | 1696.88 | 142285 | 32.3466 | 14.2709 |        574.854 |   522.005 |        0.060548 | 0.145561 | 0.090438 |   2.59389 |                2.14939 |           0.710754 |                  223.177 | 60547.6 |         10029 |      11785.4 |        0 |     1758 |
| \[     | 221 | 4965 |   477 | 143505 | 5186 | 143982 |   698 | 148470 | 149168 | 24.2668 | 5161.73 | 673.733 | 143308 | 39.9366 | 13.2337 |        654.834 |   582.935 |        0.042615 | 0.283178 | 0.075119 |   3.68518 |                3.10689 |            0.95938 |                  212.023 | 42614.7 |       3312.91 |      4679.29 |        0 |      698 |
| )      | 207 | 4979 |  1620 | 142362 | 5186 | 143982 |  1827 | 147341 | 149168 | 63.5178 | 5122.48 | 1763.48 | 142219 | 18.0032 |  9.9727 |        218.341 |   202.135 |        0.039915 | 0.079508 | 0.059033 |   1.82683 |                1.29206 |           0.513075 |                  106.207 | 39915.2 |       11251.4 |      12247.9 |        0 |     1827 |
| …      |   … |    … |     … |      … |    … |      … |     … |      … |      … |       … |       … |       … |      … |       … |       … |              … |         … |               … |        … |        … |         … |                      … |                  … |                        … |       … |             … |            … |        … |        … |

By default, collocates are calculated on the “lemma”-layer, assuming
that this is an available p-attribute in the corpus. The corresponding
parameter is `p_query` (which will fall back to “word” if the specified
attribute is not annotated in the corpus). Note that you can also
perform collocation analyses on combinations of p-attribute layers, the
most prominent use case being POS-disambiguated lemmata:

``` python
dump.collocates(['lemma', 'pos'], order='log_likelihood')
```

| *item*     | O11 |  O12 |  O21 |    O22 |   R1 |     R2 |   C1 |     C2 |      N |     E11 |     E12 |     E21 |    E22 | z_score | t_score | log_likelihood | simple_ll | min_sensitivity |  liddell |     dice | log_ratio | conservative_log_ratio | mutual_information | local_mutual_information |     ipm | ipm_reference | ipm_expected | in_nodes | marginal |
|:-----------|----:|-----:|-----:|-------:|-----:|-------:|-----:|-------:|-------:|--------:|--------:|--------:|-------:|--------:|--------:|---------------:|----------:|----------------:|---------:|---------:|----------:|-----------------------:|-------------------:|-------------------------:|--------:|--------------:|-------------:|---------:|---------:|
| bei APPR   | 360 | 4826 |  869 | 143113 | 5186 | 143982 | 1229 | 147939 | 149168 | 42.7276 | 5143.27 | 1186.27 | 142796 | 48.5376 | 16.7217 |        1014.28 |   899.961 |        0.069418 |   0.2603 | 0.112237 |   3.52376 |                3.07952 |           0.925594 |                  333.214 | 69417.7 |       6035.48 |      8239.03 |        0 |     1229 |
| ( \$(      | 314 | 4872 | 1444 | 142538 | 5186 | 143982 | 1758 | 147410 | 149168 | 61.1189 | 5124.88 | 1696.88 | 142285 | 32.3466 | 14.2709 |        574.854 |   522.005 |        0.060548 | 0.145561 | 0.090438 |   2.59389 |                2.14784 |           0.710754 |                  223.177 | 60547.6 |         10029 |      11785.4 |        0 |     1758 |
| Beifall NN | 199 | 4987 |  471 | 143511 | 5186 | 143982 |  670 | 148498 | 149168 | 23.2933 | 5162.71 | 646.707 | 143335 |  36.406 | 12.4555 |        561.382 |   502.351 |        0.038373 | 0.263432 | 0.067964 |   3.55216 |                2.94681 |           0.931621 |                  185.393 | 38372.5 |       3271.24 |      4491.58 |        0 |      670 |
| \[ \$(     | 161 | 5025 |  259 | 143723 | 5186 | 143982 |  420 | 148748 | 149168 | 14.6018 |  5171.4 | 405.398 | 143577 | 38.3118 | 11.5378 |        545.131 |   480.087 |        0.031045 | 0.349551 | 0.057438 |   4.10923 |                3.39452 |            1.04242 |                   167.83 | 31045.1 |       1798.84 |      2815.62 |        0 |      420 |
| \]: \$(    | 139 | 5047 |  340 | 143642 | 5186 | 143982 |  479 | 148689 | 149168 |  16.653 | 5169.35 | 462.347 | 143520 | 29.9811 | 10.3773 |        383.895 |    345.19 |        0.026803 | 0.256245 | 0.049073 |   3.50467 |                2.77726 |           0.921522 |                  128.092 | 26802.9 |       2361.41 |      3211.14 |        0 |      479 |
| …          |   … |    … |    … |      … |    … |      … |    … |      … |      … |       … |       … |       … |      … |       … |       … |              … |         … |               … |        … |        … |         … |                      … |                  … |                        … |       … |             … |            … |        … |        … |

By default, the dataframe contains the counts, namely

-   observed and expected absolute frequencies (columns O11, …, E22),
-   observed and expected relative frequencies (instances per million,
    IPM),
-   marginal frequencies, and
-   instances within nodes.

and is annotated with all available association measures in the
[pandas-association-measures](https://pypi.org/project/association-measures/)
package (parameter `ams`). For notation and further information
regarding association measures, see
[collocations.de](http://www.collocations.de/AM/index.html).

For improved performance, all hapax legomena in the context are dropped
after calculating the context size. You can change this behaviour via
the `min_freq` parameter.

The dataframe is sorted by co-occurrence frequency (column “O11”), and
only the first 100 most frequently co-occurring collocates are
retrieved. You can (and should) change this behaviour via the `order`
and `cut_off` parameters.

## Subcorpora

In **cwb-ccc terms**, every instance of a `Dump` is a subcorpus. There
are two possibilities to get a `dump`: either by running a traditional
query as outlined [above](#queries-and-dumps); the following query
e.g. defines a subcorpus of all sentences that contain “SPD”:

``` python
dump = corpus.query('"SPD" expand to s')
```

Alternatively, you can define subcorpora via values stored in
s-attributes. A subcorpus of all noun phrases (assuming they are indexed
as structural attribute `np`) can e.g. be extracted using

``` python
dump = corpus.query(s_query="np")
```

You can also query the respective annotations:

``` python
dump = corpus.query(s_query="text_party", s_values={"CDU", "CSU"})
```

will e.g. retrieve all `text` spans with respective constraints on the
`party` annotation.

Implementation note: While the CWB does allow storage of arbitrary meta
data in s-attributes, it does not index these attributes.
`corpus.query()` thus creates a dataframe with the spans of the
s-attribute encoded as matches and caches the result. Consequently, the
first query of an s-attribute will be compartively slow and subsequent
queries will be faster.

Note also that the CWB does not allow complex queries on s-attributes.
It is thus reasonable to store meta data in separate spreadsheets or
relational databases and link to text spans via simple identifiers. This
way (1) you can work with natural meta data queries and (2) working with
a small number of s-attributes also unburdens the cache.

In **CWB terms**, subcorpora are *named query results* (NQRs), which
consist of the corpus positions of match and matchend (and optional
anchor points called *anchor* and *keyword*). If you give a `name` when
using `corpus.query()`, the respective matches of the dump will also be
available as NQRs in CQP.

This way you can run queries on NQRs in CQP (a.k.a. *subqueries*).
Compare e.g. the frequency breakdown for a query on the whole corpus

``` python
corpus.query('[lemma="sagen"]').breakdown()
```

| *item* | freq |
|:-------|-----:|
| Sagen  |   12 |
| gesagt |  131 |
| sage   |   69 |
| sagen  |  234 |
| sagt   |   39 |
| sagte  |    6 |

with the one on a subcorpus:

``` python
# define the subcorpus via a query
tmp_dump = corpus.query(
    s_query="text_party", 
    s_values={"CDU", "CSU"}, 
    name="Union"
)
union = corpus.activate_subcorpus("Union")
print(union.subcorpus)
```

    Union

``` python
union.query('[lemma="sagen"]').breakdown()
```

| *item* | freq |
|:-------|-----:|
| Sagen  |    6 |
| gesagt |   45 |
| sage   |   30 |
| sagen  |   64 |
| sagt   |   12 |
| sagte  |    3 |

You can access all available NQRs via

``` python
corpus.show_nqr()
```

| corpus        | subcorpus | size | storage |
|:--------------|:----------|-----:|:--------|
| GERMAPARL1386 | Union     |    0 | -d-     |
| GERMAPARL1386 | Last      |    0 | -d-     |

## Keyword Analyses

Having created a dump

``` python
dump = corpus.query(s_query="text_party", s_values={"CDU", "CSU"})
```

you can use its `keywords()` method for retrieving keywords:

``` python
dump.keywords()
```

| *item* |  O11 |   O12 |  O21 |    O22 |    R1 |     R2 |    C1 |     C2 |      N |     E11 |     E12 |     E21 |     E22 | z_score | t_score | log_likelihood | simple_ll | min_sensitivity |  liddell |     dice | log_ratio | conservative_log_ratio | mutual_information | local_mutual_information |     ipm | ipm_reference | ipm_expected |
|:-------|-----:|------:|-----:|-------:|------:|-------:|------:|-------:|-------:|--------:|--------:|--------:|--------:|--------:|--------:|---------------:|----------:|----------------:|---------:|---------:|----------:|-----------------------:|-------------------:|-------------------------:|--------:|--------------:|-------------:|
| die    | 4107 | 37244 | 9658 |  98791 | 41351 | 108449 | 13765 | 136035 | 149800 | 3799.71 | 37551.3 | 9965.29 | 98483.7 |  4.9851 | 4.79498 |         37.261 |   24.2071 |         0.09932 | 0.024583 | 0.149031 |  0.157383 |               0.020783 |           0.033774 |                  138.711 | 99320.5 |       89055.7 |      91889.2 |
| ,      | 2499 | 38852 | 5371 | 103078 | 41351 | 108449 |  7870 | 141930 | 149800 | 2172.45 | 39178.6 | 5697.55 |  102751 | 7.00617 | 6.53239 |        69.6474 |   46.7967 |        0.060434 | 0.043794 | 0.101542 |  0.287183 |               0.109313 |           0.060817 |                  151.982 | 60433.8 |       49525.6 |      52536.7 |
| sie    | 2343 | 39008 | 5357 | 103092 | 41351 | 108449 |  7700 | 142100 | 149800 | 2125.52 | 39225.5 | 5574.48 |  102875 | 4.71726 | 4.49299 |        31.7949 |   21.5301 |        0.056661 | 0.029775 | 0.095533 |  0.197954 |               0.015877 |           0.042307 |                  99.1261 | 56661.3 |       49396.5 |      51401.9 |
| .      | 1742 | 39609 | 3917 | 104532 | 41351 | 108449 |  5659 | 144141 | 149800 | 1562.12 | 39788.9 | 4096.88 |  104352 | 4.55124 | 4.30986 |        29.1022 |   19.9616 |        0.042127 | 0.033035 | 0.074112 |  0.222018 |               0.009973 |           0.047334 |                  82.4563 | 42127.2 |       36118.4 |        37777 |
| und    |  942 | 40409 | 1938 | 106511 | 41351 | 108449 |  2880 | 146920 | 149800 | 794.999 |   40556 |    2085 |  106364 | 5.21358 | 4.78955 |        36.9989 |   25.6457 |        0.022781 | 0.052042 | 0.042595 |  0.350253 |               0.056744 |           0.073684 |                  69.4105 | 22780.6 |       17870.2 |      19225.6 |
| …      |    … |     … |    … |      … |     … |      … |     … |      … |      … |       … |       … |       … |       … |       … |       … |              … |         … |               … |        … |        … |         … |                      … |                  … |                        … |       … |             … |            … |

Just as with collocates, the result is a `DataFrame` with lexical items
(`p_query` layer) as index and frequency signatures and association
measures as columns. And just as with collocates, you can calculate
keywords for p-attribute combinations:

``` python
dump.keywords(["lemma", "pos"], order="log_likelihood")
```

| *item*  |  O11 |   O12 |  O21 |    O22 |    R1 |     R2 |    C1 |     C2 |      N |     E11 |     E12 |     E21 |    E22 | z_score | t_score | log_likelihood | simple_ll | min_sensitivity |  liddell |     dice | log_ratio | conservative_log_ratio | mutual_information | local_mutual_information |     ipm | ipm_reference | ipm_expected |
|:--------|-----:|------:|-----:|-------:|------:|-------:|------:|-------:|-------:|--------:|--------:|--------:|-------:|--------:|--------:|---------------:|----------:|----------------:|---------:|---------:|----------:|-----------------------:|-------------------:|-------------------------:|--------:|--------------:|-------------:|
| , \$,   | 2499 | 38288 | 5371 | 103642 | 40787 | 109013 |  7870 | 141930 | 149800 | 2142.82 | 38644.2 | 5727.18 | 103286 | 7.69455 | 7.12512 |        83.3197 |   56.1738 |         0.06127 | 0.047768 | 0.102719 |  0.314479 |               0.136118 |           0.066782 |                  166.887 | 61269.5 |       49269.4 |      52536.7 |
| F. NN   |  161 | 40626 |  192 | 108821 | 40787 | 109013 |   353 | 149447 | 149800 | 96.1136 | 40690.9 | 256.886 | 108756 | 6.61853 | 5.11377 |        54.4564 |   36.3385 |        0.003947 | 0.184248 | 0.007827 |   1.16427 |               0.366081 |           0.224041 |                  36.0706 | 3947.34 |       1761.26 |      2356.48 |
| CSU NE  |  255 | 40532 |  380 | 108633 | 40787 | 109013 |   635 | 149165 | 149800 | 172.895 | 40614.1 | 462.105 | 108551 | 6.24418 | 5.14158 |         49.731 |   33.9649 |        0.006252 | 0.129849 | 0.012312 |  0.842817 |               0.237919 |           0.168757 |                  43.0329 | 6251.99 |       3485.82 |      4238.99 |
| CDU NE  |  260 | 40527 |  390 | 108623 | 40787 | 109013 |   650 | 149150 | 149800 |  176.98 |   40610 |  473.02 | 108540 | 6.24055 |  5.1487 |        49.7162 |   33.9757 |        0.006375 |  0.12828 | 0.012549 |  0.833356 |               0.235147 |            0.16705 |                   43.433 | 6374.58 |       3577.55 |      4339.12 |
| die ART | 3443 | 37344 | 8026 | 100987 | 40787 | 109013 | 11469 | 138331 | 149800 | 3122.74 | 37664.3 | 8346.26 | 100667 |  5.7311 | 5.45805 |        47.9751 |   31.7769 |        0.084414 | 0.030239 | 0.131774 |  0.197304 |               0.047397 |           0.042402 |                  145.988 | 84414.2 |       73624.2 |      76562.1 |
| …       |    … |     … |    … |      … |     … |      … |     … |      … |      … |       … |       … |       … |      … |       … |       … |              … |         … |               … |        … |        … |         … |                      … |                  … |                        … |       … |             … |            … |

Implementation note: `dump.keywords()` looks at all unigrams at the
corpus positions in match..matchend, and compares the frequencies of
their surface realizations with their marginal frequencies. Similarly,
`dump.collocates()` uses the the union of the corpus positions in
context..contextend, excluding all corpus positions containted in any
match..matchend.
