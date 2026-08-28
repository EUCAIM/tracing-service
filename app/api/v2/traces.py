from app.core.auth import auth_dependency, require_role, UserRoles, User
from app.services.v2.dependencies import get_traces_datasets_manager, TracesDatasetsManager
from app.schemas.v2.traces.requests import TraceTypeRequest
from app.schemas.v2.traces.responses import TraceDatasetResponse
from app.schemas.common import Page, CreateTraceResponse
from app.core.exceptions import UnhandledTypeException, DataIntegrityException, NotFoundException
from app.core.settings import get_settings

import logging
from fastapi import Depends, APIRouter, HTTPException
logger = logging.getLogger(__name__)

settings = get_settings()

traces_router_v2 = APIRouter(prefix="/traces")

@traces_router_v2.get("/", tags=["traces"], response_model=Page)
async def get_traces(limit: int | None = settings.app.api.v2.default_traces_limit, 
                    offset: int | None = 0, datasetId: str | None = None, user: User = Depends(auth_dependency),
                    manager: TracesDatasetsManager = Depends(get_traces_datasets_manager)):
    try:
        filter_fields: dict[str, str | int | bool] = {}
        if datasetId is not None:
            filter_fields["dataset_id"] = datasetId
        traces,  total = await manager.get_traces(offset=offset, limit=limit, filter_fields=filter_fields)
        return Page(total=total, data=traces, position=offset, size=limit)
    except (UnhandledTypeException, DataIntegrityException) as e:
        logger.error(e, exc_info=True)
        raise HTTPException(500, "Internal server error")

@traces_router_v2.get("/{trace_id}", tags=["trace"], response_model=TraceDatasetResponse)
async def get_traces(trace_id: str, user: User = Depends(auth_dependency),
                    manager: TracesDatasetsManager = Depends(get_traces_datasets_manager)):
    try:
        trace = await manager.get_trace(trace_id)
        logger.info(trace)
        return trace
    except (UnhandledTypeException, DataIntegrityException) as e:
        logger.error(e, exc_info=True)
        raise HTTPException(500, "Internal server error")
    except NotFoundException as e:
        logger.error(e, exc_info=True)
        raise HTTPException(404, str(e))


@traces_router_v2.post("/", tags=["traces"], status_code=200, response_model=CreateTraceResponse)
async def post_trace(trace_request: TraceTypeRequest, user: User = Depends(require_role(UserRoles.WRITER.value)), 
                    manager: TracesDatasetsManager = Depends(get_traces_datasets_manager)):
    id = await manager.add(caller_id=user.user_id, trace=trace_request)
    return CreateTraceResponse(id)

# traces_router_v2.include_router(datasets_router)