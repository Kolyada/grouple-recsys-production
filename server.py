import sys
from tornado.ioloop import IOLoop
from tornado.web import Application
from yamlparams.utils import Hparam
from loguru import logger
from models.implicitALS.dataloader import Loader
from models.implicitALS.singleton import SharedModel
from http_utils import recs, updating, misc
from database.connect import Connect


def make_app():
    base_recs_config = dict(SharedModel=SharedModel,
                            config=config)
    urls = [('/topPopular', recs.TopPopularRecommendationHandler, dict(top_popular=top_popular, **base_recs_config)),
            ('/explorations', recs.ExplorationRecommendationsHandler, dict(explorations_categies=explorations_categies,
                                                                           **base_recs_config)),
            ('/recommend', recs.RecommendHandler, dict(top_popular=top_popular, **base_recs_config)),
            ('/similarItems', recs.SimilarItemsHandler, base_recs_config),
            ('/personalSimilarItems', recs.PersonalSimilarItemsHandler, base_recs_config),
            ('/rateItem', updating.RateItemHandler, base_recs_config),
            ('/recalculate', updating.RecalculateHandler, dict(loader=loader, **base_recs_config)),
            ('/healthcheck', misc.HealthcheckHandler)]
    return Application(urls)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise AttributeError('Use config name to define model config')
    cfg_path = sys.argv[1]
    config = Hparam(cfg_path)
    logger.add('logs/' + config.name + '-server.log')

    db_config = Hparam('/app/database/config.yaml')
    connect = Connect(db_config.user, db_config.password, db_config.host, db_config.database)
    loader = Loader(config.site_id,connect)
    
    updating.recalculate_handler.prepare_model(loader, config)

    explorations_categies = updating.load_explorations_model(config.explorations_path)
    top_popular = loader.get_top_popular()

    app = make_app()
    print("READY")
    app.listen(5000)
    IOLoop.instance().start()
