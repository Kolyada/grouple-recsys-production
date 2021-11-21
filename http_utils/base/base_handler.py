from multiprocessing import cpu_count
from tornado.web import RequestHandler
from loguru import logger

MAX_THREADS = cpu_count()
SOME_THREADS = max(1, cpu_count() // 2)
MIN_THREADS = 1


class BaseHandler(RequestHandler):

    def initialize(self, SharedModel, config, **kwargs):
        self.SharedModel = SharedModel
        self.config = config
        print('adding')

    def get_model_and_mapper(self):
        mapper = self.SharedModel().mapper
        model = self.SharedModel().shared_model
        return model, mapper
