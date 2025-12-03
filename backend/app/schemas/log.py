from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class LogBase(BaseModel):
    unit_name: str
    month_ref: str
    subject: str
    status: str
    recipient_list: str
    region: Optional[str] = None
    is_dry_run: bool = False

class LogCreate(LogBase):
    job_id: Optional[int] = None
    total_value: Optional[float] = None
    row_count: Optional[int] = None
    error_message: Optional[str] = None

class LogResponse(LogBase):
    id: int
    job_id: Optional[int] = None
    total_value: Optional[float] = None
    row_count: Optional[int] = None
    error_message: Optional[str] = None
    sent_at: datetime
    provider: Optional[str] = None

    class Config:
        from_attributes = True


class LogListResponse(BaseModel):
    """Resposta paginada de logs com metadados"""
    items: List[LogResponse]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True
