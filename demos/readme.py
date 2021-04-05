"""readme.py: test all snippets and create tables for the README.md"""

import pyperclip
import sys
sys.path.append("/home/ausgerechnet/implementation/cwb-ccc/")
import ccc

print(ccc.__version__)


def copymd(df, cut_off=5):

    df = df.copy()

    # deal with multi-index
    # if isinstance(df.index, MultiIndex):
    if df.index.names != [None]:
        index_names = list(df.index.names)
        col_names = list(df.columns)
        df = df.reset_index()
        df = df[index_names + col_names]
        for i in index_names:
            df = df.rename({i: "*" + i + "*"}, axis=1)

    # escape underscores
    df = df.replace("_", r"\_", regex=True)
    df.columns = [c.replace("_", r"\_") if isinstance(c, str) else c for c in df.columns]

    # apply cut-off
    vis = False
    if cut_off is not None and cut_off < len(df):
        df = df.head(cut_off)
        vis = True

    df_str = df.to_markdown(index=False)

    # visualize cut-off via "..."
    if vis:
        df_str = df_str + "\n|" + ("|".join(["..."] * len(df.columns))) + "|"

    # make it collapsible
    output = "<details>\n<summary><code>placeholder</code></summary>\n<p>\n\n" + \
        df_str + "\n\n</p>\n</details>\n<br/>"

    # copy to clipboard
    pyperclip.copy(output)


from ccc import Corpora
corpora = Corpora()
print(corpora)
corpora.show()  # returns a dataframe

corpus = corpora.activate(corpus_name="GERMAPARL1386")
# select corpus
from ccc import Corpus
corpus = Corpus("GERMAPARL1386")
# print(corpus)
copymd(corpus.attributes_available, cut_off=None)


# QUERIES AND DUMPS #

query = r'"\[" ([word="[A-Z0-9]+.?"%d]+ "/"?)+ "\]"'
dump = corpus.query(query)
copymd(dump.df)

dump = corpus.query(
    cqp_query=query,
    context=5,
    context_break='s'
)

copymd(dump.df)

dump.set_context(context_left=5, context_right=10, context_break='s')

copymd(dump.breakdown(), cut_off=None)

# CONCORDANCING

lines = dump.concordance()
copymd(lines)

lines = dump.concordance(p_show=["word", "lemma"], s_show=["text_id"])
copymd(lines)

lines = dump.concordance(form='kwic')
copymd(lines)

lines = dump.concordance(p_show=['word', 'pos', 'lemma'], form='dataframe')
copymd(lines.iloc[0]['dataframe'], cut_off=None)

# ANCHORED QUERIES #

dump = corpus.query(
    r'@1[pos="NE"]? @2[pos="NE"] @3"\[" ([word="[A-Z0-9]+.?"%d]+ "/"?)+ @4"\]"',
    context=None, context_break='s', match_strategy='longest',
)

lines = dump.concordance(form='dataframe')
copymd(lines.iloc[0]['dataframe'], cut_off=None)

dump = corpus.query(
    r'@1[pos="NE"]? @2[pos="NE"] @3"\[" ([word="[A-Z0-9]+.?"%d]+ "/"?)+ @4"\]"',
    context=0, context_break='s', match_strategy='longest',
)
lines = dump.concordance(form='slots', slots={"name": [1, 2], "party": [3, 4]})
copymd(lines)

dump.correct_anchors({3: +1, 4: -1})
lines = dump.concordance(form='slots', slots={"name": [1, 2], "party": [3, 4]})
copymd(lines)


# COLLOCATES
dump = corpus.query(
  '[lemma="SPD"]',
  context=10, context_break='s'
)

collocates = dump.collocates()
copymd(collocates)


collocates = dump.collocates(['lemma', 'pos'], order='log_likelihood')
copymd(collocates)


# SUBCORPORA
dump = corpus.query('"SPD" expand to s')
dump = corpus.query_s_att("s")
# dump = corpus.query_s_att("np")
copymd(corpus.query('[lemma="sagen"]').breakdown(), cut_off=None)
corpus.query_s_att("text_party", values={"CDU", "CSU"}, name="Union")
corpus.activate_subcorpus("Union")
copymd(corpus.query('[lemma="sagen"]').breakdown(), cut_off=None)
corpus.activate_subcorpus()
print(corpus.subcorpus)

copymd(corpus.show_nqr())


# KEYWORDS
dump = corpus.query_s_att("text_party", values={"CDU", "CSU"}, name="Union")
copymd(dump.keywords(order="log_likelihood"))

copymd(dump.keywords(['lemma', 'pos'], order="log_likelihood"))
