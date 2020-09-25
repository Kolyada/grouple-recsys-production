


class Preprocessor:
    
    def build_mappers(self, views):
        self._build_items_mapper(views)
        self._build_users_mapper(views)
    
    
    def _build_users_mapper(self, views):
        users = views['user_id'].drop_duplicates().tolist()
        self.uid2ix = {uid : i for i, uid in enumerate(users)}
        self.ix2uid = {i : uid for i, uid in enumerate(users)}
        print('mapping users size', len(self.uid2ix.values()))
        
        
    def _build_items_mapper(self, views):
        items = views['item_id'].drop_duplicates().tolist()
        self.iid2ix = {iid : i for i, iid in enumerate(items)}
        self.ix2iid = {i : iid for i, iid in enumerate(items)}
        print('mapping items size', len(self.iid2ix.values()))
        
    
    def get_user_id(self, user_ix):
        return self.ix2uid[user_ix]
    def get_user_ix(self, user_id):
        return self.uid2ix[user_id]
    
    def get_item_id(self, item_ix):
        return self.ix2iid[item_ix]
    def get_item_ix(self, item_id):
#         print('req item', item_id, end='\t')
        return self.iid2ix[item_id]
    
    
    def filter_zeros(self, views):
        return views[views.rate != 0]
    
    def filter_lazy_users(self, views, min_user_rates):
        d = views.groupby('user_id').sum()['rate']
        lazy_users = d[d <= min_user_rates].index.to_list()
        return views[~views.user_id.isin(lazy_users)]
    
    def filter_not_in_test_items(self, views, test_views):
        test_items = test_views.item_id.drop_duplicates()
        views = views[views.item_id.isin(test_items)]        
        
        users = views.user_id.drop_duplicates()
        test_views = test_views[test_views.user_id.isin(users)]
        
        return views, test_views