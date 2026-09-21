
import os
import yaml
import asyncio
import json
import httpx
from pathlib import Path
from datetime import datetime
import base64
from uuid import uuid4

import secrets
import string
conf = None

app_settings: dict = None

__test_dir_str = None

def gen_password() -> str:
    alphabet = string.ascii_letters + string.digits + ".-_"
    return ''.join(secrets.choice(alphabet) for i in range(32)) 

def get_test_dir() -> str:
    global __test_dir_str
    if __test_dir_str is None:
        id = uuid4()
        __test_dir_str = f"/tmp/tracing-test-{str(id)}"
    return __test_dir_str

def script_dir():
    return Path(__file__).parent

def get_conf() -> dict:
    global conf
    if conf is None:
        with open(os.path.join(script_dir(), "docker-compose.test.yml"), "r") as f:
            docker_comp = yaml.safe_load(f)
        
        with open(os.path.join(get_test_dir(), "keycloak-realm.test.json.private"), "r") as f:
            kecyloak = json.load(f)
        conf = {
            "app": {
                "port": int(docker_comp["services"]["tracing-test"]["ports"][0].split(":")[0])
            },
            "keycloak": {
                "users": {u["username"]: {"password": u["credentials"][0]["value"]} for u in kecyloak["users"]}
            }
        }
    return conf

def get_app_settings() -> dict:
    global app_settings
    if app_settings is None:
        with open(os.path.join(script_dir(), "app-settings.test.yml"), "r") as f:
            app_settings = yaml.safe_load(f)
    return app_settings
        
async def wait(health_url: str, max_retries: int = 30, retry_delay: int = 5):
    async with httpx.AsyncClient(timeout=5.0) as client:
        for attemmpt in range(max_retries):
            try:
                resp = await client.get(health_url)
                if resp.status_code == 200:
                    print(f"{health_url} ready")
                    return True
            except httpx.RequestError as e:
                print(f"Waiting for {health_url}, attempt {attemmpt}")
                asyncio.sleep(retry_delay)

async def get_access_token(username: str, password: str, extra_scope: str = "") -> str: 
    settings = get_app_settings()
    payload = {
        "grant_type": "password",
        "client_id": settings["oidc"]["client"],
        "username": username,
        "password": password,
        "scope": f"openid {extra_scope}"
    }
    async with httpx.AsyncClient(timeout=5.0) as client:
        url = settings["oidc"]["url"]
        if not settings["oidc"]["url"].startswith("http://"):
            url = f"http://{settings["oidc"]["url"]}"
        url = "http://localhost:8080"
        resp = await client.post(f"{url}/realms/{settings["oidc"]["realm"]}/protocol/openid-connect/token",
                                data=payload)
        if resp.status_code == 200:
            rparsed = json.loads(resp.text)
            if "access_token" in rparsed:
                return rparsed["access_token"]
            else:
                raise Exception("Access token not available in the keycloak response")
        else:
            raise Exception(f"Error getting token (code: {resp.status_code}): {resp.text}")

def is_valid_datetime(date_string):
    try:
        datetime.fromisoformat(date_string)
        return True
    except:
        return False

def get_user_id_access_token(token: str) -> str:
    # JWT has 3 parts: header.payload.signature
    payload = token.split('.')[1]

    # Add padding if needed
    payload += '=' * (4 - len(payload) % 4)

    # Decode and parse
    claims = json.loads(base64.urlsafe_b64decode(payload))
    return claims.get("sub")


def get_common_fields_response_trace() -> set: 
    return set(["id", "version", "callerId", "userAction", "userId", "createdAt"])
