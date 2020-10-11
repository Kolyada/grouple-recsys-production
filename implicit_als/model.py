from scipy.sparse import csr_matrix
from implicit.als import AlternatingLeastSquares as ALS


class ImplicitALS:
    def __init__(self, df, config):
        df = self._calc_confidence_preference(df, config.alpha)
        
        def check_index_uniformity(index):
            return index.min() == 0 and \
                   index.max() == len(index)-1
        def index_info(index):
            return 'index with min %d max %d count %d items' % (index.min(), index.max(), len(index))
        assert check_index_uniformity(df.user_id.drop_duplicates()), index_info(df.user_id.drop_duplicates())
        assert check_index_uniformity(df.item_id.drop_duplicates()), index_info(df.item_id.drop_duplicates())
        
        users = df.user_id.to_list()
        items = df.item_id.to_list()
        rate  = df.rate.to_list()
        shape = (len(set(items)), len(set(users)))
        self.iu_mat = csr_matrix((rate, (items, users)), 
                                 shape=shape)
        self.ui_mat = self.iu_mat.transpose()
        
        self.model = ALS(factors=config.factors, 
                         calculate_training_loss=True, 
                         iterations=config.iterations, 
                         regularization=config.regularization)
    
    
    def _calc_confidence_preference(self, df, alpha):
        # convert to confidence and preference according to paper
        calc_preference = lambda v: 1 if v>6 else 0
        df['metric'] = df.rate.apply(calc_preference)
        df.metric = df.metric * alpha * df.rate
        df.rate = df.metric
        df = df.drop('metric', axis=1)
        return df
    
    
    def fit(self):
        self.model.fit(self.iu_mat)
        
        
    def recommend_user(self, user, k, return_scores=False):
        user_items = set(self.ui_mat.getrow(user).indices)
        def delete_bookmarks(recs):
            # Since filter_already_liked doesnt work, filter by hand
            for i, rec in enumerate(recs):
                if rec[0] in user_items:
                    recs[i] = None
            recs = list(filter(lambda r: r is not None, recs))
            return recs
        
        # filter liked until len(recs) != given k
        base_k = k
        k = int(min(1.5*k, k+0.1*len(user_items)))
        recs = self.model.recommend(user, self.ui_mat, N=k)
        recs = delete_bookmarks(recs)
                
        while len(recs) < base_k:
            k *= 2
            with open('./n_recs.log', 'a') as f:
                f.write('recommending u={} k={}\n'.format(user, k))
            recs = self.model.recommend(user, self.ui_mat, N=k)
            recs = delete_bookmarks(recs)
                                    
        # return with or without scores
        if not return_scores:
            return [rec[0] for rec in recs]
        else:
            return recs