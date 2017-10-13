from aiohttp import web
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING

from turg.config import Config
from turg.logger import getLogger
from turg.views import (
    voxels,
    websocket,
)

logger = getLogger(__name__)
config = Config()


def create_app():
    app = web.Application()

    for view in (voxels, websocket):
        routes = view.factory(app)
        routes = routes if isinstance(routes, list) else [routes]
        for route in routes:
            app.router.add_route(**route)

    return app


async def on_start(app):
    client = AsyncIOMotorClient(config.mongodb_uri)
    app['db_client'] = client
    app['db'] = client.get_default_database()  # defined in mongodb_uri
    app['websockets'] = []
    app['players'] = {}
    await app['db'].data.create_index([('x', ASCENDING), ('y', ASCENDING)])


async def on_shutdown(app):
    app['db_client'].close()

    for ws in app['websockets']:
        await ws.close()


app = create_app()
app.on_startup.append(on_start)
app.on_shutdown.append(on_shutdown)
