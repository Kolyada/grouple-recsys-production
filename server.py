import sys
import asyncio
import aiohttp
from tornado.ioloop import IOLoop
from tornado.web import Application
from yamlparams.utils import Hparam
from loguru import logger
from models.implicitALS.dataloader import Loader
from models.implicitALS.singleton import SharedModel
from http_utils import recs, updating, misc
from database.connect import Connect

#DEVELOPMENT
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def make_app():
    base_recs_config = dict(SharedModel=SharedModel,
                            config=config)
    urls = [('/topPopular', recs.TopPopularRecommendationHandler, dict(loader=loader, **base_recs_config)),
            ('/explorations', recs.ExplorationRecommendationsHandler, dict(loader=loader,**base_recs_config)),
            ('/recommend', recs.RecommendHandler, dict(loader=loader, **base_recs_config)),
            ('/similarItems', recs.SimilarItemsHandler, base_recs_config),
            ('/personalSimilarItems', recs.PersonalSimilarItemsHandler, base_recs_config),
            ('/rateItem', updating.RateItemHandler, base_recs_config),
            ('/recalculate', updating.RecalculateHandler, dict(loader=loader, **base_recs_config)),
            ('/healthcheck', misc.HealthcheckHandler)]
    return Application(urls)

async def async_test(delay):
    await asyncio.sleep(delay)
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:5000/recalculate') as response:
            html = await response.text()
            print(html)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise AttributeError('Use config name to define model config')
    cfg_path = sys.argv[1]
    config = Hparam(cfg_path)
    logger.add('logs/' + config.name + '-server.log')

    db_config = Hparam('/app/database/config.yaml')
    connect = Connect(db_config.user, db_config.password, db_config.host, db_config.database)
    loader = Loader(config.site_id,connect)
    
    app = make_app()
    print("READY")
    app.listen(5000)

    IOLoop.instance().spawn_callback(async_test, delay = 30)
    IOLoop.instance().start()