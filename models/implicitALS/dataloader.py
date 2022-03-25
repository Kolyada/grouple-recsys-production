import pandas as pd
from tqdm import tqdm
import numpy as np
np.random.seed(2020)



class Loader:
    def __init__(self, site_id, connect):
        self.site_id = site_id
        self.connect = connect
        self.top_popular = None

    def get_views(self):
        sql = """select element_id as item_id,rate,user_id 
            from bookmark 
            where site_id = %s and coalesce(rate,-1)>=0

            union all

            select element_id, positive*10 as rate,user_id
            from likes
            where site_id = %s"""

        con = self.connect.get_con()
        df = pd.read_sql(sql, con, params = (self.site_id,self.site_id))
        con.close()

        # cache actual top popular
        n = 70
        populars = df.groupby('item_id').count()['rate'].sort_values(ascending=False)
        populars = populars.index.tolist()
        self.top_popular = populars[:n]

        return df

    def get_top_popular(self):
        if self.top_popular is None:
            raise ValueError('Data havent been loaded yet. Cant return top popular')
        return self.top_popular

    def split_train_test(self, df, min_views, test_views):
        assert min_views > test_views
        
        df = self.get_views()
        # delete users with too much or too less data
        user_freqs = list(zip(df.user_id.drop_duplicates().sort_values().tolist(), 
                              df.groupby('user_id').count()['rate'].sort_index().to_list()))
        user_freqs = {item[0] : item[1] for item in user_freqs}

        max_views = float('inf')
        avg_users = [key if 
                         val >= min_views and \
                         val <= max_views
                         else None 
                     for key, val in user_freqs.items()]

        avg_users = list(filter(lambda x: x != None, avg_users))
        df = df[df.user_id.isin(avg_users)]
        
        # create session of every user
        users_sessions = df.groupby('user_id')['item_id rate'.split()].apply(lambda l: list(zip(
                                                                                    l['item_id'].tolist(), 
                                                                                    l['rate'].tolist()
                                                                                    )
                                                                                ))
        # fetch test_views views from every session for test and other for train
        test_k = test_views
        test_df = []
        train_df= []

        print('Splitting data for train/test')
        for user, history in tqdm(list(zip( users_sessions.index.tolist(), users_sessions.tolist() ))):
            views = [(user, item, rate) for item, rate in history]
            np.random.shuffle(views, )
            test_views = views[:test_k]
            train_views= views[test_k:]

            test_df += test_views
            train_df += train_views

        train_df = pd.DataFrame.from_records(train_df, columns='user_id item_id rate'.split())
        test_df = pd.DataFrame.from_records(test_df, columns='user_id item_id rate'.split())
        
        # return data
        return train_df, test_df