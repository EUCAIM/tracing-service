import httpx
import pytest
import subprocess
import logging
import os
import json
import datetime
import uuid

from .common_data import trace_create_req, trace_update_req, trace_use_req
from app.schemas.v2.traces.responses import CreateDatasetResponse, UseDatasetResponse, UpdateDatasetResponse
from app.core.auth.user_roles import UserRoles

from .common import (get_conf, get_access_token, 
    get_user_id_access_token, script_dir)

log = logging.getLogger(__name__)


    
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


@pytest.mark.asyncio
async def test_get_server_info():
    conf = get_conf()
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"http://localhost:{conf['app']["port"]}/")
        assert resp.status_code == 200, \
            "Endpoint should be available without protection"

@pytest.mark.asyncio
async def test_get_trace_by_ID_not_auth():
    conf = get_conf()
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/4b5819a1-c1c0-47e1-9296-a63b981c03c7")
        assert resp.status_code == 401, \
            "Not authorized when there is no auth header"

@pytest.mark.asyncio
async def test_get_trace_by_ID_user_writer():
    conf = get_conf()
    access_token = await get_access_token("user_writer", conf["keycloak"]["users"]["user_writer"]["password"])
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/4b5819a1-c1c0-47e1-9296-a63b981c03c7", 
            headers={"Authorization": f"Bearer {access_token}"})
        assert resp.status_code == 403, \
            f"Auth user with {UserRoles.WRITER} role should NOT BE able to get traces by ID"

@pytest.mark.asyncio
async def test_get_not_found_trace_by_ID_user_reader():
    conf = get_conf()
    access_token = await get_access_token("user_reader", conf["keycloak"]["users"]["user_reader"]["password"])
    async with httpx.AsyncClient() as client:
        id = str(uuid.uuid4())
        resp = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/{id}", 
            headers={"Authorization": f"Bearer {access_token}"})
        assert resp.status_code == 404, \
            f"Auth user with {UserRoles.READER} role should receive 404 because the trace with the requested ID should not exist"

@pytest.mark.asyncio
async def test_get_not_found_trace_by_ID_user_reader_writer():
    conf = get_conf()
    access_token = await get_access_token("user_reader_writer", conf["keycloak"]["users"]["user_reader_writer"]["password"])
    async with httpx.AsyncClient() as client:
        id = str(uuid.uuid4())
        resp = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/{id}", 
            headers={"Authorization": f"Bearer {access_token}"})
        assert resp.status_code == 404, \
            f"Auth user with {UserRoles.READER} and {UserRoles.WRITER} roles should receive 404 because the trace with the requested ID should not exist"

@pytest.mark.asyncio
async def test_get_traces_not_auth():
    conf = get_conf()
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/")
        assert resp.status_code == 401, \
            "Not authorized when there is no auth header"

@pytest.mark.asyncio
async def test_get_traces_user_no_role():
    conf = get_conf()
    access_token = await get_access_token("user_no_role", conf["keycloak"]["users"]["user_no_role"]["password"])
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", headers={"Authorization": f"Bearer {access_token}"})
        assert resp.status_code == 403, \
            "Auth user with no roles should NOT BE able to get paginated traces"

@pytest.mark.asyncio
async def test_get_traces_user_reader():
    conf = get_conf()
    access_token = await get_access_token("user_reader", conf["keycloak"]["users"]["user_reader"]["password"])
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", headers={"Authorization": f"Bearer {access_token}"})
        assert resp.status_code == 200, \
            f"Auth user with {UserRoles.READER} role should BE able to get paginated traces"

@pytest.mark.asyncio
async def test_get_traces_user_writer():
    conf = get_conf()
    access_token = await get_access_token("user_no_role", conf["keycloak"]["users"]["user_no_role"]["password"])
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", headers={"Authorization": f"Bearer {access_token}"})
        assert resp.status_code == 403, \
            f"Auth user with {UserRoles.WRITER} role should NOT BE able to get paginated traces"

@pytest.mark.asyncio
async def test_get_traces_user_reader_writer():
    conf = get_conf()
    access_token = await get_access_token("user_reader_writer", conf["keycloak"]["users"]["user_reader_writer"]["password"])
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", headers={"Authorization": f"Bearer {access_token}"})
        assert resp.status_code ==200, \
            f"Auth user with {UserRoles.WRITER} and {UserRoles.READER} roles should BE able to get paginated traces"

@pytest.mark.asyncio
async def test_post_traces_not_auth():
    conf = get_conf()
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", json=trace_use_req.model_dump())
        assert resp.status_code == 401, \
            "Should return not authorized because auth header is missing"

@pytest.mark.asyncio
async def test_post_traces_auth_no_role():
    conf = get_conf()
    access_token = await get_access_token("user_no_role", conf["keycloak"]["users"]["user_no_role"]["password"])
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", headers={"Authorization": f"Bearer {access_token}"}, json=trace_update_req.model_dump())
        assert resp.status_code == 403, \
            f"Should return forbidden because the user has no roles ({UserRoles.WRITER} required in Keycloak)"

@pytest.mark.asyncio
async def test_post_traces_auth_reader():
    conf = get_conf()
    access_token = await get_access_token("user_reader", conf["keycloak"]["users"]["user_reader"]["password"])
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", headers={"Authorization": f"Bearer {access_token}"}, json=trace_update_req.model_dump())
        assert resp.status_code == 403, \
            f"Should return forbidden because the user has the {UserRoles.READER} role ({UserRoles.WRITER} required in Keycloak)"


@pytest.mark.asyncio
async def test_post_traces_auth_reader_writer():
    conf = get_conf()
    access_token = await get_access_token("user_reader_writer", conf["keycloak"]["users"]["user_reader_writer"]["password"])
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", headers={"Authorization": f"Bearer {access_token}"}, json=trace_update_req.model_dump())
        assert resp.status_code == 200, \
            f"Should allow the post operation because the user has the {UserRoles.READER} and {UserRoles.WRITER} roles"


@pytest.mark.asyncio
async def test_post_trace_auth_writer_update_trace():
    conf = get_conf()

    access_token = await get_access_token("user_writer", conf["keycloak"]["users"]["user_writer"]["password"])
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", headers=headers, json=trace_update_req.model_dump())

        assert "ids" in resp.json(), \
            "Should return the IDs of the newly added entries"
        assert "group" in resp.json(), \
            "Should return the group ID of the newly added entries"
        # The response should contain only one key
        assert len(resp.json()) == 2, \
            "Should only have two keys, the IDs of the newly added traces and the ID of the group"
        assert resp.status_code == 200, \
            "Should return 200 with the test's conf"

@pytest.mark.asyncio
async def test_post_user_writer_get_trace_user_reader_check_caller_id():
    conf = get_conf()

    post_access_token = await get_access_token("user_writer", conf["keycloak"]["users"]["user_writer"]["password"])
    headers = {
        "Authorization": f"Bearer {post_access_token}"
    }
    post_caller_id = get_user_id_access_token(post_access_token)
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", headers=headers, json=trace_update_req.model_dump())

        access_token_reader = await get_access_token("user_reader", conf["keycloak"]["users"]["user_reader"]["password"])
        resp_reader = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/{resp.json()["ids"][0]}", 
            headers={"Authorization": f"Bearer {access_token_reader}"})

        assert post_caller_id == resp_reader.json()["callerId"], \
            "The caller ID in the token used to post the trace should be the same with the caller ID stored in the trace"
        

@pytest.mark.asyncio
async def test_post_trace_auth_update_get_by_ID_same_user():
    conf = get_conf()

    post_access_token = await get_access_token("user_writer", conf["keycloak"]["users"]["user_writer"]["password"])
    post_caller_id = get_user_id_access_token(post_access_token)
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"http://localhost:{conf['app']["port"]}/api/v2/traces/",  
            headers={"Authorization": f"Bearer {post_access_token}"}, json=trace_update_req.model_dump())

        assert "ids" in resp.json(), \
                   "Should return the IDs of the newly added entries"
        assert "group" in resp.json(), \
            "Should return the group ID of the newly added entries"
        assert len(resp.json()) == 2, \
            "Should only have two keys, the IDs of the newly added traces and the ID of the group"
        assert resp.status_code == 200, \
            "Should return 200 with the test's conf"

        resp_get_trace = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/{resp.json()["ids"][0]}",
            headers={"Authorization": f"Bearer {post_access_token}"})
        assert resp_get_trace.status_code == 403, \
            f"User with role {UserRoles.WRITER} should not be able to retrieve the trace"

        user_reader_access_token = await get_access_token("user_reader", conf["keycloak"]["users"]["user_reader"]["password"])
        resp_get_trace = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/{resp.json()["ids"][0]}", 
            headers={"Authorization": f"Bearer {user_reader_access_token}"})        
        assert resp_get_trace.status_code == 200, \
            "Should return 200 with the test's conf"

        tmp = UpdateDatasetResponse(
            id=resp.json()["ids"][0],
            version=2,
            callerId=post_caller_id,
            createdAt=datetime.datetime.now(),
            userAction=trace_update_req.userAction,
            userId=trace_update_req.userId,
            datasetId=trace_update_req.datasetId,
            datasetGroupId=resp.json()["group"],
            details=trace_update_req.details
        ).model_dump_json()
        expected_response = json.loads(tmp)
        expected_response.pop("createdAt")
        response = resp_get_trace.json()
        response.pop("createdAt")
        assert expected_response == response

@pytest.mark.asyncio
async def test_post_trace_auth_use_get_by_ID_same_user():
    conf = get_conf()
    post_access_token = await get_access_token("user_writer", conf["keycloak"]["users"]["user_writer"]["password"])
    post_caller_id = get_user_id_access_token(post_access_token)
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", 
            headers={"Authorization": f"Bearer {post_access_token}"},  json=trace_use_req.model_dump())
        
        assert "ids" in resp.json(), \
            "Should return the IDs of the newly added entries"
        assert "group" in resp.json(), \
            "Should return the group ID of the newly added entries"
        assert len(resp.json()) == 2, \
            "Should only have two keys, the IDs of the newly added traces and the ID of the group"
        assert resp.status_code == 200, \
            "Should return 200 with the test's conf"
        expected_responses = {}
        responses = {}
        expected_datasets_ids = set()
        user_reader_access_token = await get_access_token("user_reader", conf["keycloak"]["users"]["user_reader"]["password"])
        for trace_id in resp.json()["ids"]:
            resp_get_trace = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/{trace_id}",
            headers={"Authorization": f"Bearer {post_access_token}"})
            assert resp_get_trace.status_code == 403, \
                f"User with role {UserRoles.WRITER} should not be able to retrieve the trace"

            resp_get_trace = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/{trace_id}", 
                headers={"Authorization": f"Bearer {user_reader_access_token}"})        
            assert resp_get_trace.status_code == 200, \
                "Should return 200 with the test's conf"

            
            tmp = UseDatasetResponse(
                id=trace_id,
                version=2,
                callerId=post_caller_id,
                createdAt=datetime.datetime.now(),
                userAction=trace_use_req.userAction,
                userId=trace_use_req.userId,
                datasetId=str(uuid.uuid4()),
                datasetGroupId=resp.json()["group"],
                toolName=trace_use_req.toolName,
                toolVersion=trace_use_req.toolVersion
            ).model_dump_json()
            expected_response = json.loads(tmp)
            expected_response.pop("createdAt")
            expected_response.pop("datasetId")
            response = resp_get_trace.json()
            response.pop("createdAt")
            expected_datasets_ids.add(response.pop("datasetId"))
            expected_responses[trace_id] = expected_response
            responses[trace_id] = response

        assert expected_response == response, \
            "Expected response not the same with received"
        assert expected_datasets_ids == set(trace_use_req.datasetsIds), \
            "The list of datasets IDs in the request doesn't match the datasets IDs collected from all the traces created by the request"

@pytest.mark.asyncio
async def test_post_trace_auth_create_get_by_ID_same_user():
    conf = get_conf()

    post_access_token = await get_access_token("user_writer", conf["keycloak"]["users"]["user_writer"]["password"])
    post_caller_id = get_user_id_access_token(post_access_token)
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"http://localhost:{conf['app']["port"]}/api/v2/traces/", 
            headers={"Authorization": f"Bearer {post_access_token}"}, json=trace_create_req.model_dump())

        assert "ids" in resp.json(), \
            "Should return the IDs of the newly added entries"
        assert "group" in resp.json(), \
            "Should return the group ID of the newly added entries"
        assert len(resp.json()) == 2, \
            "Should only have two keys, the IDs of the newly added traces and the ID of the group"
        assert resp.status_code == 200, \
            "Should return 200 with the test's conf"

        resp_get_trace = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/{resp.json()["ids"][0]}",
            headers={"Authorization": f"Bearer {post_access_token}"})
        assert resp_get_trace.status_code == 403, \
            f"User with role {UserRoles.WRITER} should not be able to retrieve the trace"

        user_reader_access_token = await get_access_token("user_reader", conf["keycloak"]["users"]["user_reader"]["password"])
        resp_get_trace = await client.get(f"http://localhost:{conf['app']["port"]}/api/v2/traces/{resp.json()["ids"][0]}", 
            headers={"Authorization": f"Bearer {user_reader_access_token}"})        
        assert resp_get_trace.status_code == 200, \
            "Should return 200 with the test's conf"
        
        tmp = CreateDatasetResponse(
            id=resp.json()["ids"][0],
            version=2,
            callerId=post_caller_id,
            createdAt=datetime.datetime.now(),
            userAction=trace_create_req.userAction,
            userId=trace_create_req.userId,
            datasetId=trace_create_req.datasetId,
            datasetGroupId=resp.json()["group"],
            resources=trace_create_req.resources
        ).model_dump_json()
        expected_response = json.loads(tmp)
        expected_response.pop("createdAt")
        response = resp_get_trace.json()
        response.pop("createdAt")
        assert expected_response == response


        