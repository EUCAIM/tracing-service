from pydantic_settings import BaseSettings
from pydantic import BaseModel
import tomllib
from pathlib import Path
import os

from .settings_common import ENV_VARS_PREFIX, load_settings

_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        path = os.getenv(f"{ENV_VARS_PREFIX}APP_SETTINGS", Path(__file__).parent.parent / "resources" / "settings.yaml") 
        raw_settings = load_settings(path)
        name, version = load_name_version_from_toml()
        _settings = Settings(**{"app_name": name, "version": version, "app": raw_settings})
    return _settings

def load_name_version_from_toml():
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text())
    return data["project"]["name"], data["project"]["version"]

class V2Settings(BaseModel):
    default_traces_limit: int
    
class ApiSettings(BaseModel):
    prefix: str
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
