#! /usr/bin/env python
# -*- coding: utf-8 -*-

""" frames.py: classes for dataframe types

### DumpFrame ###

=== CREATION ===

    dump_from_query
    === (match, matchend), 0*, .., 9* ===
    index <int, int> match, matchend: cpos
    columns <int> 0*, .., 9*: anchor points (optional; missing = -1)

    dump_from_s_att
    === (match, matchend), $s_cwbid, $s* ===
    index <int, int> match, matchend: cpos
    column <int> $s_cwbid: id
    column <str> $s: annotation (optional)
    no missing values

=== TRANSFORMATION (additional columns are preserved) ===

    dump2patt
    === (match, matchend), $p ===
    index <int, int> match, matchend: cpos
    column <str> $p: " "-joined tokens (match..matchend or regions of input columns)

    dump2satt
    === (match, matchend), $s_cwbid, $s_span, $s_spanend, $s* ===
    index <int, int> match, matchend: cpos
    column <int> $s_cwbid: id (missing = -1)
    column <int> $s_span: cpos (missing = -1)
    column <int> $s_spanend: cpos (missing = -1)
    column <str> $s*: annotation (optional)

    dump2context
    === (match, matchend), contextid*, context, contextend
        $s_cwbid*, $s_span*, $s_spanend* ===
    index <int, int> match, matchend: cpos
    column <int> contextid: of id (optional; duplicate of $s_cwbid)
    column <int> context: cpos
    column <int> contextend: cpos
    column <int> $s_cwbid: id (optional; missing = -1)
    column <int> $s_span: cpos (missing = -1)
    column <int> $s_spanend: cpos (missing = -1)

=== QUERY ===

    query
    === (match, matchend), 0*, ..., 9*, contextid*, context*, contextend* ===
    index <int, int> match, matchend: cpos
    columns <int> 0*, .., 9*: anchor points (optional; missing = -1)
    column <int> contextid: of id (optional)
    column <int> context: cpos (optional)
    column <int> contextend: cpos (optional)

    query_s_att
    === (match, matchend), $s_cwbid, $s* ===
    index <int, int> match, matchend: cpos
    column <int> $s_cwbid: id
    column <str> $s: annotation (optional)
    no missing values


### ConcFrame ###

    __init__ enforces context, contextend columns (optional = match, matchend)

    === (match, matchend) context contextend ===

    simple
    === (match, matchend) $p ===

    kwic
    === (match, matchend) $p_left, $p_node, $p_right ===

    slots
    === (match, matchend) $p_$slot[0]..$slot[1] ===

    dict
    === (match, matchend) dict ===

    dataframe
    === (match, matchend) dataframe ===

### FreqFrame ###

    returned by
    - Counts.cpos()
    - Counts.dump()
      + 1 counts._cpos2patts + counts.count_items
      + 2 write dump to tempfile + counts.cwb_scan_corpus
    - Counts.matches()
      + 1 cqp.count
      + 2 cqp.tabulate + counts.count_items
      + 3 cqp.dump + counts.cwb_scan_corpus
    - Counts.mwus()
      + 1 for each query: cqp.size
      + 2 for "|".joined-query: counts.dump
      + 3 for "|".joined-query: counts.matches
    - Corpus.marginals()

    == (item) freq, p_atts[0]*, p_atts[1]*, ... ==


### ScoreFrame ###

    returned by score_counts()

    == (item) freq, O11*..O22*, E11*..E22*, AM1, AM2, ... ==



### DumpsFrame ###

=== CREATION ===

    topic (= dump)
    === (match, matchend) contextid context contextend ===
    note that the contexts may overlap and even include other matches

    complex node via cluster id
    === (match, matchend) context contextend contextid match matchend offset ===

    second discourseme (= dump)
    === (match1, match1end) contextid ===

    here: discourseme co-occurs with topic, iff discourseme in context(topic)
    here: context(topic) for second-order collocation analysis
    other possibilities: context(topic & discourseme), c(t | d), ...
    left_join via contextid

    === (match, matchend) context contextend contextid match1 match1end offset1 ===

    normal row
    == (m, me) c ce ci m1 m1e o1 ==
       (5,  6) 0 10  1  2   2 -3
    surface realization of topic on cpos 5-6, discourseme 1 on cpos 2

    duplicate rows for several co-occurrences, e.g.
    == (m, me) c ce ci m1 m1e o1 ==
       (5,  6) 0 10  1  2   2 -3
       (5,  6) 0 10  1  8   8 +2
    another occurrence of discourseme 1 on cpos 8

    slicing further discoursemes:

    === (m, me) c ce ci m1 m1e m2 m2e m3 m3e ===

        (5,  6) 0 10  1  2   2 -3 3 3 -2 0 0 -5
        (5,  6) 0 10  1  8   8 +2 3 3 -2 0 0 -5
        (5,  6) 0 10  1  2   2 -3 7 7 +2 0 0 -5
        (5,  6) 0 10  1  8   8  +2 7 7 +2 0 0 -5


### CoocFrame ###





"""
