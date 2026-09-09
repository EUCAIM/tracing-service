from fastapi import FastAPI
from app.schemas.common import AppInfo
from app.api.v2 import router_api_v2
from contextlib import asynccontextmanager
from app.db.v2.dependencies import get_dbpool
from app.core.logging import logging
from app.core.settings import get_settings
from app.core.settings_secret import get_settings_secret


logger = logging.getLogger(__name__)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    dbpool = get_dbpool()
    await dbpool.start(settings.app.database, get_settings_secret().database_password)
    yield
    await dbpool.stop()

app = FastAPI(lifespan=lifespan)

app_info = AppInfo(version=settings.version, name=settings.app_name)

@app.get("/", response_model=AppInfo)
def root():
    return app_info

app.include_router(router_api_v2)
