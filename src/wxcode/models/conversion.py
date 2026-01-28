"""
Model de Conversão de projeto.

Rastreia o processo de conversão de um projeto completo.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document, Link
from pydantic import BaseModel, Field

from wxcode.models.project import Project


class ConversionPhase(str, Enum):
    """Fases do pipeline de conversão."""
    PENDING = "pending"
    SCHEMA = "schema"
    DOMAIN = "domain"
    BUSINESS = "business"
    API = "api"
    UI = "ui"
    VALIDATION = "validation"
    COMPLETED = "completed"
    ERROR = "error"


class ConversionError(BaseModel):
    """Erro ocorrido durante a conversão."""
    element_name: str = Field(..., description="Nome do elemento com erro")
    element_type: str = Field(..., description="Tipo do elemento")
    phase: ConversionPhase = Field(..., description="Fase onde ocorreu o erro")
    error_message: str = Field(..., description="Mensagem de erro")
    stack_trace: Optional[str] = Field(default=None, description="Stack trace completo")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    recoverable: bool = Field(
        default=True,
        description="Se o erro permite continuar com outros elementos"
    )


class LayerProgress(BaseModel):
    """Progresso de conversão de uma camada."""
    total: int = Field(default=0, description="Total de elementos na camada")
    converted: int = Field(default=0, description="Elementos convertidos")
    validated: int = Field(default=0, description="Elementos validados")
    errors: int = Field(default=0, description="Elementos com erro")
    skipped: int = Field(default=0, description="Elementos pulados")

    @property
    def percentage(self) -> float:
        """Percentual de conclusão."""
        if self.total == 0:
            return 100.0
        return (self.converted / self.total) * 100


class Conversion(Document):
    """
    Rastreia o processo de conversão de um projeto.

    Mantém o status geral, progresso por camada e erros encontrados.
    """

    # Relacionamento
    project_id: Link[Project] = Field(..., description="Projeto sendo convertido")

    # Configuração
    target_stack: str = Field(
        default="fastapi-jinja2",
        description="Stack alvo da conversão"
    )
    target_element_names: Optional[list[str]] = Field(
        default=None,
        description="Nomes específicos de elementos para conversão (filtering)"
    )

    # Status
    current_phase: ConversionPhase = Field(
        default=ConversionPhase.PENDING,
        description="Fase atual da conversão"
    )

    # Progresso por camada
    schema_progress: LayerProgress = Field(default_factory=LayerProgress)
    domain_progress: LayerProgress = Field(default_factory=LayerProgress)
    business_progress: LayerProgress = Field(default_factory=LayerProgress)
    api_progress: LayerProgress = Field(default_factory=LayerProgress)
    ui_progress: LayerProgress = Field(default_factory=LayerProgress)

    # Totais
    total_elements: int = Field(default=0)
    elements_converted: int = Field(default=0)
    elements_validated: int = Field(default=0)
    elements_with_errors: int = Field(default=0)

    # Erros
    errors: list[ConversionError] = Field(
        default_factory=list,
        description="Erros encontrados durante a conversão"
    )

    # Output
    output_directory: Optional[str] = Field(
        default=None,
        description="Diretório de saída do projeto convertido"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Duração
    @property
    def duration_seconds(self) -> Optional[float]:
        """Duração da conversão em segundos."""
        if self.started_at is None:
            return None
        end = self.completed_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()

    @property
    def overall_progress(self) -> float:
        """Progresso geral da conversão em percentual."""
        if self.total_elements == 0:
            return 0.0
        return (self.elements_converted / self.total_elements) * 100

    @property
    def has_errors(self) -> bool:
        """Verifica se há erros na conversão."""
        return len(self.errors) > 0

    class Settings:
        name = "conversions"
        use_state_management = True
        indexes = [
            "project_id",
            "current_phase",
            "target_element_names",
            [("project_id", 1), ("created_at", -1)],
        ]

    def __str__(self) -> str:
        return f"Conversion(project={self.project_id}, phase={self.current_phase}, progress={self.overall_progress:.1f}%)"

    def add_error(
        self,
        element_name: str,
        element_type: str,
        phase: ConversionPhase,
        error_message: str,
        stack_trace: Optional[str] = None,
        recoverable: bool = True
    ) -> None:
        """Adiciona um erro à lista de erros."""
        self.errors.append(ConversionError(
            element_name=element_name,
            element_type=element_type,
            phase=phase,
            error_message=error_message,
            stack_trace=stack_trace,
            recoverable=recoverable
        ))
        self.elements_with_errors += 1
