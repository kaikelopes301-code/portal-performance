from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Float
from sqlalchemy.sql import func
from app.database import Base

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_url = Column(String)  # Cloudinary URL ou path local
    status = Column(String, default="pending")  # pending, processing, completed, failed
    
    # Metadados do processamento
    region = Column(String, nullable=True)
    month_ref = Column(String, nullable=True)
    
    # Resultados (armazenados como JSON)
    result_summary = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
