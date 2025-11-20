# processor.py — colunas padrão + 9 extras opcionais; compatível com emailer.py
from typing import Dict, Any, List, Tuple, Optional
from decimal import Decimal, InvalidOperation
import unicodedata
import math
import re
import pandas as pd

from utils import (
    fmt_brl,
    PENDENTE_LABELS,
    split_emails,
    normalize_unit,
    parse_year_month,
    is_missing_like,
    parse_brl_money,
    normalize_text_full,
)
    
# -----------------------------
# Constantes e sinônimos
# -----------------------------
SLA_DESCONTO_CANONICAL = "Desconto SLA Mês"
SLA_DESCONTO_SYNONYMS: List[str] = [
    "Desc. SLA Mês","Desc. SLA Mês / Equip.","Desc_SLA","Desconto_SLA_Mes","Desconto_SLA_Mês",
    "Desconto SLA Mes","Desconto_SLA_Mes_Desconto_Equipamentos","SLA Desconto Mês","Desconto SLA","SLA Mês (Desconto)",
]

# As 9 colunas extras opcionais (nomes canônicos)
EXTRA_OPTIONAL_CANONICALS: List[str] = [
    "Desconto SLA Retroativo","Desconto Equipamentos","Prêmio Assiduidade","Outros descontos",
    "Taxa de prorrogação do prazo pagamento","Valor mensal com prorrogação do prazo pagamento",
    "Retroativo de dissídio","Parcela (x/x)","Valor extras validado Atlas",
]

# ------------------------------------------------------------
# Mapeamento de colunas (padrão -> possíveis variações)
# ------------------------------------------------------------
COLUMN_CANDIDATES: Dict[str, List[str]] = {
    "Unidade": ["Unidade","Shopping","Unidade/Shopping","Unid.","Unidade - Shopping"],
    "Mes_Emissao_NF": [
        "Mês de emissão da NF","Mês emissão NF","Mês de emissão Nota Fiscal","Mes Emissao NF","Mes NF",
        "Competencia NF","Competência NF","Competencia","Competência",
    ],
    "Email_Destinatario": [
        "E-mail","Email","E-mails","Emails","Contatos","Destinatários","Destinatarios",
        "Destinatários (E-mail)","Destinatários (Email)",
    ],
    "Valor_Mensal_Final": [
        "Valor Mensal Final","Valor Mensal","Total Faturamento","Valor com Descontos",
        "Valor Final","Valor Faturado (Final)","Valor Final Faturamento","Valor Faturado",
    ],
    "Contrato": ["Contrato","Número do Pedido","Pedido","OrderNumber","Nº Pedido","Nº do Pedido"],
    "Funcionario": ["Funcionário","Colaborador","Funcionário/Colaborador","Nome do Funcionário"],
    "Status": ["Status","Status do Contrato","Situação","Situacao"],
}

# Cabeçalhos padrão de exibição
DEFAULT_DISPLAY_COLUMNS: List[str] = [
    "Unidade","Categoria","Fornecedor","HC Planilha","Dias Faltas","Horas Atrasos",
    "Valor Planilha","Desc. Falta Validado Atlas","Desc. Atraso Validado Atlas",
    SLA_DESCONTO_CANONICAL,"Valor Mensal Final","Mês referência para faturamento","Mês de emissão da NF",
]
# Sinônimos aceitos na whitelist (exibição)
DISPLAY_HEADER_SYNONYMS: Dict[str, List[str]] = {
    "Desc. Falta Validado Atlas": ["Desconto Falta Validado Atlas","Desc_Falta","Desconto_Falta_Validado_Atlas"],
    "Desc. Atraso Validado Atlas": ["Desconto Atraso Validado Atlas","Desc_Atraso","Desconto_Atrasos_Validado_Atlas"],
    SLA_DESCONTO_CANONICAL: [*SLA_DESCONTO_SYNONYMS],
    "Desconto SLA Retroativo": [
        "Desc. SLA Retroativo","Desc SLA Retroativo","Retroativo SLA (desconto)","Retroativo SLA",
        "Desconto Retroativo SLA","SLA Retroativo (desconto)","SLA desconto retroativo","SLA - Desconto Retroativo",
        "Desconto SLA (Retroativo)","Retroativo (SLA)","RETROATIVO SLA",
        # abreviações e variações comuns
        "Desc. SLA Ret.","Desc SLA Ret","SLA Ret.","Retro. SLA","SLA retro","Desconto SLA Ret",
    ],
    "Desconto Equipamentos": ["Desc. Equipamentos","Desconto de Equipamentos","Desc Equipamentos"],
    "Prêmio Assiduidade": ["Premio Assiduidade","Premiação Assiduidade","Premiacao Assiduidade"],
    "Outros descontos": ["Outros Descontos","Outros desc.","Outros Desc","Outro desconto"],
    "Taxa de prorrogação do prazo pagamento": [
        "Taxa de prorrogação do prazo de pagamento","Taxa prorrogacao prazo pagamento",
        "Taxa prorrogação pagamento","Taxa prorrogação",
    ],
    "Valor mensal com prorrogação do prazo pagamento": [
        "Valor mensal com prorrogação do prazo de pagamento","Valor mensal c/ prorrogação",
        "Valor mensal prorrogado","Valor com prorrogação do prazo pagamento",
    ],
    "Retroativo de dissídio": ["Retroativo dissidio","Retroativo de Dissidio","Retroativo Dissídio"],
    "Parcela (x/x)": ["Parcela","Parcela x/x","Parcela(x/x)","Nº parcela","Numero parcela","No parcela"],
    "Valor extras validado Atlas": ["Valor extra validado Atlas","Extras validados Atlas","Valor extra (Atlas)","Valor extras Atlas"],
    "Mês referência para faturamento": ["Mes referencia para faturamento", "Mês de referência", "Mes de referencia", "Referencia faturamento"],
}

# Fallback por TOKENS (detecção leniente)
EXTRA_TOKEN_SETS: Dict[str, List[List[str]]] = {
    "Desconto SLA Retroativo": [
        ["sla","retro"], ["retroativo","sla"], ["desconto","retro"], ["sla","retroativo"],
        ["sla","ret"], ["ret","sla"], ["sla","retr"], ["retr","sla"], ["retro","sla"],
        # variações com ordem livre e sufixo abreviado
        ["desc","sla","ret"], ["retro","sla","desc"], ["sla","retro","desc"],
    ],
    "Desconto Equipamentos": [["equip"],["equipamentos"],["desc","equip"]],
    "Prêmio Assiduidade": [["premio","assiduidade"],["prêmio","assiduidade"]],
    "Outros descontos": [["outros","descont"],["outros","desc"]],
    "Taxa de prorrogação do prazo pagamento": [["taxa","prorrog"],["taxa","prazo","pagamento"]],
    "Valor mensal com prorrogação do prazo pagamento": [["valor","mensal","prorrog"],["mensal","prorrog"]],
    "Retroativo de dissídio": [["retroativo","dissidio"],["retroativo","dissídio"]],
    "Parcela (x/x)": [["parcela"]],
    "Valor extras validado Atlas": [["valor","extra","atlas"],["extras","atlas"]],
}

# -----------------------------
# Normalização / busca leniente
# -----------------------------
def _norm(s: str) -> str:
    """Normaliza texto: remove acentos, espaços extras, travessões, lowercase.
    
    Wrapper para normalize_text_full() de utils.py (consolidação de código).
    """
    return normalize_text_full(s)

def _key_equiv(s: str) -> str:
    """Chave equivalente: normaliza e remove tudo que não for [a-z0-9]."""
    return re.sub(r"[^a-z0-9]", "", _norm(s))

SLA_DESCONTO_NAMES_NORMALIZED = {_norm(n) for n in [SLA_DESCONTO_CANONICAL, *SLA_DESCONTO_SYNONYMS]}

def _pick_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    cols = list(df.columns)
    norm_map = {_norm(c): c for c in cols}
    for cand in candidates:
        nc = _norm(cand)
        if nc in norm_map:
            return norm_map[nc]
    for cand in candidates:
        nc = _norm(cand)
        for k, original in norm_map.items():
            if nc and nc in k:
                return original
    return None

def _find_col_by_tokens(df: pd.DataFrame, token_sets: List[List[str]]) -> Optional[str]:
    norm_cols = {c: _norm(c) for c in df.columns}
    for tokens in token_sets:
        toks = [_norm(t) for t in tokens if t]
        for original, n in norm_cols.items():
            if all(t in n for t in toks):
                return original
    return None

def _force_equivalent_rename(dfu: pd.DataFrame, canonical: str) -> None:
    """Se existir uma coluna 'igual' ao canônico ignorando espaços/quebras/acentos, renomeia para o canônico."""
    if canonical in dfu.columns:
        return
    tgt = _key_equiv(canonical)
    for col in list(dfu.columns):
        if col == canonical:
            return
        if _key_equiv(col) == tgt:
            dfu.rename(columns={col: canonical}, inplace=True)
            return

def map_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    mapping: Dict[str, Optional[str]] = {}
    for key, cands in COLUMN_CANDIDATES.items():
        mapping[key] = _pick_column(df, cands)

    # Fallback robusto para Mês de emissão da NF
    if not mapping.get("Mes_Emissao_NF") or mapping["Mes_Emissao_NF"] not in df.columns:
        aliases = [
            "mes de emissao da nf","mês de emissão da nf","mes emissao nf","mes emissao da nota",
            "mes de emissao da nota","mes de emissao da nota fiscal","mes emissao nota fiscal","mes nf","mês nf",
        ]
        for c in df.columns:
            nc = _norm(c)
            if any(alias in nc for alias in aliases):
                mapping["Mes_Emissao_NF"] = c
                break
        if not mapping.get("Mes_Emissao_NF"):
            for c in df.columns:
                nc = _norm(c)
                if re.search(r"\bmes\b.*\bemissa[oã]o\b.*\b(nf|nota)\b", nc) or re.search(r"\b(nf|nota)\b.*\bemissa[oã]o\b.*\bmes\b", nc):
                    mapping["Mes_Emissao_NF"] = c
                    break
    if mapping.get("Mes_Emissao_NF"):
        mapping["Mes_Emissão_NF"] = mapping["Mes_Emissao_NF"]
    return mapping

# -----------------------------
# Utilitários
# -----------------------------
def _collect_recipients(dfu: pd.DataFrame, email_col: Optional[str]) -> List[str]:
    if not email_col or email_col not in dfu.columns:
        return []
    raw = dfu[email_col].dropna().astype(str).tolist()
    bag: List[str] = []
    for cell in raw:
        bag.extend(split_emails(cell) or [])
    seen, out = set(), []
    for e in bag:
        el = e.strip().lower()
        if el and el not in seen:
            seen.add(el); out.append(e.strip())
    return out

def _ensure_alias(dfu: pd.DataFrame, target: str, sources: List[str], default: str = "") -> None:
    if target in dfu.columns:
        return
    for src in sources:
        if src and src in dfu.columns:
            dfu[target] = dfu[src]; return
    dfu[target] = default

def _ensure_alias_smart(
    dfu: pd.DataFrame,
    target: str,
    candidates: List[str],
    token_sets: Optional[List[List[str]]] = None,
    default: Any = "",
) -> None:
    if target in dfu.columns:
        return
    # tenta equivalente direto (ignora espaços/quebras/acentos)
    _force_equivalent_rename(dfu, target)
    if target in dfu.columns:
        return
    src = _pick_column(dfu, candidates) if candidates else None
    if not src and token_sets:
        src = _find_col_by_tokens(dfu, token_sets)
    if src:
        # renomeia p/ canônico (mantém 1 nome estável no fluxo todo)
        dfu.rename(columns={src: target}, inplace=True)
    else:
        dfu[target] = default

def _ensure_sla_discount_canonical(dfu: pd.DataFrame) -> None:
    cols_snapshot = list(dfu.columns)
    has_canonical = SLA_DESCONTO_CANONICAL in dfu.columns
    to_drop: List[str] = []
    for col in cols_snapshot:
        if col == SLA_DESCONTO_CANONICAL:
            has_canonical = True; continue
        norm_col = _norm(col)
        # Evitar capturar colunas que não são o "SLA do mês" (ex.: retroativo, equipamentos, etc.)
        forbidden = any(t in norm_col for t in [
            "retro", "retr", "retroativ", "equip", "equipamento", "assiduidade", "outros",
            "prorrog", "parcela", "dissidio", "dissídio", "extra"
        ])
        has_tokens = ("sla" in norm_col and ("desconto" in norm_col or "desc" in norm_col)) and not forbidden
        if norm_col in SLA_DESCONTO_NAMES_NORMALIZED or has_tokens:
            if not has_canonical:
                dfu.rename(columns={col: SLA_DESCONTO_CANONICAL}, inplace=True)
                has_canonical = True
            else:
                to_drop.append(col)
    if to_drop:
        dfu.drop(columns=[c for c in to_drop if c in dfu.columns and c != SLA_DESCONTO_CANONICAL], inplace=True)

def _to_decimal_sane(x: Any) -> Decimal:
    if isinstance(x, Decimal):
        try:
            if x.is_nan() or x.is_infinite(): return Decimal("0")
        except Exception:
            return Decimal("0")
        return x
    if x is None: return Decimal("0")
    if isinstance(x, float):
        if pd.isna(x) or math.isnan(x) or math.isinf(x): return Decimal("0")
    if isinstance(x, (int, float)):
        try: return Decimal(str(x))
        except InvalidOperation: return Decimal("0")
    s = str(x).strip()
    if not s: return Decimal("0")
    s_low = s.lower()
    if s_low in {"nan","inf","+inf","-inf","infinity","+infinity","-infinity"}: return Decimal("0")
    if "," in s: s = s.replace(".","").replace(",",".")
    try: return Decimal(s)
    except InvalidOperation: return Decimal("0")

def _fmt_brl_or_placeholder(v: Any, placeholder: str) -> str:
    return fmt_brl(v, placeholder=placeholder)

def _is_pendente_textual(v: Any) -> bool:
    s = _norm(str(v or ""))
    pend_norm = {_norm(x) for x in PENDENTE_LABELS}
    return s in pend_norm

# -----------------------------
# Núcleo
# -----------------------------
def filter_and_prepare(
    df: pd.DataFrame,
    unidade: str,
    ym: str,
    columns_whitelist: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], List[str], Dict[str, Any]]:

    mapping = map_columns(df)
    uni_col   = mapping.get("Unidade")
    mes_col   = mapping.get("Mes_Emissão_NF") or mapping.get("Mes_Emissao_NF")
    email_col = mapping.get("Email_Destinatario")
    vmf_col   = mapping.get("Valor_Mensal_Final")

    if not uni_col or not mes_col:
        return [], [], {"row_count": 0, "sum_valor_mensal_final": 0.0}

    # 1) mês
    ym_series = df[mes_col].apply(parse_year_month)
    dfm = df.loc[ym_series == ym].copy()
    if dfm.empty:
        return [], [], {"row_count": 0, "sum_valor_mensal_final": 0.0}

    # 2) unidade
    target_nu = normalize_unit(unidade)
    dfm["_nu"] = dfm[uni_col].astype(str).map(normalize_unit)
    dfu = dfm.loc[dfm["_nu"] == target_nu].copy()
    dfu.drop(columns=["_nu"], errors="ignore", inplace=True)
    if dfu.empty:
        return [], [], {"row_count": 0, "sum_valor_mensal_final": 0.0}

    # 3) Colunas canônicas --------------------------------

    # 3.1) Mês de emissão da NF -> "YYYY/MM"
    mes_fmt = lambda x: (parse_year_month(x) or ym).replace("-", "/")
    dfu["Mês de emissão da NF"] = dfu[mes_col].apply(mes_fmt) if mes_col in dfu.columns else ym.replace("-", "/")
    _ensure_alias(dfu, "Mes_Emissao_NF", ["Mês de emissão da NF", mes_col, "Mês emissão NF", "Mês de emissão Nota Fiscal"])
    _ensure_alias(dfu, "Mes_Emissão_NF", ["Mês de emissão da NF", mes_col, "Mês emissão NF", "Mês de emissão Nota Fiscal"])
    # remove duplicatas do cabeçalho por normalização
    for c in list(dfu.columns):
        if c != "Mês de emissão da NF" and _norm(c) == _norm("Mês de emissão da NF"):
            dfu.drop(columns=[c], inplace=True, errors="ignore")

    # 3.2) Valor Mensal Final (numérico -> BRL, mantendo soma numérica)
    if vmf_col and vmf_col in dfu.columns:
        vmf_num = dfu[vmf_col].apply(_to_decimal_sane)
    else:
        src = _pick_column(dfu, ["Valor Mensal Final","Valor_Mensal_Final","Valor Final","Total Faturamento"])
        vmf_num = dfu[src].apply(_to_decimal_sane) if src else pd.Series([Decimal("0")] * len(dfu), index=dfu.index)
    dfu["_vmf_num"] = vmf_num
    dfu["Valor Mensal Final"] = dfu["_vmf_num"].apply(fmt_brl)
    _ensure_alias(dfu, "Valor_Mensal_Final", (["Valor Mensal Final", vmf_col] if vmf_col else ["Valor Mensal Final"]))
    # elimina possíveis duplicatas de "Valor Mensal Final"
    for c in list(dfu.columns):
        if c != "Valor Mensal Final" and _norm(c) == _norm("Valor Mensal Final"):
            dfu.drop(columns=[c], inplace=True, errors="ignore")

    # 3.3) Aliases básicos
    _ensure_alias(dfu, "Unidade", [uni_col,"Shopping","Unidade/Shopping","Unidade - Shopping"])
    _ensure_alias(dfu, "Categoria", ["Categoria","Categoria_Contrato"])
    _ensure_alias(dfu, "Fornecedor", ["Fornecedor","Razao Social","Razão Social","Razao_Social"])
    _ensure_alias(dfu, "HC Planilha", ["HC_Planilha"])
    _ensure_alias(dfu, "Dias Faltas", ["Dias_Faltas"])
    _ensure_alias(dfu, "Horas Atrasos", ["Horas_Atrasos"])
    _ensure_alias(dfu, "Valor Planilha", ["Valor_Planilha"])

    # 3.4) Descontos — busca robusta + nomes canônicos
    _ensure_alias_smart(
        dfu, "Desc. Falta Validado Atlas",
        candidates=["Desc. Falta Validado Atlas","Desconto Falta Validado Atlas","Desc_Falta","Desconto_Falta_Validado_Atlas"],
        token_sets=[["desc","falta","validado","atlas"],["falta","validado","atlas"]],
    )
    _ensure_alias_smart(
        dfu, "Desc. Atraso Validado Atlas",
        candidates=["Desc. Atraso Validado Atlas","Desconto Atraso Validado Atlas","Desc_Atraso","Desconto_Atrasos_Validado_Atlas"],
        token_sets=[["desc","atras","validado","atlas"],["atraso","validado","atlas"],["atrasos","validado","atlas"]],
    )
    _ensure_alias_smart(
        dfu, SLA_DESCONTO_CANONICAL,
        candidates=[SLA_DESCONTO_CANONICAL, *SLA_DESCONTO_SYNONYMS],
        token_sets=[["sla","desconto"],["sla","desc"]],
    )
    _ensure_sla_discount_canonical(dfu)

    # 3.5) Placeholders e formatação BRL nas monetárias principais
    if "Valor Planilha" in dfu.columns:
        dfu["Valor Planilha"] = dfu["Valor Planilha"].apply(lambda v: _fmt_brl_or_placeholder(v, "Informação pendente"))
    if "Desc. Falta Validado Atlas" in dfu.columns:
        dfu["Desc. Falta Validado Atlas"] = dfu["Desc. Falta Validado Atlas"].apply(lambda v: _fmt_brl_or_placeholder(v, "Informação pendente"))
    if "Desc. Atraso Validado Atlas" in dfu.columns:
        dfu["Desc. Atraso Validado Atlas"] = dfu["Desc. Atraso Validado Atlas"].apply(lambda v: _fmt_brl_or_placeholder(v, "Informação pendente"))
    if SLA_DESCONTO_CANONICAL in dfu.columns:
        dfu[SLA_DESCONTO_CANONICAL] = dfu[SLA_DESCONTO_CANONICAL].apply(
            lambda v: _fmt_brl_or_placeholder(v, "Preenchimento pendente")
        )

    # 3.6) Extras opcionais — garantir existência (e manter como veio)
    for _canon in EXTRA_OPTIONAL_CANONICALS:
        _force_equivalent_rename(dfu, _canon)  # pega cabeçalhos com quebra de linha/espaços
        _syns = DISPLAY_HEADER_SYNONYMS.get(_canon, [])
        _ensure_alias_smart(
            dfu,
            _canon,
            candidates=[_canon, *_syns],
            token_sets=EXTRA_TOKEN_SETS.get(_canon, []),
            default="",   # vazio -> chip no HTML quando realmente não vier nada
        )

    # 3.7) Mês referência para faturamento - usar o ym passado como padrão
    _ensure_alias_smart(
        dfu,
        "Mês referência para faturamento",
        candidates=["Mês referência para faturamento", "Mes referencia para faturamento", "Mês de referência", "Mes de referencia", "Referencia faturamento"],
        default=ym.replace("-", "/")  # formato YYYY/MM igual ao de emissão da NF
    )
    # normaliza formato da coluna para YYYY/MM
    if "Mês referência para faturamento" in dfu.columns:
        dfu["Mês referência para faturamento"] = dfu["Mês referência para faturamento"].apply(
            lambda x: (parse_year_month(x) or ym).replace("-", "/")
        )

    # === RESCUE (estrito e auditável) — só copia se o canônico estiver realmente vazio ===
    retro_debug_before = []
    retro_debug_after = []
    rescue_src = None
    if "Desconto SLA Retroativo" in dfu.columns:
        col = "Desconto SLA Retroativo"

        def _col_all_empty(series: pd.Series) -> bool:
            try:
                s = series.fillna("").astype(str).str.strip()
                sn = s.str.lower()
                # vazio de verdade: "" | "nan" | "none"
                return ((s == "") | (sn == "nan") | (sn == "none")).all()
            except Exception:
                # fallback conservador
                try:
                    s = series
                    sn = s.str.lower()
                    return ((s == "") | (sn == "nan") | (sn == "none")).all()
                except Exception:
                    return False

        try:
            retro_debug_before = dfu[col].head(8).astype(str).tolist()
        except Exception:
            retro_debug_before = []
        rescue_src = None
        if _col_all_empty(dfu[col]):
            # candidatos: cabeçalho tem 'sla' E ('retro' OU 'retr'), e NÃO tem 'dissidio'/'dissídio'
            def _is_candidate(h: str) -> bool:
                n = _norm(h)
                if "dissidio" in n or "dissidio" in n.replace("í","i"):
                    return False
                return ("sla" in n) and (("retro" in n) or ("retr" in n))

            pick_list = [c for c in dfu.columns if c != col and _is_candidate(c)]
            for cand in pick_list:
                if not _col_all_empty(dfu[cand]):
                    dfu[col] = dfu[cand]
                    rescue_src = cand
                    break

        # --- normalização final (preserva zeros; só esvazia rótulo textual)
        pend_norm = {_norm(x) for x in PENDENTE_LABELS}

        def _normalize_retro(v):
            if v is None:
                return ""
            s = str(v).strip()
            if not s:
                return ""
            ns = _norm(s)
            if ns in {"nan", "none"} or ns in pend_norm:
                return ""
            if s.startswith("(") and s.endswith(")"):
                s = "-" + s[1:-1]
            return s

        dfu[col] = dfu[col].apply(_normalize_retro)
        try:
            retro_debug_after = dfu[col].head(8).astype(str).tolist()
        except Exception:
            retro_debug_after = []

        # (opcional) regra de negócio: onde estiver vazio, exibir "0"
        # dfu[col] = dfu[col].replace("", "0")

        # registra no summary a fonte do rescue (coluna interna temporária)
        dfu["_retro_rescue_src"] = rescue_src or ""


    # 3.7) Pendências textuais em Faltas/Atrasos
    if "Dias Faltas" in dfu.columns:
        dfu["Dias Faltas"] = dfu["Dias Faltas"].apply(lambda v: "Informação pendente" if is_missing_like(v) else v)
    if "Horas Atrasos" in dfu.columns:
        dfu["Horas Atrasos"] = dfu["Horas Atrasos"].apply(lambda v: "Informação pendente" if is_missing_like(v) else v)

    # Normalização amigável da coluna "Horas Atrasos":
    if "Horas Atrasos" in dfu.columns:
        def _format_horas_atrasos(val: Any) -> str:
            try:
                s = str(val).strip()
            except Exception:
                s = ""

            if not s or _norm(s) == _norm("Informação pendente"):
                return "Informação pendente"

            # 1) Já no formato H:MM? -> converte para minutos totais
            m = re.match(r"^\s*([+-]?\d+):\s*(\d{1,2})\s*$", s)
            if m:
                try:
                    h = int(m.group(1))
                    mi = int(m.group(2))
                    # normaliza minutos (limites e carry)
                    if mi >= 60:
                        h += mi // 60
                        mi = mi % 60
                    if mi < 0:
                        # caso improvável; normaliza levando emprestado 1h
                        borrow = (abs(mi) + 59) // 60
                        h -= borrow
                        mi = (borrow * 60 + mi) % 60
                    negative = h < 0
                    h = abs(h) if negative else h
                    total_min = h * 60 + mi
                    # converte para horas decimais com 1 casa (half-up)
                    dec = (Decimal(total_min) / Decimal("60")).quantize(Decimal("0.1"), rounding="ROUND_HALF_UP")
                    if negative:
                        dec = -dec
                    # vírgula como separador decimal
                    txt = f"{dec}".replace(".", ",")
                    return txt
                except Exception:
                    pass

            # 2) Formas como "4h 30m" ou "4h30" -> converte para minutos totais
            m2 = re.match(r"^\s*([+-]?\d+)\s*h\s*(\d{1,2})?\s*m?\s*$", s, flags=re.IGNORECASE)
            if m2:
                try:
                    h = int(m2.group(1))
                    mi = int(m2.group(2)) if m2.group(2) is not None else 0
                    if mi >= 60:
                        h += mi // 60
                        mi = mi % 60
                    negative = h < 0
                    h = abs(h) if negative else h
                    total_min = h * 60 + mi
                    dec = (Decimal(total_min) / Decimal("60")).quantize(Decimal("0.1"), rounding="ROUND_HALF_UP")
                    if negative:
                        dec = -dec
                    return f"{dec}".replace(".", ",")
                except Exception:
                    pass

            # 3) Tenta interpretar como horas decimais (com vírgula ou ponto)
            raw = s.replace(" ", "")
            # troca vírgula por ponto como separador decimal
            if "," in raw and "." in raw:
                raw = raw.replace(".", "").replace(",", ".")
            else:
                raw = raw.replace(",", ".")
            try:
                # aceita +/-
                dec = Decimal(str(raw))
                negative = dec < 0
                dec_abs = -dec if negative else dec
                # horas decimais -> 1 casa decimal (half-up)
                out = dec_abs.quantize(Decimal("0.1"), rounding="ROUND_HALF_UP")
                if negative:
                    out = -out
                return f"{out}".replace(".", ",")
            except Exception:
                # fallback: retorna como veio
                return s

        dfu["Horas Atrasos"] = dfu["Horas Atrasos"].apply(_format_horas_atrasos)

    # Flags (apenas textual)
    dfu["Dias_Faltas_is_pendente"]   = dfu["Dias Faltas"].apply(_is_pendente_textual) if "Dias Faltas" in dfu.columns else False
    dfu["Horas_Atrasos_is_pendente"] = dfu["Horas Atrasos"].apply(_is_pendente_textual) if "Horas Atrasos" in dfu.columns else False
    dfu["Desc_Falta_is_pendente"]    = dfu["Desc. Falta Validado Atlas"].apply(_is_pendente_textual) if "Desc. Falta Validado Atlas" in dfu.columns else False
    dfu["Desc_Atraso_is_pendente"]   = dfu["Desc. Atraso Validado Atlas"].apply(_is_pendente_textual) if "Desc. Atraso Validado Atlas" in dfu.columns else False
    dfu["Desc_SLA_is_pendente"]      = dfu[SLA_DESCONTO_CANONICAL].apply(_is_pendente_textual) if SLA_DESCONTO_CANONICAL in dfu.columns else False

    # 3.8) Colunas de exibição (ordem estável + sem duplicatas)
    candidate_columns = [c for c in dfu.columns if not c.startswith("_") and not c.endswith("_is_pendente")]
    # reforça presença na lista de candidatos
    if "Mês referência para faturamento" not in candidate_columns and "Mês referência para faturamento" in dfu.columns:
        candidate_columns.append("Mês referência para faturamento")

    # map normalizado -> nome real
    norm_map: Dict[str, str] = {}
    for col in candidate_columns:
        k = _norm(col)
        if k and k not in norm_map:
            norm_map[k] = col
    for canonical, synonyms in DISPLAY_HEADER_SYNONYMS.items():
        if canonical in dfu.columns:
            norm_map.setdefault(_norm(canonical), canonical)
            for syn in synonyms:
                norm_map.setdefault(_norm(syn), canonical)

    mes_column = "Mês de emissão da NF"
    additional_synonyms = {
        "competencia": mes_column,"competência": mes_column,"competencia nf": mes_column,"competência nf": mes_column,
        "mes referencia": mes_column,"mês referencia": mes_column,"mes emissao": mes_column,"mês emissao": mes_column,
        "total": "Valor Mensal Final","valor total": "Valor Mensal Final",
    }
    for alias, target in additional_synonyms.items():
        if target in dfu.columns:
            norm_map.setdefault(_norm(alias), target)

    requested = [str(c).strip() for c in (columns_whitelist or []) if str(c).strip()]
    missing: List[str] = []
    display: List[str] = []

    for col in requested:
        normed = _norm(col)
        m = norm_map.get(normed)
        if m and m not in display:
            display.append(m)
        else:
            if col in EXTRA_OPTIONAL_CANONICALS and col not in display:
                display.append(col)
            else:
                missing.append(col)

    # fallback p/ defaults
    if not display:
        defaults_available = [c for c in DEFAULT_DISPLAY_COLUMNS if c in candidate_columns]
        if defaults_available:
            display = list(defaults_available)

    # 'Desconto SLA Retroativo' deixa de ser padrão obrigatório; entra apenas se solicitado (ou por preferências do portal)

    # garante presença de colunas críticas
    if "Valor Mensal Final" in dfu.columns and "Valor Mensal Final" not in display:
        display.append("Valor Mensal Final")
    # nova coluna padrão: sempre incluir quando existir na base
    if "Mês referência para faturamento" in dfu.columns and "Mês referência para faturamento" not in display:
        display.append("Mês referência para faturamento")
    if mes_column in dfu.columns and mes_column not in display:
        display.append(mes_column)

    # ordem final estável
    seen = set(); ordered: List[str] = []
    for c in DEFAULT_DISPLAY_COLUMNS:
        if c in display and c not in seen:
            ordered.append(c); seen.add(c)
    for c in display:
        if c not in seen:
            ordered.append(c); seen.add(c)
    display_columns = ordered

    fallback_used = False
    if not display_columns:
        fallback_used = True
        display_columns = candidate_columns[:3] or list(candidate_columns)

    df_display = dfu[display_columns].copy() if display_columns else dfu.copy()

    # 4) Destinatários
    recipients = _collect_recipients(dfu, email_col)

    # 5) Somatório
    total_vmf: Decimal = dfu["_vmf_num"].sum() if "_vmf_num" in dfu.columns else Decimal("0")

    # 6) Totais numéricos por coluna de desconto (parse BRL robusto)
    def _sum_brl_column(df_src: pd.DataFrame, col: str) -> Decimal:
        if col not in df_src.columns:
            return Decimal("0")
        total = Decimal("0")
        for v in df_src[col].tolist():
            if v is None:
                continue
            # aceita numérico direto
            if isinstance(v, (int, float, Decimal)) and not isinstance(v, bool):
                try:
                    d = _to_decimal_sane(v)
                    total += d
                    continue
                except Exception:
                    pass
            s = str(v).strip()
            if not s:
                continue
            d_parsed = parse_brl_money(s)
            if d_parsed is None:
                # fallback: tenta coerção tolerante
                d_parsed = _to_decimal_sane(s)
            try:
                total += Decimal(d_parsed) if not isinstance(d_parsed, Decimal) else d_parsed
            except Exception:
                # último fallback seguro
                try:
                    total += _to_decimal_sane(d_parsed)
                except Exception:
                    pass
        return total

    # lista canônica dos descontos gerais
    _disc_cols = [
        "Desc. Falta Validado Atlas",
        "Desc. Atraso Validado Atlas",
        SLA_DESCONTO_CANONICAL,
        "Desconto SLA Retroativo",
        "Desconto Equipamentos",
        "Outros descontos",
        "Prêmio Assiduidade",
    ]
    sums_map: Dict[str, Decimal] = {}
    for dc in _disc_cols:
        try:
            sums_map[dc] = _sum_brl_column(dfu, dc)
        except Exception:
            sums_map[dc] = Decimal("0")
    descontos_gerais_total = sum(sums_map.values(), Decimal("0"))

    # 7) Saída
    rows = df_display.to_dict(orient="records")
    # extra: extrai e limpa a coluna interna de source do rescue
    rescue_src_val = ""
    if "_retro_rescue_src" in dfu.columns:
        rescue_src_val = str(dfu["_retro_rescue_src"].iloc[0] or "")
        dfu.drop(columns=["_retro_rescue_src"], inplace=True, errors="ignore")

    summary = {
        "row_count": len(rows),
        "sum_valor_mensal_final": float(total_vmf),
        # somatórios numéricos por desconto
        "sum_desc_falta": float(sums_map.get("Desc. Falta Validado Atlas", Decimal("0"))),
        "sum_desc_atraso": float(sums_map.get("Desc. Atraso Validado Atlas", Decimal("0"))),
        "sum_desc_sla_mes": float(sums_map.get(SLA_DESCONTO_CANONICAL, Decimal("0"))),
        "sum_desc_sla_retroativo": float(sums_map.get("Desconto SLA Retroativo", Decimal("0"))),
        "sum_desc_equipamentos": float(sums_map.get("Desconto Equipamentos", Decimal("0"))),
        "sum_outros_descontos": float(sums_map.get("Outros descontos", Decimal("0"))),
        "sum_premio_assiduidade": float(sums_map.get("Prêmio Assiduidade", Decimal("0"))),
        "sum_descontos_gerais": float(descontos_gerais_total),
        "display_columns": display_columns,
        "missing_columns": missing,
        "requested_columns": requested,
        "fallback_used": fallback_used,
        # DEBUGs úteis
        "sample_desconto_sla_retroativo": dfu["Desconto SLA Retroativo"].head(5).astype(str).tolist()
            if "Desconto SLA Retroativo" in dfu.columns else [],
        "debug_columns_like_retro": [c for c in dfu.columns if "retro" in _norm(c) or "retroativ" in _norm(c)],
        "rescue_source_desconto_sla_retroativo": rescue_src_val,
        "retro_debug_before": retro_debug_before,
        "retro_debug_after": retro_debug_after,
    }
    return rows, recipients, summary
