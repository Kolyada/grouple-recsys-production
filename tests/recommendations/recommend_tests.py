import unittest
import requests as r
from yamlparams.utils import Hparam


class RecommendTests(unittest.TestCase):
    def test_method_available(self):
        resp = r.get(config.url + METHOD, params=params)
        self.assertTrue(resp.status_code == 200, resp)

    def test_response_is_json(self):
        resp = r.get(config.url + METHOD, params=params)
        self.assertTrue(isinstance(resp.json()['items'], list), resp)

    def test_all_recs_are_jsons(self):
        resp = r.get(config.url + METHOD, params=params)
        self.assertTrue(all(map(lambda item: isinstance(item, dict), resp.json()['items'])), resp)

    def test_count_param(self):
        _params = dict(params)
        params['n_recs'] = 3
        resp = r.get(config.url + METHOD, params=_params)
        resp = resp.json()['items']
        self.assertTrue(len(resp) == 3, len(resp))
        self.assertTrue(all(map(lambda item: 'itemId' in item, resp)), resp)
        self.assertTrue(all(map(lambda item: 'siteId' in item, resp)), resp)
        self.assertTrue(all(map(lambda item: 'itemId' in item, resp)), resp)
        self.assertTrue(all(map(lambda item: 'score' in item, resp)), resp)


config = Hparam('config.yaml')
METHOD = f'recommend'
params = {'user_id': config.user,
          'n_recs': 10}
