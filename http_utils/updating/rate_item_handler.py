from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor
from webargs import fields
from webargs.tornadoparser import use_args
from loguru import logger
import pandas as pd
from http_utils.base import BaseHandler, MAX_THREADS


class RateItemHandler(BaseHandler):
    executor = ThreadPoolExecutor(MAX_THREADS)

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

        with open('logs/' + self.config.name + '-usage.log', 'a') as f:
            logger.info(f'rateItem item_id={iid} user_id={uid} pos={positive}')

        if all(map(lambda v: v is None, (positive, rate))):
            return self.write({'error': 'poitive or rate should be provided', 'args': reqargs})

        model, mapper = self.get_model_and_mapper()

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
        if len(user_views) % self.config.recalculate_user_every_n == 0:
            print('recalc user')
            model.update_user_data(uix, user_views)

        return self.write({'status': 'ok'})
