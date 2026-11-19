import uuid

from app.schemas.v2.traces.requests import DatasetCreateRequest, DatasetUseRequest, DatasetUpdateRequest
from app.schemas.v2.traces.common import CreateDatasetResource
from app.models.v2.common_types import UserAction, HashType, UpdateDetails

trace_update_req = DatasetUpdateRequest(
    userAction=UserAction.UPDATE_DATASET,
    datasetId=str(uuid.uuid4()),
    userId=str(uuid.uuid4()),
    details=UpdateDetails.PUBLISH
)

trace_use_req = DatasetUseRequest(
    userAction=UserAction.USE_DATASETS,
    datasetsIds=[str(uuid.uuid4()), str(uuid.uuid4())],
    userId=str(uuid.uuid4()),
    toolName="tool name",
    toolVersion="tool version"
)

trace_create_req = DatasetCreateRequest(
    userAction=UserAction.CREATE_DATASET,
    datasetId=str(uuid.uuid4()),
    userId=str(uuid.uuid4()),
    resources=[
        CreateDatasetResource(
            id="dataset_data",
            contentHash="abcd",
            contentHashType=HashType.SHA3_256
        ),
        CreateDatasetResource(
            id="dataset_data_2",
            contentHash="xyz",
            contentHashType=HashType.SHA3_512
        ),
    ]
)
