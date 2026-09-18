from app.core.auth import auth_dependency, require_role, UserRoles, User
from app.services.v2.dependencies import get_traces_datasets_manager, TracesDatasetsManager
from app.schemas.v2.traces.requests import TraceTypeRequest
from app.schemas.v2.traces.responses import TraceDatasetResponse, CreateTraceResponse
from app.schemas.common import Page
from app.core.exceptions import UnhandledTypeException, DataIntegrityException, NotFoundException
from app.core.settings import get_settings

import logging
from fastapi import Depends, APIRouter, HTTPException, Path, Query, Body
logger = logging.getLogger(__name__)

settings = get_settings()

_MAX_NUM_TRACES_PAGE = 1000

traces_router_v2 = APIRouter(prefix="/traces")

@traces_router_v2.get("/", tags=["traces"], response_model=Page)
async def get_traces(limit: int = Query(settings.app.api.v2.default_traces_limit, ge=1, le=_MAX_NUM_TRACES_PAGE, description="The max number of traces requested to be returned by this call."), 
                    skip: int = Query(0, ge=0, description="Number of items to skip for pagination."), 
                    datasetId: str | None = Query(None, description="The ID of the dataset that the traces must refer (at least once if the trace references multiple IDs)"), 
                    user: User = Depends(auth_dependency),
                    manager: TracesDatasetsManager = Depends(get_traces_datasets_manager)):
    """
    Returns a page of traces sorted descending by their creation date

    Parameters:
    ---
    limit: int | None
        Query parameter. The max number of traces requested to be returned by this call. 
        Default from SETTINGS.app.api.v2.default_traces_limit.
        Max from variable _MAX_NUM_TRACES_PAGE.
    offset: int | None
        Query parameter. Number of items to skip for pagination. 
        Default 0.
    dataset_id: str | None
        Query parameter. The ID of the dataset that the traces must refer (at least once if the trace references multiple IDs).
        Default None.
    user: User
        Dependency. The user information obtained after successful authentication.
    manager: TracesDatasetsManager
        Dependency. The manager of traces.
    
    """
    try:
        filter_fields: dict[str, str | int | bool] = {}
        if datasetId is not None:
            filter_fields["dataset_id"] = datasetId
        traces,  total = await manager.get_traces(skip=skip, limit=limit, filter_fields=filter_fields)
        return Page(total=total, data=traces, skip=skip, limit=limit)
    except (UnhandledTypeException, DataIntegrityException) as e:
        logger.error(e, exc_info=True)
        raise HTTPException(500, "Internal server error")

@traces_router_v2.get("/{trace_id}", tags=["trace"], response_model=TraceDatasetResponse)
async def get_traces(trace_id: str = Path(..., description="The ID of the trace that the user requests."),
                    user: User = Depends(auth_dependency),
                    manager: TracesDatasetsManager = Depends(get_traces_datasets_manager)):
    """
    Returns the trace with the requested ID, or not found if one doesn't exist

    Parameters:
    ---
    trace_id: str
        Path parameter. The ID of the trace that the user requests.
    user: User
        Dependency. The user information obtained after successful authentication.
    manager: TracesDatasetsManager
        Dependency. The manager of traces.

    Returns:
        The full requested trace (depending on trace type, the fields can vary).
    
    """
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
async def post_trace(trace_request: TraceTypeRequest = Body(..., description="The user request that contains the information for the trace they want to add."),
                    user: User = Depends(require_role(UserRoles.WRITER)), 
                    manager: TracesDatasetsManager = Depends(get_traces_datasets_manager)):
    """
    Add a trace to the system.

    Parameters:
    ---
    trace_request: TraceTypeRequest
        Body parameter. The user request that contains the information for the trace they want to add.
    user: User
        Dependency. The user information obtained after successful authentication.
    manager: TracesDatasetsManager
        Dependency. The manager of traces.

    Returns
    ---
        A dict with one field, the ID of the newly created trace
    
    """
    response = await manager.add(caller_id=user.user_id, trace=trace_request)
    return response