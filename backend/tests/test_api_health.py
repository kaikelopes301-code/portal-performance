# test_api_health.py - Testes para endpoints básicos

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestHealthEndpoint:
    """Testes para o endpoint de health check."""

    def test_health_check_returns_ok(self):
        """Verifica se o health check retorna status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_root_endpoint(self):
        """Verifica se a raiz retorna informações da API."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "status" in data


class TestJobsEndpoint:
    """Testes para endpoints de jobs."""

    @pytest.mark.skip(reason="Requer inicialização do banco de dados")
    def test_list_jobs_empty(self):
        """Verifica listagem de jobs quando vazia."""
        response = client.get("/api/jobs/")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data or isinstance(data, list)

    @pytest.mark.skip(reason="Requer inicialização do banco de dados")
    def test_list_jobs_with_pagination(self):
        """Verifica paginação na listagem de jobs."""
        response = client.get("/api/jobs/?limit=5&offset=0")
        assert response.status_code == 200


class TestConfigEndpoint:
    """Testes para endpoints de configuração."""

    def test_get_config(self):
        """Verifica se retorna configuração completa."""
        response = client.get("/api/config/")
        assert response.status_code == 200
        data = response.json()
        assert "defaults" in data

    def test_get_defaults(self):
        """Verifica se retorna configurações padrão."""
        response = client.get("/api/config/defaults")
        assert response.status_code == 200

    def test_get_regions(self):
        """Verifica listagem de regiões."""
        response = client.get("/api/config/regions")
        assert response.status_code == 200
        data = response.json()
        assert "regions" in data

    def test_get_units(self):
        """Verifica listagem de unidades."""
        response = client.get("/api/config/units")
        assert response.status_code == 200
        data = response.json()
        assert "units" in data


class TestTemplatesEndpoint:
    """Testes para endpoints de templates."""

    def test_list_templates(self):
        """Verifica listagem de templates."""
        response = client.get("/api/templates/")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert "count" in data

    def test_get_nonexistent_template(self):
        """Verifica erro ao buscar template inexistente."""
        response = client.get("/api/templates/nonexistent_id")
        assert response.status_code == 404


class TestSchedulesEndpoint:
    """Testes para endpoints de agendamentos."""

    def test_list_schedules(self):
        """Verifica listagem de agendamentos."""
        response = client.get("/api/schedules/")
        assert response.status_code == 200
        data = response.json()
        assert "schedules" in data
        assert "count" in data

    def test_create_schedule(self):
        """Verifica criação de agendamento."""
        schedule_data = {
            "name": "Teste Automatizado",
            "description": "Criado por teste",
            "region": "teste",
            "units": ["Unidade Teste"],
            "frequency": "monthly",
            "day_of_month": 1,
            "time": "10:00"
        }
        response = client.post("/api/schedules/", json=schedule_data)
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["name"] == "Teste Automatizado"
        assert "id" in data

        # Cleanup - deletar o agendamento criado
        schedule_id = data["id"]
        cleanup_response = client.delete(f"/api/schedules/{schedule_id}")
        assert cleanup_response.status_code in [200, 204]

    def test_create_schedule_invalid_frequency(self):
        """Verifica validação de frequência inválida."""
        schedule_data = {
            "name": "Teste Inválido",
            "region": "teste",
            "units": [],
            "frequency": "invalid_frequency",
            "time": "10:00"
        }
        response = client.post("/api/schedules/", json=schedule_data)
        assert response.status_code == 422  # Validation error

    def test_get_nonexistent_schedule(self):
        """Verifica erro ao buscar agendamento inexistente."""
        response = client.get("/api/schedules/nonexistent_id")
        assert response.status_code == 404

    def test_pause_and_resume_schedule(self):
        """Verifica pause e resume de agendamento."""
        # Criar agendamento
        schedule_data = {
            "name": "Teste Pause/Resume",
            "region": "teste",
            "units": ["Unidade"],
            "frequency": "daily",
            "time": "08:00"
        }
        create_response = client.post("/api/schedules/", json=schedule_data)
        schedule_id = create_response.json()["id"]

        # Pausar
        pause_response = client.post(f"/api/schedules/{schedule_id}/pause")
        assert pause_response.status_code == 200
        assert pause_response.json()["status"] == "paused"

        # Resumir
        resume_response = client.post(f"/api/schedules/{schedule_id}/resume")
        assert resume_response.status_code == 200
        assert resume_response.json()["status"] == "active"

        # Cleanup
        client.delete(f"/api/schedules/{schedule_id}")
