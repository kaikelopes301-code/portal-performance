# schedule.py — Schemas para agendamentos

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ScheduleFrequency(str, Enum):
    """Frequência do agendamento."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ONCE = "once"


class ScheduleStatus(str, Enum):
    """Status do agendamento."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ScheduleBase(BaseModel):
    """Base para agendamento."""
    name: str = Field(..., description="Nome do agendamento")
    description: Optional[str] = Field(None, description="Descrição")
    region: str = Field(..., description="Código da região (SP1, RJ, etc)")
    units: List[str] = Field(..., description="Lista de unidades a processar")
    frequency: ScheduleFrequency = Field(..., description="Frequência de execução")
    day_of_month: Optional[int] = Field(None, ge=1, le=28, description="Dia do mês para execução (1-28)")
    day_of_week: Optional[int] = Field(None, ge=0, le=6, description="Dia da semana (0=Segunda, 6=Domingo)")
    time: str = Field("09:00", description="Horário de execução (HH:MM)")
    auto_send_email: bool = Field(False, description="Enviar email automaticamente após processamento")


class ScheduleCreate(ScheduleBase):
    """Schema para criação de agendamento."""
    pass


class ScheduleUpdate(BaseModel):
    """Schema para atualização de agendamento."""
    name: Optional[str] = None
    description: Optional[str] = None
    region: Optional[str] = None
    units: Optional[List[str]] = None
    frequency: Optional[ScheduleFrequency] = None
    day_of_month: Optional[int] = Field(None, ge=1, le=28)
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    time: Optional[str] = None
    auto_send_email: Optional[bool] = None
    status: Optional[ScheduleStatus] = None


class ScheduleResponse(ScheduleBase):
    """Schema de resposta de agendamento."""
    id: str
    status: ScheduleStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    
    class Config:
        from_attributes = True


class ScheduleExecution(BaseModel):
    """Registro de execução de agendamento."""
    id: str
    schedule_id: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    units_processed: int = 0
    errors: List[str] = Field(default_factory=list)


class ScheduleListResponse(BaseModel):
    """Resposta da listagem de agendamentos."""
    schedules: List[ScheduleResponse]
    count: int
