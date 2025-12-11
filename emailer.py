from pathlib import Path
from typing import List, Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
import urllib.parse
import platform
import unicodedata

from utils import to_base64_image, fmt_brl, fmt_percentage, normalize_text_full, is_missing_like

from processor import DISPLAY_HEADER_SYNONYMS

SLA_DISCOUNT_CANONICAL = "Desconto SLA Mês"
SLA_DISCOUNT_COLUMN_ALIASES = {
    SLA_DISCOUNT_CANONICAL,
    "Desc. SLA Mês",
    "Desc. SLA Mês / Equip.",
    "Desc_SLA",
    "Desconto_SLA_Mes",
    "Desconto SLA Mes",
    "Desconto_SLA_Mes_Desconto_Equipamentos",
    "SLA Desconto Mês",
    "Desconto SLA",
    "SLA Mês (Desconto)",
    "Desconto_SLA_Mês",
}

ANCHOR_VALOR_MENSAL = "Valor Mensal"
ANCHOR_VALOR_PLANILHA = "Valor Planilha"
ANCHOR_VALOR_MENSAL_FINAL = "Valor Mensal Final"
ANCHOR_MES_EMISSAO_NF = "Mês de emissão da NF"

COLUMN_ALIASES: Dict[str, set] = {
    SLA_DISCOUNT_CANONICAL: set(SLA_DISCOUNT_COLUMN_ALIASES),
    ANCHOR_VALOR_MENSAL: {"Valor Mensal", "valor mensal"},
    ANCHOR_VALOR_PLANILHA: {"Valor Planilha", "valor planilha"},
    ANCHOR_VALOR_MENSAL_FINAL: {"Valor Mensal Final", "valor mensal final"},
    ANCHOR_MES_EMISSAO_NF: {
        "Mês de emissão da NF", "Mes de emissao da NF", "mes de emissao da nf",
        "Mês NF", "Mes NF", "mes nf",
    },
}

# Incorpora sinônimos consolidados do processor para evitar duplicação
for canon, aliases in DISPLAY_HEADER_SYNONYMS.items():
    if canon not in COLUMN_ALIASES:
        COLUMN_ALIASES[canon] = set()
    COLUMN_ALIASES[canon].update(aliases)
    COLUMN_ALIASES[canon].add(canon)

def _norm_txt(s: Optional[str]) -> str:
    """Normaliza texto: remove acentos, espaços extras, travessões, lowercase.
    
    Wrapper para normalize_text_full() de utils.py (consolidação de código).
    """
    return normalize_text_full(s)

def _canon(name: Optional[str]) -> Optional[str]:
    if not name:
        return name
    n_raw = str(name).strip()
    n = _norm_txt(n_raw)

    for canon, aliases in COLUMN_ALIASES.items():
        if _norm_txt(canon) == n:
            return canon
        for a in aliases:
            if _norm_txt(a) == n:
                return canon

    for a in SLA_DISCOUNT_COLUMN_ALIASES:
        if _norm_txt(a) == n:
            return SLA_DISCOUNT_CANONICAL

    return n_raw

class Emailer:
    COPY_ENV_KEYS = {
        "greeting": "COPY_GREETING",
        "intro": "COPY_INTRO",
        "observation": "COPY_OBSERVATION",
        "reminder": "COPY_REMINDER",
        "cta_label": "COPY_CTA_LABEL",
        "footer_signature": "COPY_FOOTER_SIGNATURE",
        "title_prefix": "COPY_TITLE_PREFIX",
        "month_ref_label": "COPY_MONTH_REF_LABEL",
        "sla_link_label": "COPY_SLA_LINK_LABEL",
        "pending_fill_label": "COPY_PENDING_FILL_LABEL",
        "pending_info_label": "COPY_PENDING_INFO_LABEL",
        "sum_final_label": "COPY_SUM_FINAL_LABEL",
        "recipients_label": "COPY_RECIPIENTS_LABEL",
        "footer_autogen": "COPY_FOOTER_AUTOGEN",
    }

    COPY_DEFAULTS = {
        "greeting": "Prezados(as),",
        "intro": (
            "Encaminhamos a medição mensal referente à <strong style=\"color:#e5e7eb;\">{{ unidade }}</strong>. "
            "Solicitamos a validação dos valores abaixo e, caso haja divergências, pedimos o envio das ocorrências "
            "de faltas e atrasos que constem como pendentes para o período. Reforçamos a importância do "
            "preenchimento do SLA, utilizado na composição do relatório mensal da diretoria."
        ),
        "observation": (
            "Observação: caso a Nota Fiscal já tenha sido emitida sem considerar os descontos ora apontados, "
            "os valores poderão ser objeto de desconto retroativo na competência subsequente."
        ),
        "cta_label": "Preencher SLA",
        "footer_signature": (
            "Atenciosamente,<br><strong style=\"color:#e5e7eb;\">{{ sender_name }} &lt;{{ sender_email }}&gt;</strong>"
        ),
        "title_prefix": "Medição —",
        "month_ref_label": "Mês de referência:",
        "sla_link_label": "SLA / validação",
        "pending_fill_label": "Preenchimento<br>pendente",
        "pending_info_label": "Informação<br>pendente",
        "sum_final_label": "Soma Valor Mensal Final:",
        "recipients_label": "Destinatários:",
        "footer_autogen": "E-mail gerado automaticamente pela automação Atlas Inovações.",
    }

    DEFAULT_TABLE_COLUMNS = [
        "Unidade",
        "Categoria",
        "Fornecedor",
        "HC Planilha",
        "Dias Faltas",
        "Horas Atrasos",
        ANCHOR_VALOR_PLANILHA,
        "Desc. Falta Validado Atlas",
        "Desc. Atraso Validado Atlas",
        SLA_DISCOUNT_CANONICAL,
        ANCHOR_VALOR_MENSAL_FINAL,
        "Mês referência para faturamento",
        ANCHOR_MES_EMISSAO_NF,
    ]

    EXTRA_AFTER_SLA = [
        "Desconto SLA Retroativo",
        "Desconto Equipamentos",
        "Prêmio Assiduidade",
        "Outros descontos",
    ]
    EXTRA_AFTER_FINAL = [
        "Taxa de prorrogação do prazo pagamento",
        "Valor mensal com prorrogação do prazo pagamento",
    ]
    EXTRA_EXTRAS = [
        "Retroativo de dissídio",
        "Parcela (x/x)",
        "Valor extras validado Atlas",
    ]
    GROUP_AFTER_VALOR_MENSAL = [
        "Taxa de prorrogação do prazo pagamento",
        "Valor mensal com prorrogação do prazo pagamento",
        "Retroativo de dissídio",
        "Parcela (x/x)",
        "Valor extras validado Atlas",
    ]

    TABLE_MONEY_COLUMNS = {
        ANCHOR_VALOR_PLANILHA,
        "Desc. Falta Validado Atlas",
        "Desc. Atraso Validado Atlas",
        "Desconto SLA Retroativo",
        "Desconto Equipamentos",
        "Prêmio Assiduidade",
        "Outros descontos",
        "Valor mensal com prorrogação do prazo pagamento",
        "Retroativo de dissídio",
        "Valor extras validado Atlas",
        SLA_DISCOUNT_CANONICAL,
        ANCHOR_VALOR_MENSAL_FINAL,
    }

    TABLE_PERCENTAGE_COLUMNS = {
        "Taxa de prorrogação do prazo pagamento",
    }

    TABLE_NUMERIC_COLUMNS = {
        "HC Planilha",
        "Dias Faltas",
        "Horas Atrasos",
    } | TABLE_MONEY_COLUMNS | TABLE_PERCENTAGE_COLUMNS

    def __init__(self, templates_dir: Path, assets_dir: Path, env_cfg: Dict[str, str]):
        self.templates_dir = templates_dir
        self.assets_dir = assets_dir
        self.env_cfg = env_cfg
        self.jenv = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        # Filtros customizados
        def _money_to_float(v: Any) -> float:
            if v is None:
                return 0.0
            s = str(v)
            s = s.replace("\u00A0", " ").strip()
            if not s:
                return 0.0
            low = s.lower()
            if low in {"nan", "none", "inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"}:
                return 0.0
            s = s.replace("R$", "").replace(".", "").replace(",", ".").replace(" ", "")
            try:
                return float(s)
            except Exception:
                try:
                    return float(str(v))
                except Exception:
                    return 0.0
        self.jenv.filters["money_to_float"] = _money_to_float
        self.jenv.filters["urlencode"] = lambda x: urllib.parse.quote(str(x or ""))

    def _int_cfg(self, key: str, default: int) -> int:
        val = str(self.env_cfg.get(key, str(default))).strip()
        try:
            return int(val)
        except Exception:
            return default

    def _resolve_logo_path(self) -> Optional[Path]:
        """
        Resolve o caminho do arquivo de logo.
        Prioriza LOGO_FILE, depois nomes comuns, depois LOGO_URL (compatibilidade).
        """
        # Lista de nomes de arquivo comuns
        LOGO_NAMES = ["logo-performance-horizontal-azul.png", "logo-performance-horizontal-azul.png", "logo.png", "atlas.png", "logo.jpg", "logo.jpeg"]
        
        # 1. Tentar LOGO_FILE do .env
        env_name = (self.env_cfg.get("LOGO_FILE") or "").strip()
        if env_name:
            p = Path(env_name)
            if not p.is_absolute():
                p = self.assets_dir / env_name
            if p.exists():
                return p
        
        # 2. Tentar nomes comuns em assets/
        for name in LOGO_NAMES:
            p = self.assets_dir / name
            if p.exists():
                return p
        
        # 3. Tentar LOGO_URL (compatibilidade com versões antigas)
        compat = (self.env_cfg.get("LOGO_URL") or "").strip()
        if compat:
            p = Path(compat)
            if not p.is_absolute():
                p = self.assets_dir / compat
            if p.exists():
                return p
        
        return None

    def _resolve_logo_data_uri(self) -> Optional[str]:
        """Retorna a logo como data URI (base64) para uso em HTML."""
        logo_path = self._resolve_logo_path()
        if logo_path:
            return to_base64_image(logo_path)
        return None

    def _resolve_logo_file_path(self) -> Optional[Path]:
        """Retorna o caminho de arquivo da logo para uso como CID no Outlook."""
        return self._resolve_logo_path()

    def today_str(self) -> str:
        import datetime as dt
        return dt.datetime.now().strftime("%d/%m/%Y %H:%M")

    def format_mes_extenso(self, ym: str) -> str:
        y, m = int(ym[:4]), int(ym[-2:])
        PT_BR = ["",
                 "Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                 "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        return f"{PT_BR[m]}/{y}"

    @staticmethod
    def _insert_after(lst: List[str], anchor: str, items: List[str]) -> List[str]:
        res = lst[:]
        if not items:
            return res
        if anchor in res:
            idx = res.index(anchor) + 1
            for i, it in enumerate(items):
                if it not in res:
                    res.insert(idx + i, it)
        else:
            if ANCHOR_VALOR_MENSAL_FINAL in res:
                idx = res.index(ANCHOR_VALOR_MENSAL_FINAL)
                for it in reversed(items):
                    if it not in res:
                        res.insert(idx, it)
            else:
                for it in items:
                    if it not in res:
                        res.append(it)
        return res

    @staticmethod
    def _insert_before(lst: List[str], anchor: str, items: List[str]) -> List[str]:
        res = lst[:]
        if not items:
            return res
        if anchor in res:
            idx = res.index(anchor)
            for it in reversed(items):
                if it not in res:
                    res.insert(idx, it)
        else:
            for it in items:
                if it not in res:
                    res.append(it)
        return res

    def _compute_final_order(self, table_columns: Optional[List[str]]) -> List[str]:
        """
        - Mantém padrão se nada for selecionado.
        - Grupo A: após "Desconto SLA Mês".
        - Grupo B: após "Valor Mensal Final".
        - "Mês de emissão da NF" por último.
        - Remove duplicatas preservando ordem.
        """
        if table_columns:
            seen = set()
            user_cols: List[str] = []
            for c in table_columns:
                if c is None:
                    continue
                canon = _canon(str(c).strip())
                if canon and canon not in seen:
                    seen.add(canon)
                    user_cols.append(canon)
        else:
            user_cols = list(self.DEFAULT_TABLE_COLUMNS)

        user_cols = [SLA_DISCOUNT_CANONICAL if (col in SLA_DISCOUNT_COLUMN_ALIASES) else col for col in user_cols]

        extras_a = [c for c in self.EXTRA_AFTER_SLA if c in user_cols]
        extras_b = [c for c in self.GROUP_AFTER_VALOR_MENSAL if c in user_cols]

        base = [c for c in user_cols if c not in set(extras_a + extras_b)]
        base = self._insert_after(base, SLA_DISCOUNT_CANONICAL, extras_a)
        base = self._insert_after(base, ANCHOR_VALOR_MENSAL_FINAL, extras_b)

        if ANCHOR_MES_EMISSAO_NF in base:
            base = [c for c in base if c != ANCHOR_MES_EMISSAO_NF] + [ANCHOR_MES_EMISSAO_NF]

        seen2 = set()
        final_order = [c for c in base if (c not in seen2 and not seen2.add(c))]
        return final_order

    def render_html(
        self,
        unidade: str,
        regiao: str,
        ym: str,
        rows: List[Dict[str, Any]],
        summary: Dict[str, Any],
        destinatarios_exibicao: str = "",
        copy_overrides: Optional[Dict[str, str]] = None,
        table_columns: Optional[List[str]] = None,
        rows_prev: Optional[List[Dict[str, Any]]] = None,
        rows_ytd: Optional[List[List[Dict[str, Any]]]] = None,
        rows_ytd_prev: Optional[List[List[Dict[str, Any]]]] = None,
        extra_prev: Optional[Dict[str, Any]] = None,
    ) -> str:
        mes_extenso = self.format_mes_extenso(ym)
        template = self.jenv.get_template("email_template_dark.html")
        logo_b64 = self._resolve_logo_data_uri()
        logo_cid = self.env_cfg.get("LOGO_CID", "atlas-logo").strip() or "atlas-logo"
        logo_http_url = self.env_cfg.get("LOGO_HTTP_URL", "").strip() or None

        brand_vars = {
            "BODY_BG": self.env_cfg.get("BODY_BG", "#0F172A"),
            "TABLE_HEADER_BG": self.env_cfg.get("TABLE_HEADER_BG", "#182A4B"),
            "TABLE_HEADER_FG": self.env_cfg.get("TABLE_HEADER_FG", "#FFFFFF"),
            "TABLE_BORDER": self.env_cfg.get("TABLE_BORDER", "#243045"),
            "BRAND_COLOR_PRIMARY": self.env_cfg.get("BRAND_COLOR_PRIMARY", "#182A4B"),
            "BRAND_COLOR_ACCENT": self.env_cfg.get("BRAND_COLOR_ACCENT", "#3B82F6"),
            "NOTICE_BG": self.env_cfg.get("NOTICE_BG", "#14223B"),
            "NOTICE_BORDER": self.env_cfg.get("NOTICE_BORDER", "#2B3B55"),
            "ZEBRA_BG": self.env_cfg.get("ZEBRA_BG", "#121D34"),
            "LOGO_WIDTH": self._int_cfg("LOGO_WIDTH", 176),
        }

        ctx = {
            "unidade": unidade,
            "regiao": regiao,
            "mes_extenso": mes_extenso,
            "SLA_URL": self.env_cfg.get("SLA_URL", ""),
            "sender_name": self.env_cfg.get("SENDER_NAME", ""),
            "sender_email": self.env_cfg.get("SENDER_EMAIL", ""),
            "destinatarios_exibicao": destinatarios_exibicao,
            "fmt_brl": fmt_brl,
        }

        def render_copy(value: str) -> str:
            return self.jenv.from_string(value).render(**ctx)

        copy_overrides = copy_overrides or {}

        def resolve_copy(key: str) -> str:
            # Se o portal/CLI informou a chave, mesmo que vazia, respeitamos (permite deixar em branco)
            if key in copy_overrides:
                return str(copy_overrides.get(key) or "")
            env_key = self.COPY_ENV_KEYS[key]
            env_val = self.env_cfg.get(env_key)
            if env_val is not None and str(env_val).strip():
                return str(env_val)
            return self.COPY_DEFAULTS[key]

        copy = {k: render_copy(resolve_copy(k)) for k in self.COPY_DEFAULTS}

        # -------- Ordem final das colunas (preferir as do processor) --------
        requested_cols = table_columns or summary.get("display_columns")
        resolved_columns = self._compute_final_order(requested_cols)

        # -------- Totais já formatados --------
        sum_vmf_num = summary.get("sum_valor_mensal_final", 0.0)
        sum_desc_geral_num = summary.get("sum_descontos_gerais", 0.0)
        soma_fmt = fmt_brl(sum_vmf_num)

        # -------- Saneamento final das linhas --------
        def _sanitize_rows(rs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            out: List[Dict[str, Any]] = []
            for r in rs or []:
                row = dict(r) if isinstance(r, dict) else {}

                # Canoniza chaves via aliases
                new_row: Dict[str, Any] = {}
                for k, v in list(row.items()):
                    ck = _canon(k)
                    if ck in new_row:
                        if not new_row[ck] and v not in (None, "", 0):
                            new_row[ck] = v
                    else:
                        new_row[ck] = v
                row = new_row


                # ✅ SIMPLIFICADO: Formata colunas de mês para MM/YY
                for k in list(row.keys()):
                    if k in ["Mês de referência para faturamento", "Mês de emissão da NF"]:
                        val = row.get(k)
                        if not val:
                            row[k] = ""
                            continue
                        
                        vstr = str(val).strip()
                        
                        # Se já está em formato válido (MM/YY ou contém texto), mantém
                        import re
                        if re.match(r"^\d{2}/\d{2,4}$", vstr) or any(c.isalpha() for c in vstr):
                            row[k] = vstr
                        else:
                            # Tenta parsear e formatar para MM/YY
                            from utils import parse_year_month
                            parsed = parse_year_month(vstr)
                            if parsed:
                                try:
                                    y, m = parsed.split('-')
                                    row[k] = f"{m}/{y[2:]}"  # MM/YY
                                except:
                                    row[k] = vstr  # Fallback seguro
                            else:
                                row[k] = vstr  # Fallback seguro
                    elif k in self.TABLE_MONEY_COLUMNS:
                        val = row.get(k)
                        if k == "Desconto SLA Retroativo":
                            if is_missing_like(val):
                                row[k] = ""
                            else:
                                s = str(val).strip()
                                row[k] = s
                            continue
                        if is_missing_like(val):
                            row[k] = "" if val is None else str(val).strip()
                        else:
                            s = str(val).strip()
                            row[k] = s if s.startswith("R$") else fmt_brl(val)
                    elif k in self.TABLE_PERCENTAGE_COLUMNS:
                        val = row.get(k)
                        if is_missing_like(val):
                            row[k] = "" if val is None else str(val).strip()
                        else:
                            row[k] = fmt_percentage(val)

                out.append(row)
            return out

        rows_sanitized = _sanitize_rows(rows or [])
        rows_prev_sanitized = _sanitize_rows(rows_prev or []) if rows_prev is not None else []
        def _sanitize_rows_nested(nested: Optional[List[List[Dict[str, Any]]]]) -> List[List[Dict[str, Any]]]:
            out: List[List[Dict[str, Any]]] = []
            for sub in nested or []:
                out.append(_sanitize_rows(sub or []))
            return out
        rows_ytd_sanitized = _sanitize_rows_nested(rows_ytd)
        rows_ytd_prev_sanitized = _sanitize_rows_nested(rows_ytd_prev)

        html = template.render(
            unidade=unidade,
            regiao=regiao,
            mes_extenso=mes_extenso,
            hoje=self.today_str(),
            summary=summary,
            rows=rows_sanitized,
            rows_prev=rows_prev_sanitized,
            rows_ytd=rows_ytd_sanitized,
            rows_ytd_prev=rows_ytd_prev_sanitized,
            total_linhas=summary.get("row_count", 0),
            soma_valor_mensal_final=soma_fmt,
            SLA_URL=self.env_cfg.get("SLA_URL", ""),
            sender_name=self.env_cfg.get("SENDER_NAME", ""),
            sender_email=self.env_cfg.get("SENDER_EMAIL", ""),
            destinatarios_exibicao=destinatarios_exibicao,
            copy=copy,
            logo_img_src=logo_b64,
            logo_cid=logo_cid,
            logo_http_url=logo_http_url,
            table_columns=resolved_columns,
            table_numeric_columns=self.TABLE_NUMERIC_COLUMNS,
            table_money_columns=self.TABLE_MONEY_COLUMNS,
            table_percentage_columns=self.TABLE_PERCENTAGE_COLUMNS,
            fmt_brl=fmt_brl,
            fmt_percentage=fmt_percentage,
            prev_summary=(extra_prev or {}),
            **brand_vars,
        )
        return html

    def subject(
        self,
        unidade: str,
        ym: str,
        *,
        regiao: str,
        template: Optional[str] = None,
        copy_overrides: Optional[Dict[str, str]] = None,
    ) -> str:
        mes_extenso = self.format_mes_extenso(ym)
        context = {"unidade": unidade, "mes_ref": ym, "mes_extenso": mes_extenso, "regiao": regiao}
        candidates = [template]
        if copy_overrides:
            candidates.append(copy_overrides.get("SUBJECT_TEMPLATE"))
        candidates.append(self.env_cfg.get("SUBJECT_TEMPLATE"))
        subject_value = None
        for cand in candidates:
            if cand and str(cand).strip():
                subject_value = str(cand).strip()
                break
        if subject_value:
            try:
                subject = subject_value.format(**context)
            except Exception:
                subject = subject_value
        else:
            subject = f"Medição mensal - {unidade} - {mes_extenso}"
        if (self.env_cfg.get("USE_TEST_SUBJECT", "false") or "").lower() == "true":
            subject = "(Teste) " + subject
        return subject

    def send_outlook(
        self,
        subject: str,
        html: str,
        recipients: List[str],
        sender_email: str,
        attachments: Optional[List[Path]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> None:
        if "Windows" not in platform.system():
            raise RuntimeError("Envio Outlook disponível apenas no Windows com Outlook instalado.")
        if not recipients:
            raise RuntimeError("Nenhum destinatário informado.")

        import win32com.client as win32
        outlook = win32.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.Subject = subject
        # Anexa a logo como CID para compatibilidade com Outlook
        try:
            logo_path = self._resolve_logo_file_path()
        except Exception:
            logo_path = None
        if attachments:
            for att in attachments:
                if att and Path(att).exists():
                    mail.Attachments.Add(str(att))

        if logo_path and logo_path.exists():
            try:
                att = mail.Attachments.Add(str(logo_path))
                pa = att.PropertyAccessor
                # PR_ATTACH_CONTENT_ID (Unicode)
                pa.SetProperty("http://schemas.microsoft.com/mapi/proptag/0x3712001F", self.env_cfg.get("LOGO_CID", "atlas-logo"))
                # PR_ATTACHMENT_HIDDEN (bool)
                pa.SetProperty("http://schemas.microsoft.com/mapi/proptag/0x3714000B", True)
                # MIME tag
                mime = "image/png" if logo_path.suffix.lower() == ".png" else "image/jpeg"
                pa.SetProperty("http://schemas.microsoft.com/mapi/proptag/0x370E001F", mime)
                # posição de renderização (0)
                try:
                    pa.SetProperty("http://schemas.microsoft.com/mapi/proptag/0x37160003", 0)
                except Exception:
                    pass
            except Exception:
                pass

        mail.HTMLBody = html
        mail.To = "; ".join(recipients)
        
        # Adiciona CC
        if cc:
            cc_clean = [e.strip() for e in cc if e and e.strip()]
            if cc_clean:
                mail.CC = "; ".join(cc_clean)
        
        # Adiciona BCC
        if bcc:
            bcc_clean = [e.strip() for e in bcc if e and e.strip()]
            if bcc_clean:
                mail.BCC = "; ".join(bcc_clean)

        try:
            from utils import pick_account
            account = pick_account(outlook, sender_email)
            if account is not None:
                mail._oleobj_.Invoke(*(64209, 0, 8, 0, account))
            else:
                try:
                    mail.SentOnBehalfOfName = sender_email
                except Exception:
                    pass
        except Exception:
            pass

        mail.Send()
        
        # Log melhorado
        cc_info = f" (CC: {', '.join(cc)})" if cc else ""
        print(f"✓ E-mail enviado via Outlook{cc_info}")

    def send_sendgrid(
        self,
        subject: str,
        html: str,
        recipients: List[str],
        sender_email: str,
        sender_name: str = "",
        attachments: Optional[List[Path]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> None:
        """
        Envia e-mail via SendGrid API.
        
        Args:
            subject: Assunto do e-mail
            html: Conteúdo HTML do e-mail
            recipients: Lista de endereços TO (destinatários principais)
            sender_email: E-mail do remetente
            sender_name: Nome do remetente (opcional)
            attachments: Lista de caminhos de arquivos para anexar (opcional)
            cc: Lista de endereços em cópia (CC) (opcional)
            bcc: Lista de endereços em cópia oculta (BCC) (opcional)
        
        Raises:
            RuntimeError: Se SENDGRID_API_KEY não estiver configurada ou houver erro no envio
        """
        if not recipients:
            raise RuntimeError("Nenhum destinatário informado.")
        
        api_key = self.env_cfg.get("SENDGRID_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "SENDGRID_API_KEY não configurada no .env. "
                "Obtenha uma API key em https://app.sendgrid.com/settings/api_keys"
            )
        
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition, Cc, Bcc
            import base64
        except ImportError:
            raise RuntimeError(
                "Biblioteca sendgrid não instalada. Execute: pip install sendgrid"
            )
        
        # Prepara o remetente
        from_email = (sender_email, sender_name) if sender_name else sender_email
        
        # Cria a mensagem
        message = Mail(
            from_email=from_email,
            to_emails=recipients,
            subject=subject,
            html_content=html
        )
        
        # Adiciona CC se fornecido
        if cc:
            for cc_email in cc:
                if cc_email and cc_email.strip():
                    message.add_cc(Cc(cc_email.strip()))
        
        # Adiciona BCC se fornecido
        if bcc:
            for bcc_email in bcc:
                if bcc_email and bcc_email.strip():
                    message.add_bcc(Bcc(bcc_email.strip()))
        
        # Adiciona anexos se houver
        if attachments:
            for att_path in attachments:
                if att_path and Path(att_path).exists():
                    try:
                        with open(att_path, 'rb') as f:
                            data = f.read()
                        encoded = base64.b64encode(data).decode()
                        
                        # Determina o tipo MIME baseado na extensão
                        ext = Path(att_path).suffix.lower()
                        mime_types = {
                            '.pdf': 'application/pdf',
                            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            '.xls': 'application/vnd.ms-excel',
                            '.png': 'image/png',
                            '.jpg': 'image/jpeg',
                            '.jpeg': 'image/jpeg',
                            '.gif': 'image/gif',
                            '.txt': 'text/plain',
                            '.csv': 'text/csv',
                        }
                        file_type = mime_types.get(ext, 'application/octet-stream')
                        
                        attached_file = Attachment(
                            FileContent(encoded),
                            FileName(att_path.name),
                            FileType(file_type),
                            Disposition('attachment')
                        )
                        message.add_attachment(attached_file)
                    except Exception as e:
                        print(f"Aviso: Não foi possível anexar {att_path.name}: {e}")
        
        # Configura o cliente SendGrid
        try:
            sg = SendGridAPIClient(api_key)
            
            # Verifica se deve usar EU Data Residency
            use_eu = self.env_cfg.get("SENDGRID_USE_EU_REGION", "false").lower() == "true"
            if use_eu:
                sg.client.host = "https://api.eu.sendgrid.com"
            
            # Envia o e-mail
            response = sg.send(message)
            
            # Log melhorado com informação de CC
            cc_info = f" (CC: {', '.join(cc)})" if cc else ""
            if response.status_code in (200, 202):
                print(f"✓ E-mail enviado via SendGrid com sucesso (Status: {response.status_code}){cc_info}")
            else:
                print(f"⚠ SendGrid retornou status {response.status_code}")
                
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                raise RuntimeError(
                    "Erro de autenticação SendGrid. Verifique se a SENDGRID_API_KEY está correta."
                )
            elif "403" in error_msg or "Forbidden" in error_msg:
                raise RuntimeError(
                    "Acesso negado pelo SendGrid. Verifique as permissões da API key."
                )
            else:
                raise RuntimeError(f"Erro ao enviar via SendGrid: {error_msg}")

