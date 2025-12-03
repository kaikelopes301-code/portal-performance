"""
Testes robustos para o router de upload.

Testa:
- Upload de arquivo único
- Upload de múltiplos arquivos (batch)
- Validação de extensões
- Validação de regiões
- Limites de arquivos
"""

import pytest
from fastapi.testclient import TestClient
from io import BytesIO
from unittest.mock import patch, MagicMock


class TestUploadSingle:
    """Testes para upload de arquivo único."""
    
    def test_upload_valid_xlsx(self, client: TestClient):
        """Deve aceitar arquivo .xlsx válido."""
        # Cria um arquivo Excel simulado
        file_content = BytesIO(b"PK\x03\x04" + b"\x00" * 100)  # Simula zip/xlsx
        file_content.name = "test_medicao.xlsx"
        
        response = client.post(
            "/api/upload/",
            files={"file": ("test_medicao.xlsx", file_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        
        # Debug: mostra erro se houver
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["filename"] == "test_medicao.xlsx"
        assert data["status"] == "pending"
    
    def test_upload_with_region(self, client: TestClient):
        """Deve aceitar upload com região especificada."""
        file_content = BytesIO(b"PK\x03\x04" + b"\x00" * 100)
        
        response = client.post(
            "/api/upload/",
            files={"file": ("medicao_rj.xlsx", file_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"region": "RJ"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["region"] == "RJ"
    
    def test_upload_invalid_extension_txt(self, client: TestClient):
        """Deve rejeitar arquivo .txt."""
        file_content = BytesIO(b"texto qualquer")
        
        response = client.post(
            "/api/upload/",
            files={"file": ("arquivo.txt", file_content, "text/plain")}
        )
        
        assert response.status_code == 400
        assert "Excel" in response.json()["detail"]
    
    def test_upload_invalid_extension_csv(self, client: TestClient):
        """Deve rejeitar arquivo .csv."""
        file_content = BytesIO(b"col1,col2\nval1,val2")
        
        response = client.post(
            "/api/upload/",
            files={"file": ("dados.csv", file_content, "text/csv")}
        )
        
        assert response.status_code == 400
    
    def test_upload_invalid_region(self, client: TestClient):
        """Deve rejeitar região inválida."""
        file_content = BytesIO(b"PK\x03\x04" + b"\x00" * 100)
        
        response = client.post(
            "/api/upload/",
            files={"file": ("test.xlsx", file_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"region": "INVALID_REGION"}
        )
        
        assert response.status_code == 400
        assert "Região inválida" in response.json()["detail"]
    
    def test_upload_all_valid_regions(self, client: TestClient):
        """Deve aceitar todas as regiões válidas."""
        valid_regions = ["RJ", "SP1", "SP2", "SP3", "NNE"]
        
        for region in valid_regions:
            file_content = BytesIO(b"PK\x03\x04" + b"\x00" * 100)
            response = client.post(
                "/api/upload/",
                files={"file": (f"test_{region}.xlsx", file_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                data={"region": region}
            )
            assert response.status_code == 200, f"Falha para região {region}"
            assert response.json()["region"] == region


class TestUploadBatch:
    """Testes para upload de múltiplos arquivos."""
    
    def test_batch_upload_two_files(self, client: TestClient):
        """Deve aceitar upload de 2 arquivos."""
        files = [
            ("files", ("file1.xlsx", BytesIO(b"PK\x03\x04" + b"\x00" * 100), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
            ("files", ("file2.xlsx", BytesIO(b"PK\x03\x04" + b"\x00" * 100), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
        ]
        
        response = client.post(
            "/api/upload/batch",
            files=files,
            data={"regions": "RJ,SP1"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["region"] == "RJ"
        assert data[1]["region"] == "SP1"
    
    def test_batch_upload_five_files(self, client: TestClient):
        """Deve aceitar upload de até 5 arquivos."""
        files = [
            ("files", (f"file{i}.xlsx", BytesIO(b"PK\x03\x04" + b"\x00" * 100), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))
            for i in range(5)
        ]
        
        response = client.post(
            "/api/upload/batch",
            files=files,
            data={"regions": "RJ,SP1,SP2,SP3,NNE"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
    
    def test_batch_upload_exceeds_limit(self, client: TestClient):
        """Deve rejeitar mais de 5 arquivos."""
        files = [
            ("files", (f"file{i}.xlsx", BytesIO(b"PK\x03\x04" + b"\x00" * 100), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))
            for i in range(6)
        ]
        
        response = client.post(
            "/api/upload/batch",
            files=files
        )
        
        assert response.status_code == 400
        assert "5 arquivos" in response.json()["detail"]
    
    def test_batch_upload_empty(self, client: TestClient):
        """Deve rejeitar upload sem arquivos."""
        response = client.post(
            "/api/upload/batch",
            files=[]
        )
        
        # FastAPI retorna 422 para campo obrigatório faltando
        assert response.status_code in [400, 422]
    
    def test_batch_upload_with_invalid_file(self, client: TestClient):
        """Deve rejeitar se algum arquivo for inválido."""
        files = [
            ("files", ("valid.xlsx", BytesIO(b"PK\x03\x04" + b"\x00" * 100), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
            ("files", ("invalid.txt", BytesIO(b"texto"), "text/plain")),
        ]
        
        response = client.post(
            "/api/upload/batch",
            files=files
        )
        
        assert response.status_code == 400
        assert "Excel" in response.json()["detail"]
    
    def test_batch_upload_without_regions(self, client: TestClient):
        """Deve aceitar upload sem regiões especificadas."""
        files = [
            ("files", ("file1.xlsx", BytesIO(b"PK\x03\x04" + b"\x00" * 100), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
            ("files", ("file2.xlsx", BytesIO(b"PK\x03\x04" + b"\x00" * 100), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
        ]
        
        response = client.post(
            "/api/upload/batch",
            files=files
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(job["region"] is None for job in data)


class TestUploadRegions:
    """Testes para o endpoint de listagem de regiões."""
    
    def test_list_regions(self, client: TestClient):
        """Deve retornar lista de regiões válidas."""
        response = client.get("/api/upload/regions")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "regions" in data
        assert "description" in data
        assert set(data["regions"]) == {"RJ", "SP1", "SP2", "SP3", "NNE"}
        assert len(data["description"]) == 5
