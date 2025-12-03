from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models.log import EmailLog
from app.schemas.log import LogResponse, LogListResponse

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("/", response_model=LogListResponse)
def list_logs(
    skip: int = 0, 
    limit: int = 50,
    unit_name: Optional[str] = Query(None, description="Filtrar por nome da unidade"),
    status: Optional[str] = Query(None, description="Filtrar por status (sent, failed, queued)"),
    month_ref: Optional[str] = Query(None, description="Filtrar por mês de referência (ex: 2025-11)"),
    date_from: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    is_dry_run: Optional[bool] = Query(None, description="Filtrar por tipo: True=teste, False=envio real"),
    region: Optional[str] = Query(None, description="Filtrar por região (RJ, SP1, SP2, SP3, NNE)"),
    db: Session = Depends(get_db)
):
    """
    Lista logs de envio de email com filtros opcionais.
    """
    query = db.query(EmailLog)
    
    # Aplicar filtros
    filters = []
    
    if unit_name:
        filters.append(EmailLog.unit_name.ilike(f"%{unit_name}%"))
    
    if status:
        filters.append(EmailLog.status == status)
    
    if month_ref:
        filters.append(EmailLog.month_ref == month_ref)
    
    if is_dry_run is not None:
        filters.append(EmailLog.is_dry_run == is_dry_run)
    
    if region:
        filters.append(EmailLog.region == region)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d")
            filters.append(EmailLog.sent_at >= from_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data inválido para date_from. Use YYYY-MM-DD")
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)  # Inclui o dia inteiro
            filters.append(EmailLog.sent_at < to_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data inválido para date_to. Use YYYY-MM-DD")
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Contar total para paginação
    total = query.count()
    
    # Aplicar ordenação e paginação
    logs = query.order_by(EmailLog.sent_at.desc()).offset(skip).limit(limit).all()
    
    return LogListResponse(
        items=logs,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/stats")
def get_log_stats(db: Session = Depends(get_db)):
    """
    Retorna estatísticas dos logs.
    """
    total = db.query(EmailLog).count()
    sent = db.query(EmailLog).filter(EmailLog.status == "sent").count()
    failed = db.query(EmailLog).filter(EmailLog.status == "failed").count()
    
    # Dry runs vs envios reais
    dry_runs = db.query(EmailLog).filter(EmailLog.is_dry_run == True).count()
    real_sends = db.query(EmailLog).filter(EmailLog.is_dry_run == False).count()
    
    # Logs nos últimos 7 dias
    week_ago = datetime.now() - timedelta(days=7)
    recent = db.query(EmailLog).filter(EmailLog.sent_at >= week_ago).count()
    
    # Unidades únicas
    unique_units = db.query(EmailLog.unit_name).distinct().count()
    
    return {
        "total": total,
        "sent": sent,
        "failed": failed,
        "dry_runs": dry_runs,
        "real_sends": real_sends,
        "recent_7_days": recent,
        "unique_units": unique_units
    }


@router.delete("/cleanup")
def cleanup_old_logs(
    days: int = Query(90, description="Remover logs mais antigos que X dias"),
    db: Session = Depends(get_db)
):
    """
    Remove logs mais antigos que o período especificado.
    Por padrão, remove logs com mais de 90 dias.
    """
    if days < 7:
        raise HTTPException(status_code=400, detail="Período mínimo de retenção é 7 dias")
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Contar antes de deletar
    count = db.query(EmailLog).filter(EmailLog.sent_at < cutoff_date).count()
    
    # Deletar logs antigos
    db.query(EmailLog).filter(EmailLog.sent_at < cutoff_date).delete(synchronize_session=False)
    db.commit()
    
    return {
        "message": f"Removidos {count} logs com mais de {days} dias",
        "deleted_count": count,
        "cutoff_date": cutoff_date.isoformat()
    }


@router.delete("/{log_id}")
def delete_log(log_id: int, db: Session = Depends(get_db)):
    """
    Remove um log específico por ID.
    """
    log = db.query(EmailLog).filter(EmailLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log não encontrado")
    
    db.delete(log)
    db.commit()
    
    return {"message": "Log removido com sucesso", "id": log_id}

