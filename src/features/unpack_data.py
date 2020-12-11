#!/usr/bin/env python

# unpacks sql dump to tables for every service (separately for dorama, manga and books)
# Data is unprocessed - only NULLs deleted

from read_dump import read_dump
import pandas as pd


# # Convert data
# full sql dump -> csv. Next load the data to the table
path_ptn = '/data/groupLe_recsys/raw/{name}-recommender-users.sql'
tmp_csv_ptn = '/data/groupLe_recsys/interim/{name}.csv'
csv_path_ptn = '/data/groupLe_recsys/processed/{name}/views.csv'
table_ptn = '{name}_recomm'

print('Reading sql dump')
read_dump(path_ptn.format(name='all'),
          table_ptn.format(name='all'),
          tmp_csv_ptn.format(name='all'),
          (0, 1, 2, 3, 4), 6)

print('Reading likes')
read_dump('/data/groupLe_recsys/raw/likes.sql',
          'likes',
          '/data/groupLe_recsys/raw/likes.csv',
          (0, 1, 2, 3), 4)
df_likes = pd.read_csv('/data/groupLe_recsys/raw/likes.csv', header=None, na_values='NULL')
df_likes.columns = 'item_id site_id user_id positive'.split()
df_likes['rate'] = df_likes.positive.apply(lambda p: 1 if str(p) == "_binary ''" else 0) * 10
df_likes['status'] = None
df_likes = df_likes.drop('positive', axis=1)
df_likes = df_likes.drop_duplicates()
print('Likes rows:', len(df_likes))



df = pd.read_csv(tmp_csv_ptn.format(name='all'), 
                 header=None, 
                 na_values='NULL')
df.columns = 'item_id site_id rate user_id status'.split()
df = df.append(df_likes)
print()
print('Dataset shape:', df.shape)


# # delete NA
print('na percent', round(df[df.rate.isna()].shape[0]/df.shape[0]*100, 2))
df = df[~df.rate.isna()]


site_ids = {'dorama': 5,
            'manga':  1,
            'mint': 2,
            'book':   6,
            'selfmanga': 3}
for site_name, site_id in site_ids.items():
    print('\nSeparating %s data' % site_name)
    sub_df = df[df.site_id == site_id]
    print('Saving to directory')
    sub_df.to_csv(csv_path_ptn.format(name=site_name), 
                  index=False, 
                  columns='item_id rate user_id'.split())
    
