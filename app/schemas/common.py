
from pydantic import BaseModel
from typing import Generic, TypeVar, Annotated
from annotated_types import MinLen

T = TypeVar("T")

class AppInfo(BaseModel):
    version: str
    name: str

class Page(BaseModel, Generic[T]):

    total: int
    skip: int
    limit: int
    data: T

NonNullOrEmptyStr = Annotated[str, MinLen(1)]
