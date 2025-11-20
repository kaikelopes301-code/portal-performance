# utils.py — versão final revisada

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
import unicodedata

import pandas as pd

# --------------------------
# Helpers
# --------------------------
def normalize_text_full(
    s: Any, 
    remove_accents: bool = True,
    lowercase: bool = True,
    normalize_dashes: bool = True
) -> str:
    """Normalização completa de texto (consolidada de _norm, _norm_txt, _norm_spaces).
    
    Args:
        s: Texto a normalizar (aceita qualquer tipo)
        remove_accents: Remove acentos via NFD decomposition (padrão: True)
        lowercase: Converte para minúsculas (padrão: True)
        normalize_dashes: Converte travessões (–, —) em hífens (-) (padrão: True)
    
    Returns:
        String normalizada (vazia se input for None)
    
    Exemplos:
        >>> normalize_text_full("  Café—Bar  ")
        'cafe-bar'
        >>> normalize_text_full("HELLO\\nWORLD", lowercase=False)
        'HELLO WORLD'
    """
    if s is None:
        return ""
    
    s = str(s)
    
    # Remove NBSP (non-breaking space) e quebras de linha
    s = s.replace("\u00A0", " ").replace("\n", " ").replace("\r", " ")
    
    # Normaliza travessões para hífen
    if normalize_dashes:
        s = s.replace("–", "-").replace("—", "-")
    
    # Strip inicial e lowercase
    s = s.strip()
    if lowercase:
        s = s.lower()
    
    # Remove acentos (NFD decomposition)
    if remove_accents:
        s = "".join(
            ch for ch in unicodedata.normalize("NFD", s) 
            if unicodedata.category(ch) != "Mn"
        )
    
    # Condensa múltiplos espaços em um único
    s = " ".join(s.split())
    
    return s.strip()


def _norm_spaces(s: str) -> str:
    """Normaliza espaços: troca NBSP por espaço, remove quebras e condensa.
    
    DEPRECATED: Use normalize_text_full(s, remove_accents=False, lowercase=False, normalize_dashes=False)
    Mantido para compatibilidade com código existente.
    """
    return normalize_text_full(s, remove_accents=False, lowercase=False, normalize_dashes=False)

def safe_read_text(path, encoding="utf-8"):
    """Lê um arquivo de texto de forma segura, retornando None em caso de erro."""
    try:
        with open(path, "r", encoding=encoding) as f:
            return f.read()
    except Exception:
        return None

def safe_write_text(path: Path, content: str, encoding: str = "utf-8") -> bool:
    """Grava conteúdo em um arquivo de texto de forma segura.
    Retorna True se conseguir gravar, False em caso de erro.
    """
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding=encoding) as f:
            f.write(content if content is not None else "")
        return True
    except Exception:
        return False

def safe_parse_json(text):
    """Converte uma string em JSON de forma segura, retornando None se falhar."""
    try:
        return json.loads(text)
    except Exception:
        return None

def configure_utf8_stdio() -> None:
    """Force stdout/stderr to UTF-8 to avoid mangled accents."""
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
                    continue
                except Exception:
                    pass
        except Exception:
            pass


# ==========================
# Placeholders (pendências)
# ==========================

def _normalize_placeholder_label(value: Any) -> str:
    text = "" if value is None else _norm_spaces(str(value).lower())
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return " ".join(text.split())

PENDENTE_DEFAULT = "Informação pendente"
PENDENTE_LABELS = {
    # principais
    "Informação pendente", "Preenchimento pendente", "Pendente",
    # variações minúsculas / sem acento
    "informação pendente", "informacao pendente",
    "preenchimento pendente", "pendente",
}

PENDENTE_LABELS_NORMALIZED = {
    _normalize_placeholder_label(label)
    for label in PENDENTE_LABELS
}

# Regra especial por coluna (se quiser usar em templates)
BRL_PLACEHOLDER = "Preenchimento pendente"

PLACEHOLDER_BY_COLUMN = {
    "Desconto SLA Mês": BRL_PLACEHOLDER,
}

def is_missing_like(x: Any) -> bool:
    """True para None/''/NaN/Inf e strings equivalentes ('nan','inf',...)."""
    if x is None:
        return True
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return True
    s = _norm_spaces(str(x)).lower()  # <-- NBSP/espacos normalizados
    return s == "" or s in {"nan", "inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"}

def coalesce_placeholder(x: Any, placeholder: str = PENDENTE_DEFAULT):
    """Retorna placeholder quando vazio/NaN/rotulado como pendente; caso contrário, retorna o próprio valor."""
    if is_missing_like(x):
        return placeholder
    if isinstance(x, str) and _normalize_placeholder_label(x) in PENDENTE_LABELS_NORMALIZED:
        return placeholder
    return x


# ==========================
# Constantes e Normalização
# ==========================

BR_MONTHS = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}

def normalize_text(s: Any) -> str:
    return "" if s is None else str(s).strip()

def normalize_unit(s: str) -> str:
    """Normaliza acentos/espaços/caixa para comparação de unidade."""
    s = normalize_text(s)
    s = unicodedata.normalize("NFD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


# ==========================
# Datas (mês/ano)
# ==========================

def parse_year_month(s: Optional[str]) -> Optional[str]:
    """
    Retorna 'YYYY-MM' a partir de:
      - 'YYYY-MM', 'YYYY/MM'
      - 'MM/YYYY'
      - 'DD/MM/YYYY'
      - 'YYYY-MM-DD' (ou com hora)
      - 'Agosto/2025' (mês por extenso, PT-BR)
      - serial Excel (ex.: 45073)
    """
    if s is None:
        return None
    s = _norm_spaces(str(s))
    if not s:
        return None

    # Remover hora (ou 'T')
    s = s.replace("T", " ")
    if " " in s:
        s = s.split(" ")[0].strip()

    # YYYY-MM
    m = re.match(r"^(\d{4})[-/.](\d{1,2})$", s)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        if 1 <= mo <= 12:
            return f"{y:04d}-{mo:02d}"

    # MM/YYYY
    m = re.match(r"^(\d{1,2})[-/.](\d{4})$", s)
    if m:
        mo, y = int(m.group(1)), int(m.group(2))
        if 1 <= mo <= 12:
            return f"{y:04d}-{mo:02d}"

    # DD/MM/YYYY
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", s)
    if m:
        _, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12:
            return f"{y:04d}-{mo:02d}"

    # mês por extenso
    s_low = s.lower()
    for k, v in BR_MONTHS.items():
        if v.lower() in s_low:
            m2 = re.search(r"(20\d{2}|19\d{2})", s_low)
            if m2:
                y = int(m2.group(1))
                return f"{y:04d}-{k:02d}"

    # YYYY-MM-DD
    m = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", s)
    if m:
        y, mo, _ = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12:
            return f"{y:04d}-{mo:02d}"

    # serial Excel
    if s.isdigit():
        try:
            base = date(1899, 12, 30)  # epoch Excel
            d = base + timedelta(days=int(s))
            return f"{d.year:04d}-{d.month:02d}"
        except Exception:
            pass

    return None

def previous_month_from_today(today: Optional[date] = None) -> str:
    if not today:
        today = date.today()
    first = today.replace(day=1)
    prev_last = first - timedelta(days=1)
    return prev_last.strftime("%Y-%m")

def format_year_month_extenso(ym: str) -> str:
    """'YYYY-MM' -> 'Mês/AAAA'."""
    y = int(ym[:4]); m = int(ym[-2:])
    return f"{BR_MONTHS.get(m, str(m))}/{y}"


# ==========================
# Dinheiro (BRL)
# ==========================

def parse_brl_money(s: Optional[str]) -> Optional[Decimal]:
    """
    Converte strings de moeda BR (ex.: "R$ 3.351,13", "-R$ 3.351,13", "3351,13")
    em Decimal("3351.13"). Retorna None em caso de falha.
    """
    if s is None:
        return None
    raw = _norm_spaces(str(s))  # <-- NBSP/espacos normalizados
    if not raw:
        return None

    negative = False
    if raw.startswith("(") and raw.endswith(")"):
        negative = True
        raw = raw[1:-1].strip()

    raw = raw.replace("R$", "").strip()

    if not raw:
        return None

    minus_count = raw.count("-")
    if minus_count % 2 == 1:
        negative = not negative
    raw = raw.replace("-", "").replace("+", "")

    # remove quaisquer espaços residuais
    raw = raw.replace(" ", "")

    # mantém apenas dígitos, pontos e vírgulas
    raw = re.sub(r"[^0-9.,]", "", raw)

    # Trata separadores
    if "," in raw and "." in raw:
        raw = raw.replace(".", "").replace(",", ".")
    else:
        if raw.count(",") > 1:
            head, tail = raw.rsplit(",", 1)
            raw = head.replace(",", "") + "." + tail
        elif raw.count(",") == 1:
            raw = raw.replace(",", ".")
        if raw.count(".") > 1:
            head, tail = raw.rsplit(".", 1)
            raw = head.replace(".", "") + "." + tail

    raw = re.sub(r"[^0-9.]", "", raw)
    if raw.count(".") > 1:
        head, tail = raw.rsplit(".", 1)
        raw = head.replace(".", "") + "." + tail

    if not raw or raw == ".":
        return None

    try:
        value = Decimal(raw)
    except (InvalidOperation, ValueError):
        return None
    if value.is_nan() or value.is_infinite():
        return None
    return -value if negative else value

def _coerce_decimal_for_brl(value: Any) -> Optional[Decimal]:
    if isinstance(value, Decimal):
        try:
            if value.is_nan() or value.is_infinite():
                return None
        except Exception:
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
        stripped = _norm_spaces(value)
        if not stripped:
            return None
        return parse_brl_money(stripped)
    stripped = _norm_spaces(str(value))
    if not stripped:
        return None
    return parse_brl_money(stripped)

def fmt_brl(value: Any, placeholder: Optional[str] = BRL_PLACEHOLDER) -> str:
    """
    Formata como "R$ 1.234,56" (ROUND_HALF_UP).
    Retorna placeholder quando vazio ou não parseável.
    """
    if placeholder is not None and is_missing_like(value):
        return placeholder

    normalized_placeholders = set(PENDENTE_LABELS_NORMALIZED)
    if placeholder is not None:
        normalized_placeholders.add(_normalize_placeholder_label(placeholder))

    if isinstance(value, str):
        stripped = _norm_spaces(value)
        if not stripped:
            return placeholder if placeholder is not None else "R$ 0,00"
        if placeholder is not None and _normalize_placeholder_label(stripped) in normalized_placeholders:
            return placeholder

    try:
        dec = _coerce_decimal_for_brl(value)
    except (InvalidOperation, ValueError, TypeError):
        dec = None

    if dec is None:
        if placeholder is not None:
            return placeholder
        dec = Decimal("0")

    dec = dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    negative = dec < 0
    magnitude = -dec if negative else dec
    formatted = f"{magnitude:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    sign = "-" if negative else ""
    return f"R$ {sign}{formatted}" if sign else f"R$ {formatted}"

# Compatibilidade: algumas partes do projeto usam 'format_brl'
def format_brl(value: Any) -> str:
    return fmt_brl(value)

def fmt_percentage(value: Any, placeholder: Optional[str] = None) -> str:
    """
    Formata como porcentagem "1,23%" (ROUND_HALF_UP).
    - Aceita valores numéricos (Decimal/float/int) ou strings no padrão BR.
    - Se o valor vier em fração (ex.: 0,02), converte para 2,00% multiplicando por 100.
    - Se já vier em pontos percentuais (ex.: 2,00), mantém como 2,00%.
    - Retorna placeholder quando vazio ou não parseável.
    """
    if placeholder is not None and is_missing_like(value):
        return placeholder

    normalized_placeholders = set(PENDENTE_LABELS_NORMALIZED)
    if placeholder is not None:
        normalized_placeholders.add(_normalize_placeholder_label(placeholder))

    if isinstance(value, str):
        stripped = _norm_spaces(value)
        if not stripped:
            return placeholder if placeholder is not None else "0,00%"
        if placeholder is not None and _normalize_placeholder_label(stripped) in normalized_placeholders:
            return placeholder

    try:
        dec = _coerce_decimal_for_brl(value)
    except (InvalidOperation, ValueError, TypeError):
        dec = None

    if dec is None:
        if placeholder is not None:
            return placeholder
        dec = Decimal("0")

    # Heurística: se o valor absoluto for <= 1, interpretamos como fração (ex.: 0,02 => 2%)
    try:
        if abs(dec) <= Decimal("1"):
            dec = dec * Decimal("100")
    except Exception:
        # Em caso de qualquer problema de comparação/conversão, segue sem multiplicar
        pass

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
    """
    Retorna True se existir pelo menos um envio bem-sucedido no log.
    - Filtra por regiao/unidade/mes quando informados.
    - Por padrão ignora registros de dry-run.
    - Considera status em ok_status (default: ['success', 'sent']).
    """
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

def to_base64_image(img_path: Path) -> Optional[str]:
    try:
        if img_path.exists():
            data = img_path.read_bytes()
            mime = "image/png" if img_path.suffix.lower() == ".png" else "image/jpeg"
            b64 = base64.b64encode(data).decode("ascii")
            return f"data:{mime};base64,{b64}"
    except Exception:
        return None
    return None


# ==========================
# E-mails / JSON helpers
# ==========================

def split_emails(s: str) -> List[str]:
    s = (s or "").replace(",", ";").replace("|", ";").replace("\n", ";").replace("\r", ";")
    parts = [p.strip() for p in s.split(";") if p.strip()]
    good: List[str] = []
    for p in parts:
        # aceita "Nome <email@dominio>"
        m = re.search(r"<([^>]+)>", p)
        if m:
            p = m.group(1)
        if "@" in p and "." in p.split("@")[-1]:
            good.append(p)
    # dedupe preservando ordem
    seen = set(); out: List[str] = []
    for g in good:
        gl = g.lower()
        if gl not in seen:
            seen.add(gl); out.append(g)
    return out

def read_json_env_value(s: str) -> Any:
    try:
        return json.loads(s)
    except Exception:
        return {}

def pick_account(outlook, sender_email: str):
    """Seleciona a conta do Outlook com SMTP igual ao sender_email, se existir."""
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
