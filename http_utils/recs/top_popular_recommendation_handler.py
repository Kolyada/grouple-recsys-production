from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor
from webargs import fields
from webargs.tornadoparser import use_args
from loguru import logger
from http_utils.base import BaseHandler, MAX_THREADS


class TopPopularRecommendationHandler(BaseHandler):
    executor = ThreadPoolExecutor(MAX_THREADS)

    def initialize(self, **kwargs):
        self.loader = kwargs['loader']
        super().initialize(**kwargs)

    def get_top_popular(self, n):
        return self.loader.top_popular[:n]

    @run_on_executor()
    @use_args({'n_recs': fields.Int(required=False, missing=20)}, location='querystring')
    def get(self, reqargs):
        # Returns n top popular items. default n=20
        n_recs = reqargs['n_recs']

        with open('logs/' + self.config.name + '-usage.log', 'a') as f:
            logger.info(f'topPopular n_recs={n_recs}')

        make_item = lambda idx, score: {'itemId': idx,  'siteId': self.config.site_id, 'score': score,
                                        'item_id': idx, 'site_id': self.config.site_id}
        items = [make_item(item, None) for item in self.get_top_popular(n_recs)]

        return self.write({'isTopPop': 1, 'items': items, 'args': reqargs,
                           'is_top_pop': 1})
