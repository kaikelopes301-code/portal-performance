# schedules.py — Router para gerenciamento de agendamentos

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging

from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    ScheduleListResponse,
    ScheduleExecution
)
from app.services.schedule_service import ScheduleService, ScheduleServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/schedules", tags=["schedules"])

# Instância do serviço (singleton)
_schedule_service = ScheduleService()


@router.get("/", response_model=ScheduleListResponse)
def list_schedules():
    """
    Lista todos os agendamentos.
    
    Inclui informações sobre próxima execução e contagem de execuções.
    """
    try:
        schedules = _schedule_service.list_schedules()
        return {
            "schedules": schedules,
            "count": len(schedules)
        }
    except ScheduleServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending")
def get_pending_schedules():
    """
    Retorna agendamentos que devem ser executados agora.
    
    Usado pelo worker para verificar o que precisa rodar.
    """
    try:
        pending = _schedule_service.get_pending_schedules()
        return {
            "pending": pending,
            "count": len(pending)
        }
    except ScheduleServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions")
def get_all_executions(
    schedule_id: Optional[str] = Query(None, description="Filtrar por agendamento"),
    limit: int = Query(20, ge=1, le=100, description="Limite de resultados")
):
    """
    Retorna histórico de execuções de agendamentos.
    """
    try:
        executions = _schedule_service.get_executions(
            schedule_id=schedule_id,
            limit=limit
        )
        return {
            "executions": executions,
            "count": len(executions)
        }
    except ScheduleServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{schedule_id}")
def get_schedule(schedule_id: str):
    """Retorna um agendamento específico."""
    try:
        schedule = _schedule_service.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail=f"Agendamento '{schedule_id}' não encontrado")
        return schedule
    except ScheduleServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=dict)
def create_schedule(request: ScheduleCreate):
    """
    Cria um novo agendamento.
    
    Campos obrigatórios variam de acordo com a frequência:
    - weekly: requer day_of_week (0-6)
    - monthly: requer day_of_month (1-28)
    """
    try:
        schedule = _schedule_service.create_schedule(
            name=request.name,
            description=request.description,
            region=request.region,
            units=request.units,
            frequency=request.frequency.value,
            day_of_month=request.day_of_month,
            day_of_week=request.day_of_week,
            time=request.time,
            auto_send_email=request.auto_send_email
        )
        return schedule
    except ScheduleServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{schedule_id}")
def update_schedule(schedule_id: str, request: ScheduleUpdate):
    """
    Atualiza um agendamento existente.
    
    Aceita atualizações parciais.
    """
    try:
        update_data = request.model_dump(exclude_none=True)
        
        # Converte enums para strings
        if "frequency" in update_data and update_data["frequency"]:
            update_data["frequency"] = update_data["frequency"].value
        if "status" in update_data and update_data["status"]:
            update_data["status"] = update_data["status"].value
        
        schedule = _schedule_service.update_schedule(schedule_id, **update_data)
        return schedule
    except ScheduleServiceError as e:
        if "não encontrado" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: str):
    """Remove um agendamento."""
    try:
        deleted = _schedule_service.delete_schedule(schedule_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Agendamento '{schedule_id}' não encontrado")
        return {"message": f"Agendamento '{schedule_id}' removido com sucesso"}
    except ScheduleServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{schedule_id}/pause")
def pause_schedule(schedule_id: str):
    """Pausa um agendamento."""
    try:
        schedule = _schedule_service.pause_schedule(schedule_id)
        return schedule
    except ScheduleServiceError as e:
        if "não encontrado" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{schedule_id}/resume")
def resume_schedule(schedule_id: str):
    """Retoma um agendamento pausado."""
    try:
        schedule = _schedule_service.resume_schedule(schedule_id)
        return schedule
    except ScheduleServiceError as e:
        if "não encontrado" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{schedule_id}/executions")
def get_schedule_executions(
    schedule_id: str,
    limit: int = Query(20, ge=1, le=100)
):
    """Retorna histórico de execuções de um agendamento específico."""
    try:
        # Verifica se agendamento existe
        schedule = _schedule_service.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail=f"Agendamento '{schedule_id}' não encontrado")
        
        executions = _schedule_service.get_executions(
            schedule_id=schedule_id,
            limit=limit
        )
        return {
            "schedule_id": schedule_id,
            "executions": executions,
            "count": len(executions)
        }
    except ScheduleServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{schedule_id}/run")
def run_schedule_now(schedule_id: str):
    """
    Executa um agendamento imediatamente (manual trigger).
    
    Nota: Esta rota apenas registra a intenção de execução.
    O processamento real deve ser feito pelo worker/job processor.
    """
    try:
        schedule = _schedule_service.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail=f"Agendamento '{schedule_id}' não encontrado")
        
        # Por agora, apenas retorna informações para execução manual
        # Em produção, isso enfileiraria uma task no Celery
        return {
            "message": "Execução manual solicitada",
            "schedule": schedule,
            "action_required": "Execute o processamento usando POST /api/process/{job_id} para cada unidade",
            "units_to_process": schedule.get("units", []),
            "region": schedule.get("region")
        }
    except ScheduleServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
