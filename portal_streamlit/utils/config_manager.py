import json
import os
from typing import Any, Dict
from dotenv import load_dotenv

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CONFIG_DIR = os.path.abspath(CONFIG_DIR)
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
OVERRIDES_PATH = os.path.join(CONFIG_DIR, "overrides.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "python_path": "python",
    "main_py_path": "c:/backpperformance/main.py",
    "xlsx_dir": "c:/backpperformance/planilhas",
    "output_html_dir": "c:/backpperformance/output_html",
    "default_regiao": "SP1",
    "default_mes": "2025-08",
}

# defaults for per-unit text overrides (displayed in email header/footer)
DEFAULT_OVERRIDES: Dict[str, Dict[str, Any]] = {}


def ensure_dirs():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load_json(path: str, default: Any):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path: str, data: Any):
    ensure_dirs()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_config() -> Dict[str, Any]:
    ensure_dirs()
    data = load_json(CONFIG_PATH, DEFAULT_CONFIG)
    # backfill defaults if new keys were added
    for k, v in DEFAULT_CONFIG.items():
        data.setdefault(k, v)
    return data


def save_config(cfg: Dict[str, Any]):
    save_json(CONFIG_PATH, cfg)


def get_units_overrides() -> Dict[str, Dict[str, Any]]:
    ensure_dirs()
    data = load_json(OVERRIDES_PATH, DEFAULT_OVERRIDES)
    return data


def save_unit_override(unidade: str, fields: Dict[str, Any]):
    overrides = get_units_overrides()
    overrides.setdefault(unidade, {}).update(fields)
    save_json(OVERRIDES_PATH, overrides)


def get_env_variable(key: str, default: str = None) -> str:
    """Carrega uma variável do arquivo .env."""
    load_dotenv()
    return os.getenv(key, default)
