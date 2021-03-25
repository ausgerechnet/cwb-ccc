"""test all snippets and create tables for the README.md"""

from pandas import MultiIndex
import pyperclip
import sys
sys.path.append("/home/ausgerechnet/implementation/cwb-ccc/")
import ccc

print(ccc.__version__)


def copymd(df, cut_off=None):

    df = df.copy()

    # deal with multi-index
    if isinstance(df.index, MultiIndex):
        index_names = list(df.index.names)
        col_names = list(df.columns)
        df = df.reset_index()
        df = df[index_names + col_names]
        for i in index_names:
            df = df.rename({i: "*" + i + "*"}, axis=1)

    # escape underscores
    df = df.replace("_", r"\_", regex=True)

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
df = corpus.attributes_available
copymd(df)

query = r'"\[" ([pos="NE"] "/"?)+ "\]"'
dump = corpus.query(query)
copymd(dump.df.head())

dump = corpus.query(
    cqp_query=query,
    context=5,
    context_break='s'
)

copymd(dump.df, cut_off=5)

dump.set_context(context_left=5, context_right=10, context_break='s')

copymd(dump.breakdown())
