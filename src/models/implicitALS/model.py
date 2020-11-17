from scipy.sparse import csr_matrix
from implicit.als import AlternatingLeastSquares as ALS
from math import log


class ImplicitALS:
    def __init__(self, df, config, orig_df):
        df = self._calc_confidence_preference(df, config.alpha)
        self.orig_df = orig_df
        
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
        self.max_uix = max(users)
    
    
    def _calc_confidence_preference(self, df, alpha):
        # convert to confidence and preference
        # use split_rate as a threshold for bad and good classes.
        # to enlarge negative effect, use quadratic transform for rate
        split_rate = 6
        eps = 1e-4
        get_p = lambda v: 1 if v>split_rate else 0
        get_logp = lambda v: log(1+get_p(v/eps))
        df['rate'] = 1 + alpha*df.rate.apply(get_logp)
        return df
    
    
    def _delete_bookmarks(self, recs, seen_items):
        # Since filter_already_liked doesnt work, filter by hand
            for i, rec in enumerate(recs):
                if rec[0] in seen_items:
                    recs[i] = None
            recs = list(filter(lambda r: r is not None, recs))
            return recs
        
    
    def fit(self):
        self.model.fit(self.iu_mat)
        
        
    def recommend_user(self, user, k, return_scores=False):
        user_items = self.orig_df[self.orig_df.user_id == user].item_id.tolist()

        # filter liked until len(recs) != given k
        base_k = k
        k = int(min(1.5*k, k+0.1*len(user_items)))
        recs = self.model.recommend(user, self.ui_mat, N=k)
        recs = self._delete_bookmarks(recs, user_items)
                
        while len(recs) < base_k:
            k *= 2
            recs = self.model.recommend(user, self.ui_mat, N=k)
            recs = self._delete_bookmarks(recs, user_items)
                                
        recs = recs[:base_k]
        # return with or without scores
        if not return_scores:
            return [rec[0] for rec in recs]
        else:
            return recs
        
        
    def similar_items(self, item, k, return_scores=False):
        # Returns items that are similar to item with given id
        recs = self.model.similar_items(item, k+1)

        # avoid recommending same item
        recs = self._delete_bookmarks(recs, [item])
        recs = recs[:k]

        # return with or without scores
        if not return_scores:
            return [rec[0] for rec in recs]
        else:
            return recs
        
    
    def similar_items_for_user(self, item, user, k, return_scores=False):
        # Returns items that are similar to item with given id and havent
        # been seen by user with given id
        user_items = self.orig_df[self.orig_df.user_id == user].item_id.tolist()
        user_items += [item] # avoid recommending same item
        
        # filter liked until len(recs) != given k
        base_k = k
        k = int(min(1.5*k, k+0.1*len(user_items)))
        recs = self.model.similar_items(item, k)
        recs = self._delete_bookmarks(recs, user_items)
                
        while len(recs) < base_k:
            k *= 2
            recs = self.model.recommend(item, k)
            recs = self._delete_bookmarks(recs, user_items)
                                
        recs = recs[:base_k]
        # return with or without scores
        if not return_scores:
            return [rec[0] for rec in recs]
        else:
            return recs