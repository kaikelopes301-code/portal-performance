"""Core modules for data extraction, processing and email generation."""
from pathlib import Path
import sys

# Adiciona a raiz do projeto ao path para imports dos módulos originais
ROOT_DIR = Path(__file__).parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Re-exporta módulos da raiz
from extractor import Extractor
from processor import filter_and_prepare, map_columns, DEFAULT_DISPLAY_COLUMNS
from emailer import Emailer
import utils

__all__ = [
    'Extractor', 
    'filter_and_prepare', 
    'map_columns', 
    'DEFAULT_DISPLAY_COLUMNS',
    'Emailer', 
    'utils',
    'ROOT_DIR',
]
