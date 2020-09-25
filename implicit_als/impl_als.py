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
loader = Loader(config.path.replace('views.csv', ''))
preprocessor = Preprocessor()


train_df = loader.get_train_views()
test_df = loader.get_test_views()

train_df = preprocessor.filter_zeros(train_df)
train_df = preprocessor.filter_lazy_users(train_df, 0)
train_df, test_df = preprocessor.filter_not_in_test_items(train_df, test_df)
preprocessor.build_mappers(train_df.append(test_df))

train_df.user_id  = train_df.user_id.apply(preprocessor.get_user_ix)
train_df.item_id = train_df.item_id.apply(preprocessor.get_item_ix)
test_df.user_id   = test_df.user_id.apply(preprocessor.get_user_ix)
test_df.item_id  = test_df.item_id.apply(preprocessor.get_item_ix)
print('Train df contains', train_df.shape[0], 'items')



# config = Hparam('./experiment.yml')
model = ImplicitALS(train_df, config)
model.fit()



## calc recommendations
rec_items = []
uixs = []
for uix in tqdm(range(0, train_df.user_id.max()+1,1)):
    uixs.append(uix)
    rec_items.append(model.recommend_user(uix, config.testing.test_samples))
gt = test_df[test_df.user_id.isin(uixs)].groupby('user_id')['item_id'].apply(list).tolist()

## calc metrics
for k in [config.testing.test_samples//2, config.testing.test_samples]:
    print('\nMAP@%d' % k,    round(mean_average_presision_k(rec_items, gt, k=k), 5))
    print('Hitrate@%d' % k,  round(hitrate_k(rec_items, gt, k=k), 4))
    print('Novelty@%d' % k,  round(novelty(rec_items, k), 2))
    print('Coverage@%d' % k, round(coverage(rec_items, train_df.item_id.drop_duplicates().tolist(), k), 5))

