import pandas as pd
from tqdm import tqdm
from yamlparams.utils import Hparam
import sys

from metrics import mean_average_presision_k, hitrate_k, novelty, coverage
from dataloader import Loader
from preprocessor import Preprocessor
from model import ImplicitALS

# Read config
if len(sys.argv) < 2:
    raise AttributeError('Use config name to define model config')
cfg_path = sys.argv[1] #'books_big_setting.yml'
print('Using config ' + cfg_path)
config = Hparam(cfg_path)

loader = Loader(config.path)
preprocessor = Preprocessor()


print('Reading data')
df = loader.get_views()

print('Preprocessing')

df = preprocessor.filter_lazy_users(df, 0)
train_df, test_df = loader.split_train_test(df, config.min_user_views, config.testing.samples)

train_df, test_df = preprocessor.filter_not_in_test_items(train_df, test_df)
# copy for filtering already viewd items from recommendations later
orig_train = train_df.copy()

# make transforms and filters
train_df = preprocessor.filter_zeros(train_df)
train_df = preprocessor.cut_last_k_views(train_df, config.cut_last_k_views)

preprocessor.build_mappers(train_df.append(test_df))
train_df = preprocessor.map_ids(train_df)
test_df  = preprocessor.map_ids(test_df)
orig_train = preprocessor.map_ids(orig_train)





print('Train df contains', train_df.shape[0], 'items')


model = ImplicitALS(train_df, config, orig_train)
model.fit()


print('Calculating recommendations')
rec_items = []
uixs = []
stepsize = int(train_df.user_id.max()/config.testing.users_n)
for uix in tqdm(range(0, train_df.user_id.max()+1, stepsize)):
    uixs.append(uix)
    rec_items.append(model.recommend_user(uix, config.testing.samples))
gt = test_df[test_df.user_id.isin(uixs)].groupby('user_id')['item_id'].apply(list).tolist()

## calc metrics
for k in [config.testing.samples//2, config.testing.samples]:
    print('\nMAP@%d' % k,    round(mean_average_presision_k(rec_items, gt, k=k), 5))
    print('Hitrate@%d' % k,  round(hitrate_k(rec_items, gt, k=k), 4))
    print('Novelty@%d' % k,  round(novelty(rec_items, k), 2))
    print('Coverage@%d' % k, round(coverage(rec_items, train_df.item_id.drop_duplicates().tolist(), k), 5))

