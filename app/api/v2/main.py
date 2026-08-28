from fastapi import FastAPI, Depends, APIRouter
from app.schemas.common import AppInfo
from app.core.settings import get_settings, Settings
from app.api.v2.traces import traces_router_v2

router_api_v2 = APIRouter(prefix="/api/v2", tags=["api_v2"])

app_info = AppInfo(version=get_settings().version, name=get_settings().app_name)

@router_api_v2.get("/", response_model=AppInfo)
def root():
    return app_info


router_api_v2.include_router(traces_router_v2)