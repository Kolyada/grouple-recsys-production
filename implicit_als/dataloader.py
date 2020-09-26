import pandas as pd



class Loader:
    def __init__(self, data_path):
        self.data_path = data_path
        self.global_path = self._generalized_path(data_path)
        
        
    def get_train_views(self):
        return pd.read_csv(self.data_path + 'train/views.csv')
    
    def get_test_views(self):
        return pd.read_csv(self.data_path + 'test/views.csv')
    
    def get_views(self):
        df1 = pd.read_csv(self.data_path + 'train/views.csv')
        df2 = pd.read_csv(self.data_path + 'test/views.csv')
        return df1.append(df2).sort_values(by='user_id')
    
    def get_views_from_file(self, path):
        df = pd.read_csv(path, header=None)
        df.columns = 'item_id rate user_id'.split()
        df = df[~df.rate.isna()]
        return df
    
    
    def _generalized_path(self, path):
        s1 = '/30k'
        s2 = '/900k'
        return path.replace(s1, '').replace(s2, '')
    
    def get_users(self):
        return pd.read_csv(self.global_path + 'users.csv')
    
    def get_items(self):
        return pd.read_csv(self.global_path + 'items.csv')