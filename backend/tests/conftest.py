# conftest.py - Fixtures compartilhadas para testes

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from io import BytesIO
import tempfile
import os
from contextlib import contextmanager


# ============================================================================
# CONFIGURAÇÃO DE TESTE
# ============================================================================

# Desabilita o scheduler durante testes
os.environ["TESTING"] = "true"

# Cria banco SQLite em memória como engine de teste global
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def client():
    """Cliente de teste para a API FastAPI."""
    from app.database import Base, get_db
    from app.main import app
    
    # Cria as tabelas no banco de teste
    Base.metadata.create_all(bind=TEST_ENGINE)
    
    # Cria session factory para o banco de teste
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    # Faz override da dependência
    app.dependency_overrides[get_db] = override_get_db
    
    # Cria cliente
    with TestClient(app) as test_client:
        yield test_client
    
    # Limpa
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def sample_job_data():
    """Dados de exemplo para criação de job."""
    return {
        "filename": "test_medicao.xlsx",
        "status": "pending",
        "region": "RJ"
    }


@pytest.fixture
def sample_excel_file():
    """Arquivo Excel simulado para testes de upload."""
    # Cria um arquivo que simula um XLSX (começa com PK como ZIP)
    content = BytesIO(b"PK\x03\x04" + b"\x00" * 100)
    content.name = "test_medicao.xlsx"
    return content


@pytest.fixture
def sample_excel_files():
    """Múltiplos arquivos Excel para testes de batch upload."""
    files = []
    regions = ["RJ", "SP1", "SP2", "SP3", "NNE"]
    
    for i, region in enumerate(regions):
        content = BytesIO(b"PK\x03\x04" + b"\x00" * 100)
        files.append({
            "file": content,
            "filename": f"medicao_{region}.xlsx",
            "region": region
        })
    
    return files


@pytest.fixture
def sample_schedule_data():
    """Dados de exemplo para criação de agendamento."""
    return {
        "name": "Agendamento Teste",
        "description": "Agendamento para testes",
        "region": "RJ",
        "units": ["Shopping Teste 1", "Shopping Teste 2"],
        "frequency": "monthly",
        "day_of_month": 15,
        "time": "09:00",
        "auto_send_email": False
    }


@pytest.fixture
def sample_config_data():
    """Dados de exemplo para configuração."""
    return {
        "copy_texts": {
            "greeting": "Prezados(as),",
            "intro": "Segue medição para análise.",
            "observation": "Qualquer dúvida, entrar em contato.",
            "cta_label": "Ver Medição",
            "footer_signature": "Equipe Atlas"
        },
        "visible_columns": ["unidade", "valor", "data", "status"],
        "sender": {
            "name": "Atlas Inovações",
            "email": "medicao@atlasinovacoes.com"
        }
    }


@pytest.fixture
def sample_log_data():
    """Dados de exemplo para log de email."""
    return {
        "unit_name": "Shopping Teste",
        "recipient": "teste@example.com",
        "status": "success",
        "month_ref": "2024-11"
    }


@pytest.fixture
def valid_regions():
    """Lista de regiões válidas."""
    return ["RJ", "SP1", "SP2", "SP3", "NNE"]


@pytest.fixture
def temp_output_dir():
    """Diretório temporário para output de testes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# ============================================================================
# HELPERS
# ============================================================================

def create_mock_xlsx_content():
    """Cria conteúdo de arquivo XLSX simulado."""
    return BytesIO(b"PK\x03\x04" + b"\x00" * 100)


def create_upload_tuple(filename: str, region: str = None):
    """Cria tupla para upload de arquivo."""
    content = create_mock_xlsx_content()
    return ("files", (filename, content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))
