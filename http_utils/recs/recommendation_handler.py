from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor
from webargs import fields
from webargs.tornadoparser import use_args
from loguru import logger
from http_utils.base import BaseHandler, MAX_THREADS


class RecommendHandler(BaseHandler):
    executor = ThreadPoolExecutor(MAX_THREADS)

    def initialize(self, **kwargs):
        self.top_popular = kwargs['top_popular']
        super().initialize(**kwargs)

    @run_on_executor()
    @use_args({'user_id': fields.Int(required=True),
               'n_recs': fields.Int(required=False, missing=5)}, location='querystring')
    def get(self, reqargs):
        # Recommends n_recs items to user with id user_id. Fallbacks to top popular recommendation

        # Process request arguments
        uid = reqargs['user_id']
        n_rec = reqargs['n_recs']

        model, mapper = self.get_model_and_mapper()

        # with open('logs/' + self.config.name + '-usage.log', 'a') as f:
        logger.info(f'recommend user_id={uid} n_recs={n_rec}')

        # Handle broken user_id
        make_item = lambda idx, score: {'itemId': idx,  'siteId':  self.config.site_id, 'score': score,
                                        'item_id': idx, 'site_id': self.config.site_id}
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
            recs = [make_item(idx, None) for idx in self.top_popular[:n_rec]]

        return self.write({'isTopPop': is_top_popular, 'items': recs, 'args': reqargs,
                           'is_top_pop': is_top_popular})
