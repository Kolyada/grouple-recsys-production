from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor
from webargs import fields
from webargs.tornadoparser import use_args
from loguru import logger
from http_utils.base import BaseHandler, MAX_THREADS


class SimilarItemsHandler(BaseHandler):
    executor = ThreadPoolExecutor(MAX_THREADS)

    @run_on_executor()
    @use_args({'item_id': fields.Int(required=True),
               'n_recs': fields.Int(required=False, missing=10)}, location='querystring')
    def get(self, reqargs):
        iid = reqargs['item_id']
        n_recs = reqargs['n_recs']

        model, mapper = self.get_model_and_mapper()

        with open('logs/' + self.config.name + '-usage.log', 'a') as f:
            logger.info(f'similarItems item_id={iid} n_recs={n_recs}')

        if mapper.get_item_ix(int(iid)) == -1:
            return self.write({'error': 'invalid item id', 'args': reqargs})

        iix = mapper.get_item_ix(int(iid))
        recs = model.similar_items(iix, n_recs, return_scores=True)

        # map to real ids
        make_item = lambda idx, score: {'itemId': idx,  'siteId': self.config.site_id, 'score': float(score),
                                        'item_id': idx, 'site_id': self.config.site_id}
        recs = [make_item(mapper.get_item_id(idx), score) for idx, score in recs]
        return self.write({'items': recs, 'args': reqargs})
