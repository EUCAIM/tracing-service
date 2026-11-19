
from .traces import TracesDatasetsManager
from app.db.v2.dependencies import get_traces_repository

def get_traces_datasets_manager() -> TracesDatasetsManager:
    return TracesDatasetsManager(get_traces_repository())
