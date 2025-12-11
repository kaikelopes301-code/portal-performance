"""
Serviço de pipeline: orquestra extração → processamento → geração HTML → envio.
"""
import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

logger = logging.getLogger(__name__)

# Importa módulos core
from app.core import Extractor, filter_and_prepare, map_columns, Emailer, utils, ROOT_DIR

# Caminhos
PLANILHAS_DIR = ROOT_DIR / "planilhas"
UPLOADS_DIR = ROOT_DIR / "backend" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)  # Garante que existe
TEMPLATES_DIR = ROOT_DIR / "templates"
ASSETS_DIR = ROOT_DIR / "assets"
OUTPUT_HTML_DIR = ROOT_DIR / "output_html"


@dataclass
class PipelineResult:
    """Resultado de uma execução do pipeline."""
    success: bool = False
    html_content: str = ""
    html_path: Optional[str] = None
    emails_found: List[str] = field(default_factory=list)
    emails_sent_to: List[str] = field(default_factory=list)
    error: Optional[str] = None
    rows_count: int = 0
    summary: Dict[str, Any] = field(default_factory=dict)
    unit: str = ""
    region: str = ""
    month: str = ""


class PipelineService:
    """Serviço que orquestra o pipeline de extração, processamento e envio."""
    
    def __init__(self):
        self.extractor = Extractor(PLANILHAS_DIR)
        # Extractor secundário para uploads (sempre existe pois criamos o dir)
        self.extractor_uploads = Extractor(UPLOADS_DIR)
        
        logger.info(f"[PIPELINE] Pasta planilhas: {PLANILHAS_DIR}")
        logger.info(f"[PIPELINE] Pasta uploads: {UPLOADS_DIR}")
        
        # Carrega variáveis de ambiente para o emailer
        self.env_cfg = {
            "SENDER_NAME": os.getenv("SENDGRID_FROM_NAME", os.getenv("SENDER_NAME", "Equipe Financeira")),
            "SENDER_EMAIL": os.getenv("SENDGRID_FROM_EMAIL", os.getenv("SENDER_EMAIL", "")),
            "SLA_URL": os.getenv("SLA_URL", ""),
            "LOGO_FILE": os.getenv("LOGO_FILE", "logo-performance-horizontal-azul.png"),
            "SUBJECT_TEMPLATE": os.getenv("SUBJECT_TEMPLATE", "Medição {unidade} - {mes_ref}"),
            "USE_TEST_SUBJECT": os.getenv("USE_TEST_SUBJECT", "false"),
        }
        
        self.emailer = Emailer(TEMPLATES_DIR, ASSETS_DIR, self.env_cfg)
        
        # Importa ConfigService aqui para evitar circular import
        from app.services.config_service import ConfigService
        self.config_service = ConfigService()
    
    def _find_workbook_with_priority(self, region: str) -> Optional[Path]:
        """
        Busca planilha priorizando uploads recentes sobre pasta padrão.
        
        Ordem de busca:
        1. Primeiro busca nos uploads (backend/uploads/)
        2. Se não encontrar, busca na pasta padrão (planilhas/)
        
        Returns:
            Path da planilha encontrada ou None
        """
        # 1. Busca primeiro nos uploads (planilhas enviadas via portal)
        workbook = self.extractor_uploads.find_workbook(region)
        if workbook:
            logger.info(f"[PIPELINE] Planilha encontrada nos UPLOADS: {workbook.name}")
            return workbook
        
        # 2. Fallback: busca na pasta padrão (planilhas/)
        workbook = self.extractor.find_workbook(region)
        if workbook:
            logger.info(f"[PIPELINE] Planilha encontrada na pasta PADRÃO: {workbook.name}")
            return workbook
        
        logger.warning(f"[PIPELINE] Planilha NÃO encontrada para região {region} em nenhuma pasta")
        return None
    
    def _extract_emails_from_html(self, html: str) -> List[str]:
        """Extrai emails do HTML (do rodapé/destinatários)."""
        # Procura no footer-meta por "Destinatários:"
        pattern = r'Destinat[áa]rios:</strong>\s*([^<]+)'
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            emails_str = match.group(1).strip()
            emails = [e.strip() for e in emails_str.split(',') if '@' in e]
            return emails
        
        # Fallback: procura qualquer email no HTML
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        all_emails = re.findall(email_pattern, html)
        # Remove duplicatas e emails do sistema
        system_emails = {'consultoria@atlasinovacoes.com.br', 'noreply@'}
        return list(set(e for e in all_emails if not any(s in e.lower() for s in system_emails)))
    
    def _extract_subject_from_html(self, html: str) -> Optional[str]:
        """Extrai o subject da tag <title> do HTML, ou do h1.report-title como fallback."""
        # Primeiro tenta extrair da tag <title>
        pattern = r'<title[^>]*>([^<]+)</title>'
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Fallback: extrair do h1.report-title
        h1_pattern = r'<h1[^>]*class=["\'][^"\']*report-title[^"\']*["\'][^>]*>([^<]+)</h1>'
        h1_match = re.search(h1_pattern, html, re.IGNORECASE)
        if h1_match:
            return h1_match.group(1).strip()
        
        return None
    
    def execute(
        self,
        region: str,
        unit: str,
        month: str,  # Formato YYYY-MM
        dry_run: bool = True,
        send_email: bool = False,
        visible_columns: Optional[List[str]] = None,
        copy_overrides: Optional[Dict[str, str]] = None,
        # Configurações de email
        sender_email: Optional[str] = None,
        sender_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        mandatory_cc: Optional[str] = None,  # Email obrigatório em cópia (consultoria)
        use_existing_html: bool = False,  # Se True, usa HTML existente sem regenerar
    ) -> PipelineResult:
        """
        Executa o pipeline completo para uma unidade.
        
        Args:
            region: Código da região (RJ, SP1, NNE, etc.)
            unit: Nome da unidade
            month: Mês de referência (YYYY-MM)
            dry_run: Se True, apenas gera HTML sem enviar
            send_email: Se True, envia email via SendGrid
            visible_columns: Colunas a exibir (opcional, usa config se None)
            copy_overrides: Textos personalizados (opcional, usa config se None)
            sender_email: Email do remetente (opcional, usa env se None)
            sender_name: Nome do remetente (opcional, usa env se None)
            reply_to: Email para respostas (opcional)
            cc_emails: Lista de emails em cópia (opcional)
            mandatory_cc: Email obrigatório em cópia (consultoria)
            use_existing_html: Se True, usa HTML existente (editado) sem regenerar
        
        Returns:
            PipelineResult com o resultado da execução
        """
        result = PipelineResult(unit=unit, region=region, month=month)
        
        try:
            logger.info(f"[PIPELINE] Iniciando: {unit} ({region}) - {month}")
            
            # Verifica se deve usar HTML existente
            safe_unit = unit.replace(" ", "_").replace("/", "_")
            filename = f"{safe_unit}_{month}.html"
            html_path = OUTPUT_HTML_DIR / filename
            
            if use_existing_html and html_path.exists():
                # Usa o HTML existente (editado na tela de preview)
                logger.info(f"[PIPELINE] Usando HTML existente: {html_path}")
                html = html_path.read_text(encoding='utf-8')
                result.html_content = html
                result.html_path = str(html_path)
                
                # Extrai emails do HTML existente (do footer)
                emails = self._extract_emails_from_html(html)
                result.emails_found = emails
                result.rows_count = -1  # Indica que usou HTML existente
                result.summary = {"source": "existing_html"}
                
            else:
                # Pipeline normal: regenera do Excel
                # 1. Localiza a planilha (busca primeiro nos uploads, depois na pasta padrão)
                workbook_path = self._find_workbook_with_priority(region)
                if not workbook_path:
                    result.error = f"Planilha não encontrada para região {region}. Faça upload da planilha no Dashboard."
                    logger.error(result.error)
                    return result
                
                # Determina qual extractor usar baseado no path
                if str(workbook_path).startswith(str(UPLOADS_DIR)):
                    extractor = self.extractor_uploads
                else:
                    extractor = self.extractor
                
                # 2. Lê a aba da região
                df, sheet_name = extractor.read_region_sheet(workbook_path, region)
                logger.info(f"[PIPELINE] Aba lida: {sheet_name} ({len(df)} linhas)")
                
                # 3. Obtém configuração mesclada para a unidade
                config = self.config_service.get_effective_config(unit, region)
                
                # Usa parâmetros passados ou da config
                if visible_columns is None:
                    visible_columns = config.get("visible_columns")
                if copy_overrides is None:
                    copy_overrides = config.get("copy", {})
                
                # 4. Filtra e processa os dados
                rows, emails, summary = filter_and_prepare(
                    df=df,
                    unidade=unit,
                    ym=month,
                    columns_whitelist=visible_columns
                )
                
                if not rows:
                    result.error = f"Nenhum dado encontrado para {unit} em {month}"
                    logger.warning(result.error)
                    return result
                
                result.rows_count = len(rows)
                result.summary = summary
                result.emails_found = emails
                
                logger.info(f"[PIPELINE] Dados processados: {len(rows)} linhas, {len(emails)} emails")
                
                # 5. Gera o HTML
                destinatarios_str = ", ".join(emails) if emails else ""
                html = self.emailer.render_html(
                    unidade=unit,
                    regiao=region,
                    ym=month,
                    rows=rows,
                    summary=summary,
                    destinatarios_exibicao=destinatarios_str,
                    copy_overrides=copy_overrides,
                    table_columns=visible_columns,
                )
                
                result.html_content = html
                
                # 6. Salva o HTML
                OUTPUT_HTML_DIR.mkdir(parents=True, exist_ok=True)
                html_path.write_text(html, encoding='utf-8')
                result.html_path = str(html_path)
                
                logger.info(f"[PIPELINE] HTML salvo: {html_path}")
            
            # 7. Envia email se não for dry_run (comum aos dois fluxos)
            emails = result.emails_found
            html = result.html_content
            
            if not dry_run and send_email and emails:
                # Se usou HTML existente, extrai o subject do HTML (pode ter sido editado)
                if use_existing_html:
                    subject = self._extract_subject_from_html(html)
                    if not subject:
                        # Fallback se não conseguir extrair
                        subject = self.emailer.subject(unit, month, regiao=region, copy_overrides=copy_overrides)
                    logger.info(f"[PIPELINE] Subject extraído do HTML: {subject}")
                else:
                    subject = self.emailer.subject(
                        unit, month, 
                        regiao=region, 
                        copy_overrides=copy_overrides
                    )
                
                # Monta lista de CCs (obrigatório + adicionais)
                # Remove duplicatas: emails que já estão em TO não devem estar em CC
                all_cc = []
                recipients_lower = {e.lower() for e in emails}
                
                if mandatory_cc and mandatory_cc.lower() not in recipients_lower:
                    all_cc.append(mandatory_cc)
                if cc_emails:
                    for cc in cc_emails:
                        if cc.lower() not in recipients_lower and cc.lower() not in [c.lower() for c in all_cc]:
                            all_cc.append(cc)
                
                logger.debug(f"[PIPELINE] Recipients (TO): {emails}")
                logger.debug(f"[PIPELINE] CCs: {all_cc}")
                
                sent = self._send_via_sendgrid(
                    subject=subject,
                    html=html,
                    recipients=emails,
                    cc_emails=all_cc if all_cc else None,
                    sender_email=sender_email,
                    sender_name=sender_name,
                    reply_to=reply_to,
                )
                if sent:
                    result.emails_sent_to = emails
                    logger.info(f"[PIPELINE] Email enviado para: {', '.join(emails)}")
                    if all_cc:
                        logger.info(f"[PIPELINE] CC: {', '.join(all_cc)}")
                else:
                    logger.warning("[PIPELINE] Falha ao enviar email")
            
            result.success = True
            logger.info(f"[PIPELINE] Concluído com sucesso: {unit}")
            
        except Exception as e:
            result.error = str(e)
            logger.exception(f"[PIPELINE] Erro: {e}")
        
        return result
    
    def _send_via_sendgrid(
        self,
        subject: str,
        html: str,
        recipients: List[str],
        cc_emails: Optional[List[str]] = None,
        sender_email: Optional[str] = None,
        sender_name: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> bool:
        """Envia email via SendGrid."""
        try:
            api_key = os.getenv("SENDGRID_API_KEY")
            if not api_key:
                logger.error("SENDGRID_API_KEY não configurada")
                return False
            
            # Usa parâmetros passados ou variáveis de ambiente
            from_email = sender_email or os.getenv("SENDGRID_FROM_EMAIL")
            from_name = sender_name or os.getenv("SENDGRID_FROM_NAME", "")
            
            if not from_email:
                logger.error("SENDGRID_FROM_EMAIL não configurada")
                return False
            
            # Importa SendGrid
            try:
                import sendgrid
                from sendgrid.helpers.mail import Mail, Email, To, Cc, Content, ReplyTo
            except ImportError:
                logger.error("Pacote sendgrid não instalado. Execute: pip install sendgrid")
                return False
            
            sg = sendgrid.SendGridAPIClient(api_key)
            
            message = Mail(
                from_email=Email(from_email, from_name),
                to_emails=[To(email) for email in recipients],
                subject=subject,
                html_content=Content("text/html", html)
            )
            
            # Adiciona CCs se fornecidos
            if cc_emails:
                for cc_email in cc_emails:
                    message.add_cc(Cc(cc_email))
            
            # Adiciona Reply-To se fornecido
            if reply_to:
                message.reply_to = ReplyTo(reply_to)
            
            response = sg.send(message)
            logger.info(f"Email enviado! Status: {response.status_code}")
            return response.status_code in [200, 201, 202]
            
        except Exception as e:
            logger.exception(f"Falha ao enviar email: {e}")
            return False
    
    def list_available_units(self, region: str) -> List[str]:
        """Lista unidades disponíveis em uma região."""
        try:
            workbook_path = self.extractor.find_workbook(region)
            if not workbook_path:
                return []
            
            df, _ = self.extractor.read_region_sheet(workbook_path, region)
            
            # Tenta encontrar coluna de unidade
            mapping = map_columns(df, warn_missing=False)
            uni_col = mapping.get("Unidade")
            
            if uni_col and uni_col in df.columns:
                units = df[uni_col].dropna().unique().tolist()
                return sorted([str(u).strip() for u in units if str(u).strip()])
            
            return []
        except Exception as e:
            logger.exception(f"Erro ao listar unidades: {e}")
            return []
    
    def list_available_months(self, region: str) -> List[str]:
        """Lista meses disponíveis em uma região."""
        try:
            workbook_path = self.extractor.find_workbook(region)
            if not workbook_path:
                return []
            
            df, _ = self.extractor.read_region_sheet(workbook_path, region)
            
            mapping = map_columns(df, warn_missing=False)
            mes_col = mapping.get("Mes_Emissao_NF") or mapping.get("Mes_Emissão_NF")
            
            if mes_col and mes_col in df.columns:
                months = set()
                for val in df[mes_col].dropna():
                    parsed = utils.parse_year_month(val)
                    if parsed:
                        months.add(parsed)
                return sorted(list(months), reverse=True)
            
            return []
        except Exception as e:
            logger.exception(f"Erro ao listar meses: {e}")
            return []
    
    def list_available_regions(self) -> List[str]:
        """Lista regiões disponíveis (baseado em planilhas existentes)."""
        regions = []
        for file in PLANILHAS_DIR.glob("*.xlsx"):
            if file.name.startswith("~$"):
                continue
            for region in ["RJ", "SP1", "SP2", "SP3", "NNE"]:
                if region in file.name and region not in regions:
                    regions.append(region)
        return sorted(regions)


# Singleton
_pipeline_service: Optional[PipelineService] = None

def get_pipeline_service() -> PipelineService:
    """Retorna instância singleton do PipelineService."""
    global _pipeline_service
    if _pipeline_service is None:
        _pipeline_service = PipelineService()
    return _pipeline_service
