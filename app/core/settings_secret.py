import os
from pydantic import BaseModel, SecretStr, Field

from .settings_common import ENV_VARS_PREFIX, load_settings
from .logging import logging

logger = logging.getLogger(__name__)


def get_settings_secret():
    return settings_secret

class SettingsSecret(BaseModel):
    database_password: SecretStr = Field(...)

settings_secret_path = os.getenv(f"{ENV_VARS_PREFIX}APP_SETTINGS_SECRET", None)

if settings_secret_path is not None:
    settings_secret = SettingsSecret(**load_settings(settings_secret_path))
else:
    settings_secret = SettingsSecret(
        database_password=os.environ[f"{ENV_VARS_PREFIX}DATABASE__PASSWORD"]
        )
