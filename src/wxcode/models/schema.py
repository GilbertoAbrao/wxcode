"""
Models para schema de banco de dados extraído de arquivos .xdd (Analysis WinDev).

Representa a estrutura completa do banco: conexões, tabelas, colunas, índices.
"""

from datetime import datetime
from typing import Optional

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field


class SchemaConnection(BaseModel):
    """Conexão de banco definida na Analysis."""

    name: str = Field(..., description="Nome da conexão (ex: CNX_BASE_HOMOLOG)")
    type_code: int = Field(..., description="Tipo de conexão (1 = SQL Server)")
    database_type: str = Field("", description="Tipo do banco (sqlserver, mysql, postgresql, etc.)")
    driver_name: str = Field("", description="Nome legível do driver (SQL Server, MySQL, etc.)")
    source: str = Field("", description="Servidor/host da conexão")
    port: str = Field("", description="Porta da conexão (extraída ou padrão)")
    database: str = Field("", description="Nome do banco de dados")
    user: Optional[str] = Field(None, description="Usuário da conexão")
    extended_info: str = Field("", description="Informações estendidas (INFOS_ETENDUES)")


class SchemaColumn(BaseModel):
    """Coluna (RUBRIQUE) da Analysis."""

    name: str = Field(..., description="Nome da coluna")
    hyperfile_type: int = Field(..., description="Código do tipo HyperFile")
    python_type: str = Field(..., description="Tipo Python equivalente")
    size: int = Field(0, description="Tamanho/precisão da coluna")
    nullable: bool = Field(True, description="Permite NULL")
    default_value: Optional[str] = Field(None, description="Valor default")

    is_primary_key: bool = Field(False, description="É chave primária (TYPE_CLE=1)")
    is_indexed: bool = Field(False, description="Tem índice (TYPE_CLE > 0)")
    is_unique: bool = Field(False, description="Índice único (TYPE_CLE=3)")
    is_auto_increment: bool = Field(False, description="Auto-increment (TYPE=24)")


class SchemaIndex(BaseModel):
    """Índice inferido das colunas."""

    name: str = Field(..., description="Nome do índice")
    columns: list[str] = Field(default_factory=list, description="Colunas do índice")
    is_unique: bool = Field(False, description="É índice único")
    is_primary: bool = Field(False, description="É chave primária")


class SchemaTable(BaseModel):
    """Tabela (FICHIER) da Analysis."""

    name: str = Field(..., description="Nome da tabela")
    physical_name: str = Field("", description="Nome físico (NomPhysique)")
    connection_name: str = Field("", description="Nome da conexão associada")
    supports_null: bool = Field(True, description="Suporta NULL (FicNullSupporte)")

    columns: list[SchemaColumn] = Field(
        default_factory=list, description="Colunas da tabela"
    )
    indexes: list[SchemaIndex] = Field(
        default_factory=list, description="Índices da tabela"
    )

    # Campos de análise de dependências
    topological_order: Optional[int] = Field(None, description="Ordem topológica")
    layer: Optional[str] = Field(None, description="Camada (schema, domain, etc.)")
    conversion_status: Optional[str] = Field(None, description="Status de conversão")

    @property
    def column_count(self) -> int:
        """Número de colunas."""
        return len(self.columns)

    @property
    def primary_key_columns(self) -> list[str]:
        """Nomes das colunas que são PK."""
        return [col.name for col in self.columns if col.is_primary_key]


class DatabaseSchema(Document):
    """
    Schema completo de um projeto WinDev.

    Representa toda a estrutura do banco de dados extraída do arquivo .xdd.
    """

    project_id: PydanticObjectId = Field(..., description="ID do projeto")
    source_file: str = Field(..., description="Caminho do arquivo .xdd")
    version: int = Field(0, description="Versão da Analysis (GenNum)")

    connections: list[SchemaConnection] = Field(
        default_factory=list, description="Conexões de banco definidas"
    )
    tables: list[SchemaTable] = Field(
        default_factory=list, description="Tabelas do schema"
    )

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "schemas"

    @property
    def total_tables(self) -> int:
        """Número total de tabelas."""
        return len(self.tables)

    @property
    def total_columns(self) -> int:
        """Número total de colunas em todas as tabelas."""
        return sum(len(table.columns) for table in self.tables)

    @property
    def total_connections(self) -> int:
        """Número total de conexões."""
        return len(self.connections)
