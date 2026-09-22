import pytest
import subprocess
import os
import httpx
import uuid
import datetime
import json

from .common import script_dir, get_conf, get_access_token, get_user_id_access_token, get_app_settings
from .common_data import trace_create_req, trace_update_req, trace_use_req
from app.schemas.v2.traces.responses import CreateDatasetResponse, UseDatasetResponse, UpdateDatasetResponse
from app.core.auth.user_roles import UserRoles

@pytest.fixture(scope="module", autouse=True)
def start_dependencies():
    subprocess.run(
        ["docker", "compose", "-f", os.path.join(script_dir(), "docker-compose.test.yml"), "up", "-d", "--wait", "--build"],
        check=True
    )
    
    yield

    subprocess.run(
        ["docker", "compose", "-f", os.path.join(script_dir(), "docker-compose.test.yml"), "down"],
        check=True
    )

@pytest.fixture(scope="function", autouse=True)
def reset_immudb():
    subprocess.run(
            ["docker", "compose", "-f", os.path.join(script_dir(), "docker-compose.test.yml"), 
                "down", "immudb-tracing-test", "immudb-init", "tracing-test"],
            check=True
        )

    subprocess.run(
        ["docker", "compose", "-f", os.path.join(script_dir(), "docker-compose.test.yml"), "up", "-d", "--force-recreate", "--wait",
            "immudb-tracing-test", "immudb-init", "tracing-test"],
        check=True
    )


@pytest.mark.asyncio
async def test_post_traces_all_types_user_reader_writer_get_them_user_writer_and_user_no_role():
    conf = get_conf()
    reader_writer_access_token = await get_access_token("user_reader_writer", conf["keycloak"]["users"]["user_reader_writer"]["password"])
    headers = {
        "Authorization": f"Bearer {reader_writer_access_token}"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", headers=headers, json=trace_update_req.model_dump())
        assert resp.status_code == 200, \
            "The trace should have been added successfully"
        resp = await client.post(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", headers=headers, json=trace_use_req.model_dump())
        assert resp.status_code == 200, \
            "The trace should have been added successfully"
        resp = await client.post(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", headers=headers, json=trace_create_req.model_dump())
        assert resp.status_code == 200, \
            "The trace should have been added successfully"

        resp_get_reader_writer = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", 
                    headers={"Authorization": f"Bearer {reader_writer_access_token}"})
        assert resp_get_reader_writer.status_code == 200, \
            f"User with {UserRoles.WRITER}, {UserRoles.READER} roles should be authorized to retrieve the traces"

        writer_access_token = await get_access_token("user_writer", conf["keycloak"]["users"]["user_writer"]["password"])
        resp_get_writer = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", 
            headers={"Authorization": f"Bearer {writer_access_token}"})
        assert resp_get_writer.status_code == 403, \
            f"User with {UserRoles.WRITER} role shouldn't be authorized to retrieve the traces"

        no_role_access_token = await get_access_token("user_no_role", conf["keycloak"]["users"]["user_no_role"]["password"])
        resp_get_user_no_roles = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", 
            headers={"Authorization": f"Bearer {no_role_access_token}"})
        assert resp_get_user_no_roles.status_code == 403, \
            "User with no roles shouldn't be authorized to retrieve the traces"

        reader_access_token = await get_access_token("user_reader", conf["keycloak"]["users"]["user_reader"]["password"])
        resp_get_user_reader = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", 
            headers={"Authorization": f"Bearer {reader_access_token}"})
        assert resp_get_user_reader.status_code == 200, \
            f"User with {UserRoles.READER} role should be authorized to retrieve the traces"

        assert resp_get_reader_writer.json() == resp_get_user_reader.json()

@pytest.mark.asyncio
async def test_post_traces_all_types_get_them_and_check_fields():
    conf = get_conf()
    access_token = await get_access_token("user_reader_writer", conf["keycloak"]["users"]["user_reader_writer"]["password"])
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    caller_id = get_user_id_access_token(access_token)
    expected_traces = dict()
    created_at_mock = datetime.datetime.now().isoformat()
    use_datasets_dataset_id_mock = str(uuid.uuid4())
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", headers=headers, json=trace_update_req.model_dump())
        assert resp.status_code == 200, \
            "The trace should have been added successfully"
        assert len(resp.json()["ids"]) == 1, \
            "Ony one ID should have been returned"
        expected_traces[resp.json()["ids"][0]] = json.loads(UpdateDatasetResponse(
                id=resp.json()["ids"][0],
                version=2,
                callerId=caller_id,
                createdAt=created_at_mock,
                userAction=trace_update_req.userAction,
                userId=trace_update_req.userId,
                datasetId=trace_update_req.datasetId,
                datasetGroupId=resp.json()["group"],
                details=trace_update_req.details
            ).model_dump_json())

        resp = await client.post(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", headers=headers, json=trace_use_req.model_dump())
        assert resp.status_code == 200, \
            "The trace should have been added successfully"

        assert len(resp.json()["ids"]) == len(trace_use_req.datasetsIds), \
            "The number of IDs of the added traces is different than the number of referenced datasets in the request"
        for idx in range(0, len(trace_use_req.datasetsIds)):
            expected_traces[resp.json()["ids"][idx]] = json.loads(UseDatasetResponse(
                    id=resp.json()["ids"][idx],
                    version=2,
                    callerId=caller_id,
                    createdAt=created_at_mock,
                    userAction=trace_use_req.userAction,
                    userId=trace_use_req.userId,
                    datasetId=use_datasets_dataset_id_mock,
                    datasetGroupId=resp.json()["group"],
                    toolName=trace_use_req.toolName,
                    toolVersion=trace_use_req.toolVersion
                ).model_dump_json())

        resp = await client.post(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", headers=headers, json=trace_create_req.model_dump())
        assert resp.status_code == 200, \
            "The trace should have been added successfully"
        assert len(resp.json()["ids"]) == 1, \
            "Ony one ID should have been returned"
        expected_traces[resp.json()["ids"][0]] = json.loads(CreateDatasetResponse(
                id=resp.json()["ids"][0],
                version=2,
                callerId=caller_id,
                createdAt=created_at_mock,
                userAction=trace_create_req.userAction,
                userId=trace_create_req.userId,
                datasetId=trace_create_req.datasetId,
                datasetGroupId=resp.json()["group"],
                resources=trace_create_req.resources
            ).model_dump_json())

        resp_get = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", headers=headers)
        assert resp_get.status_code == 200, \
                "Problem when trying to get the traces with the user with writing rights"
        settings = get_app_settings()
        assert "total" in resp_get.json(), "No total present in the response"
        assert (len(trace_use_req.datasetsIds) + 1 + 1) == resp_get.json()["total"], "Bad total"
        assert 0 == resp_get.json()["skip"], "Skip should be 0"
        assert settings["api"]["v2"]["default_traces_limit"] == resp_get.json()["limit"], \
            "The limit should have the default value defined in the app settings"
        assert (len(trace_use_req.datasetsIds) + 1 + 1) == len(resp_get.json()["data"]), "Length not the same as the number of elements added"
        # for t in resp_get.json()["data"]:
        #     check_trace_fields(expected_traces[t["userAction"]] , t)

        resp_traces = resp_get.json()["data"]
        use_datasets_ids = set()
        for t in resp_traces:
            # Change the created date of a trace to the mock value to allow the comparison of the rest of the fields 
            #t["createdAt"] = created_at_mock
            t.pop("createdAt")

            # The dataset id of the traces with type USE_DATASETS must be set to a mock to do the general comparison
            if t["userAction"] == "USE_DATASETS":
                use_datasets_ids.add(t["datasetId"])
                t["datasetId"] = use_datasets_dataset_id_mock

        for t in expected_traces.values():
            t.pop("createdAt")

        assert set(trace_use_req.datasetsIds) == use_datasets_ids, \
            "The set of datasets IDs sent to be added as a USE_DATASETS request is different from the set of datasets IDs in all traces with action USE_DATASETS "
        assert expected_traces == {t["id"]: t for t in resp_traces}, \
            "The expected traces dict is different from the dict created with the traces available in the database"


@pytest.mark.asyncio
async def test_post_trace_auth_create_use_update_get_by_action():
    conf = get_conf()

    access_token_reader_writer = await get_access_token("user_reader_writer", conf["keycloak"]["users"]["user_reader_writer"]["password"])
    headers = {
        "Authorization": f"Bearer {access_token_reader_writer}"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", headers=headers, json=trace_create_req.model_dump())
        resp = await client.post(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", headers=headers, json=trace_update_req.model_dump())
        resp = await client.post(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", headers=headers, json=trace_use_req.model_dump())
        caller_id_writer = get_user_id_access_token(access_token_reader_writer)


        resp_get_traces = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/?userAction={trace_create_req.userAction.value}&datasetId={trace_create_req.datasetId}", headers=headers)
        
        assert resp_get_traces.status_code == 200, \
            "Should return 200 with the test's conf"
        assert resp_get_traces.json()["total"] == 1, \
            "Only one trace should be CREATE for a dataset ID, total should be one"
        assert len(resp_get_traces.json()["data"]) == 1, \
            "Only one trace should be CREATE for a dataset ID, the length of the data array should be 1"
        
        response = resp_get_traces.json()["data"][0]
        tmp = CreateDatasetResponse(
            id=response["id"],
            version=2,
            callerId=caller_id_writer,
            createdAt=datetime.datetime.now(),
            userAction=trace_create_req.userAction,
            userId=trace_create_req.userId,
            datasetId=trace_create_req.datasetId,
            datasetGroupId=response["datasetGroupId"],
            resources=trace_create_req.resources
        ).model_dump_json()
        expected_response = json.loads(tmp)
        expected_response.pop("createdAt")
        response.pop("createdAt")
        assert expected_response == response

        resp_get_traces = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/?userAction={trace_update_req.userAction.value}&datasetId={trace_update_req.datasetId}", headers=headers)
        assert resp_get_traces.status_code == 200, \
            "Should return 200 with the test's conf"
        assert resp_get_traces.json()["total"] == 1, \
            "Only one trace should be UPDATE for a dataset ID, total should be one"
        assert len(resp_get_traces.json()["data"]) == 1, \
            "Only one trace should be UPDATE for a dataset ID, the length of the data array should be 1"
        
        response = resp_get_traces.json()["data"][0]
        tmp = UpdateDatasetResponse(
            id=response["id"],
            version=2,
            callerId=caller_id_writer,
            createdAt=datetime.datetime.now(),
            userAction=trace_update_req.userAction,
            userId=trace_update_req.userId,
            datasetId=trace_update_req.datasetId,
            datasetGroupId=response["datasetGroupId"],
            details=trace_update_req.details
        ).model_dump_json()
        expected_response = json.loads(tmp)
        expected_response.pop("createdAt")
        response.pop("createdAt")
        assert expected_response == response

        for dataset_id in trace_use_req.datasetsIds:
            resp_get_traces = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/?userAction={trace_use_req.userAction.value}&datasetId={dataset_id}", headers=headers)
            assert resp_get_traces.status_code == 200, \
                "Should return 200 with the test's conf"
            assert resp_get_traces.json()["total"] == 1, \
                "Only one trace should be UPDATE for a dataset ID, total should be one"
            assert len(resp_get_traces.json()["data"]) == 1, \
                "Only one trace should be UPDATE for a dataset ID, the length of the data array should be 1"
            
            response = resp_get_traces.json()["data"][0]
            tmp = UseDatasetResponse(
                id=response["id"],
                version=2,
                callerId=caller_id_writer,
                createdAt=datetime.datetime.now(),
                userAction=trace_use_req.userAction,
                userId=trace_use_req.userId,
                datasetId=dataset_id,
                datasetGroupId=response["datasetGroupId"],
                toolName=trace_use_req.toolName,
                toolVersion=trace_use_req.toolVersion
            ).model_dump_json()
            expected_response = json.loads(tmp)
            expected_response.pop("createdAt")
            response.pop("createdAt")
            assert expected_response == response