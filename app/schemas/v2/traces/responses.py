from pydantic import Field, BaseModel
from typing import Annotated, Literal
from annotated_types import MinLen
from app.models.v2.common_types import HashType, UserAction, UpdateDetails, TraceVersion
from .common import CreateDatasetResource
from datetime import datetime
from uuid import UUID

class BaseResponse(BaseModel): 
    id: UUID = Field(...)
    callerId: str = Field(...)
    createdAt: datetime = Field(...)
    version: TraceVersion

class TraceResponse(BaseResponse): 
    version: Literal[TraceVersion.V2] = Field(frozen=True)

    # The ID of the user (person, application, service etc.) that performed the traced action
    userId: str = Field(...)
    # # The action of a user (person, application, service etc.) represented by this trace
    # userAction: UserAction = Field(...)


class DatasetResponse(TraceResponse):

    # The id of the dataset referenced by this trace
    datasetId: str = Field(...)

class CreateDatasetResponse(DatasetResponse): 
    userAction: Literal[UserAction.CREATE_DATASET] = Field(UserAction.CREATE_DATASET, frozen=True)
    # The list of resources
    resources: list[CreateDatasetResource] = Field(...)

class UpdateDatasetResponse(DatasetResponse):
    userAction: Literal[UserAction.UPDATE_DATASET] = Field(UserAction.UPDATE_DATASET, frozen=True)
    # The details about the updated dataset, such as the performed action or the field that has been changed.
    details: UpdateDetails = Field(...)

class UseDatasetResponse(TraceResponse):
    userAction: Literal[UserAction.USE_DATASETS] = Field(UserAction.USE_DATASETS, frozen=True)
    # The list of IDs used by the traced action
    datasetsIds: Annotated[list[str], MinLen(1)] = Field(...)
    
    # the name of the tool used for this user action
    toolName: str = Field(...)
    # the version of the tool used for this user action
    toolVersion: str = Field(...)

TraceDatasetResponse = Annotated[CreateDatasetResponse | UpdateDatasetResponse | UseDatasetResponse, Field(discriminator="userAction")]
