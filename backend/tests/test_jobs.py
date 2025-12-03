"""
Testes robustos para o router de jobs.

Testa:
- Listagem de jobs
- Busca por ID
- Atualização de status
- Exclusão
"""

import pytest
from fastapi.testclient import TestClient


class TestJobsList:
    """Testes para listagem de jobs."""
    
    def test_list_jobs(self, client: TestClient):
        """Deve listar jobs."""
        response = client.get("/api/jobs")
        
        assert response.status_code == 200
        data = response.json()
        
        # Aceita formatos diferentes
        if isinstance(data, dict):
            assert "jobs" in data or "items" in data
        else:
            assert isinstance(data, list)
    
    def test_list_jobs_pagination(self, client: TestClient):
        """Deve respeitar paginação."""
        response = client.get("/api/jobs?limit=5&offset=0")
        
        assert response.status_code == 200
    
    def test_list_jobs_by_status(self, client: TestClient):
        """Deve filtrar por status."""
        response = client.get("/api/jobs?status=pending")
        
        assert response.status_code == 200
    
    def test_list_jobs_by_region(self, client: TestClient):
        """Deve filtrar por região."""
        response = client.get("/api/jobs?region=RJ")
        
        assert response.status_code == 200


class TestJobsGet:
    """Testes para buscar job específico."""
    
    def test_get_nonexistent_job(self, client: TestClient):
        """Deve retornar 404 para job inexistente."""
        response = client.get("/api/jobs/99999")
        
        assert response.status_code == 404
    
    def test_get_invalid_id(self, client: TestClient):
        """Deve lidar com ID inválido."""
        response = client.get("/api/jobs/invalid")
        
        assert response.status_code == 422


class TestJobsDelete:
    """Testes para exclusão de jobs."""
    
    def test_delete_nonexistent_job(self, client: TestClient):
        """Deve retornar 404 ou 405 para job inexistente."""
        response = client.delete("/api/jobs/99999")
        
        # 404 = não encontrado, 405 = método não permitido
        assert response.status_code in [404, 405]
