
import pytest
import os
import yaml
import json
import logging
import shutil
import uuid

from .common import (script_dir, get_test_dir, gen_password, get_app_settings)
from app.core.auth.user_roles import UserRoles

log = logging.getLogger(__name__)

@pytest.fixture(scope="session", autouse=True)
def prepare_secrets():
    log.warning(f"Using tmp folder {get_test_dir()}")
    settings = get_app_settings()
    os.mkdir(get_test_dir())
    app_secret = {
        "database_password": gen_password()
    }
    with open(os.path.join(get_test_dir(), "app-settings-secret.test.yml.private"), "w") as f:
        yaml.dump(app_secret, f)

    with open(os.path.join(get_test_dir(), "IMMUDB_ADMIN_PASSWORD.private"), "w") as f:
        immudb_passwd = gen_password()
        f.write(immudb_passwd)

    with open(os.path.join(script_dir(), "keycloak-realm.test.json"), "r") as f:
        keycloak = json.load(f)
        for u in keycloak["users"]:
            cred = u["credentials"][0]
            cred["value"] = gen_password()

        # Generate the ID of the client and bind it to the realm role
        tracing_client = next((c for c in keycloak["clients"] if c["clientId"] == settings["oidc"]["client"]), None)
        if tracing_client is None:
            raise Exception("Can't find client tracing in keycloak conf file")
        tracing_role = next((c for c in keycloak["roles"]["client"][settings["oidc"]["client"]] if c["name"] == UserRoles.WRITER), None)
        if tracing_role is None:
            raise Exception("Can't find writer role in keycloak conf file")
        tracing_client["id"] = str(uuid.uuid4())
        tracing_role["containerId"] = tracing_client["id"]

        with open(os.path.join(get_test_dir(), "keycloak-realm.test.json.private"), "w") as o:
            json.dump(keycloak, o)


    os.environ['TRACING_TEST_DIR'] = get_test_dir()
    os.environ['TRACING_IMMUDB_ADMIN_PASSWORD'] = immudb_passwd
    os.environ['TRACING_KC_BOOTSTRAP_ADMIN_PASSWORD'] = gen_password()

    yield

    shutil.rmtree(get_test_dir())