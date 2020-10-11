#!/usr/bin/env python

# unpacks sql dump to tables for every service (separately for dorama, manga and books)
# Data is unprocessed - only NULLs deleted

from implicit_als.read_dump import read_dump
import pandas as pd
import matplotlib.pyplot as plt


# # Convert data
# full sql dump -> csv. Next load the data to the table
path_ptn = '/data/groupLe_recsys/{name}/raw/{name}-recommender-users.sql'
csv_path_ptn = '/data/groupLe_recsys/{name}/views.csv'
table_ptn = '{name}_recomm'

print('Reading sql dump')
read_dump(path_ptn.format(name='all'), 
          table_ptn.format(name='all'), 
          csv_path_ptn.format(name='all'))


df = pd.read_csv(csv_path_ptn.format(name='all'), 
                 header=None, 
                 na_values='NULL')
df.columns = 'item_id site_id rate user_id status'.split()
print()
print('Dataset shape:', df.shape)


# # delete NA
print('na percent', round(df[df.rate.isna()].shape[0]/df.shape[0]*100, 2))
df = df[~df.rate.isna()]


site_ids = {'dorama': 5,
            'manga':  1,
            'mint': 2,
            'book':   6}
for site_name, site_id in site_ids.items():
    print('\nSeparating %s data' % site_name)
    sub_df = df[df.site_id == site_id]
    print('Saving to directory')
    sub_df.to_csv(csv_path_ptn.format(name=site_name), 
                  index=False, 
                  columns='item_id rate user_id'.split())
    
