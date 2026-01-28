"""
Model de Elemento de projeto WinDev.

Representa páginas, procedures, classes, queries, etc.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from beanie import Document, Link
from pydantic import BaseModel, Field

from wxcode.models.project import Project


class ElementType(str, Enum):
    """Tipos de elementos WinDev."""
    PAGE = "page"                    # .wwh - Página web
    PAGE_TEMPLATE = "page_template"  # .wwt - Template de página
    PROCEDURE_GROUP = "procedure_group"  # .wdg - Grupo de procedures
    BROWSER_PROCEDURE = "browser_procedure"  # .wwn - Procedures navegador
    CLASS = "class"                  # .wdc - Classe
    QUERY = "query"                  # .WDR - Query SQL
    REPORT = "report"                # .wde - Relatório
    REST_API = "rest_api"            # .wdrest - API REST
    WEBSERVICE = "webservice"        # .wdsdl - Webservice WSDL
    STRUCTURE = "structure"          # Estrutura de dados
    WINDOW = "window"                # .wdw - Janela (WinDev)
    COMPONENT = "component"          # Componente interno
    UNKNOWN = "unknown"


class ElementLayer(str, Enum):
    """Camada do elemento para ordenação de conversão."""
    SCHEMA = "schema"      # Modelo de dados
    DOMAIN = "domain"      # Entidades de domínio
    BUSINESS = "business"  # Lógica de negócio
    API = "api"            # Endpoints REST
    UI = "ui"              # Interface


class ConversionStatus(str, Enum):
    """Status de conversão do elemento."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PROPOSAL_GENERATED = "proposal_generated"
    CONVERTED = "converted"
    VALIDATED = "validated"
    ERROR = "error"
    SKIPPED = "skipped"


class ElementChunk(BaseModel):
    """
    Chunk de conteúdo para elementos grandes.

    Usado quando o conteúdo não cabe na janela de contexto do LLM.
    """
    index: int = Field(..., description="Índice do chunk (0-based)")
    content: str = Field(..., description="Conteúdo do chunk")
    tokens: int = Field(..., description="Número de tokens estimado")
    overlap_start: Optional[int] = Field(
        default=None,
        description="Tokens de overlap do chunk anterior"
    )
    semantic_type: Optional[str] = Field(
        default=None,
        description="Tipo semântico (GLOBAL, EVENTS, PROCEDURES, etc.)"
    )


class ElementAST(BaseModel):
    """
    AST/IR (Abstract Syntax Tree / Intermediate Representation).

    Representação estruturada do código WLanguage.
    """
    procedures: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Procedures/funções extraídas"
    )
    variables: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Variáveis globais"
    )
    controls: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Controles UI (para páginas)"
    )
    events: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Eventos (OnClick, OnLoad, etc.)"
    )
    queries: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Queries SQL embutidas"
    )
    imports: list[str] = Field(
        default_factory=list,
        description="Dependências importadas"
    )
    exports: list[str] = Field(
        default_factory=list,
        description="Símbolos exportados"
    )

    # Campos específicos para elementos do tipo QUERY
    sql: Optional[str] = Field(
        default=None,
        description="SQL completo (para elementos do tipo QUERY)"
    )
    parameters: list[str] = Field(
        default_factory=list,
        description="Parâmetros da query (para elementos do tipo QUERY)"
    )
    tables: list[str] = Field(
        default_factory=list,
        description="Tabelas referenciadas (para elementos do tipo QUERY)"
    )
    incomplete: bool = Field(
        default=False,
        description="True se SQL não foi encontrado no PDF"
    )


class ElementDependencies(BaseModel):
    """Grafo de dependências do elemento."""
    uses: list[str] = Field(
        default_factory=list,
        description="Elementos que este elemento usa/importa"
    )
    used_by: list[str] = Field(
        default_factory=list,
        description="Elementos que usam este elemento"
    )
    data_files: list[str] = Field(
        default_factory=list,
        description="Arquivos de dados (tabelas) acessados"
    )
    external_apis: list[str] = Field(
        default_factory=list,
        description="APIs externas chamadas"
    )
    bound_tables: list[str] = Field(
        default_factory=list,
        description="Tabelas vinculadas via DataBinding de controles"
    )

    def add_bound_table(self, table_name: str) -> None:
        """
        Adiciona tabela à lista de tabelas vinculadas (sem duplicatas).

        Args:
            table_name: Nome da tabela
        """
        if table_name and table_name not in self.bound_tables:
            self.bound_tables.append(table_name)


class ConvertedFile(BaseModel):
    """Arquivo gerado na conversão."""
    path: str = Field(..., description="Caminho relativo do arquivo gerado")
    file_type: str = Field(..., description="Tipo (model, service, route, template)")
    content: str = Field(..., description="Conteúdo do arquivo")


class ElementConversion(BaseModel):
    """Metadados de conversão do elemento."""
    status: ConversionStatus = Field(default=ConversionStatus.PENDING)
    target_stack: str = Field(default="fastapi-jinja2")
    target_files: list[ConvertedFile] = Field(default_factory=list)
    issues: list[str] = Field(
        default_factory=list,
        description="Problemas encontrados na conversão"
    )
    human_review_required: bool = Field(
        default=False,
        description="Precisa revisão humana"
    )
    converted_at: Optional[datetime] = None
    validated_at: Optional[datetime] = None


class Element(Document):
    """
    Representa um elemento de projeto WinDev.

    Pode ser uma página, procedure, classe, query, etc.
    Armazena o conteúdo original, AST, dependências e status de conversão.
    """

    # Relacionamento
    project_id: Link[Project] = Field(..., description="Projeto pai")

    # Identificação WinDev
    source_type: ElementType = Field(..., description="Tipo do elemento")
    source_name: str = Field(..., description="Nome do elemento")
    source_file: str = Field(..., description="Nome do arquivo original")
    windev_type: Optional[int] = Field(
        default=None,
        description="Código de tipo interno do WinDev"
    )
    identifier: Optional[str] = Field(
        default=None,
        description="Identificador hexadecimal único do WinDev"
    )

    # Conteúdo
    raw_content: str = Field(default="", description="Conteúdo bruto do elemento")
    chunks: list[ElementChunk] = Field(
        default_factory=list,
        description="Chunks para elementos grandes"
    )

    # AST/IR
    ast: Optional[ElementAST] = Field(
        default=None,
        description="AST extraída do código"
    )

    # Dependências
    dependencies: ElementDependencies = Field(
        default_factory=ElementDependencies,
        description="Grafo de dependências"
    )

    # Conversão
    conversion: ElementConversion = Field(
        default_factory=ElementConversion,
        description="Metadados de conversão"
    )

    # Ordenação
    topological_order: Optional[int] = Field(
        default=None,
        description="Ordem de conversão (calculada pelo grafo)"
    )
    layer: Optional[ElementLayer] = Field(
        default=None,
        description="Camada para conversão"
    )

    # Configurações de exclusão
    excluded_from: list[str] = Field(
        default_factory=list,
        description="IDs de configurações que excluem este elemento"
    )

    # Dados do PDF de documentação (preenchidos pelo enrich)
    general_properties: Optional[dict[str, Any]] = Field(
        default=None,
        description="Propriedades gerais extraídas do PDF"
    )
    screenshot_path: Optional[str] = Field(
        default=None,
        description="Caminho do screenshot no filesystem"
    )
    controls_count: int = Field(
        default=0,
        description="Quantidade de controles do elemento"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "elements"
        use_state_management = True
        indexes = [
            "project_id",
            "source_type",
            "source_name",
            [("project_id", 1), ("source_type", 1), ("source_name", 1)],
            [("project_id", 1), ("topological_order", 1)],
            [("project_id", 1), ("layer", 1)],
            [("project_id", 1), ("conversion.status", 1)],
            "dependencies.uses",
            "dependencies.used_by",
        ]

    def __str__(self) -> str:
        return f"Element({self.source_name}, type={self.source_type})"

    @property
    def needs_chunking(self) -> bool:
        """Verifica se o elemento precisa ser dividido em chunks."""
        # Estimativa: ~4 caracteres por token
        estimated_tokens = len(self.raw_content) // 4
        return estimated_tokens > 3500  # Deixa margem para contexto

    @property
    def is_converted(self) -> bool:
        """Verifica se o elemento foi convertido."""
        return self.conversion.status in [
            ConversionStatus.CONVERTED,
            ConversionStatus.VALIDATED
        ]
