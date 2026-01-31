"""
API de Schema de banco de dados.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from wxcode.models import Project, DatabaseSchema


router = APIRouter()


class SchemaTableResponse(BaseModel):
    """Tabela do schema."""
    name: str
    physical_name: str
    connection_name: str
    column_count: int
    index_count: int
    primary_key: list[str]


class SchemaConnectionResponse(BaseModel):
    """Conexão do schema."""
    name: str
    database_type: str
    driver_name: str
    source: str
    port: str
    database: str
    user: str | None


class SchemaResponse(BaseModel):
    """Resposta do schema completo."""
    project: str
    source_file: str
    version: int
    total_tables: int
    tables: list[SchemaTableResponse]
    total_connections: int
    connections: list[SchemaConnectionResponse]


@router.get("/{project_name}", response_model=SchemaResponse)
async def get_schema(project_name: str) -> SchemaResponse:
    """Busca schema de um projeto por nome."""
    # Find project by name
    project = await Project.find_one(Project.name == project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    # Find schema for project
    schema = await DatabaseSchema.find_one(DatabaseSchema.project_id == project.id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema não encontrado")

    return SchemaResponse(
        project=project.name,
        source_file=schema.source_file,
        version=schema.version,
        total_tables=len(schema.tables),
        tables=[
            SchemaTableResponse(
                name=t.name,
                physical_name=t.physical_name,
                connection_name=t.connection_name,
                column_count=len(t.columns),
                index_count=len(t.indexes),
                primary_key=t.primary_key_columns,
            )
            for t in schema.tables
        ],
        total_connections=len(schema.connections),
        connections=[
            SchemaConnectionResponse(
                name=c.name,
                database_type=c.database_type,
                driver_name=c.driver_name,
                source=c.source,
                port=c.port,
                database=c.database,
                user=c.user,
            )
            for c in schema.connections
        ],
    )
