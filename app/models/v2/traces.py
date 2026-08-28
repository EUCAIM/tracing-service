from pydantic import Field, BaseModel, TypeAdapter
from typing import Annotated, Literal
from annotated_types import MinLen, MaxLen
from datetime import datetime
import uuid
from psycopg.types.json import Json

from .common_types import HashType, UserAction, UpdateDetails, TraceVersion

class TraceResource(BaseModel):

    # The ID of the resource, must be anonymized.
    id: str = Field(...)
    # Base64 encoded String of the hash of the content
    content_hash: Annotated[str, MinLen(1)] = Field(...)
    content_hash_type: HashType = Field(...)

class BaseTrace(BaseModel): 

    # The UUID of the trace
    id: uuid.UUID = Field(...)

    # The ID of the (person, application, service etc.) called the service to add a trace
    caller_id: str = Field(...)
    # Creation date/time 
    created_at: datetime = Field(...)
    # Trace version
    # @property
    # def trace_version(self) -> TraceVersion:
    #     raise NotImplementedError

class Trace(BaseTrace): 
    trace_version: Literal[TraceVersion.V2] = Field(default=TraceVersion.V2, frozen=True)
    # The ID of the user (person, application, service etc.) that performed the traced action
    user_id: str = Field(...)
    # The action of a user (person, application, service etc.) represented by this trace
    # @property
    # def user_action(self) -> UserAction:
    #     raise NotImplementedError



class CreateDataset(Trace): 
    # The id of the dataset referenced by this trace
    datasets_ids: str = Field(...) #Annotated[list[str], MinLen(1), MaxLen(1)] = Field(...)
    user_action: Literal[UserAction.CREATE_DATASET] = Field(default=UserAction.CREATE_DATASET, frozen=True)
    create_resources: str = Field(...) #list[TraceResource] = Field(...) 

class UpdateDataset(Trace):
    # The id of the dataset referenced by this trace
    datasets_ids:  str = Field(...) # Annotated[list[str], MinLen(1), MaxLen(1)] = Field(...)
    user_action: Literal[UserAction.UPDATE_DATASET] = Field(default=UserAction.UPDATE_DATASET, frozen=True)
    # The details about the updated dataset, such as the performed action or the field that has been changed.
    update_details: UpdateDetails = Field(...)

class UseDataset(Trace):
    user_action: Literal[UserAction.USE_DATASETS] = Field(default=UserAction.USE_DATASETS, frozen=True)
    # The list of IDs used by the traced action
    datasets_ids: str = Field(...) #Annotated[list[str], MinLen(1)] = Field(...)
    
    # the name of the tool used for this user action
    use_tool_name: str
    # the version of the tool used for this user action
    use_tool_version: str


TraceDataset = Annotated[CreateDataset | UpdateDataset | UseDataset, Field(discriminator="user_action")]
TraceDatasetAdapter = TypeAdapter(TraceDataset)

# class TraceDataset(BaseModel):
#     # The UUID of the trace
#     id: uuid.UUID = Field(...)

#     # The ID of the (person, application, service etc.) called the service to add a trace
#     caller_id: str = Field(...)
#     # Creation date/time 
#     created_at: datetime = Field(...)
#     version: Literal[TraceVersion.V2] = Field(frozen=True)
#     # The ID of the user (person, application, service etc.) that performed the traced action
#     user_id: str = Field(...)
#     # The action of a user (person, application, service etc.) represented by this trace
#     user_action: UserAction = Field(...)
#     # The id of the dataset referenced by this trace
#     dataset_id: str = Field(...)
#     create_resources: list[TraceResource] | None = None
#     # The details about the updated dataset, such as the performed action or the field that has been changed.
#     update_details: UpdateDetails | None = None
#     # the name of the tool used for this user action
#     use_tool_name: str | None = None
#     # the version of the tool used for this user action
#     use_tool_version: str | None = None