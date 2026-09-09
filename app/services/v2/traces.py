from app.services.traces import AbstractTracesManager
from app.db.v2.traces import TracesRepo
from app.models.v2.traces import CreateDataset, UseDataset, UpdateDataset, TraceResource, BaseTrace
from app.schemas.v2.traces.requests import DatasetCreateRequest, DatasetUseRequest, DatasetUpdateRequest, TraceRequest
from app.schemas.v2.traces.responses import BaseResponse, CreateDatasetResponse, UseDatasetResponse, UpdateDatasetResponse
from app.schemas.v2.traces.common import CreateDatasetResource
from app.core.exceptions import UnhandledTypeException

import datetime
import uuid
import logging
import json
logger = logging.getLogger(__name__)

class TracesDatasetsManager(AbstractTracesManager):

    def __init__(self, repository: TracesRepo):
        super().__init__()
        self.repository = repository

    async def add(self, caller_id: str, trace: TraceRequest) -> uuid.UUID:
        id = uuid.uuid4()
        created_at = self.get_now()
        if isinstance(trace, DatasetCreateRequest):
            resources = []
            for r in trace.resources:
                resources.append(TraceResource(id=r.id, content_hash=r.contentHash, 
                                                content_hash_type=r.contentHashType).model_dump())
            await self.repository.add(CreateDataset(
                id=id,
                caller_id=caller_id,
                user_id=trace.userId,
                created_at=created_at,
                datasets_ids=json.dumps([trace.datasetId]),
                create_resources=json.dumps(resources),
                
            ))
        elif isinstance(trace, DatasetUseRequest):
            await self.repository.add(UseDataset(
                id=id,
                caller_id=caller_id,
                user_id=trace.userId,
                created_at=created_at,
                datasets_ids=json.dumps(trace.datasetsIds),
                use_tool_name=trace.toolName,
                use_tool_version=trace.toolVersion
            ))
        elif isinstance(trace, DatasetUpdateRequest):
            await self.repository.add(UpdateDataset(
                id=id,
                caller_id=caller_id,
                user_id=trace.userId,
                created_at=created_at,
                datasets_ids=json.dumps([trace.datasetId]),
                update_details=trace.details
            ))
        else:
            raise UnhandledTypeException(f"Unhandled request type {type(trace).__name__}")
        return id

    async def get_trace(self, trace_id: str) -> BaseResponse:
        trace: BaseTrace = await self.repository.get_trace(trace_id)
        return self.get_trace_response(trace)

    async def get_traces(self, limit: int, offset: int, filter_fields: dict[str, str | int | bool]) -> tuple[list[BaseResponse], int]:
        traces, total = await self.repository.get_traces(limit, offset, filter_fields)
        return [self.get_trace_response(t) for t in traces], total

    def get_trace_response(self, trace: BaseTrace) -> BaseResponse:
        if isinstance(trace, CreateDataset):        
            return CreateDatasetResponse(
                id=trace.id,
                callerId=trace.caller_id,
                createdAt=trace.created_at,
                version=trace.trace_version,
                userId=trace.user_id,
                datasetId=json.loads(trace.datasets_ids)[0],
                resources=[CreateDatasetResource(id=r["id"], contentHash=r["content_hash"], 
                                                contentHashType=r["content_hash_type"]) for r in json.loads(trace.create_resources)]
            )
        elif isinstance(trace, UseDataset):
            return UseDatasetResponse(
                id=trace.id,
                callerId=trace.caller_id,
                createdAt=trace.created_at,
                version=trace.trace_version,
                userId=trace.user_id,
                datasetsIds=json.loads(trace.datasets_ids),
                toolName=trace.use_tool_name,
                toolVersion=trace.use_tool_version
            )
        elif isinstance(trace, UpdateDataset):
            return UpdateDatasetResponse(
                id=trace.id,
                callerId=trace.caller_id,
                createdAt=trace.created_at,
                version=trace.trace_version,
                userId=trace.user_id,
                datasetId=json.loads(trace.datasets_ids)[0],
                details=trace.update_details)
        else:
            raise UnhandledTypeException(f"Unhandled type {type(trace).__name__}")

    def get_now(self) -> datetime:
        return datetime.datetime.now(datetime.timezone.utc)
