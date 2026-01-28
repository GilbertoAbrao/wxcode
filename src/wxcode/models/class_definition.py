"""
Model de ClassDefinition WinDev.

Representa uma classe extraída de um arquivo .wdc.
"""

from datetime import datetime
from typing import Optional

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field

from wxcode.models.procedure import ProcedureParameter


class ClassMember(BaseModel):
    """
    Membro de uma classe.

    Representa um campo/propriedade com nome, tipo e visibilidade.
    """

    name: str = Field(..., description="Nome do membro")
    type: str = Field(..., description="Tipo do membro (string, int, datetime, etc.)")
    visibility: str = Field(
        default="public",
        description="Visibilidade (public, private, protected)"
    )
    default_value: Optional[str] = Field(
        default=None,
        description="Valor padrão se especificado"
    )
    serialize: bool = Field(
        default=True,
        description="True se deve ser serializado (Serialize = false desativa)"
    )


class ClassConstant(BaseModel):
    """
    Constante de uma classe.

    Representa uma constante declarada na seção CONSTANT.
    """

    name: str = Field(..., description="Nome da constante")
    value: str = Field(..., description="Valor da constante")
    type: Optional[str] = Field(
        default=None,
        description="Tipo inferido da constante"
    )


class ClassMethod(BaseModel):
    """
    Método de uma classe.

    Representa um método (constructor, destructor, ou método normal).
    """

    name: str = Field(..., description="Nome do método")
    method_type: str = Field(
        default="method",
        description="Tipo do método (constructor, destructor, method)"
    )
    visibility: str = Field(
        default="public",
        description="Visibilidade (public, private, protected)"
    )
    parameters: list[ProcedureParameter] = Field(
        default_factory=list,
        description="Parâmetros do método"
    )
    return_type: Optional[str] = Field(
        default=None,
        description="Tipo de retorno"
    )
    code: str = Field(default="", description="Código WLanguage do método")
    code_lines: int = Field(default=0, description="Número de linhas de código")
    is_static: bool = Field(default=False, description="True se método é estático")

    # Propriedades WinDev originais
    procedure_id: Optional[str] = Field(
        default=None,
        description="ID interno WinDev"
    )
    type_code: Optional[int] = Field(
        default=None,
        description="Código de tipo WinDev (27=constructor, 28=destructor, 12=method)"
    )
    windev_type: Optional[int] = Field(
        default=None,
        description="Campo 'type' original do .wdc"
    )
    internal_properties: Optional[str] = Field(
        default=None,
        description="Campo internal_properties original (base64)"
    )


class ClassDependencies(BaseModel):
    """
    Dependências de uma classe.

    Identificadas via análise estática do código.
    """

    uses_classes: list[str] = Field(
        default_factory=list,
        description="Classes usadas (herança ou composição)"
    )
    uses_files: list[str] = Field(
        default_factory=list,
        description="Arquivos HyperFile usados"
    )
    calls_procedures: list[str] = Field(
        default_factory=list,
        description="Procedures globais chamadas"
    )


class ClassDefinition(Document):
    """
    Representa uma classe WinDev extraída de um arquivo .wdc.

    Armazena estrutura completa: herança, membros, métodos, constantes.
    """

    # Relacionamentos
    element_id: PydanticObjectId = Field(
        ...,
        description="ID do Element pai (.wdc)"
    )
    project_id: PydanticObjectId = Field(
        ...,
        description="ID do Project"
    )

    # Identificação
    name: str = Field(..., description="Nome da classe")
    identifier: Optional[str] = Field(
        default=None,
        description="ID interno WinDev (identifier do .wdc)"
    )

    # Estrutura da classe
    inherits_from: Optional[str] = Field(
        default=None,
        description="Classe pai (herança)"
    )
    is_abstract: bool = Field(
        default=False,
        description="True se classe é abstrata"
    )

    # Membros
    members: list[ClassMember] = Field(
        default_factory=list,
        description="Membros/campos da classe"
    )
    methods: list[ClassMethod] = Field(
        default_factory=list,
        description="Métodos da classe"
    )
    constants: list[ClassConstant] = Field(
        default_factory=list,
        description="Constantes da classe"
    )

    # Dependências
    dependencies: ClassDependencies = Field(
        default_factory=ClassDependencies,
        description="Dependências identificadas"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "class_definitions"
        use_state_management = True
        indexes = [
            "element_id",
            "project_id",
            "name",
            "inherits_from",
            [("project_id", 1), ("name", 1)],
            [("project_id", 1), ("inherits_from", 1)],
            "dependencies.uses_classes",
            "dependencies.uses_files",
        ]

    def __str__(self) -> str:
        inheritance = f" extends {self.inherits_from}" if self.inherits_from else ""
        abstract = "abstract " if self.is_abstract else ""
        return f"{abstract}class {self.name}{inheritance}"

    @property
    def total_members(self) -> int:
        """Retorna o total de membros."""
        return len(self.members)

    @property
    def total_methods(self) -> int:
        """Retorna o total de métodos."""
        return len(self.methods)

    @property
    def total_code_lines(self) -> int:
        """Retorna o total de linhas de código dos métodos."""
        return sum(m.code_lines for m in self.methods)
