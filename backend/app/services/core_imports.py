# core_imports.py — Importa módulos core da raiz do projeto
# Este módulo garante que o backend use os mesmos módulos core que o CLI

import sys
from pathlib import Path

# Adiciona raiz do projeto ao path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Re-exporta módulos core da raiz
# Assim outros módulos do backend podem fazer:
# from app.services.core_imports import Extractor, filter_and_prepare, etc.

from extractor import Extractor
from processor import (
    filter_and_prepare,
    map_columns,
    DEFAULT_DISPLAY_COLUMNS,
    DISPLAY_HEADER_SYNONYMS,
    SLA_DESCONTO_CANONICAL,
)
from emailer import Emailer
from config_loader import (
    load_overrides,
    resolve_overrides,
    ResolvedConfig,
    OverrideConfigError,
)
from utils import (
    fmt_brl,
    normalize_unit,
    parse_year_month,
    previous_month_from_today,
    safe_write_text,
    safe_read_text,
    safe_parse_json,
    load_env,
    ensure_sqlite,
    log_sqlite,
    has_successful_send,
    normalize_text_full,
    is_missing_like,
    split_emails,
)

__all__ = [
    # Extractor
    'Extractor',
    # Processor
    'filter_and_prepare',
    'map_columns',
    'DEFAULT_DISPLAY_COLUMNS',
    'DISPLAY_HEADER_SYNONYMS',
    'SLA_DESCONTO_CANONICAL',
    # Emailer
    'Emailer',
    # Config Loader
    'load_overrides',
    'resolve_overrides',
    'ResolvedConfig',
    'OverrideConfigError',
    # Utils
    'fmt_brl',
    'normalize_unit',
    'parse_year_month',
    'previous_month_from_today',
    'safe_write_text',
    'safe_read_text',
    'safe_parse_json',
    'load_env',
    'ensure_sqlite',
    'log_sqlite',
    'has_successful_send',
    'normalize_text_full',
    'is_missing_like',
    'split_emails',
]
