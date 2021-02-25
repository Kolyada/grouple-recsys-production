import pandas as pd


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
        
    def map_ids(self, views):
        # maps user_id->user_ix and item_id->item_ix
        views.user_id  = views.user_id.apply(self.get_user_ix)
        views.item_id  = views.item_id.apply(self.get_item_ix)
        return views
    
    def get_user_id(self, user_ix):
        try: return self.ix2uid[user_ix]
        except KeyError: return -1
    def get_user_ix(self, user_id):
        try: return self.uid2ix[user_id]
        except KeyError: return -1
    def add_user_id(self, user_id):
        max_uix = max(list(self.uid2ix.values()))
        self.uid2ix[user_id] = max_uix+1
        self.ix2uid[max_uix+1] = user_id
    
    def get_item_id(self, item_ix):
        try: return self.ix2iid[item_ix]
        except KeyError: return -1
    def get_item_ix(self, item_id):
        try: return self.iid2ix[item_id]
        except KeyError: return -1
    
    
    def filter_zeros(self, views):
        return views[views.rate != 0]
    
    def filter_lazy_users(self, views, min_user_rates):
        d = views.groupby('user_id').sum()['rate']
        lazy_users = d[d <= min_user_rates].index.to_list()
        return views[~views.user_id.isin(lazy_users)]
    
    def filter_smalldata_users(self, views, min_user_rates):
        raise NotImplemented
    
    def filter_not_in_test_items(self, views, test_views):
        test_items = test_views.item_id.drop_duplicates()
        views = views[views.item_id.isin(test_items)]        
        
        users = views.user_id.drop_duplicates()
        test_views = test_views[test_views.user_id.isin(users)]
        
        return views, test_views
    
    def cut_last_k_views(self, views, k):
        cut = lambda row: list(row)[:k]
        to_records = lambda col1, col2: list(zip(col1, col2))

        cutted = views.groupby('user_id').apply(lambda row: to_records(cut(row['item_id']), 
                                                                       cut(row['rate'])))
        records = []
        for user, user_views in cutted.to_dict().items():
            for item, rate in user_views:
                records.append((item, rate, user))

        cutted_views = pd.DataFrame.from_records(records, columns='item_id rate user_id'.split())
        return cutted_views