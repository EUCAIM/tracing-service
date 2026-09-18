from unittest.mock import AsyncMock, Mock
from uuid import uuid4
import json
import pytest

from app.services.v2.traces import TracesDatasetsManager
from app.models.v2.common_types import UserAction, HashType, TraceVersion
from app.models.v2.traces import CreateDataset, TraceResource, UpdateDataset, UpdateDetails, UseDataset, Trace
from app.schemas.v2.traces.requests import DatasetCreateRequest, DatasetUpdateRequest, DatasetUseRequest, TraceRequest
from app.schemas.v2.traces.responses import CreateDatasetResponse, UseDatasetResponse, UpdateDatasetResponse
from app.schemas.v2.traces.common import CreateDatasetResource
from app.core.exceptions import UnhandledTypeException

@pytest.mark.asyncio
async def test_add_trace_create_dataset():
    repo = AsyncMock()
    svc = TracesDatasetsManager(repo)
    caller_id = str(uuid4())
    user_id = str(uuid4())
    dataset_id = str(uuid4())
    res_id = "data"
    res_ch = "abc"
    res_cht = HashType.SHA3_256
    await svc.add(caller_id, DatasetCreateRequest(
        userAction = UserAction.CREATE_DATASET,
        userId = user_id,
        datasetId = dataset_id,
        resources = [
            CreateDatasetResource(
                id=res_id,
                contentHash=res_ch,
                contentHashType=res_cht
            )
        ]    
    ))

    repo.add.assert_called_once()
    sentobj = repo.add.call_args.args[0]
    assert isinstance(sentobj, CreateDataset)
    assert CreateDataset(
        id = sentobj.id,
        caller_id = caller_id,
        created_at = sentobj.created_at,
        trace_version = TraceVersion.V2,
        user_id = user_id,
        dataset_id = dataset_id,
        dataset_group_id=sentobj.dataset_group_id,
        user_action = UserAction.CREATE_DATASET,
        create_resources = json.dumps([
            TraceResource(
                id=res_id,
                content_hash=res_ch,
                content_hash_type=res_cht
            ).model_dump()
        ])
    ).model_dump() == sentobj.model_dump()

@pytest.mark.asyncio
async def test_add_trace_update_dataset():
    repo = AsyncMock()
    svc = TracesDatasetsManager(repo)
    caller_id = str(uuid4())
    user_id = str(uuid4())
    dataset_id = str(uuid4())
    await svc.add(caller_id, DatasetUpdateRequest(
        userAction = UserAction.UPDATE_DATASET,
        userId = user_id,
        datasetId = dataset_id,
        details = UpdateDetails.RELEASE
    ))

    repo.add.assert_called_once()
    sentobj = repo.add.call_args.args[0]
    assert isinstance(sentobj, UpdateDataset)
    assert UpdateDataset(
        id = sentobj.id,
        caller_id = caller_id,
        created_at = sentobj.created_at,
        trace_version = TraceVersion.V2,
        user_id = user_id,
        dataset_id = dataset_id,
        dataset_group_id=sentobj.dataset_group_id,
        user_action = UserAction.UPDATE_DATASET,
        update_details = UpdateDetails.RELEASE
    ).model_dump() == sentobj.model_dump()

@pytest.mark.asyncio
async def test_add_trace_use_datasets():
    repo = AsyncMock()
    svc = TracesDatasetsManager(repo)
    caller_id = str(uuid4())
    user_id = str(uuid4())
    datasets_ids = [str(uuid4()), str(uuid4()), str(uuid4())]
    tool_name = "tool"
    tool_ver = "ver"
    await svc.add(caller_id, DatasetUseRequest(
        userAction = UserAction.USE_DATASETS,
        userId = user_id,
        datasetsIds = datasets_ids,
        toolName=tool_name,
        toolVersion=tool_ver
    ))

    assert repo.add.call_count == len(datasets_ids), \
        "Call count to the repo is not equal to the number of datasets IDs in the request"

    sent_objects = [args[0] for args, kwargs in repo.add.call_args_list]

    assert len(sent_objects) == len(datasets_ids), \
        "The number of sent objects to the repo is not equal to the number of datasets IDs in the request"
    
    expected_objects = []
    sent_datasets_ids = []
    sent_dataset_group_id = []
    for obj in sent_objects:
        assert isinstance(obj, UseDataset), \
            "The object sent to the repo is not of type UseDataset"
        expected_objects.append(
            UseDataset(
                id = obj.id,
                caller_id = caller_id,
                created_at = obj.created_at,
                trace_version = TraceVersion.V2,
                user_id = user_id,
                dataset_id = obj.dataset_id,
                dataset_group_id = obj.dataset_group_id,
                use_tool_name=tool_name,
                use_tool_version=tool_ver
            ).model_dump()
        )
        sent_datasets_ids.append(obj.dataset_id)
        sent_dataset_group_id.append(obj.dataset_group_id)


    assert expected_objects == [o.model_dump() for o in sent_objects], \
        "The expected objects and the ones that were created and sent are different"

    assert sent_datasets_ids == datasets_ids, \
        "The datasets IDs sent to the repo don't match the expected"

    assert len(set(sent_dataset_group_id)) == 1, \
        "The length of the set representing the dataset group ID should be 1"

@pytest.mark.asyncio
async def test_add_trace_type_not_handled():
    repo = AsyncMock()
    svc = TracesDatasetsManager(repo)
    caller_id = str(uuid4())
    user_id = str(uuid4())
    with pytest.raises(UnhandledTypeException) as exc_info:
        await svc.add(caller_id, TraceRequest(
            userAction = UserAction.USE_DATASETS,
            userId = user_id
        ))
    assert "Unhandled request type TraceRequest" == str(exc_info.value)

def test_get_response_create_dataset():
    repo = Mock()
    svc = TracesDatasetsManager(repo)
    id = uuid4()
    caller_id = str(uuid4())
    user_id = str(uuid4())
    dataset_id = str(uuid4())
    dataset_group_id = uuid4()
    created_at = svc.get_now()
    res_id = "data"
    res_ch = "abc"
    res_cht = HashType.SHA3_256
    trace = svc.get_trace_response(CreateDataset(
        id = id,
        caller_id = caller_id,
        created_at = created_at,
        trace_version = TraceVersion.V2,
        user_id = user_id,
        dataset_id = dataset_id,
        dataset_group_id = dataset_group_id,
        user_action = UserAction.CREATE_DATASET,
        create_resources = json.dumps([
            TraceResource(
                id=res_id,
                content_hash=res_ch,
                content_hash_type=res_cht
            ).model_dump()
        ])
    ))

    assert CreateDatasetResponse(
        id = id,
        callerId = caller_id,
        createdAt = created_at,
        version = TraceVersion.V2,
        userId = user_id,
        datasetId = dataset_id,
        datasetGroupId = dataset_group_id,
        userAction = UserAction.CREATE_DATASET,
        resources = [
            CreateDatasetResource(
                id=res_id,
                contentHash=res_ch,
                contentHashType=res_cht
            )
        ]
    ).model_dump() == trace.model_dump()


def test_get_response_update_dataset():
    repo = Mock()
    svc = TracesDatasetsManager(repo)
    id = uuid4()
    caller_id = str(uuid4())
    user_id = str(uuid4())
    dataset_id = str(uuid4())
    dataset_group_id = uuid4()
    created_at = svc.get_now()
    trace = svc.get_trace_response(UpdateDataset(
        id = id,
        caller_id = caller_id,
        created_at = created_at,
        trace_version = TraceVersion.V2,
        user_id = user_id,
        dataset_id = dataset_id,
        dataset_group_id = dataset_group_id,
        user_action = UserAction.UPDATE_DATASET,
        update_details=UpdateDetails.PID_UPDATED
    ))

    assert UpdateDatasetResponse(
        id = id,
        callerId = caller_id,
        createdAt = created_at,
        version = TraceVersion.V2,
        userId = user_id,
        datasetId = dataset_id,
        datasetGroupId = dataset_group_id,
        userAction = UserAction.UPDATE_DATASET,
        details=UpdateDetails.PID_UPDATED
    ).model_dump() == trace.model_dump()


def test_get_response_use_datasets():
    repo = Mock()
    svc = TracesDatasetsManager(repo)
    id = uuid4()
    caller_id = str(uuid4())
    user_id = str(uuid4())
    dataset_id = str(uuid4())
    dataset_group_id = uuid4()
    created_at = svc.get_now()
    tool_name = "tool"
    tool_ver = "ver"
    trace = svc.get_trace_response(UseDataset(
        id = id,
        caller_id = caller_id,
        created_at = created_at,
        trace_version = TraceVersion.V2,
        user_id = user_id,
        dataset_id = dataset_id,
        dataset_group_id=dataset_group_id,
        user_action = UserAction.USE_DATASETS,
        use_tool_name=tool_name,
        use_tool_version=tool_ver
    ))

    assert UseDatasetResponse(
        id = id,
        callerId = caller_id,
        createdAt = created_at,
        version = TraceVersion.V2,
        userId = user_id,
        datasetId = dataset_id,
        datasetGroupId=dataset_group_id,
        userAction = UserAction.USE_DATASETS,
        toolName=tool_name,
        toolVersion=tool_ver
    ).model_dump() == trace.model_dump()

def test_get_response_type_not_handled():
    repo = Mock()
    svc = TracesDatasetsManager(repo)
    with pytest.raises(UnhandledTypeException) as exc_info:
        svc.get_trace_response(Trace(
            id = uuid4(),
            caller_id = "123",
            created_at = svc.get_now()
        ))
    assert "Unhandled type Trace" == str(exc_info.value)