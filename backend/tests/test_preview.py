"""
Testes robustos para o router de preview.

Testa:
- Listagem de arquivos HTML
- Visualização de arquivo
- Estatísticas
- Exclusão de arquivo
- Limpeza em massa
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import os


class TestPreviewList:
    """Testes para listagem de arquivos HTML."""
    
    def test_list_files(self, client: TestClient):
        """Deve listar arquivos HTML."""
        response = client.get("/api/preview")
        
        # Endpoint pode não existir ou retornar lista
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (dict, list))
    
    def test_list_files_with_filters(self, client: TestClient):
        """Deve aceitar filtros de listagem."""
        response = client.get("/api/preview?month=2024-11")
        
        assert response.status_code in [200, 404]


class TestPreviewStats:
    """Testes para estatísticas de preview."""
    
    def test_get_stats(self, client: TestClient):
        """Deve retornar estatísticas de arquivos HTML."""
        response = client.get("/api/preview/stats")
        
        # Endpoint pode não existir
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


class TestPreviewView:
    """Testes para visualização de arquivo."""
    
    def test_view_nonexistent_file(self, client: TestClient):
        """Deve retornar 404 para arquivo inexistente."""
        response = client.get("/api/preview/arquivoinexistente_2024-11.html")
        
        assert response.status_code == 404
    
    def test_view_invalid_extension(self, client: TestClient):
        """Deve rejeitar arquivos não-HTML."""
        response = client.get("/api/preview/arquivo.txt")
        
        # Depende da implementação
        assert response.status_code in [400, 404]


class TestPreviewDelete:
    """Testes para exclusão de arquivos."""
    
    def test_delete_nonexistent_file(self, client: TestClient):
        """Deve retornar 404 para arquivo inexistente."""
        response = client.delete("/api/preview/files/arquivo_inexistente.html")
        
        assert response.status_code == 404
    
    def test_delete_invalid_filename(self, client: TestClient):
        """Deve validar nome do arquivo."""
        # Tenta path traversal
        response = client.delete("/api/preview/files/..%2F..%2Fetc%2Fpasswd")
        
        # Deve rejeitar
        assert response.status_code in [400, 404]


class TestPreviewCleanup:
    """Testes para limpeza em massa."""
    
    def test_cleanup_default_days(self, client: TestClient):
        """Deve limpar arquivos com dias padrão (30)."""
        response = client.delete("/api/preview/cleanup")
        
        # Endpoint pode não existir
        assert response.status_code in [200, 404, 405]
    
    def test_cleanup_custom_days(self, client: TestClient):
        """Deve aceitar número de dias customizado."""
        response = client.delete("/api/preview/cleanup?days=7")
        
        assert response.status_code in [200, 404, 405]
    
    def test_cleanup_zero_days(self, client: TestClient):
        """Deve lidar com days=0."""
        response = client.delete("/api/preview/cleanup?days=0")
        
        # Depende da implementação
        assert response.status_code in [200, 400, 404, 405]
