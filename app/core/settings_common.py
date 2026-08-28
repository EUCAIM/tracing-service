import yaml


ENV_VARS_PREFIX = "TRACING_"

def load_settings(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)
