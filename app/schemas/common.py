
from pydantic import BaseModel
from typing import Generic, TypeVar, Annotated
from annotated_types import MinLen
from uuid import UUID
from dataclasses import dataclass

T = TypeVar("T")

class AppInfo(BaseModel):
    version: str
    name: str

class Page(BaseModel, Generic[T]):

    total: int
    position: int
    size: int
    data: T

@dataclass
class CreateTraceResponse:
    id: UUID


NonNullOrEmptyStr = Annotated[str, MinLen(1)]
