"""
Model de historico de conversoes.

Registra cada conversao completada (sucesso ou falha) para auditoria.
"""

from datetime import datetime
from typing import Optional

from beanie import Document, PydanticObjectId
from pydantic import Field

from wxcode.models.product import ProductStatus


class ConversionHistoryEntry(Document):
    """
    Entrada de historico de conversao.

    Criada quando uma conversao termina (sucesso ou falha).
    Fornece trilha de auditoria e habilita visualizacao de historico.
    """

    # IDs (stored as ObjectId, not Link to avoid circular import)
    project_id: PydanticObjectId = Field(..., description="Projeto da conversao")
    product_id: PydanticObjectId = Field(..., description="Produto convertido")

    # Detalhes da conversao
    element_names: list[str] = Field(..., description="Elementos convertidos")
    status: ProductStatus = Field(..., description="Status final (completed/failed)")

    # Timing
    started_at: datetime = Field(..., description="Inicio da conversao")
    completed_at: datetime = Field(default_factory=datetime.utcnow, description="Fim da conversao")
    duration_seconds: float = Field(..., description="Duracao total em segundos")

    # Output info
    output_path: Optional[str] = Field(None, description="Caminho do output gerado")
    files_generated: int = Field(default=0, description="Numero de arquivos gerados")

    # Error info (if failed)
    error_message: Optional[str] = Field(None, description="Mensagem de erro se falhou")

    class Settings:
        name = "conversion_history"
        indexes = [
            "project_id",
            "product_id",
            [("project_id", 1), ("completed_at", -1)],  # For sorted history query
        ]
