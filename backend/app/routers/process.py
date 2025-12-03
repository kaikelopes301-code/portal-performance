# process.py — Router para processamento de jobs
# IMPORTANTE: Rotas específicas (/execute, /metadata/regions) DEVEM vir ANTES
# de rotas com parâmetros dinâmicos (/{job_id}) para evitar conflitos de roteamento.

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from app.database import get_db
from app.models.job import ProcessingJob
from app.schemas.job import JobResponse
from app.services.job_processor import JobProcessor, JobProcessorError
from app.services.pipeline_service import get_pipeline_service, PipelineResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/process", tags=["process"])


# ============================================================================
# SCHEMAS
# ============================================================================

class ProcessRequest(BaseModel):
    """Schema para requisição de processamento."""
    region: str = Field(..., description="Código da região (SP1, RJ, NNE, SP2, SP3)")
    unit: str = Field(..., description="Nome da unidade a processar")
    month: str = Field(..., description="Mês de referência no formato YYYY-MM", pattern=r"^\d{4}-\d{2}$")
    dry_run: bool = Field(default=False, description="Se True, não envia emails")


class ProcessResponse(BaseModel):
    """Schema para resposta de processamento."""
    job_id: int
    status: str
    message: str
    result: Optional[dict] = None
    
    class Config:
        from_attributes = True


class MetadataResponse(BaseModel):
    """Schema para resposta de metadados de arquivo."""
    job_id: int
    sheet_name: str
    units: List[str]
    months: List[str]
    row_count: int
    columns: List[str]


class ExecuteRequest(BaseModel):
    """Schema para requisição de execução do pipeline."""
    region: str = Field(..., description="Código da região (SP1, RJ, NNE, SP2, SP3)")
    unit: str = Field(..., description="Nome da unidade")
    month: str = Field(..., description="Mês de referência (YYYY-MM)")
    dry_run: bool = Field(default=True, description="Se True, só gera HTML sem enviar email")
    send_email: bool = Field(default=False, description="Se True, envia via SendGrid")
    visible_columns: Optional[List[str]] = Field(default=None, description="Colunas a exibir (usa config se None)")
    copy_overrides: Optional[Dict[str, str]] = Field(default=None, description="Textos personalizados")
    # Configurações de email
    sender_email: Optional[str] = Field(default=None, description="Email do remetente")
    sender_name: Optional[str] = Field(default=None, description="Nome do remetente")
    reply_to: Optional[str] = Field(default=None, description="Email para respostas")
    cc_emails: Optional[List[str]] = Field(default=None, description="Emails em cópia adicionais")
    mandatory_cc: Optional[str] = Field(default="consultoria@atlasinovacoes.com.br", description="Email obrigatório em cópia (consultoria)")
    use_existing_html: bool = Field(default=False, description="Se True, usa HTML existente (editado) sem regenerar")


class BatchExecuteRequest(BaseModel):
    """Schema para execução em lote."""
    units: List[ExecuteRequest] = Field(..., description="Lista de unidades a processar")


class ExecuteResponse(BaseModel):
    """Resposta de execução do pipeline."""
    success: bool
    unit: str
    region: str
    month: str
    html_path: Optional[str] = None
    preview_url: Optional[str] = None
    rows_count: int = 0
    emails_found: List[str] = []
    emails_sent_to: List[str] = []
    summary: Dict[str, Any] = {}
    error: Optional[str] = None


class BatchExecuteResponse(BaseModel):
    """Resposta de execução em lote."""
    total: int
    successful: int
    failed: int
    results: List[ExecuteResponse]


class RegionMetadataResponse(BaseModel):
    """Metadados de uma região."""
    region: str
    units: List[str]
    months: List[str]


class AvailableRegionsResponse(BaseModel):
    """Lista de regiões disponíveis."""
    regions: List[str]


# ============================================================================
# ROTAS ESPECÍFICAS (DEVEM VIR ANTES DAS ROTAS COM PARÂMETROS DINÂMICOS)
# ============================================================================

@router.post("/execute", response_model=ExecuteResponse)
def execute_pipeline(request: ExecuteRequest):
    """
    Executa o pipeline completo para uma unidade.
    
    1. Extrai dados da planilha (da pasta planilhas/)
    2. Processa e filtra para a unidade/mês especificados
    3. Gera HTML usando o template email_template_dark.html
    4. Salva em output_html/
    5. Se send_email=True e dry_run=False, envia via SendGrid
    
    Args:
        request: Parâmetros de execução
    
    Returns:
        Resultado da execução com caminho do HTML e estatísticas
    """
    service = get_pipeline_service()
    
    logger.info(f"[EXECUTE] Request recebido: region={request.region}, unit={request.unit}, month={request.month}, dry_run={request.dry_run}")
    
    result = service.execute(
        region=request.region,
        unit=request.unit,
        month=request.month,
        dry_run=request.dry_run,
        send_email=request.send_email,
        visible_columns=request.visible_columns,
        copy_overrides=request.copy_overrides,
        # Configurações de email
        sender_email=request.sender_email,
        sender_name=request.sender_name,
        reply_to=request.reply_to,
        cc_emails=request.cc_emails,
        mandatory_cc=request.mandatory_cc,
        use_existing_html=request.use_existing_html,
    )
    
    # Monta URL de preview
    preview_url = None
    if result.html_path:
        from pathlib import Path
        filename = Path(result.html_path).name
        preview_url = f"/api/preview/file/{filename}"
    
    return ExecuteResponse(
        success=result.success,
        unit=result.unit,
        region=result.region,
        month=result.month,
        html_path=result.html_path,
        preview_url=preview_url,
        rows_count=result.rows_count,
        emails_found=result.emails_found,
        emails_sent_to=result.emails_sent_to,
        summary=result.summary,
        error=result.error,
    )


@router.post("/execute/batch", response_model=BatchExecuteResponse)
def execute_pipeline_batch(request: BatchExecuteRequest):
    """
    Executa o pipeline para múltiplas unidades.
    
    Args:
        request: Lista de unidades a processar
    
    Returns:
        Resumo da execução em lote
    """
    service = get_pipeline_service()
    results = []
    successful = 0
    failed = 0
    
    for unit_request in request.units:
        result = service.execute(
            region=unit_request.region,
            unit=unit_request.unit,
            month=unit_request.month,
            dry_run=unit_request.dry_run,
            send_email=unit_request.send_email,
            visible_columns=unit_request.visible_columns,
            copy_overrides=unit_request.copy_overrides,
            sender_email=unit_request.sender_email,
            sender_name=unit_request.sender_name,
            reply_to=unit_request.reply_to,
            cc_emails=unit_request.cc_emails,
            mandatory_cc=unit_request.mandatory_cc,
            use_existing_html=unit_request.use_existing_html,
        )
        
        preview_url = None
        if result.html_path:
            from pathlib import Path
            filename = Path(result.html_path).name
            preview_url = f"/api/preview/file/{filename}"
        
        results.append(ExecuteResponse(
            success=result.success,
            unit=result.unit,
            region=result.region,
            month=result.month,
            html_path=result.html_path,
            preview_url=preview_url,
            rows_count=result.rows_count,
            emails_found=result.emails_found,
            emails_sent_to=result.emails_sent_to,
            summary=result.summary,
            error=result.error,
        ))
        
        if result.success:
            successful += 1
        else:
            failed += 1
    
    return BatchExecuteResponse(
        total=len(request.units),
        successful=successful,
        failed=failed,
        results=results,
    )


@router.get("/metadata/regions", response_model=AvailableRegionsResponse)
def get_available_regions():
    """
    Retorna lista de regiões disponíveis.
    
    Baseado nas planilhas existentes em planilhas/.
    """
    service = get_pipeline_service()
    regions = service.list_available_regions()
    return AvailableRegionsResponse(regions=regions)


@router.get("/metadata/{region}", response_model=RegionMetadataResponse)
def get_region_metadata(region: str):
    """
    Retorna metadados de uma região (unidades e meses disponíveis).
    
    Útil para popular dropdowns no frontend.
    
    Args:
        region: Código da região (RJ, SP1, NNE, SP2, SP3)
    
    Returns:
        Unidades e meses encontrados na planilha
    """
    service = get_pipeline_service()
    
    units = service.list_available_units(region)
    months = service.list_available_months(region)
    
    if not units:
        logger.warning(f"Nenhuma unidade encontrada para região {region}")
    
    return RegionMetadataResponse(
        region=region,
        units=units,
        months=months,
    )


# ============================================================================
# ROTAS COM PARÂMETROS DINÂMICOS (DEVEM VIR POR ÚLTIMO)
# ============================================================================

@router.post("/job/{job_id}", response_model=ProcessResponse)
def process_job(
    job_id: int,
    request: ProcessRequest,
    db: Session = Depends(get_db)
):
    """
    Processa um job de planilha.
    
    Este endpoint:
    1. Valida que o job existe
    2. Extrai dados da planilha para a região/unidade/mês especificados
    3. Gera o relatório HTML
    4. Salva o resultado e atualiza o status do job
    
    Args:
        job_id: ID do job criado pelo upload
        request: Parâmetros de processamento (região, unidade, mês)
    
    Returns:
        Status do processamento e resultado
    """
    processor = JobProcessor(db)
    
    # Verifica se job existe
    job = processor.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
    
    try:
        result = processor.process_job(
            job_id=job_id,
            region=request.region,
            unit=request.unit,
            month=request.month,
            dry_run=request.dry_run
        )
        
        return ProcessResponse(
            job_id=job_id,
            status="completed",
            message=f"Processamento concluído: {result['row_count']} linhas processadas",
            result=result
        )
        
    except JobProcessorError as e:
        logger.warning(f"Erro no processamento do job {job_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Erro inesperado no job {job_id}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/job/{job_id}/metadata", response_model=MetadataResponse)
def get_job_metadata(
    job_id: int,
    region: str,
    db: Session = Depends(get_db)
):
    """
    Extrai metadados de um arquivo de job (unidades, meses disponíveis).
    
    Útil para popular dropdowns no frontend antes do processamento.
    
    Args:
        job_id: ID do job
        region: Código da região para extrair metadados
    
    Returns:
        Metadados do arquivo (unidades, meses, colunas)
    """
    processor = JobProcessor(db)
    
    job = processor.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
    
    from pathlib import Path
    file_path = Path(job.file_url)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo do job não encontrado")
    
    try:
        metadata = processor.extract_metadata_from_file(file_path, region)
        
        return MetadataResponse(
            job_id=job_id,
            sheet_name=metadata["sheet_name"],
            units=metadata["units"],
            months=metadata["months"],
            row_count=metadata["row_count"],
            columns=metadata["columns"]
        )
        
    except JobProcessorError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Erro ao extrair metadados do job {job_id}")
        raise HTTPException(status_code=500, detail=f"Erro ao ler arquivo: {str(e)}")


@router.get("/job/{job_id}/result")
def get_job_result(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Retorna o HTML gerado pelo processamento do job.
    
    Args:
        job_id: ID do job processado
    
    Returns:
        Arquivo HTML do relatório
    """
    processor = JobProcessor(db)
    
    job = processor.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
    
    if job.status != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Job ainda não foi processado (status: {job.status})"
        )
    
    result = processor.get_job_result_file(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Arquivo de resultado não encontrado")
    
    file_path, filename = result
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="text/html"
    )


@router.get("/job/{job_id}/result/preview", response_class=HTMLResponse)
def preview_job_result(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Retorna o HTML para preview no navegador (sem download).
    
    Args:
        job_id: ID do job processado
    
    Returns:
        HTML renderizado
    """
    processor = JobProcessor(db)
    
    job = processor.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")
    
    if job.status != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Job ainda não foi processado (status: {job.status})"
        )
    
    result = processor.get_job_result_file(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Arquivo de resultado não encontrado")
    
    file_path, _ = result
    
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    return HTMLResponse(content=html_content)

