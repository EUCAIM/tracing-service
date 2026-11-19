from .client import DBPool
from app.core.settings import get_settings
from .traces import TracesRepo


_dbpool = None

def get_dbpool() -> DBPool:
    global _dbpool
    if _dbpool is None:
        _dbpool = DBPool()
    return _dbpool

def get_traces_repository():
    return TracesRepo(get_dbpool().get_pool())