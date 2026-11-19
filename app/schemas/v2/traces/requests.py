from pydantic import Field, BaseModel, ConfigDict
from app.models.v2.common_types import UserAction, HashType, UpdateDetails
from typing import Annotated, Literal
from annotated_types import MinLen
from ...common import NonNullOrEmptyStr
from .common import CreateDatasetResource

class TraceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    userAction: UserAction
    userId: str

class DatasetCreateRequest(TraceRequest):
    model_config = ConfigDict(extra="forbid")
    userAction: Literal[UserAction.CREATE_DATASET]
    datasetId: NonNullOrEmptyStr
    resources: Annotated[list[CreateDatasetResource], MinLen(1)]

class DatasetUpdateRequest(TraceRequest):
    model_config = ConfigDict(extra="forbid")
    userAction: Literal[UserAction.UPDATE_DATASET]
    datasetId: NonNullOrEmptyStr
    details: UpdateDetails

class DatasetUseRequest(TraceRequest):
    model_config = ConfigDict(extra="forbid")
    userAction: Literal[UserAction.USE_DATASETS]
    datasetsIds: Annotated[list[str], MinLen(1)]
    toolName: NonNullOrEmptyStr
    toolVersion: NonNullOrEmptyStr



TraceTypeRequest = Annotated[DatasetCreateRequest | DatasetUpdateRequest | DatasetUseRequest, Field(discriminator="userAction")]