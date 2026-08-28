from pydantic import BaseModel
from enum import Enum
from typing import Annotated, Literal

from .common import UserAction, BlockchainType, UpdateDetails, HashType

class Base(BaseModel):

    userAction: UserAction
    userId: str	
    blockchains: list[BlockchainType]

class Dataset(Base): 
    datasetId: str

class UpdateDataset(Dataset):
    userAction: Literal[UserAction.UPDATE]
    details: UpdateDetails

class UseDatasets(Base):
    userAction: Literal[UserAction.USE]
    toolName: str
    toolVersion: str

class CreateDataset(Dataset):
    userAction: Literal[UserAction.CREATE]
    resources: list[CreateDatasetResources]

class ContentType(Enum):
	HASH = "HASH"

class CreateDatasetResources(BaseModel):
	id: str
	contentType: ContentType

class CreateDatasetResourcesHash(CreateDatasetResources):
    contentType: Literal[ContentType.HASH]
    # Base64 encoded hash
    hash: str
    hashType: HashType