from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class JobBase(BaseModel):
    filename: str
    region: Optional[str] = None
    month_ref: Optional[str] = None

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    status: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class JobResponse(JobBase):
    id: int
    status: str
    file_url: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
