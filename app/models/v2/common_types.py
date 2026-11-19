
from enum import Enum
from enum import IntEnum

class UserAction(str, Enum):
    CREATE_DATASET = "CREATE_DATASET"
    UPDATE_DATASET = "UPDATE_DATASET"
    USE_DATASETS = "USE_DATASETS"

class HashType(str, Enum):
    SHA3_256 = "SHA3_256"
    SHA3_512 = "SHA3_512"

class UpdateDetails(str, Enum):
    RELEASE = "RELEASE"
    PUBLISH = "PUBLISH"
    INVALIDATE = "INVALIDATE"
    REACTIVATE = "REACTIVATE"
    UNPUBLISH = "UNPUBLISH"
    LICENSE_UPDATED = "LICENSE_UPDATED"
    PID_UPDATED = "PID_UPDATED"
    CONTACT_INFORMATION_UPDATED = "CONTACT_INFORMATION_UPDATED"
    AUTHOR_CHANGED = "AUTHOR_CHANGED"

class TraceVersion(IntEnum):
    V1 = 1
    V2 = 2

class TraceTarget(str, Enum):
    DATASET = "DATASET"
    