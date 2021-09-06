import os
from datetime import datetime as dt
from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor
from models.implicitALS.model import ImplicitALS
from models.implicitALS.preprocessor import Preprocessor
from http_utils.base import BaseHandler, MIN_THREADS
from models.implicitALS.singleton import SharedModel


class RecalculateHandler(BaseHandler):
    executor = ThreadPoolExecutor(MIN_THREADS)

    def initialize(self, **kwargs):
        self.loader = kwargs['loader']
        super().initialize(**kwargs)

    @run_on_executor()
    def get(self):
        # Updates recommender model and top popular list
        # If current views table is too old, recalc dump and fetch fresh data from it
        curr_timestamp = int(dt.now().timestamp())
        last_modified = int(os.stat(self.config.path).st_mtime)
        if abs(curr_timestamp - last_modified) > 3600:  # older then 1 hour
            os.system(
                "mysqldump -uroot -proot recommend bookmark > /data/groupLe_recsys/raw/all-recommender-users.sql")
            os.system("mysqldump -uroot -proot recommend likes > /data/groupLe_recsys/raw/likes.sql")
            os.system("python3 ../src/features/unpack_data.py")

            prepare_model(self.loader, self.config)
        return self.write({'status': 'ok', 'lastDataUpdateTimestamp': last_modified})


def prepare_model(loader, config):
    preprocessor = Preprocessor()

    train_df = loader.get_views()
    train_df = preprocessor.filter_lazy_users(train_df, 0)
    # copy for filtering already viewd items from recommendations later
    orig_train = train_df.copy()

    # apply filters
    train_df = preprocessor.filter_zeros(train_df)
    train_df = preprocessor.cut_last_k_views(train_df, config.cut_last_k_views)

    preprocessor.build_mappers(train_df)
    train_df = preprocessor.map_ids(train_df)
    orig_train = preprocessor.map_ids(orig_train)
    print('Train df contains', train_df.shape[0], 'items')

    model = ImplicitALS(train_df, config, orig_train)
    model.fit()

    shared_model = SharedModel()
    shared_model.shared_model = model
    shared_model.mapper = preprocessor

    return
