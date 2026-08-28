from fastapi import FastAPI, Depends
from app.schemas.common import AppInfo
from app.api.v1 import router_api_v1
from app.api.v2 import router_api_v2
from contextlib import asynccontextmanager
from app.db.v2.dependencies import get_dbpool
from app.core.logging import logging
from app.core.settings import get_settings
from app.core.settings_secret import get_settings_secret


logger = logging.getLogger(__name__)
settings = get_settings()

# import argparse

# parser = argparse.ArgumentParser()
# parser.add_argument("--config")
# args = parser.parse_args()

# init_settings(args.config)
# print("here")

@asynccontextmanager
async def lifespan(app: FastAPI):
    dbpool = get_dbpool()
    await dbpool.start(settings.app.database, get_settings_secret().database_password)
    # app.state.pool = dbpool.get_pool()
    yield
    await dbpool.stop()

app = FastAPI(lifespan=lifespan)

app_info = AppInfo(version=settings.version, name=settings.app_name)

@app.get("/", response_model=AppInfo)
def root():
    return app_info

app.include_router(router_api_v1)
app.include_router(router_api_v2)

