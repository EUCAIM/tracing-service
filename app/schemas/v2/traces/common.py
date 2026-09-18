from pydantic import BaseModel, ConfigDict
from ...common import NonNullOrEmptyStr
from app.models.v2.common_types import HashType

class CreateDatasetResource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # The id of the submitted resource with the request to add a trace.
	# It has to uniquely identify this resource on the system and t has to be anonymized
	# The uniqueness is not verified by this service.
    id: NonNullOrEmptyStr
    # Base64 encoded String of the hash of the content
    contentHash: NonNullOrEmptyStr
    # The type of the hash of the actual resource
    contentHashType: HashType
