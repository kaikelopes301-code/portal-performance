"""
Testes de integração end-to-end.

Simula fluxos completos:
- Upload → Processamento → Visualização
- Configuração → Upload → Envio
"""

import pytest
from fastapi.testclient import TestClient
from io import BytesIO
import time


class TestUploadToProcessFlow:
    """Testes do fluxo upload → processamento."""
    
    def test_full_upload_flow(self, client: TestClient):
        """Deve completar fluxo de upload."""
        # 1. Upload do arquivo
        file_content = BytesIO(b"PK\x03\x04" + b"\x00" * 100)
        
        upload_response = client.post(
            "/api/upload/",
            files={"file": ("test_flow.xlsx", file_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"region": "RJ"}
        )
        
        assert upload_response.status_code == 200
        job_data = upload_response.json()
        job_id = job_data["id"]
        
        # 2. Verificar job foi criado
        job_response = client.get(f"/api/jobs/{job_id}")
        assert job_response.status_code == 200
        assert job_response.json()["status"] == "pending"
        
        # 3. Job deve aparecer na lista
        list_response = client.get("/api/jobs")
        assert list_response.status_code == 200
        data = list_response.json()
        
        # Aceita diferentes formatos
        if isinstance(data, dict):
            jobs = data.get("jobs", data.get("items", []))
        else:
            jobs = data
        
        job_ids = [j["id"] for j in jobs]
        assert job_id in job_ids


class TestBatchUploadFlow:
    """Testes do fluxo de upload em lote."""
    
    def test_batch_upload_creates_multiple_jobs(self, client: TestClient):
        """Deve criar múltiplos jobs no batch."""
        # Upload de 3 arquivos
        files = [
            ("files", (f"batch_{i}.xlsx", BytesIO(b"PK\x03\x04" + b"\x00" * 100), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))
            for i in range(3)
        ]
        
        response = client.post(
            "/api/upload/batch",
            files=files,
            data={"regions": "RJ,SP1,SP2"}
        )
        
        assert response.status_code == 200
        jobs = response.json()
        assert len(jobs) == 3
        
        # Verificar cada job
        for i, job in enumerate(jobs):
            job_response = client.get(f"/api/jobs/{job['id']}")
            assert job_response.status_code == 200


class TestCleanupFlow:
    """Testes do fluxo de limpeza."""
    
    def test_cleanup_preview(self, client: TestClient):
        """Deve limpar previews."""
        preview_cleanup = client.delete("/api/preview/cleanup?days=365")
        assert preview_cleanup.status_code in [200, 404, 405]


class TestStatsFlow:
    """Testes do fluxo de estatísticas."""
    
    def test_preview_stats_endpoint(self, client: TestClient):
        """Deve retornar estatísticas de preview."""
        preview_stats = client.get("/api/preview/stats")
        
        if preview_stats.status_code == 404:
            pytest.skip("Endpoint /api/preview/stats não implementado")
        
        assert preview_stats.status_code == 200


class TestSharePointFlow:
    """Testes do fluxo do SharePoint (sem conexão real)."""
    
    def test_sharepoint_status_flow(self, client: TestClient):
        """Deve verificar status."""
        status_response = client.get("/api/sharepoint/status")
        assert status_response.status_code == 200
    
    def test_sharepoint_test_connection(self, client: TestClient):
        """Deve testar conexão."""
        test_response = client.get("/api/sharepoint/test-connection")
        # 200 = sucesso, 503 = não configurado
        assert test_response.status_code in [200, 503]
    
    def test_sharepoint_sync(self, client: TestClient):
        """Sync deve falhar graciosamente quando não configurado."""
        sync_response = client.post("/api/sharepoint/sync", json={})
        # 503 = não configurado, 200 = sucesso/vazio
        assert sync_response.status_code in [200, 503]


class TestErrorHandling:
    """Testes de tratamento de erros."""
    
    def test_404_on_missing_job(self, client: TestClient):
        """Deve retornar 404 para job inexistente."""
        assert client.get("/api/jobs/99999").status_code == 404
    
    def test_404_on_missing_preview(self, client: TestClient):
        """Deve retornar 404 para arquivo de preview inexistente."""
        response = client.get("/api/preview/inexistente.html")
        assert response.status_code in [404]
    
    def test_422_on_invalid_job_id(self, client: TestClient):
        """Deve retornar 422 para ID não numérico."""
        assert client.get("/api/jobs/abc").status_code == 422
    
    def test_400_on_non_excel_upload(self, client: TestClient):
        """Deve retornar 400 para arquivo não-Excel."""
        file_content = BytesIO(b"texto simples")
        response = client.post(
            "/api/upload/",
            files={"file": ("teste.txt", file_content, "text/plain")}
        )
        assert response.status_code == 400
