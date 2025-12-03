from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean
from sqlalchemy.sql import func
from app.database import Base

class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Contexto
    job_id = Column(Integer, nullable=True, index=True)
    unit_name = Column(String, index=True)
    month_ref = Column(String)
    region = Column(String, nullable=True, index=True)  # RJ, SP1, SP2, SP3, NNE
    
    # Tipo de execução
    is_dry_run = Column(Boolean, default=False, index=True)  # True = teste, False = envio real
    
    # Detalhes do Envio
    recipient_list = Column(Text)  # Lista de emails separados por ;
    subject = Column(String)
    status = Column(String)  # sent, failed, queued, dry_run
    provider = Column(String, default="sendgrid")
    
    # Dados Financeiros (para histórico)
    total_value = Column(Float, nullable=True)
    row_count = Column(Integer, nullable=True)
    
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
