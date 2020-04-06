from ccc.discoursemes import discourseme_concordance


def test_discourseme_concordance():

    topic_query = '"Merkel" | "Seehofer" | "Steinmeier"'
    query1 = '"Regierung" | "Bundesregierung"'
    corpus_name = 'GERMAPARL_1114'
    s_break = 's'
    s_meta = 'text_id'

    df = discourseme_concordance(corpus_name, topic_query, query1,
                                 s_break, s_meta, cut_off=None,
                                 simplify=True)
    print(df)
