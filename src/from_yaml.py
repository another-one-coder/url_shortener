from pathlib import Path
from yaml import safe_load


def get_yaml(file_path: str):
    with open(Path(__file__).parent.parent / file_path) as f:
        return safe_load(f)


DATABASE_CONFIG: dict[str, str] = get_yaml('config/config.yaml')
PROTOCOLS: dict[str, str] = get_yaml('data/http_protocols.yaml')
