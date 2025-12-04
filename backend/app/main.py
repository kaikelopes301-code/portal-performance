from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pathlib import Path
import os
import logging

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# ============================================================================
# JOBS DE LIMPEZA PERIÓDICA
# ============================================================================

# Caminho para a pasta output_html
OUTPUT_HTML_PATH = Path(__file__).parent.parent.parent / "output_html"

# Configuração de retenção (dias)
HTML_RETENTION_DAYS = int(os.getenv("HTML_RETENTION_DAYS", "30"))
JOB_RETENTION_DAYS = int(os.getenv("JOB_RETENTION_DAYS", "90"))  # Histórico de jobs


async def cleanup_old_html_files():
    """
    Job para limpar arquivos HTML mais antigos que HTML_RETENTION_DAYS.
    Executado diariamente às 3h da manhã.
    """
    logger.info(f"[Scheduler] Iniciando limpeza de HTMLs (retenção: {HTML_RETENTION_DAYS} dias)")
    
    if not OUTPUT_HTML_PATH.exists():
        logger.info("[Scheduler] Pasta output_html não existe, pulando limpeza")
        return
    
    cutoff_time = datetime.now() - timedelta(days=HTML_RETENTION_DAYS)
    deleted_count = 0
    
    for file in OUTPUT_HTML_PATH.glob("*.html"):
        try:
            file_mtime = datetime.fromtimestamp(file.stat().st_mtime)
            if file_mtime < cutoff_time:
                file.unlink()
                deleted_count += 1
                logger.info(f"[Scheduler] Arquivo removido: {file.name}")
        except Exception as e:
            logger.error(f"[Scheduler] Erro ao remover {file.name}: {e}")
    
    logger.info(f"[Scheduler] Limpeza de HTMLs concluída. {deleted_count} arquivos removidos.")


async def cleanup_old_jobs():
    """
    Job para limpar histórico de jobs mais antigos que JOB_RETENTION_DAYS.
    Mantém o histórico de processamentos por um período configurável.
    Executado diariamente às 4h da manhã.
    """
    from app.database import SessionLocal
    from app.models.job import ProcessingJob
    
    logger.info(f"[Scheduler] Iniciando limpeza de jobs (retenção: {JOB_RETENTION_DAYS} dias)")
    
    cutoff_date = datetime.now() - timedelta(days=JOB_RETENTION_DAYS)
    
    try:
        db = SessionLocal()
        # Conta antes de deletar para logging
        count_before = db.query(ProcessingJob).filter(ProcessingJob.created_at < cutoff_date).count()
        
        if count_before > 0:
            deleted_count = db.query(ProcessingJob).filter(
                ProcessingJob.created_at < cutoff_date
            ).delete(synchronize_session=False)
            db.commit()
            logger.info(f"[Scheduler] Limpeza de jobs concluída. {deleted_count} registros removidos.")
        else:
            logger.info("[Scheduler] Nenhum job antigo para remover.")
        
        db.close()
    except Exception as e:
        logger.error(f"[Scheduler] Erro na limpeza de jobs: {e}")


# ============================================================================
# SCHEDULER SETUP (LIFESPAN)
# ============================================================================

# Verifica se está em modo de teste
TESTING = os.getenv("TESTING", "false").lower() == "true"

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.
    Inicia e para o scheduler de tarefas agendadas.
    """
    # Cria as tabelas do banco de dados automaticamente
    from app.database import engine, Base
    from app.models.job import ProcessingJob  # Importa o model para registrar na Base
    from app.models.log import EmailLog  # Importa o model de logs
    
    logger.info("[Lifespan] Criando tabelas do banco de dados...")
    Base.metadata.create_all(bind=engine)
    logger.info("[Lifespan] Tabelas criadas/verificadas com sucesso!")
    
    # Pula scheduler em modo de teste
    if TESTING:
        logger.info("[Lifespan] Modo de teste - scheduler desabilitado")
        yield
        return
    
    # Startup
    logger.info("[Lifespan] Configurando scheduler de limpeza periódica...")
    
    # Job de limpeza de HTMLs - todos os dias às 3h
    scheduler.add_job(
        cleanup_old_html_files,
        CronTrigger(hour=3, minute=0),
        id="cleanup_html",
        name="Limpeza de HTMLs antigos",
        replace_existing=True
    )
    
    # Job de limpeza de jobs - todos os dias às 4h
    scheduler.add_job(
        cleanup_old_jobs,
        CronTrigger(hour=4, minute=0),
        id="cleanup_jobs",
        name="Limpeza de jobs antigos",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("[Lifespan] Scheduler iniciado com sucesso!")
    
    yield  # Aplicação rodando
    
    # Shutdown
    logger.info("[Lifespan] Parando scheduler...")
    scheduler.shutdown()
    logger.info("[Lifespan] Scheduler parado.")


app = FastAPI(
    title="Portal Performance API",
    description="""
## API para processamento de planilhas e geração de relatórios de medição

### Autenticação
Para rotas protegidas, inclua o header `X-API-Key` com sua chave de API.
Alternativamente, use o query parameter `api_key`.

### Rotas Públicas
- `GET /` - Informações da API
- `GET /health` - Health check
- `GET /docs` - Documentação Swagger
- `GET /redoc` - Documentação ReDoc

### Módulos
- **Upload**: Envio de planilhas Excel
- **Jobs**: Gerenciamento de processamentos
- **Config**: Configurações do sistema
- **Templates**: Templates de email
- **Schedules**: Agendamentos automáticos

### Limpeza Automática (executada diariamente)
- **HTMLs**: Removidos após 30 dias (configurável via `HTML_RETENTION_DAYS`)
- **Jobs**: Removidos após 90 dias (configurável via `JOB_RETENTION_DAYS`)
    """,
    version="2.0.0",
    contact={
        "name": "Atlas Inovações",
        "email": "suporte@atlasinovacoes.com",
    },
    lifespan=lifespan,
)

# Handler para erros de validação (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error on {request.url}: {exc.errors()}")
    logger.error(f"Request body: {await request.body()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(await request.body())[:500]},
    )

# CORS - Permite todas as origens em desenvolvimento
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas em dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Sistema de Faturamento API v2.0"}

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}

from app.routers import upload, jobs, config, process, templates, schedules, preview, logs, auth

app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(jobs.router)
app.include_router(process.router)
app.include_router(config.router)
app.include_router(templates.router)
app.include_router(schedules.router)
app.include_router(preview.router)
app.include_router(logs.router)
