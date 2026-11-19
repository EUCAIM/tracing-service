from fastapi import FastAPI, Depends, APIRouter
from app.core.auth import auth_dependency, require_role, UserRoles
from app.services.v1.dependencies import get_traces_manager
from app.schemas.v1.requests import Base as BaseTraceRequest

traces_router_v1 = APIRouter(prefix="/traces")

@traces_router_v1.get("/", tags=["traces"])
async def get_traces(user = Depends(auth_dependency), manager = Depends(get_traces_manager)):
    return 

@traces_router_v1.post("/")
def post_trace(body = BaseTraceRequest, user = Depends(require_role(UserRoles.WRITER)), manager = Depends(get_traces_manager)):
    return ["alice", "bob"]