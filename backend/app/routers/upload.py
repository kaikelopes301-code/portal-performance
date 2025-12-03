from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.job import ProcessingJob
from app.schemas.job import JobResponse
import shutil
import os
from datetime import datetime
from pathlib import Path

router = APIRouter(prefix="/api/upload", tags=["upload"])

# Diretório de uploads (caminho absoluto)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # backpperformance/
UPLOAD_DIR = BASE_DIR / "backend" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Regiões válidas
VALID_REGIONS = ["RJ", "SP1", "SP2", "SP3", "NNE"]


def delete_existing_region_files(db: Session, region: str):
    """
    Remove todos os arquivos e jobs existentes de uma região específica.
    Mantém apenas 1 planilha por região.
    """
    if not region:
        return
    
    # Busca jobs existentes da região
    existing_jobs = db.query(ProcessingJob).filter(
        ProcessingJob.region == region.upper()
    ).all()
    
    for job in existing_jobs:
        # Remove arquivo físico se existir
        if job.file_url:
            file_path = Path(job.file_url)
            if file_path.exists():
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Aviso: Não foi possível remover arquivo {file_path}: {e}")
        
        # Remove job do banco
        db.delete(job)
    
    db.commit()


@router.post("/", response_model=JobResponse)
async def upload_file(
    file: UploadFile = File(...), 
    region: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Upload de arquivo de planilha Excel.
    
    O arquivo é salvo localmente e um job é criado para rastrear o processamento.
    Opcionalmente, especifique a região (RJ, SP1, SP2, SP3, NNE).
    """
    # Valida extensão
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400, 
            detail="Apenas arquivos Excel (.xlsx, .xls) são aceitos"
        )
    
    # Valida região se fornecida
    if region and region.upper() not in VALID_REGIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Região inválida. Regiões válidas: {', '.join(VALID_REGIONS)}"
        )
    
    # Remove arquivos anteriores da mesma região (apenas 1 por região)
    if region:
        delete_existing_region_files(db, region)
    
    # 1. Salvar arquivo localmente
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = "".join(c if c.isalnum() or c in ('_', '-', '.') else '_' for c in file.filename)
    filename = f"{timestamp}_{safe_filename}"
    file_path = UPLOAD_DIR / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 2. Criar Job no Banco
    job = ProcessingJob(
        filename=file.filename,
        file_url=str(file_path),  # Salva como string para compatibilidade
        status="pending",
        region=region.upper() if region else None
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return job


@router.post("/batch", response_model=List[JobResponse])
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    regions: Optional[str] = Form(None),  # Formato: "RJ,SP1,SP2" ou vazio
    db: Session = Depends(get_db)
):
    """
    Upload de múltiplas planilhas Excel (até 5 por vez).
    
    Cada arquivo pode ser associado a uma região específica.
    O parâmetro `regions` é uma string separada por vírgulas, correspondendo
    à ordem dos arquivos enviados.
    
    Exemplo: files=[plan_rj.xlsx, plan_sp1.xlsx], regions="RJ,SP1"
    """
    # Limita a 5 arquivos
    if len(files) > 5:
        raise HTTPException(
            status_code=400,
            detail="Máximo de 5 arquivos por upload"
        )
    
    if len(files) == 0:
        raise HTTPException(
            status_code=400,
            detail="Nenhum arquivo enviado"
        )
    
    # Parse das regiões
    region_list = []
    if regions:
        region_list = [r.strip().upper() for r in regions.split(",")]
        for r in region_list:
            if r and r not in VALID_REGIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Região inválida: {r}. Regiões válidas: {', '.join(VALID_REGIONS)}"
                )
    
    jobs = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for i, file in enumerate(files):
        # Valida extensão
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400, 
                detail=f"Arquivo '{file.filename}' não é um arquivo Excel válido"
            )
        
        # Determina região para este arquivo
        file_region = None
        if i < len(region_list) and region_list[i]:
            file_region = region_list[i]
            # Remove arquivos anteriores da mesma região
            delete_existing_region_files(db, file_region)
        
        # Salvar arquivo
        safe_filename = "".join(c if c.isalnum() or c in ('_', '-', '.') else '_' for c in file.filename)
        filename = f"{timestamp}_{i+1}_{safe_filename}"
        file_path = UPLOAD_DIR / filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Criar Job
        job = ProcessingJob(
            filename=file.filename,
            file_url=str(file_path),
            status="pending",
            region=file_region
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        jobs.append(job)
    
    return jobs


@router.get("/regions")
async def list_valid_regions():
    """
    Lista as regiões válidas para upload de planilhas.
    """
    return {
        "regions": VALID_REGIONS,
        "description": {
            "RJ": "Rio de Janeiro",
            "SP1": "São Paulo - Região 1 (Curitiba, Goiânia, Londrina, Maringá, etc.)",
            "SP2": "São Paulo - Região 2 (Bauru, Franca, Campo Limpo, Dom Pedro, etc.)",
            "SP3": "São Paulo - Região 3 (BH, Uberlândia, Mooca, Cuiabá, etc.)",
            "NNE": "Norte e Nordeste (Manaus, Belém, Bahia, Parangaba, etc.)"
        }
    }
