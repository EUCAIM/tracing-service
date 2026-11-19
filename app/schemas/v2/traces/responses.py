from pydantic import Field, BaseModel
from typing import Annotated, Literal
from app.models.v2.common_types import UserAction, UpdateDetails, TraceVersion
from .common import CreateDatasetResource
from datetime import datetime
from uuid import UUID
from dataclasses import dataclass


@dataclass
class CreateTraceResponse:
    ids: list[UUID]
    group: UUID

class TraceResponse(BaseModel): 
    id: UUID = Field(...)
    callerId: str = Field(...)
    createdAt: datetime = Field(...)


class DatasetResponse(TraceResponse):

    version: Literal[TraceVersion.V2] = Field(frozen=True)
    # The id of the dataset referenced by this trace
    datasetId: str = Field(...)
    datasetGroupId: UUID = Field(...)
    userId: str = Field(...)

class CreateDatasetResponse(DatasetResponse): 
    userAction: Literal[UserAction.CREATE_DATASET] = Field(UserAction.CREATE_DATASET, frozen=True)
    # The list of resources
    resources: list[CreateDatasetResource] = Field(...)

class UpdateDatasetResponse(DatasetResponse):
    userAction: Literal[UserAction.UPDATE_DATASET] = Field(UserAction.UPDATE_DATASET, frozen=True)
    # The details about the updated dataset, such as the performed action or the field that has been changed.
    details: UpdateDetails = Field(...)

class UseDatasetResponse(DatasetResponse):
    userAction: Literal[UserAction.USE_DATASETS] = Field(UserAction.USE_DATASETS, frozen=True)
    
    # the name of the tool used for this user action
    toolName: str = Field(...)
    # the version of the tool used for this user action
    toolVersion: str = Field(...)

TraceDatasetResponse = Annotated[CreateDatasetResponse | UpdateDatasetResponse | UseDatasetResponse, Field(discriminator="userAction")]
