"""
Router para preview de arquivos HTML gerados.
Serve os arquivos reais da pasta output_html.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import os
import re
import logging
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/preview", tags=["Preview"])

# Caminho para a pasta output_html (relativo ao root do projeto)
# __file__ = backend/app/routers/preview.py
# parent.parent.parent.parent = raiz do projeto (c:\backpperformance)
OUTPUT_HTML_PATH = Path(__file__).parent.parent.parent.parent / "output_html"

# Mapeamento de prefixos de unidade para região (baseado na estrutura de dados)
UNIT_REGION_MAP = {
    # RJ
    'Bangu': 'RJ', 'Carioca': 'RJ', 'Caxias': 'RJ', 'Independência': 'RJ',
    'Norte Shopping': 'RJ', 'Passeio Shopping': 'RJ', 'Recreio': 'RJ',
    'Rio Design': 'RJ', 'Grande Rio': 'RJ', 'Shopping Leblon': 'RJ',
    'Vila Velha': 'RJ', 'Tijuca': 'RJ', 'Plaza Niterói': 'RJ', 'Leblon': 'RJ',
    # SP1
    'Catuaí': 'SP1', 'Catuai': 'SP1', 'São Bernardo': 'SP1', 'Campo Grande': 'SP1',
    'Shopping Curitiba': 'SP1', 'Curitiba': 'SP1', 'Shopping Goiânia': 'SP1', 'Metrópole': 'SP1',
    'Passeio das Águas': 'SP1', 'Tamboré': 'SP1', 'Londrina': 'SP1', 'Maringá': 'SP1',
    # NNE
    'Amazonas': 'NNE', 'Boulevard Belém': 'NNE', 'Boulevard Feira': 'NNE',
    'Cariri': 'NNE', 'Manauara': 'NNE', 'Parque Shopping Belém': 'NNE',
    'Shopping da Bahia': 'NNE', 'Bahia': 'NNE', 'Parangaba': 'NNE', 'Plaza Sul': 'NNE',
    'Rio Anil': 'NNE', 'Taboão': 'NNE',
    # SP2
    'Boulevard Bauru': 'SP2', 'Bauru': 'SP2', 'Franca': 'SP2', 'Praça Nova': 'SP2',
    'Campo Limpo': 'SP2', 'Dom Pedro': 'SP2', 'Piracicaba': 'SP2',
    'Villa Lobos': 'SP2', 'Villagio': 'SP2', 'Araçatuba': 'SP2',
    # SP3
    'Boulevard BH': 'SP3', 'Center Shopping Uberlândia': 'SP3', 'Uberlândia': 'SP3', 
    'Mooca': 'SP3', 'Del Rey': 'SP3', 'Estação BH': 'SP3', 'Estação Cuiabá': 'SP3',
    'Metrô Santa Cruz': 'SP3', 'Cuiabá': 'SP3',
}


def detect_region(unit_name: str) -> str:
    """Detecta a região baseada no nome da unidade."""
    for prefix, region in UNIT_REGION_MAP.items():
        if prefix.lower() in unit_name.lower():
            return region
    return "OUTROS"


def parse_filename(filename: str) -> Dict[str, Any]:
    """
    Extrai informações do nome do arquivo.
    Formato esperado: Nome_Unidade_YYYY-MM.html
    """
    stem = Path(filename).stem
    
    # Tentar extrair mês (formato YYYY-MM no final)
    month_match = re.search(r'_(\d{4}-\d{2})$', stem)
    if month_match:
        month = month_match.group(1)
        unit_name = stem[:month_match.start()].replace('_', ' ')
    else:
        month = ""
        unit_name = stem.replace('_', ' ')
    
    region = detect_region(unit_name)
    
    return {
        "filename": filename,
        "unit_name": unit_name,
        "month": month,
        "region": region,
        "full_path": str(OUTPUT_HTML_PATH / filename)
    }


@router.get("/files", summary="Listar arquivos HTML disponíveis")
async def list_html_files() -> List[Dict[str, Any]]:
    """
    Lista todos os arquivos HTML disponíveis na pasta output_html.
    Retorna lista de objetos com filename, unit_name, month, region, full_path.
    """
    if not OUTPUT_HTML_PATH.exists():
        return []
    
    files = []
    for file in OUTPUT_HTML_PATH.glob("*.html"):
        file_info = parse_filename(file.name)
        # Adicionar tamanho e data de modificação
        stat = file.stat()
        file_info["size_bytes"] = stat.st_size
        file_info["modified_at"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        files.append(file_info)
    
    # Ordenar por nome da unidade
    files.sort(key=lambda x: x["unit_name"])
    
    return files


@router.get("/stats", summary="Estatísticas da pasta de HTMLs")
async def get_html_stats() -> Dict[str, Any]:
    """
    Retorna estatísticas sobre os arquivos HTML armazenados.
    """
    if not OUTPUT_HTML_PATH.exists():
        return {
            "total_files": 0,
            "total_size_mb": 0,
            "oldest_file": None,
            "newest_file": None,
            "files_by_region": {}
        }
    
    files = list(OUTPUT_HTML_PATH.glob("*.html"))
    if not files:
        return {
            "total_files": 0,
            "total_size_mb": 0,
            "oldest_file": None,
            "newest_file": None,
            "files_by_region": {}
        }
    
    total_size = sum(f.stat().st_size for f in files)
    files_with_dates = [(f, f.stat().st_mtime) for f in files]
    files_with_dates.sort(key=lambda x: x[1])
    
    # Contar por região
    files_by_region: Dict[str, int] = {}
    for f in files:
        info = parse_filename(f.name)
        region = info.get("region", "OUTROS")
        files_by_region[region] = files_by_region.get(region, 0) + 1
    
    return {
        "total_files": len(files),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "oldest_file": {
            "name": files_with_dates[0][0].name,
            "date": datetime.fromtimestamp(files_with_dates[0][1]).isoformat()
        },
        "newest_file": {
            "name": files_with_dates[-1][0].name,
            "date": datetime.fromtimestamp(files_with_dates[-1][1]).isoformat()
        },
        "files_by_region": files_by_region
    }


@router.delete("/files/{filename}", summary="Remover arquivo HTML específico")
async def delete_html_file(filename: str) -> Dict[str, Any]:
    """
    Remove um arquivo HTML específico.
    """
    file_path = OUTPUT_HTML_PATH / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {filename}")
    
    try:
        file_path.unlink()
        logger.info(f"Arquivo removido: {filename}")
        return {
            "success": True,
            "message": f"Arquivo {filename} removido com sucesso"
        }
    except Exception as e:
        logger.error(f"Erro ao remover arquivo {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao remover arquivo: {str(e)}")


@router.delete("/cleanup", summary="Limpeza de arquivos HTML antigos")
async def cleanup_old_html_files(days: int = 30) -> Dict[str, Any]:
    """
    Remove arquivos HTML mais antigos que o período especificado (em dias).
    Por padrão, remove arquivos com mais de 30 dias.
    """
    if days < 7:
        raise HTTPException(status_code=400, detail="Período mínimo de retenção é 7 dias")
    
    if not OUTPUT_HTML_PATH.exists():
        return {
            "success": True,
            "deleted_count": 0,
            "message": "Pasta de output não existe"
        }
    
    from datetime import timedelta
    cutoff_time = datetime.now() - timedelta(days=days)
    
    deleted_files = []
    errors = []
    
    for file in OUTPUT_HTML_PATH.glob("*.html"):
        try:
            file_mtime = datetime.fromtimestamp(file.stat().st_mtime)
            if file_mtime < cutoff_time:
                file.unlink()
                deleted_files.append(file.name)
                logger.info(f"Arquivo antigo removido: {file.name}")
        except Exception as e:
            errors.append({"file": file.name, "error": str(e)})
            logger.error(f"Erro ao remover {file.name}: {e}")
    
    return {
        "success": True,
        "deleted_count": len(deleted_files),
        "deleted_files": deleted_files,
        "errors": errors if errors else None,
        "cutoff_date": cutoff_time.isoformat(),
        "message": f"Removidos {len(deleted_files)} arquivos com mais de {days} dias"
    }


# ============================================================================
# SCHEMAS PARA EDIÇÃO (devem estar ANTES dos endpoints)
# ============================================================================

class EditableTexts(BaseModel):
    """Textos editáveis do email."""
    subject: Optional[str] = Field(None, description="Assunto do email (da tag <title>)")
    greeting: Optional[str] = Field(None, description="Saudação inicial")
    intro: Optional[str] = Field(None, description="Texto de introdução")
    observation: Optional[str] = Field(None, description="Texto de observação/alerta")


class UpdateTextsRequest(BaseModel):
    """Request para atualizar textos do HTML."""
    subject: Optional[str] = Field(None, description="Novo assunto")
    greeting: Optional[str] = Field(None, description="Nova saudação")
    intro: Optional[str] = Field(None, description="Nova introdução")
    observation: Optional[str] = Field(None, description="Nova observação")


# ============================================================================
# ENDPOINTS DE TEXTOS (devem vir ANTES do endpoint genérico /files/{filename})
# ============================================================================

@router.get("/files/{filename}/texts", summary="Extrair textos editáveis do HTML")
async def get_html_texts(filename: str) -> EditableTexts:
    """
    Extrai os textos editáveis de um arquivo HTML.
    """
    file_path = OUTPUT_HTML_PATH / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {filename}")
    
    html_content = file_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extrair subject da tag <title>, ou do h1.report-title como fallback
    title_tag = soup.find('title')
    if title_tag:
        subject = title_tag.get_text(strip=True)
    else:
        # Fallback: extrair do h1.report-title
        report_title = soup.find('h1', class_='report-title')
        subject = report_title.get_text(strip=True) if report_title else ""
    
    # Extrair textos intro-text (geralmente são greeting e intro)
    intro_texts = soup.find_all('p', class_='intro-text')
    greeting = intro_texts[0].get_text(strip=True) if len(intro_texts) > 0 else ""
    intro = intro_texts[1].get_text(strip=True) if len(intro_texts) > 1 else ""
    
    # Extrair observação do alert-content
    alert_div = soup.find('div', class_='alert-content')
    observation = ""
    if alert_div:
        strong = alert_div.find('strong')
        if strong:
            observation = alert_div.get_text(strip=True).replace(strong.get_text(strip=True), '').strip()
        else:
            observation = alert_div.get_text(strip=True)
    
    return EditableTexts(
        subject=subject,
        greeting=greeting,
        intro=intro,
        observation=observation
    )


@router.put("/files/{filename}/texts", summary="Atualizar textos do HTML")
async def update_html_texts(filename: str, request: UpdateTextsRequest) -> Dict[str, Any]:
    """
    Atualiza os textos editáveis de um arquivo HTML.
    """
    file_path = OUTPUT_HTML_PATH / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {filename}")
    
    html_content = file_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html_content, 'html.parser')
    changes_made = []
    
    # Atualizar subject (na tag <title> e no h1.report-title)
    if request.subject is not None:
        title_tag = soup.find('title')
        if title_tag:
            title_tag.string = request.subject
        else:
            # Criar a tag <title> se não existir
            head = soup.find('head')
            if head:
                new_title = soup.new_tag('title')
                new_title.string = request.subject
                head.append(new_title)
        changes_made.append("subject")
        
        # Também atualizar o h1.report-title para manter consistência visual
        report_title = soup.find('h1', class_='report-title')
        if report_title:
            report_title.string = request.subject
    
    # Atualizar greeting e intro
    intro_texts = soup.find_all('p', class_='intro-text')
    
    if request.greeting is not None and len(intro_texts) > 0:
        intro_texts[0].string = request.greeting
        changes_made.append("greeting")
    
    if request.intro is not None and len(intro_texts) > 1:
        intro_texts[1].string = request.intro
        changes_made.append("intro")
    
    # Atualizar observação
    if request.observation is not None:
        alert_div = soup.find('div', class_='alert-content')
        if alert_div:
            strong = alert_div.find('strong')
            if strong:
                strong_html = str(strong)
                alert_div.clear()
                alert_div.append(BeautifulSoup(strong_html, 'html.parser'))
                alert_div.append(f" {request.observation}")
            else:
                alert_div.string = request.observation
            changes_made.append("observation")
    
    # Salvar o arquivo modificado
    if changes_made:
        file_path.write_text(str(soup), encoding="utf-8")
    
    return {
        "success": True,
        "filename": filename,
        "changes_made": changes_made,
        "message": f"Arquivo atualizado com sucesso. Campos modificados: {', '.join(changes_made)}" if changes_made else "Nenhuma alteração realizada"
    }


# ============================================================================
# ENDPOINT GENÉRICO PARA SERVIR HTML (deve ser o ÚLTIMO com {filename})
# ============================================================================

@router.get("/files/{filename}", response_class=HTMLResponse, summary="Obter conteúdo HTML")
async def get_html_file(filename: str):
    """
    Retorna o conteúdo de um arquivo HTML específico.
    """
    file_path = OUTPUT_HTML_PATH / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {filename}")
    
    if not file_path.suffix.lower() == ".html":
        raise HTTPException(status_code=400, detail="Apenas arquivos HTML são permitidos")
    
    # Verificar se o arquivo está dentro da pasta permitida (segurança)
    try:
        file_path.resolve().relative_to(OUTPUT_HTML_PATH.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    return file_path.read_text(encoding="utf-8")


@router.get("/regions", summary="Listar regiões disponíveis")
async def list_regions() -> List[Dict[str, Any]]:
    """
    Lista todas as regiões que possuem arquivos HTML gerados.
    Retorna lista de objetos com code e count.
    """
    if not OUTPUT_HTML_PATH.exists():
        return []
    
    region_counts: Dict[str, int] = {}
    
    for file in OUTPUT_HTML_PATH.glob("*.html"):
        file_info = parse_filename(file.name)
        region = file_info["region"]
        region_counts[region] = region_counts.get(region, 0) + 1
    
    return [
        {"code": code, "count": count}
        for code, count in sorted(region_counts.items())
    ]


@router.get("/months", summary="Listar meses disponíveis")
async def list_months() -> List[str]:
    """
    Lista todos os meses que possuem arquivos HTML gerados.
    """
    if not OUTPUT_HTML_PATH.exists():
        return []
    
    months = set()
    for file in OUTPUT_HTML_PATH.glob("*.html"):
        file_info = parse_filename(file.name)
        if file_info["month"]:
            months.add(file_info["month"])
    
    return sorted(list(months), reverse=True)


@router.get("/stats", summary="Estatísticas dos arquivos HTML")
async def get_stats() -> Dict[str, Any]:
    """
    Retorna estatísticas sobre os arquivos HTML gerados.
    """
    if not OUTPUT_HTML_PATH.exists():
        return {
            "total_files": 0,
            "total_size": "0 KB",
            "regions": [],
            "months": [],
            "last_generated": None,
            "output_path": str(OUTPUT_HTML_PATH)
        }
    
    files = list(OUTPUT_HTML_PATH.glob("*.html"))
    total_size = sum(f.stat().st_size for f in files)
    
    months = set()
    regions = set()
    last_modified = None
    
    for file in files:
        stat = file.stat()
        if last_modified is None or stat.st_mtime > last_modified:
            last_modified = stat.st_mtime
        
        file_info = parse_filename(file.name)
        if file_info["month"]:
            months.add(file_info["month"])
        regions.add(file_info["region"])
    
    return {
        "total_files": len(files),
        "total_size": f"{total_size / 1024:.1f} KB",
        "regions": sorted(list(regions)),
        "months": sorted(list(months), reverse=True),
        "last_generated": datetime.fromtimestamp(last_modified).isoformat() if last_modified else None,
        "output_path": str(OUTPUT_HTML_PATH)
    }


# ============================================================
# ENVIO DE EMAIL DIRETO DO PREVIEW
# ============================================================

class SendEmailRequest(BaseModel):
    """Request para enviar email diretamente do preview."""
    email_subject: str = Field(..., description="Assunto do email (linha de assunto)")
    recipients: Optional[List[str]] = Field(None, description="Lista de destinatários (se vazio, extrai do HTML)")
    cc_emails: Optional[List[str]] = Field(None, description="Lista de CCs adicionais")
    mandatory_cc: str = Field(default="consultoria@atlasinovacoes.com.br", description="CC obrigatório")
    sender_email: Optional[str] = Field(None, description="Email do remetente")
    sender_name: Optional[str] = Field(None, description="Nome do remetente")


@router.post("/files/{filename}/send", summary="Envia email com o HTML atual")
async def send_email_from_preview(filename: str, request: SendEmailRequest) -> Dict[str, Any]:
    """
    Envia email usando o HTML atual (com edições) e subject customizado.
    
    - **filename**: Nome do arquivo HTML
    - **email_subject**: Assunto do email (aparece na caixa de entrada)
    - **recipients**: Destinatários (opcional - extrai do HTML se não informado)
    """
    from app.services.pipeline_service import PipelineService
    
    file_path = OUTPUT_HTML_PATH / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {filename}")
    
    html_content = file_path.read_text(encoding="utf-8")
    
    # Inicializar o serviço do pipeline para usar o método de envio
    pipeline = PipelineService()
    
    # Extrair destinatários do HTML se não foram fornecidos
    recipients = request.recipients
    if not recipients:
        recipients = pipeline._extract_emails_from_html(html_content)
    
    if not recipients:
        raise HTTPException(
            status_code=400, 
            detail="Nenhum destinatário encontrado. Forneça a lista de recipients ou verifique se o HTML contém emails."
        )
    
    # Montar lista de CCs (evitando duplicatas com TO)
    all_cc = []
    recipients_lower = {e.lower() for e in recipients}
    
    if request.mandatory_cc and request.mandatory_cc.lower() not in recipients_lower:
        all_cc.append(request.mandatory_cc)
    
    if request.cc_emails:
        for cc in request.cc_emails:
            if cc.lower() not in recipients_lower and cc.lower() not in [c.lower() for c in all_cc]:
                all_cc.append(cc)
    
    logger.info(f"[PREVIEW] Enviando email - Subject: {request.email_subject}")
    logger.info(f"[PREVIEW] Recipients: {recipients}")
    logger.info(f"[PREVIEW] CCs: {all_cc}")
    
    # Enviar usando o método do pipeline
    try:
        sent = pipeline._send_via_sendgrid(
            subject=request.email_subject,
            html=html_content,
            recipients=recipients,
            cc_emails=all_cc if all_cc else None,
            sender_email=request.sender_email,
            sender_name=request.sender_name,
            reply_to=None
        )
        
        if sent:
            logger.info(f"[PREVIEW] Email enviado com sucesso para: {recipients}")
            return {
                "success": True,
                "message": "Email enviado com sucesso",
                "emails_sent_to": recipients,
                "cc_emails": all_cc,
                "subject": request.email_subject
            }
        else:
            return {
                "success": False,
                "error": "Falha ao enviar email via SendGrid"
            }
    except Exception as e:
        logger.error(f"[PREVIEW] Erro ao enviar email: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao enviar email: {str(e)}")