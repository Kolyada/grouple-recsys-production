from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor
from webargs import fields
from webargs.tornadoparser import use_args
from loguru import logger
from http_utils.base import BaseHandler, MAX_THREADS


class ExplorationRecommendationsHandler(BaseHandler):
    executor = ThreadPoolExecutor(MAX_THREADS)

    def initialize(self, **kwargs):
        self.explorations_categies = kwargs['explorations_categies']
        super().initialize(**kwargs)

    def local2global_ids(self, expl_obj):
        # maps all items of explorational recs object to global ids
        _, mapper = self.get_model_and_mapper()

        mapped_expl_obj = dict()
        for cat in expl_obj.keys():
            mapped_expl_obj[cat] = [mapper.get_item_id(idx) for idx in expl_obj[cat]]
        return mapped_expl_obj

    def ids2items(self, expl_obj):
        make_item = lambda idx, score: {'itemId': idx,  'siteId':  self.config.site_id, 'score': score,
                                        'item_id': idx, 'site_id': self.config.site_id}

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

        model, mapper =  self.get_model_and_mapper()

        uid = reqargs['user_id']

        with open('logs/' + self.config.name + '-usage.log', 'a') as f:
            logger.info(f'explorations user_id={uid}')

        uix = mapper.get_user_ix(int(uid))
        if uix == -1:  # unknown user
            return self.write({'categories': self.cats2list(
                self.ids2items(
                    self.local2global_ids(self.explorations_categies)))})
        else:  # known user
            viewed_items = set(model.orig_df[model.orig_df.user_id == uix]['item_id'].tolist())
            # delete viewed items and empty categories from categories lists
            filtred_explorations = dict()
            for cat in self.explorations_categies.keys():
                # categories items are in local ids format. Dont forget to map to foreign ids when responsing
                filtred_items = [idx for idx in self.explorations_categies[cat] if idx not in viewed_items]
                if len(filtred_items):
                    filtred_explorations[cat] = filtred_items
            return self.write({'categories': self.cats2list(
                self.ids2items(
                    self.local2global_ids(filtred_explorations)))})
