"""
Modelo de sessão de importação para o wizard.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from beanie import Document
from pydantic import BaseModel, Field
from pymongo import IndexModel


class StepResult(BaseModel):
    """Resultado de uma etapa do wizard."""

    step: int
    name: str  # "import", "enrich", etc.
    status: Literal["pending", "running", "completed", "failed", "skipped"]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Métricas extraídas do output
    metrics: Dict[str, Any] = Field(default_factory=dict)

    # Logs capturados
    log_lines: int = 0
    error_message: Optional[str] = None


class ImportSession(Document):
    """Estado de uma sessão do wizard de importação."""

    session_id: str = Field(default_factory=lambda: str(uuid4()))
    project_path: str
    project_id: Optional[str] = None  # ObjectId do projeto criado
    pdf_docs_path: Optional[str] = None

    # Workspace tracking
    workspace_id: Optional[str] = None  # ID do workspace (8 hex chars)
    workspace_path: Optional[str] = None  # Caminho completo do workspace
    project_name: Optional[str] = None  # Nome original do projeto (extraido do .wwp)

    current_step: int = 1  # 1-6
    status: Literal["pending", "running", "completed", "failed", "cancelled"] = "pending"

    steps: List[StepResult] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "import_sessions"
        indexes = [
            IndexModel([("session_id", 1)], unique=True),
            IndexModel([("created_at", -1)]),
        ]

    def get_step_result(self, step: int) -> Optional[StepResult]:
        """Retorna resultado de uma etapa específica."""
        for step_result in self.steps:
            if step_result.step == step:
                return step_result
        return None

    def update_step_status(
        self,
        step: int,
        status: Literal["pending", "running", "completed", "failed", "skipped"],
        error_message: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Atualiza status de uma etapa."""
        step_result = self.get_step_result(step)
        if not step_result:
            # Cria nova etapa se não existe
            step_names = {
                1: "selection",
                2: "import",
                3: "enrich",
                4: "parse",
                5: "analyze",
                6: "sync-neo4j",
            }
            step_result = StepResult(
                step=step,
                name=step_names.get(step, f"step-{step}"),
                status=status,
            )
            self.steps.append(step_result)
        else:
            step_result.status = status
            if error_message:
                step_result.error_message = error_message
            if metrics:
                step_result.metrics.update(metrics)

        # Atualizar timestamps
        if status == "running" and not step_result.started_at:
            step_result.started_at = datetime.utcnow()
        elif status in ["completed", "failed", "skipped"]:
            step_result.completed_at = datetime.utcnow()

        self.updated_at = datetime.utcnow()
