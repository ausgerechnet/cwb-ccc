from ccc import Corpus


def test_kwic_export():
    corpus = Corpus('BREXIT_EUROPA_DE', s_meta='tweet_id')
    corpus.query('[lemma="Volk*"] | [lemma="Bürger*"] | [lemma="Wähler*"]', context=None, s_break='tweet')
    conc = corpus.concordance()
    lines = list(conc.lines(cut_off=None).values())

    with open("concordance-lines.tsv", "wt") as f:
        f.write("\t".join(['tweet_id', 'left', 'match', 'right']) + '\n')
        for line in lines:
            left = line.loc[line['offset'] < 0]
            match = line.loc[line['offset'] == 0]
            right = line.loc[line['offset'] > 0]
            idx = conc.meta.loc[match.index]['s_id'].values[0]

            left = " ".join(list(left['word'].values))
            match = " ".join(list(match['word'].values))
            right = " ".join(list(right['word'].values))

            row = "\t".join([idx, left, match, right])
            f.write(row + "\n")
