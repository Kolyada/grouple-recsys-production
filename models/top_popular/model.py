class TopPopular:
    def __init__(self, df, config):
        self.df = df
        self.config = config
        
        def check_index_uniformity(index):
            return index.min() == 0 and \
                   index.max() == len(index)-1
        def index_info(index):
            return 'index with min %d max %d count %d items' % (index.min(), index.max(), len(index))
        assert check_index_uniformity(df.user_id.drop_duplicates()), index_info(df.user_id.drop_duplicates())
        assert check_index_uniformity(df.item_id.drop_duplicates()), index_info(df.item_id.drop_duplicates())
        

    def fit(self):
        views_per_item = self.df.groupby('item_id').count()['rate']
        sorted_item_ids = views_per_item.sort_values(ascending=False).index.tolist()
        self.sorted_item_ids = sorted_item_ids
        
    
    def _recommend(self, k):
        return self.sorted_item_ids[:k]
    
        
    def recommend_user(self, user, k, return_scores=False):
        user_items = self.df[self.df.user_id == user]['item_id'].tolist()
        
        def delete_bookmarks(recs):
            # Since filter_already_liked doesnt work, filter by hand
            return list(set(recs).difference(set(user_items)))
        
        # filter liked until len(recs) != given k
        base_k = k
        k = int(min(1.5*k, k+0.1*len(user_items)))
        recs = self._recommend(k)
        recs = delete_bookmarks(recs)
                
        while len(recs) < base_k:
            k *= 2
            recs = self._recommend(k)
            recs = delete_bookmarks(recs)
                                    
        # return with or without scores
        if return_scores:
            rec = list(zip(recs, [0]*len(recs)))
        
        return recs