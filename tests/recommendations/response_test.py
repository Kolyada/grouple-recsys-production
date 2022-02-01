import requests as r
import unittest
from yamlparams import Hparam


class ResponseTest(unittest.TestCase):
    def test_recommendations(self):
        resp = r.get(config.url + METHOD, params=params)
        self.assertTrue(resp.status_code == 200, resp)


def run():
    unittest.main()


config = Hparam('config.yaml')
METHOD = f'recommend'
params = {'user_id': config.user,
          'n_recs': 10}
