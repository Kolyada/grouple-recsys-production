import pandas as pd
from tqdm import tqdm
import numpy as np
np.random.seed(2020)

class Loader:
    def __init__(self, data_path):
        self.data_path = data_path  
        
    def get_views(self):
        df = pd.read_csv(self.data_path)
        return df
        
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