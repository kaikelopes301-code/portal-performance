import os
import subprocess
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from functools import lru_cache

# Garante acesso ao projeto raiz (extractor, emailer) e carrega utils.py da raiz
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from extractor import Extractor  # type: ignore

# Carrega funções do utils.py da raiz sem colidir com portal_streamlit.utils
_normalize_unit = None
_parse_year_month = None
_root_utils_path = PROJECT_ROOT / "utils.py"
try:
    if _root_utils_path.exists():
        spec = importlib.util.spec_from_file_location("root_utils", str(_root_utils_path))
        if spec and spec.loader:
            _root_utils = importlib.util.module_from_spec(spec)
            sys.modules["root_utils"] = _root_utils  # ajuda em depuração
            spec.loader.exec_module(_root_utils)  # type: ignore[attr-defined]
            _normalize_unit = getattr(_root_utils, "normalize_unit", None)
            _parse_year_month = getattr(_root_utils, "parse_year_month", None)
except Exception:
    # fallback simples definido abaixo
    _normalize_unit = None
    _parse_year_month = None

def normalize_unit(x: str) -> str:  # type: ignore[override]
    if callable(_normalize_unit):
        try:
            return _normalize_unit(x)
        except Exception:
            pass
    return str(x).strip()

def parse_year_month(x: str) -> Optional[str]:  # type: ignore[override]
    if callable(_parse_year_month):
        try:
            return _parse_year_month(x)
        except Exception:
            pass
    import re
    s = str(x)
    m = re.search(r"(20\d{2})[-/](0?[1-9]|1[0-2])", s)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    return None


def run_pipeline(
    python_path: str,
    main_py_path: str,
    regiao: str,
    mes: str,
    xlsx_dir: str,
    dry_run: bool,
    unidades: Optional[List[str]] = None,
    selecionar_colunas: Optional[List[str]] = None,
    portal_overrides_path: Optional[str] = None,
    allow_resend: bool = False,
) -> subprocess.CompletedProcess:
    args = [python_path, main_py_path, "--regiao", regiao, "--mes", mes, "--force-mes", mes, "--xlsx-dir", xlsx_dir]
    if dry_run:
        args.append("--dry-run")
    # força modo não interativo para evitar menus no subprocess
    args.append("--non-interactive")
    if selecionar_colunas:
        args.extend(["--columns", ",".join(selecionar_colunas)])
    if unidades:
        args.extend(["--units", ",".join(unidades)])
    if portal_overrides_path:
        args.extend(["--portal-overrides-path", portal_overrides_path])
    if allow_resend:
        args.append("--allow-resend")

    print("Executando:", " ".join(args))
    # Força decodificação em UTF-8 com fallback para evitar UnicodeDecodeError no Windows (cp1252)
    completed = subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    return completed


def list_output_html_files(output_dir: str) -> List[str]:
    if not output_dir or not os.path.isdir(output_dir):
        return []
    files = [f for f in os.listdir(output_dir) if f.lower().endswith(".html")]
    files.sort()
    return [os.path.join(output_dir, f) for f in files]


def read_html_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Erro ao ler {path}: {e}"


# ---- Auxiliares de UI ----
REGIOES = ["SP1", "SP2", "SP3", "RJ", "NNE"]

def get_regions() -> List[str]:
    return REGIOES

@lru_cache(maxsize=64)
def list_units_for_region(xlsx_dir: str, regiao: str) -> List[str]:
    try:
        ex = Extractor(Path(xlsx_dir))
        wb = ex.find_workbook(regiao)
        if not wb or not wb.exists():
            return []
        df, _ = ex.read_region_sheet(wb, regiao)
        # coleta unidades similares ao main.collect_units
        units = []
        seen = set()
        # heurística: encontrar coluna de unidade
        unit_cols = [c for c in df.columns if str(c).strip().lower().startswith("unidade") or "shopping" in str(c).strip().lower()]
        unit_col = unit_cols[0] if unit_cols else None
        if not unit_col:
            return []
        INVALID_MARKERS = {
            "", "-", "nan", "na", "n/a", "preenchimento pendente", "pendente", "nao informado", "não informado",
        }
        for v in df[unit_col].dropna().astype(str):
            raw = v.strip()
            low = raw.lower()
            if low in INVALID_MARKERS:
                continue
            nu = normalize_unit(raw)
            if nu and nu not in seen:
                seen.add(nu); units.append(raw)
        units.sort()
        return units
    except Exception:
        return []

def list_months_for_region(xlsx_dir: str, regiao: str) -> List[str]:
    try:
        ex = Extractor(Path(xlsx_dir))
        wb = ex.find_workbook(regiao)
        if not wb or not wb.exists():
            return []
        df, _ = ex.read_region_sheet(wb, regiao)
        # tentar detectar coluna de mês via map_columns do processor, se disponível
        try:
            from processor import map_columns as _map  # type: ignore
            m = _map(df)
            mes_col = m.get("Mes_Emissao_NF") or m.get("Mes_Emissão_NF")
        except Exception:
            mes_col = None
        if not mes_col or mes_col not in df.columns:
            # heurística simples
            for c in df.columns:
                s = str(c).strip().lower()
                if ("emissao" in s or "emissão" in s or "competencia" in s or "competência" in s) and ("nf" in s or "nota" in s):
                    mes_col = c
                    break
        if not mes_col:
            return []
        ys: List[str] = []
        for v in df[mes_col].dropna().astype(str):
            ym = parse_year_month(v)
            if ym:
                ys.append(ym)
        uniq: List[str] = []
        seen = set()
        for y in ys:
            if y not in seen:
                seen.add(y); uniq.append(y)
        uniq.sort()
        return uniq
    except Exception:
        return []

def sanitize_filename_unit(unidade: str) -> str:
    s = "".join(ch for ch in unidade if ch.isalnum() or ch in {"_","-"," "}).strip()
    return s.replace(" ", "_")

def find_unit_html(output_dir: str, unidade: str, ym: str) -> Optional[str]:
    base = sanitize_filename_unit(unidade)
    candidate = os.path.join(output_dir, f"{base}_{ym}.html")
    return candidate if os.path.exists(candidate) else None
