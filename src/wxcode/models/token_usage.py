"""
Model para tracking de consumo de tokens do Claude Code.
"""

from datetime import datetime
from typing import Optional

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import IndexModel, ASCENDING, DESCENDING


class TokenUsageLog(Document):
    """
    Registra o consumo de tokens de uma sessão Claude Code.

    Cada execução de comando no Claude Code gera um log com métricas
    de tokens utilizados e custo total da operação.
    """

    # Identificação
    tenant_id: str = Field(..., description="ID do tenant (usuário/organização)")
    project_id: PydanticObjectId = Field(..., description="ID do projeto")
    session_id: str = Field(..., description="ID da sessão Claude Code")
    change_id: Optional[str] = Field(
        default=None, description="ID da change/conversão associada"
    )

    # Métricas de tokens
    input_tokens: int = Field(default=0, description="Tokens de entrada")
    output_tokens: int = Field(default=0, description="Tokens de saída")
    cache_creation_tokens: int = Field(
        default=0, description="Tokens usados para criar cache"
    )
    cache_read_tokens: int = Field(
        default=0, description="Tokens lidos do cache"
    )

    # Custo e modelo
    total_cost_usd: float = Field(default=0.0, description="Custo total em USD")
    model: Optional[str] = Field(default=None, description="Modelo utilizado (ex: claude-sonnet-4)")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "token_usage_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("project_id", ASCENDING)],
                name="tenant_project_idx"
            ),
            IndexModel(
                [("created_at", DESCENDING)],
                name="created_at_idx"
            ),
            IndexModel(
                [("session_id", ASCENDING)],
                name="session_idx"
            ),
        ]

    @property
    def total_tokens(self) -> int:
        """Total de tokens consumidos (input + output)."""
        return self.input_tokens + self.output_tokens

    def __str__(self) -> str:
        return (
            f"TokenUsageLog(session={self.session_id[:8]}..., "
            f"tokens={self.total_tokens}, cost=${self.total_cost_usd:.4f})"
        )
