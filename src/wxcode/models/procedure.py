"""
Model de Procedure WinDev.

Representa uma procedure individual extraída de:
- Arquivos .wdg (grupos de procedures globais)
- Arquivos .wwh/.wdw (procedures locais de páginas/windows)

Para procedures locais:
- is_local = True
- scope = "page" | "window" | "report"
- element_id aponta para a página/window pai
"""

from datetime import datetime
from typing import Any, Optional

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field


class ProcedureParameter(BaseModel):
    """
    Parâmetro de uma procedure.

    Representa um parâmetro com nome, tipo e modificadores.
    """

    name: str = Field(..., description="Nome do parâmetro")
    type: Optional[str] = Field(
        default=None,
        description="Tipo do parâmetro (string, int, JSON, etc.)"
    )
    is_local: bool = Field(
        default=False,
        description="True se declarado como LOCAL"
    )
    default_value: Optional[str] = Field(
        default=None,
        description="Valor padrão se especificado"
    )


class ProcedureDependencies(BaseModel):
    """
    Dependências de uma procedure.

    Identificadas via análise estática do código.
    """

    calls_procedures: list[str] = Field(
        default_factory=list,
        description="Procedures chamadas no código"
    )
    uses_files: list[str] = Field(
        default_factory=list,
        description="Arquivos HyperFile usados (CLIENTE, PEDIDO, etc.)"
    )
    uses_apis: list[str] = Field(
        default_factory=list,
        description="APIs externas (REST, HTTP, etc.)"
    )
    uses_queries: list[str] = Field(
        default_factory=list,
        description="Queries SQL referenciadas"
    )


class Procedure(Document):
    """
    Representa uma procedure WinDev extraída de um arquivo .wdg.

    Armazena assinatura, código, dependências e metadados.
    """

    # Relacionamentos
    element_id: PydanticObjectId = Field(
        ...,
        description="ID do Element pai (.wdg)"
    )
    project_id: PydanticObjectId = Field(
        ...,
        description="ID do Project"
    )

    # Identificação
    name: str = Field(..., description="Nome da procedure")
    procedure_id: Optional[str] = Field(
        default=None,
        description="ID interno WinDev (procedure_id do .wdg)"
    )
    type_code: int = Field(
        default=15,
        description="Código de tipo (15 = procedure normal)"
    )

    # Assinatura
    parameters: list[ProcedureParameter] = Field(
        default_factory=list,
        description="Parâmetros da procedure"
    )
    return_type: Optional[str] = Field(
        default=None,
        description="Tipo de retorno (JSON, boolean, string, etc.)"
    )

    # Código
    code: str = Field(default="", description="Código WLanguage completo")
    code_lines: int = Field(default=0, description="Número de linhas de código")

    # Dependências
    dependencies: ProcedureDependencies = Field(
        default_factory=ProcedureDependencies,
        description="Dependências identificadas"
    )

    # Metadados
    has_documentation: bool = Field(
        default=False,
        description="True se tem comentários de documentação"
    )
    is_public: bool = Field(
        default=True,
        description="True se procedure é pública"
    )
    is_internal: bool = Field(
        default=False,
        description="True se é INTERNAL PROCEDURE"
    )
    is_local: bool = Field(
        default=False,
        description="True se é procedure local de página/window/report"
    )
    scope: Optional[str] = Field(
        default=None,
        description="Escopo da procedure local: 'page', 'window', 'report' ou None para global"
    )
    has_error_handling: bool = Field(
        default=False,
        description="True se tem CASE ERROR ou CASE EXCEPTION"
    )

    # Propriedades WinDev originais
    windev_type: Optional[int] = Field(
        default=None,
        description="Campo 'type' original do .wdg"
    )
    internal_properties: Optional[str] = Field(
        default=None,
        description="Campo internal_properties original (base64)"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "procedures"
        use_state_management = True
        indexes = [
            "element_id",
            "project_id",
            "name",
            "is_local",
            "scope",
            [("element_id", 1), ("name", 1)],
            [("project_id", 1), ("name", 1)],
            [("project_id", 1), ("is_local", 1)],
            "dependencies.calls_procedures",
            "dependencies.uses_files",
        ]

    def __str__(self) -> str:
        params = ", ".join(p.name for p in self.parameters)
        ret = f": {self.return_type}" if self.return_type else ""
        return f"Procedure({self.name}({params}){ret})"

    @property
    def signature(self) -> str:
        """Retorna a assinatura completa da procedure."""
        params = []
        for p in self.parameters:
            param_str = p.name
            if p.type:
                param_str += f" is {p.type}"
            if p.default_value:
                param_str += f" = {p.default_value}"
            if p.is_local:
                param_str = f"LOCAL {param_str}"
            params.append(param_str)

        sig = f"PROCEDURE {self.name}({', '.join(params)})"
        if self.return_type:
            sig += f": {self.return_type}"
        return sig
