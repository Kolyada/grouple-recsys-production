import json
import sys
import gc
import os
from datetime import datetime as dt
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from webargs import fields
from webargs.tornadoparser import use_args
from yamlparams.utils import Hparam

from models.implicitALS.dataloader import Loader
from models.implicitALS.model import ImplicitALS
from models.implicitALS.preprocessor import Preprocessor
from models.implicitALS.singleton import SharedModel


def get_mapper():
    shared_model = SharedModel()
    return shared_model.mapper


def get_model():
    shared_model = SharedModel()
    return shared_model.shared_model


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


def load_explorations_model(path):
    mapper = get_mapper()

    categories = json.load(open(path))
    # map data
    for cat in categories.keys():
        items = list(map(mapper.get_item_ix, categories[cat]))
        items = list(filter(lambda i: i != -1, items))  # filter unknown items
        categories[cat] = items
    return categories



time = lambda: '[%s]' % dt.now().strftime('%Y-%m-%d %H:%M:%S')


def make_app():
    urls = [('/topPopular', TopPopularHandler),
            ('/explorations', ExplorationsHandler, dict(SharedModel=SharedModel)),
            ('/rateItem', RateItemHandler, dict(SharedModel=SharedModel)),
            ('/recommend', RecommendHandler, dict(SharedModel=SharedModel)),
            ('/similarItems', SimilarItemsHandler, dict(SharedModel=SharedModel)),
            ('/recalculate', RecalculateHandler, dict(SharedModel=SharedModel, config=config, loader=loader)),
            ('/healthcheck', HealthcheckHandler)]
    return Application(urls)


class TopPopularHandler(RequestHandler):
    executor = ThreadPoolExecutor(8)

    @staticmethod
    def get_top_popular(n):
        return top_popular[:n]

    @run_on_executor()
    @use_args({'n_recs': fields.Int(required=False, missing=20)}, location='querystring')
    def get(self, reqargs):
        # Returns n top popular items. default n=20
        n_recs = reqargs['n_recs']

        with open('logs/' + config.name + '-usage.log', 'a') as f:
            f.write('[%s] /topPopular n_recs=%s\n' % (time(), str(n_recs)))

        make_item = lambda idx, score: {'itemId': idx, 'siteId': config.site_id, 'score': score,
                                        'item_id': idx, 'site_id': config.site_id}
        items = [make_item(item, None) for item in TopPopularHandler.get_top_popular(n_recs)]

        return self.write({'isTopPop': 1, 'items': items, 'args': reqargs,
                           'is_top_pop': 1})


class ExplorationsHandler(RequestHandler):
    executor = ThreadPoolExecutor(8)

    def initialize(self, SharedModel):
        self.SharedModel = SharedModel

    @staticmethod
    def local2global_ids(expl_obj):
        # maps all items of explorational recs object to global ids
        mapper = get_mapper()

        mapped_expl_obj = dict()
        for cat in expl_obj.keys():
            mapped_expl_obj[cat] = [mapper.get_item_id(idx) for idx in expl_obj[cat]]
        return mapped_expl_obj

    @staticmethod
    def ids2items(expl_obj):
        make_item = lambda idx, score: {'itemId': idx, 'siteId': config.site_id, 'score': score,
                                        'item_id': idx, 'site_id': config.site_id}

        items_expl_obj = dict()
        for cat in expl_obj.keys():
            items_expl_obj[cat] = [make_item(idx, None) for idx in expl_obj[cat]]
        return items_expl_obj

    @staticmethod
    def cats2list(expl_obj):
        explorations = [{'name': 'smf_%d' % i, 'items': v} for i, (k, v) in enumerate(expl_obj.items())]
        return explorations

    @run_on_executor()
    @use_args({'user_id': fields.Int(required=False, missing=-1)}, location='querystring')
    def get(self, reqargs):
        # Returns no-context recommendations based on items smartly groupped by genres
        # If user id provided, returns recommendations without already viewd items
        # explorations format
        # {category_name: [most_viewed_item1, ], }

        mapper = get_mapper()
        model = get_model()

        uid = reqargs['user_id']

        with open('logs/' + config.name + '-usage.log', 'a') as f:
            f.write('[%s] /explorations user_id=%s\n' % (time(), str(uid)))

        uix = mapper.get_user_ix(int(uid))
        if uix == -1:  # unknown user
            return self.write({'categories': ExplorationsHandler.cats2list(
                ExplorationsHandler.ids2items(
                    ExplorationsHandler.local2global_ids(explorations_categies)))})
        else:  # known user
            viewed_items = set(model.orig_df[model.orig_df.user_id == uix]['item_id'].tolist())
            # delete viewed items and empty categories from categories lists
            filtred_explorations = dict()
            for cat in explorations_categies.keys():
                # categories items are in local ids format. Dont forget to map to foreign ids when responsing
                filtred_items = [idx for idx in explorations_categies[cat] if idx not in viewed_items]
                if len(filtred_items):
                    filtred_explorations[cat] = filtred_items
            return self.write({'categories': ExplorationsHandler.cats2list(
                ExplorationsHandler.ids2items(
                    ExplorationsHandler.local2global_ids(filtred_explorations)))})


class RateItemHandler(RequestHandler):
    executor = ThreadPoolExecutor(8)

    def initialize(self, SharedModel):
        self.SharedModel = SharedModel

    @run_on_executor()
    @use_args({'user_id': fields.Int(required=True),
               'item_id': fields.Int(required=True),
               'positive': fields.Int(required=False, missing=None),
               'rate': fields.Number(required=False, missing=None)}, location='querystring')
    def post(self, reqargs):
        # saves information about user rate action
        # saves locally and writes out once per 30 minutes
        uid = reqargs['user_id']
        iid = reqargs['item_id']
        positive = reqargs['positive']
        rate = reqargs['rate']

        with open('logs/' + config.name + '-usage.log', 'a') as f:
            f.write('[%s] /rateItem item_id=%s user_id= %s pos=%s\n' % (time(), str(iid), str(uid), str(positive)))

        if all(map(lambda v: v is None, (positive, rate))):
            return self.write({'error': 'poitive or rate should be provided', 'args': reqargs})

        mapper = get_mapper()
        model = get_model()

        uid, iid = list(map(int, (uid, iid)))
        uix = mapper.get_user_ix(uid)
        iix = mapper.get_item_ix(iid)
        # rate is binary, system needs 0..10
        if positive is not None:
            rate = float(positive) * 10
        elif rate is not None:
            rate = float(rate) * 10
        else:
            return self.write({'error': 'rate or positive args should be provided'})

        if iix == -1:
            return self.write({'error': 'unknown item id', 'args': reqargs})

        if uix == -1:  # unknown user
            # add user to mapper and update his data
            mapper.add_user_id(uid)
            uix = mapper.get_user_ix(uid)
            model.add_user(uix, user_views=None)

        view = pd.DataFrame.from_records([(iix, rate, uix)], columns='item_id rate user_id'.split())
        model.orig_df = model.orig_df.append(view, ignore_index=True)
        # appending data to dataframe in runtime allows model to filter its recommendations
        # to aware already rated items. Nothing writes to filesystem cause of frequent model
        # recalculating. During recalculation, model pulls data from original database which
        # must contains all users rate actions

        # Every N user action its recommendations recalculates
        user_views = model.orig_df[model.orig_df.user_id == uix]
        if len(user_views) % config.recalculate_user_every_n == 0:
            print('recalc user')
            model.update_user_data(uix, user_views)

        return self.write({'status': 'ok'})


class RecommendHandler(RequestHandler):
    executor = ThreadPoolExecutor(8)

    def initialize(self, SharedModel):
        self.SharedModel = SharedModel

    @run_on_executor()
    @use_args({'user_id': fields.Int(required=True),
               'n_recs': fields.Int(required=False, missing=5)}, location='querystring')
    def get(self, reqargs):
        # Recommends n_recs items to user with id user_id. Fallbacks to top popular recommendation

        # Process request arguments
        uid = reqargs['user_id']
        n_rec = reqargs['n_recs']

        mapper = get_mapper()
        model = get_model()

        with open('logs/' + config.name + '-usage.log', 'a') as f:
            f.write('[%s] /recommend user_id=%s n_recs=%s\n' % (time(), str(uid), str(n_rec)))

        # Handle broken user_id
        make_item = lambda idx, score: {'itemId': idx, 'siteId': config.site_id, 'score': score,
                                        'item_id': idx, 'site_id': config.site_id}
        is_top_popular = 0
        recs = []
        try:
            uix = mapper.get_user_ix(int(uid))
            if uix == -1 or uix > model.max_uix:  # unknown to service or unknown to model
                raise KeyError
            # Calculate recommendations
            items = model.recommend_user(uix, n_rec, return_scores=True)
            # to real ids
            items = [(mapper.get_item_id(idx), score) for idx, score in items]
            # to response format
            recs = [make_item(idx, float(score)) for idx, score in items]
        except KeyError:
            is_top_popular = 1
            recs = [make_item(idx, None) for idx in TopPopularHandler.get_top_popular(n_rec)]

        return self.write({'isTopPop': is_top_popular, 'items': recs, 'args': reqargs,
                           'is_top_pop': is_top_popular})


class SimilarItemsHandler(RequestHandler):
    executor = ThreadPoolExecutor(8)

    def initialize(self, SharedModel):
        self.SharedModel = SharedModel

    @run_on_executor()
    @use_args({'item_id': fields.Int(required=True),
               'user_id': fields.Int(required=False, missing=-1),
               'n_recs': fields.Int(required=False, missing=10)}, location='querystring')
    def get(self, reqargs):
        iid = reqargs['item_id']
        n_recs = reqargs['n_recs']

        mapper = get_mapper()
        model = get_model()

        with open('logs/' + config.name + '-usage.log', 'a') as f:
            f.write('[%s] /similarItems item_id=%s n_recs=%s\n' % (time(), str(iid), str(n_recs)))

        if mapper.get_item_ix(int(iid)) == -1:
            return self.write({'error': 'invalid item id', 'args': reqargs})

        iix = mapper.get_item_ix(int(iid))

        # Similar items may be anonimized or filtred by user's views
        # If user id provided, return similar items that user havent seen
        uid = reqargs['user_id']
        uix = mapper.get_user_ix(int(uid))
        if uix != -1 and uix < model.max_uix:  # if model knows this user
            recs = model.similar_items_for_user(iix, uix, n_recs, return_scores=True)
        else:
            recs = model.similar_items(iix, n_recs, return_scores=True)

        # map to real ids
        make_item = lambda idx, score: {'itemId': idx, 'siteId': config.site_id, 'score': float(score),
                                        'item_id': idx, 'site_id': config.site_id}
        recs = [make_item(mapper.get_item_id(idx), score) for idx, score in recs]
        return self.write({'items': recs, 'args': reqargs})


class HealthcheckHandler(RequestHandler):
    def get(self):
        return self.write({'status': 'ok'})


class RecalculateHandler(RequestHandler):
    executor = ThreadPoolExecutor(1)

    def initialize(self, SharedModel, config, loader):
        self.SharedModel = SharedModel
        self.config = config
        self.loader = loader

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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise AttributeError('Use config name to define model config')
    cfg_path = sys.argv[1]
    config = Hparam(cfg_path)

    loader = Loader(config.path)
    prepare_model(loader, config)

    explorations_categies = load_explorations_model(config.explorations_path)
    top_popular = loader.get_top_popular()

    app = make_app()
    print("READY")
    app.listen(5000)
    IOLoop.instance().start()
