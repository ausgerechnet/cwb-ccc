"""readme.py: create tables for the README.md"""

import sys

import pyperclip

sys.path.append("/home/ausgerechnet/implementation/cwb-ccc/")
import ccc
from ccc import Corpora, Corpus

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


corpus = Corpus("GERMAPARL1386")
copymd(corpus.attributes_available, cut_off=None)
dump = corpus.query('[lemma="Arbeit"]', context_break='s')
copymd(dump.concordance())
copymd(dump.concordance(form='kwic', order='random'))
copymd(dump.collocates())
dump = corpus.query(s_query='text_party', s_values={'CDU', 'CSU'})
copymd(dump.keywords(order='conservative_log_ratio'))
