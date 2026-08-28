from fastapi import APIRouter
from app.schemas.common import AppInfo
from app.core.settings import get_settings
from app.api.v1.traces import traces_router_v1

router_api_v1 = APIRouter(prefix="/api/v1", tags=["api_v1"])

app_info = AppInfo(version=get_settings().version, name=get_settings().app_name)

@router_api_v1.get("/", response_model=AppInfo)
def root():
    return app_info


router_api_v1.include_router(traces_router_v1)