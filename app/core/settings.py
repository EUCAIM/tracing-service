from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel
import tomllib
import yaml
from pathlib import Path
import os

from .settings_common import ENV_VARS_PREFIX, load_settings


def get_settings() -> Settings:
    if settings is None:
        raise Exception("Settings with secret not initialized.")
    return settings

def load_name_version_from_toml():
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text())
    return data["project"]["name"], data["project"]["version"]

class V2Settings(BaseModel):
    default_traces_limit: int
    
class ApiSettings(BaseModel):
    v2: V2Settings


class OIDC(BaseModel):
    url: str
    realm: str
    client: str
    audiences: list[str]


class PoolSettings(BaseModel):
    min_size: int
    max_size: int
    
class DatabaseSettings(BaseModel):
    user: str
    host: str
    port: int
    name: str
    pool: PoolSettings

class AppSettings(BaseModel):
    database: DatabaseSettings
    oidc: OIDC
    api: ApiSettings

class Settings(BaseSettings):
    app: AppSettings
    app_name: str
    version: str
    # model_config = SettingsConfigDict(env_prefix=ENV_VARS_PREFIX, env_nested_delimiter="__", env_file=".env", extra="ignore",case_sensitive=False)

# def init_settings(arg_path: str | None) -> None:
#     path = 
#     if not os.getenv("APP_SETTINGS") is None: 
        
#     elif not arg_path is None:
#         path = arg_path
path = os.getenv(f"{ENV_VARS_PREFIX}APP_SETTINGS", Path(__file__).parent.parent / "resources" / "settings.yaml") 
raw_settings = load_settings(path)
name, version = load_name_version_from_toml()

settings = Settings(**{"app_name": name, "version": version, "app": raw_settings})

# settings.app_name = name
# settings.version = version
# app_settings = AppSettings(**raw_settings)
# settings.app = app_settings
