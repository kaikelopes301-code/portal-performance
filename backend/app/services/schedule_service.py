# schedule_service.py — Serviço de gerenciamento de agendamentos

import json
import logging
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # backpperformance/
DATA_DIR = BASE_DIR / "backend" / "data"
SCHEDULES_FILE = DATA_DIR / "schedules.json"

# Garante que diretório existe
DATA_DIR.mkdir(parents=True, exist_ok=True)


class ScheduleServiceError(Exception):
    """Erro no serviço de agendamentos."""
    pass


class ScheduleService:
    """
    Serviço para gerenciamento de agendamentos de processamento.
    
    Os agendamentos são persistidos em JSON no disco.
    A execução real dos agendamentos é feita por um worker separado (Celery/APScheduler).
    """
    
    def __init__(self, schedules_path: Optional[Path] = None):
        self.schedules_path = schedules_path or SCHEDULES_FILE
        self._cache: Optional[Dict[str, Any]] = None
    
    def _load_schedules(self) -> Dict[str, Any]:
        """Carrega agendamentos do disco."""
        if not self.schedules_path.exists():
            default_data = {"schedules": {}, "executions": []}
            self._save_schedules(default_data)
            return default_data
        
        try:
            with open(self.schedules_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Garante estrutura mínima
            if "schedules" not in data:
                data["schedules"] = {}
            if "executions" not in data:
                data["executions"] = []
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao parsear JSON de agendamentos: {e}")
            raise ScheduleServiceError(f"Arquivo de agendamentos corrompido: {e}")
        except Exception as e:
            logger.error(f"Erro ao carregar agendamentos: {e}")
            raise ScheduleServiceError(f"Erro ao carregar agendamentos: {e}")
    
    def _save_schedules(self, data: Dict[str, Any]) -> None:
        """Salva agendamentos no disco."""
        try:
            with open(self.schedules_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            self._cache = None
        except Exception as e:
            logger.error(f"Erro ao salvar agendamentos: {e}")
            raise ScheduleServiceError(f"Erro ao salvar agendamentos: {e}")
    
    def _calculate_next_run(self, schedule: Dict[str, Any]) -> Optional[str]:
        """Calcula próxima execução de um agendamento."""
        if schedule.get("status") != "active":
            return None
        
        frequency = schedule.get("frequency")
        time_str = schedule.get("time", "09:00")
        
        try:
            hour, minute = map(int, time_str.split(":"))
        except:
            hour, minute = 9, 0
        
        now = datetime.now()
        
        if frequency == "once":
            # Para execução única, usa last_run para verificar se já executou
            if schedule.get("last_run"):
                return None
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()
        
        elif frequency == "daily":
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run.isoformat()
        
        elif frequency == "weekly":
            day_of_week = schedule.get("day_of_week", 0)  # 0 = Segunda
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            days_ahead = day_of_week - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_run += timedelta(days=days_ahead)
            return next_run.isoformat()
        
        elif frequency == "monthly":
            day_of_month = schedule.get("day_of_month", 1)
            next_run = now.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                # Próximo mês
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)
            return next_run.isoformat()
        
        return None
    
    def list_schedules(self) -> List[Dict[str, Any]]:
        """Lista todos os agendamentos."""
        data = self._load_schedules()
        schedules = []
        
        for schedule_id, schedule in data.get("schedules", {}).items():
            schedule_info = {
                "id": schedule_id,
                **schedule,
                "next_run": self._calculate_next_run(schedule)
            }
            schedules.append(schedule_info)
        
        return schedules
    
    def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Retorna um agendamento específico."""
        data = self._load_schedules()
        schedule = data.get("schedules", {}).get(schedule_id)
        
        if not schedule:
            return None
        
        return {
            "id": schedule_id,
            **schedule,
            "next_run": self._calculate_next_run(schedule)
        }
    
    def create_schedule(
        self,
        name: str,
        region: str,
        units: List[str],
        frequency: str,
        description: Optional[str] = None,
        day_of_month: Optional[int] = None,
        day_of_week: Optional[int] = None,
        time: str = "09:00",
        auto_send_email: bool = False
    ) -> Dict[str, Any]:
        """Cria um novo agendamento."""
        data = self._load_schedules()
        
        # Gera ID único
        schedule_id = str(uuid.uuid4())[:8]
        
        # Valida frequência
        valid_frequencies = ["daily", "weekly", "monthly", "once"]
        if frequency not in valid_frequencies:
            raise ScheduleServiceError(f"Frequência inválida. Use: {', '.join(valid_frequencies)}")
        
        # Valida campos obrigatórios por frequência
        if frequency == "weekly" and day_of_week is None:
            raise ScheduleServiceError("day_of_week é obrigatório para agendamentos semanais")
        if frequency == "monthly" and day_of_month is None:
            raise ScheduleServiceError("day_of_month é obrigatório para agendamentos mensais")
        
        schedule = {
            "name": name,
            "description": description,
            "region": region,
            "units": units,
            "frequency": frequency,
            "day_of_month": day_of_month,
            "day_of_week": day_of_week,
            "time": time,
            "auto_send_email": auto_send_email,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": None,
            "last_run": None,
            "run_count": 0
        }
        
        data["schedules"][schedule_id] = schedule
        self._save_schedules(data)
        
        return {
            "id": schedule_id,
            **schedule,
            "next_run": self._calculate_next_run(schedule)
        }
    
    def update_schedule(
        self,
        schedule_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        region: Optional[str] = None,
        units: Optional[List[str]] = None,
        frequency: Optional[str] = None,
        day_of_month: Optional[int] = None,
        day_of_week: Optional[int] = None,
        time: Optional[str] = None,
        auto_send_email: Optional[bool] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Atualiza um agendamento existente."""
        data = self._load_schedules()
        
        if schedule_id not in data.get("schedules", {}):
            raise ScheduleServiceError(f"Agendamento '{schedule_id}' não encontrado")
        
        schedule = data["schedules"][schedule_id]
        
        # Atualiza campos fornecidos
        if name is not None:
            schedule["name"] = name
        if description is not None:
            schedule["description"] = description
        if region is not None:
            schedule["region"] = region
        if units is not None:
            schedule["units"] = units
        if frequency is not None:
            schedule["frequency"] = frequency
        if day_of_month is not None:
            schedule["day_of_month"] = day_of_month
        if day_of_week is not None:
            schedule["day_of_week"] = day_of_week
        if time is not None:
            schedule["time"] = time
        if auto_send_email is not None:
            schedule["auto_send_email"] = auto_send_email
        if status is not None:
            valid_statuses = ["active", "paused", "completed", "failed"]
            if status not in valid_statuses:
                raise ScheduleServiceError(f"Status inválido. Use: {', '.join(valid_statuses)}")
            schedule["status"] = status
        
        schedule["updated_at"] = datetime.utcnow().isoformat()
        
        self._save_schedules(data)
        
        return {
            "id": schedule_id,
            **schedule,
            "next_run": self._calculate_next_run(schedule)
        }
    
    def delete_schedule(self, schedule_id: str) -> bool:
        """Remove um agendamento."""
        data = self._load_schedules()
        
        if schedule_id not in data.get("schedules", {}):
            return False
        
        del data["schedules"][schedule_id]
        self._save_schedules(data)
        
        return True
    
    def pause_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Pausa um agendamento."""
        return self.update_schedule(schedule_id, status="paused")
    
    def resume_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Retoma um agendamento pausado."""
        return self.update_schedule(schedule_id, status="active")
    
    def record_execution(
        self,
        schedule_id: str,
        status: str,
        units_processed: int = 0,
        errors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Registra uma execução de agendamento."""
        data = self._load_schedules()
        
        if schedule_id not in data.get("schedules", {}):
            raise ScheduleServiceError(f"Agendamento '{schedule_id}' não encontrado")
        
        execution = {
            "id": str(uuid.uuid4())[:8],
            "schedule_id": schedule_id,
            "started_at": datetime.utcnow().isoformat(),
            "finished_at": datetime.utcnow().isoformat(),
            "status": status,
            "units_processed": units_processed,
            "errors": errors or []
        }
        
        # Adiciona execução ao histórico (mantém últimas 100)
        data["executions"].append(execution)
        data["executions"] = data["executions"][-100:]
        
        # Atualiza agendamento
        schedule = data["schedules"][schedule_id]
        schedule["last_run"] = datetime.utcnow().isoformat()
        schedule["run_count"] = schedule.get("run_count", 0) + 1
        
        # Se for execução única e completou, marca como completed
        if schedule.get("frequency") == "once" and status == "completed":
            schedule["status"] = "completed"
        
        self._save_schedules(data)
        
        return execution
    
    def get_executions(
        self,
        schedule_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Retorna histórico de execuções."""
        data = self._load_schedules()
        executions = data.get("executions", [])
        
        if schedule_id:
            executions = [e for e in executions if e.get("schedule_id") == schedule_id]
        
        # Ordena por data (mais recente primeiro)
        executions.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        
        return executions[:limit]
    
    def get_pending_schedules(self) -> List[Dict[str, Any]]:
        """
        Retorna agendamentos que devem ser executados agora.
        
        Usado pelo worker para verificar o que precisa rodar.
        """
        schedules = self.list_schedules()
        now = datetime.now()
        pending = []
        
        for schedule in schedules:
            if schedule.get("status") != "active":
                continue
            
            next_run_str = schedule.get("next_run")
            if not next_run_str:
                continue
            
            try:
                next_run = datetime.fromisoformat(next_run_str)
                if next_run <= now:
                    pending.append(schedule)
            except:
                continue
        
        return pending
