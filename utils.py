# utils_optimized.py — versão otimizada com cache e menos conversões

import re
import json
import sqlite3
import math
import base64
import os
import sys
import io
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from functools import lru_cache
import unicodedata

import pandas as pd

# --------------------------
# Cache para normalização (evita reprocessamento)
# --------------------------
@lru_cache(maxsize=1024)
def normalize_text_full(
    s: str,  # Removido Any para permitir cache
    remove_accents: bool = True,
    lowercase: bool = True,
    normalize_dashes: bool = True
) -> str:
    """Normalização completa com cache."""
    if not s:
        return ""
    
    # Remove NBSP e quebras
    s = s.replace("\u00A0", " ").replace("\n", " ").replace("\r", " ")
    
    if normalize_dashes:
        s = s.replace("–", "-").replace("—", "-")
    
    s = s.strip()
    if lowercase:
        s = s.lower()
    
    if remove_accents:
        s = "".join(
            ch for ch in unicodedata.normalize("NFD", s) 
            if unicodedata.category(ch) != "Mn"
        )
    
    # Condensa espaços
    s = " ".join(s.split())
    return s.strip()


# Wrapper para compatibilidade (converte para string antes)
def normalize_text_full_safe(s: Any, **kwargs) -> str:
    """Wrapper seguro que aceita Any."""
    if s is None:
        return ""
    return normalize_text_full(str(s), **kwargs)


def _norm_spaces(s: str) -> str:
    """DEPRECATED: Use normalize_text_full."""
    return normalize_text_full(s, remove_accents=False, lowercase=False, normalize_dashes=False)


# --------------------------
# Regex pré-compilados
# --------------------------
YEAR_MONTH_PATTERNS = [
    re.compile(r"^(\d{4})[-/.](\d{1,2})$"),
    re.compile(r"^(\d{1,2})[-/.](\d{4})$"),
    re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$"),
    re.compile(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$"),
    re.compile(r"(20\d{2}|19\d{2})"),
]

BRL_CLEAN_PATTERN = re.compile(r"[^0-9.,]")
MULTIPLE_SPACES = re.compile(r"\s+")


def safe_read_text(path, encoding="utf-8"):
    """Lê arquivo de forma segura."""
    try:
        with open(path, "r", encoding=encoding) as f:
            return f.read()
    except Exception:
        return None


def safe_write_text(path: Path, content: str, encoding: str = "utf-8") -> bool:
    """Grava arquivo de forma segura."""
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding=encoding) as f:
            f.write(content if content is not None else "")
        return True
    except Exception:
        return False


def safe_parse_json(text):
    """Parse JSON seguro."""
    try:
        return json.loads(text)
    except Exception:
        return None


def configure_utf8_stdio() -> None:
    """Força UTF-8 em stdout/stderr."""
    try:
        if os.name == "nt":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)
            kernel32.SetConsoleCP(65001)
    except Exception:
        pass

    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
            continue
        except AttributeError:
            if hasattr(stream, "buffer"):
                try:
                    wrapper = io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace")
                    setattr(sys, stream_name, wrapper)
                except Exception:
                    pass


# ==========================
# Placeholders (otimizado)
# ==========================
PENDENTE_DEFAULT = "Informação pendente"

# ✅ Lista original para compatibilidade com processor.py
PENDENTE_LABELS = [
    "Informação pendente",
    "Preenchimento pendente",
    "Pendente",
    "Não informado",
]

# ✅ Versão normalizada para comparações rápidas
PENDENTE_LABELS_NORMALIZED = frozenset([
    "informacao pendente", 
    "preenchimento pendente", 
    "pendente",
    "nao informado",
])

BRL_PLACEHOLDER = "Preenchimento pendente"
PLACEHOLDER_BY_COLUMN = {"Desconto SLA Mês": BRL_PLACEHOLDER}

# Set pré-computado para verificação rápida
MISSING_VALUES = frozenset({"", "nan", "inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"})


def is_missing_like(x: Any) -> bool:
    """
    Verifica se valor é missing/ausente (otimizado).
    
    Considera como missing:
    - None
    - NaN e Inf (float)
    - Strings vazias
    - Valores em MISSING_VALUES ("nan", "inf", etc.)
    - Placeholders normalizados (PENDENTE_LABELS_NORMALIZED)
    """
    if x is None:
        return True
    if isinstance(x, float):
        return math.isnan(x) or math.isinf(x)
    
    s = str(x).strip()
    if not s:  # String vazia
        return True
    
    low = s.lower()
    if low in MISSING_VALUES:
        return True
    
    # Verifica placeholders normalizados
    norm = _normalize_placeholder_label_cached(s)
    return norm in PENDENTE_LABELS_NORMALIZED


@lru_cache(maxsize=256)
def _normalize_placeholder_label_cached(value: str) -> str:
    """Versão com cache da normalização de placeholder."""
    text = unicodedata.normalize("NFD", value.lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return " ".join(text.split())


def coalesce_placeholder(x: Any, placeholder: str = PENDENTE_DEFAULT):
    """Retorna placeholder quando necessário."""
    if is_missing_like(x):
        return placeholder
    if isinstance(x, str):
        if _normalize_placeholder_label_cached(x.strip()) in PENDENTE_LABELS_NORMALIZED:
            return placeholder
    return x


# ==========================
# Constantes
# ==========================
BR_MONTHS = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


def normalize_text(s: Any) -> str:
    """Normalização básica."""
    return "" if s is None else str(s).strip()


@lru_cache(maxsize=512)
def normalize_unit(s: str) -> str:
    """Normaliza unidade com cache."""
    if not s:
        return ""
    s = unicodedata.normalize("NFD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = MULTIPLE_SPACES.sub(" ", s).strip().lower()
    return s


# ==========================
# Datas (otimizado com regex pré-compilados)
# ==========================
@lru_cache(maxsize=1024)
def parse_year_month(s: Any, warn: bool = False) -> Optional[str]:
    """
    Tenta extrair YYYY-MM de uma string variada.
    Retorna None se falhar.
    """
    if not s:
        return None
    
    s_orig = s
    s = str(s).strip()
    if not s:
        return None

    # Remove hora
    if " " in s or "T" in s:
        s = s.replace("T", " ").split(" ")[0].strip()

    # YYYY-MM
    m = YEAR_MONTH_PATTERNS[0].match(s)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        if 1 <= mo <= 12:
            return f"{y:04d}-{mo:02d}"

    # MM/YYYY
    m = YEAR_MONTH_PATTERNS[1].match(s)
    if m:
        mo, y = int(m.group(1)), int(m.group(2))
        if 1 <= mo <= 12:
            return f"{y:04d}-{mo:02d}"

    # DD/MM/YYYY
    m = YEAR_MONTH_PATTERNS[2].match(s)
    if m:
        _, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12:
            return f"{y:04d}-{mo:02d}"

    # Mês por extenso
    s_low = s.lower()
    for k, v in BR_MONTHS.items():
        if v.lower() in s_low:
            m2 = YEAR_MONTH_PATTERNS[4].search(s_low)
            if m2:
                y = int(m2.group(1))
                return f"{y:04d}-{k:02d}"

    # YYYY-MM-DD
    m = YEAR_MONTH_PATTERNS[3].match(s)
    if m:
        y, mo, _ = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12:
            return f"{y:04d}-{mo:02d}"

    # Serial Excel
    if s.isdigit():
        try:
            base = date(1899, 12, 30)
            d = base + timedelta(days=int(s))
            return f"{d.year:04d}-{d.month:02d}"
        except Exception:
            pass

    if warn:
        print(f"[WARN] Falha ao parsear data: '{s_orig}'")
    return None


def previous_month_from_today(today: Optional[date] = None) -> str:
    """Retorna mês anterior."""
    if not today:
        today = date.today()
    first = today.replace(day=1)
    prev_last = first - timedelta(days=1)
    return prev_last.strftime("%Y-%m")


def format_year_month_extenso(ym: str) -> str:
    """Formata YYYY-MM para extenso."""
    y = int(ym[:4])
    m = int(ym[-2:])
    return f"{BR_MONTHS.get(m, str(m))}/{y}"


# ==========================
# Dinheiro (otimizado)
# ==========================
def parse_brl_money(s: Optional[str]) -> Optional[Decimal]:
    """Parse BRL otimizado."""
    if not s:
        return None
    
    raw = str(s).replace("\u00A0", " ").strip()
    if not raw:
        return None

    negative = False
    if raw.startswith("(") and raw.endswith(")"):
        negative = True
        raw = raw[1:-1].strip()

    raw = raw.replace("R$", "").strip()
    if not raw:
        return None

    # Conta negativos
    minus_count = raw.count("-")
    if minus_count % 2 == 1:
        negative = not negative
    
    raw = raw.replace("-", "").replace("+", "").replace(" ", "")
    raw = BRL_CLEAN_PATTERN.sub("", raw)

    # Trata separadores
    if "," in raw and "." in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif raw.count(",") > 1:
        head, tail = raw.rsplit(",", 1)
        raw = head.replace(",", "") + "." + tail
    elif raw.count(",") == 1:
        raw = raw.replace(",", ".")
    
    if raw.count(".") > 1:
        head, tail = raw.rsplit(".", 1)
        raw = head.replace(".", "") + "." + tail

    if not raw or raw == ".":
        return None

    try:
        value = Decimal(raw)
        if value.is_nan() or value.is_infinite():
            return None
        return -value if negative else value
    except (InvalidOperation, ValueError):
        return None


def _coerce_decimal_for_brl(value: Any) -> Optional[Decimal]:
    """Coerção para Decimal otimizada."""
    if isinstance(value, Decimal):
        if value.is_nan() or value.is_infinite():
            return None
        return value
    
    if value is None:
        return None
    
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(value, float):
            if pd.isna(value) or math.isnan(value) or math.isinf(value):
                return None
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None
    
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        return parse_brl_money(stripped)
    
    return parse_brl_money(str(value).strip())


def fmt_brl(value: Any, placeholder: Optional[str] = BRL_PLACEHOLDER) -> str:
    """Formata BRL."""
    if placeholder is not None and is_missing_like(value):
        return placeholder

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return placeholder if placeholder is not None else "R$ 0,00"
        # Verifica placeholder
        if placeholder and _normalize_placeholder_label_cached(stripped) in PENDENTE_LABELS_NORMALIZED:
            return placeholder

    dec = _coerce_decimal_for_brl(value)
    if dec is None:
        return placeholder if placeholder is not None else "R$ 0,00"

    dec = dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    negative = dec < 0
    magnitude = -dec if negative else dec
    formatted = f"{magnitude:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    sign = "-" if negative else ""
    return f"R$ {sign}{formatted}" if sign else f"R$ {formatted}"


def format_brl(value: Any) -> str:
    """Compatibilidade."""
    return fmt_brl(value)


def fmt_percentage(value: Any, placeholder: Optional[str] = None) -> str:
    """Formata porcentagem."""
    if placeholder is not None and is_missing_like(value):
        return placeholder

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return placeholder if placeholder is not None else "0,00%"

    dec = _coerce_decimal_for_brl(value)
    if dec is None:
        return placeholder if placeholder is not None else "0,00%"

    # Heurística: se <= 1, multiplica por 100
    if abs(dec) <= Decimal("1"):
        dec = dec * Decimal("100")

    dec = dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    negative = dec < 0
    magnitude = -dec if negative else dec
    formatted = f"{magnitude:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    sign = "-" if negative else ""
    return f"{sign}{formatted}%" if sign else f"{formatted}%"


# ==========================
# Env / Arquivos / Banco
# ==========================
def load_env(env_path: Path) -> Dict[str, str]:
    """Carrega .env."""
    data: Dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                data[k.strip()] = v.strip()
    return data


def ensure_sqlite(db_path: Path):
    """Garante tabela SQLite."""
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS send_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            regiao TEXT,
            unidade TEXT,
            mes TEXT,
            dry_run INTEGER,
            status TEXT,
            subject TEXT,
            recipients TEXT,
            html_path TEXT,
            workbook_path TEXT,
            sheet_name TEXT,
            row_count INTEGER,
            sum_valor_mensal_final REAL,
            error TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def log_sqlite(db_path: Path, row: Dict[str, Any]):
    """Loga no SQLite."""
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cols = [
        "ts","regiao","unidade","mes","dry_run","status","subject","recipients",
        "html_path","workbook_path","sheet_name","row_count","sum_valor_mensal_final","error"
    ]
    vals = [row.get(c) for c in cols]
    cur.execute(
        f"INSERT INTO send_logs ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})",
        vals
    )
    conn.commit()
    conn.close()


def has_successful_send(
    db_path: Path,
    regiao: Optional[str] = None,
    unidade: Optional[str] = None,
    mes: Optional[str] = None,
    include_dry_run: bool = False,
    ok_status: Optional[List[str]] = None,
) -> bool:
    """Verifica envio bem-sucedido."""
    try:
        statuses = ok_status or ["success", "sent"]
        placeholders = ",".join(["?"] * len(statuses))
        sql = f"SELECT 1 FROM send_logs WHERE LOWER(status) IN ({placeholders})"
        params: List[Any] = [s.lower() for s in statuses]

        if not include_dry_run:
            sql += " AND (dry_run IS NULL OR dry_run = 0)"

        if regiao:
            sql += " AND regiao = ?"
            params.append(regiao)
        if unidade:
            sql += " AND unidade = ?"
            params.append(unidade)
        if mes:
            sql += " AND mes = ?"
            params.append(mes)

        sql += " LIMIT 1"

        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute(sql, params)
        row = cur.fetchone()
        conn.close()
        return row is not None
    except Exception:
        return False


# Cache para imagens base64
_IMAGE_CACHE: Dict[str, str] = {}

def to_base64_image(img_path: Path) -> Optional[str]:
    """Converte imagem para base64 com cache."""
    key = str(img_path)
    if key in _IMAGE_CACHE:
        return _IMAGE_CACHE[key]
    
    try:
        if img_path.exists():
            data = img_path.read_bytes()
            mime = "image/png" if img_path.suffix.lower() == ".png" else "image/jpeg"
            b64 = base64.b64encode(data).decode("ascii")
            result = f"data:{mime};base64,{b64}"
            _IMAGE_CACHE[key] = result
            return result
    except Exception:
        return None
    return None


# ==========================
# E-mails
# ==========================
def split_emails(s: str, warn: bool = False) -> List[str]:
    """Split de emails otimizado."""
    s = (s or "").replace(",", ";").replace("|", ";").replace("\n", ";").replace("\r", ";")
    parts = [p.strip() for p in s.split(";") if p.strip()]
    good: List[str] = []
    seen = set()
    
    for p in parts:
        # Extrai email de "Nome <email>"
        m = re.search(r"<([^>]+)>", p)
        if m:
            p = m.group(1)
        if "@" in p and "." in p.split("@")[-1]:
            pl = p.lower()
            if pl not in seen:
                seen.add(pl)
                good.append(p)
        elif warn:
            print(f"[WARN] Email inválido descartado: '{p}'")
    
    return good


def read_json_env_value(s: str) -> Any:
    """Parse JSON de env."""
    try:
        return json.loads(s)
    except Exception:
        return {}


def pick_account(outlook, sender_email: str):
    """Seleciona conta Outlook."""
    try:
        ns = outlook.Session
        accounts = ns.Accounts
        for i in range(1, accounts.Count + 1):
            acc = accounts.Item(i)
            if getattr(acc, "SmtpAddress", "").lower() == sender_email.lower():
                return acc
    except Exception:
        return None
    return None