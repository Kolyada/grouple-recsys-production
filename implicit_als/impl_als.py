import pandas as pd
from tqdm import tqdm
from yamlparams.utils import Hparam
import sys


from metrics import mean_average_presision_k, hitrate_k, novelty, coverage
from dataloader import Loader
from preprocessor import Preprocessor
from model import ImplicitALS


if len(sys.argv) < 2:
    raise AttributeError('Use config name to define model config')
cfg_path = sys.argv[1] #'books_big_setting.yml'
print(cfg_path,' cfg')
config = Hparam(cfg_path)
loader = Loader(config.path)
preprocessor = Preprocessor()


print('Reading data')
df = loader.get_views()
# train_df = preprocessor.filter_zeros(train_df)
df = preprocessor.filter_lazy_users(df, 0)
train_df, test_df = loader.split_train_test(df, config.min_user_views, config.testing.samples)

train_df, test_df = preprocessor.filter_not_in_test_items(train_df, test_df)
preprocessor.build_mappers(train_df.append(test_df))

train_df.user_id  = train_df.user_id.apply(preprocessor.get_user_ix)
train_df.item_id  = train_df.item_id.apply(preprocessor.get_item_ix)
test_df.user_id   = test_df.user_id.apply(preprocessor.get_user_ix)
test_df.item_id   = test_df.item_id.apply(preprocessor.get_item_ix)
print('Train df contains', train_df.shape[0], 'items')


model = ImplicitALS(train_df, config)
model.fit()


## calc recommendations
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

