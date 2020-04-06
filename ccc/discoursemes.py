from ccc import Corpus

from pandas import merge


def discourseme_concordance(corpus_name, topic_query, query1, s_break,
                            s_meta=None, context=20, order='first',
                            cut_off=100, simplify=True):

    # init corpus
    corpus = Corpus(corpus_name, data_path=None, s_meta=s_meta)

    # query for topic items
    df_topic = corpus.query(topic_query, name='topic', s_break=s_break, context=context)

    # activate context regions (topic windows) as subcorpus
    df_topic.reset_index(inplace=True)
    df_topic = df_topic.set_index(['region_start', 'region_end'], drop=False)
    df_topic.drop([0, 1], inplace=True, axis=1)
    corpus.define_subcorpus(df_node=df_topic, name='topic', activate=True)

    # query for discourseme items on subcorpus
    df1 = corpus.query(query1, s_break=s_break, context=0, name='discourseme1')

    # re-format nodes of discourseme
    df1.reset_index(inplace=True)
    df1.drop(['region_start', 'region_end'], inplace=True, axis=1)
    df1.drop([0, 1], inplace=True, axis=1)

    # merge nodes; NB: this adds duplicates where necessary
    df_nodes = merge(df_topic, df1, on="s_id")

    # remove lines where items are too far away
    df_nodes['offset'] = df_nodes.apply(calculate_offset, axis=1)
    df_nodes = df_nodes[
        abs(df_nodes['offset']) <= context
    ]

    # implementation perfect until here
    # can be easily extended for more than one discourseme
    # what follows is a mere hack

    # re-format dataframe
    df_nodes.rename(
        columns={
            'match_x': 'match',
            'matchend_x': 'matchend',
            'match_y': 0,
            'matchend_y': 1
        },
        inplace=True
    )

    # TODO: HOW TO FORMAT DUPLICATES?
    # for now: drop duplicate rows
    df_nodes.drop_duplicates(subset=['match'], inplace=True)
    # print(df_nodes)
    # potentially with duplicate indices
    df_nodes.set_index(['match', 'matchend'], inplace=True)

    df_nodes.drop('offset', axis=1, inplace=True)
    conc = corpus.concordance(df_nodes)
    df = conc.lines(order=order, cut_off=cut_off, simplify=simplify)
    return df


def calculate_offset(row):
    """ calculates appropriate offset of y considering match and matchend of x """
    match_x = row['match_x']
    matchend_x = row['matchend_x']
    match_y = row['match_y']
    if match_x > match_y:
        offset = match_y - match_x
    elif matchend_x < match_y:
        offset = match_y - matchend_x
    else:
        offset = 0
    return offset
