class UFA:

    def __init__(self, corpus, splits, p_query, s_query):
        for s in sorted(splits.keys()):
            corpus.subcorpus_from_s_att(s_query, splits[s])
            corpus.cqp()

    # create dumps from s_att
    # collect frequency lists for each dump
    # merge
    # add ams
