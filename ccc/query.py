class QueryResult:
    """ result of a query """

    def __init__(self, df_dump, parameters, corpus, subcorpus,
                 name_cache=None):

        # parameters = {
        #     'query': query,
        #     'context_left': context_left,
        #     'context_right': context_right,
        #     's_context': s_context,
        #     's_meta': s_meta,
        #     'match_strategy': match_strategy
        # }

        self.dump = df_dump
        self.parameters = parameters
        self.corpus = corpus
        self.subcorpus = subcorpus
        self.name_cache = name_cache
        self.size = len(self.dump)

    def __str__(self):
        desc = 'query result on corpus "%s" ("%s") with %d matches' % (
            self.corpus, self.subcorpus, self.size
        )
        if self.name_cache is not None:
            desc += '\nresult can be accessed via cache: ""'
        return desc
