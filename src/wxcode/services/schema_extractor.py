"""
Servico de extracao de schema para contexto GSD.

Extrai tabelas do banco de dados vinculadas a elementos em uma Configuration scope.
"""

from typing import Optional

from beanie import PydanticObjectId

from wxcode.models.element import Element
from wxcode.models.schema import DatabaseSchema
from wxcode.parser.global_state_extractor import GlobalStateExtractor
from wxcode.models.global_state_context import GlobalStateContext


async def extract_schema_for_configuration(
    project_id: PydanticObjectId,
    configuration_id: Optional[str],
) -> list[dict]:
    """
    Extrai tabelas usadas por elementos na Configuration.

    Consulta o schema do projeto e filtra apenas as tabelas que sao
    referenciadas pelos elementos incluidos na Configuration scope.

    Se nao houver Configuration (configuration_id=None) ou se nenhuma
    dependencia for encontrada nos elementos, retorna TODAS as tabelas
    do schema como fallback.

    Args:
        project_id: ID do Knowledge Base (Project)
        configuration_id: ID opcional da Configuration para scoping.
                         Se None, inclui todas as tabelas do schema.

    Returns:
        Lista de dicts com estrutura de tabelas:
        - name: Nome da tabela
        - physical_name: Nome fisico da tabela
        - columns: Lista de colunas com tipos e constraints
        - indexes: Lista de indices da tabela
    """
    # Busca schema do projeto
    schema = await DatabaseSchema.find_one(
        DatabaseSchema.project_id == project_id
    )
    if not schema:
        return []

    def _table_to_dict(table) -> dict:
        """Converte SchemaTable para dict."""
        return {
            "name": table.name,
            "physical_name": table.physical_name,
            "columns": [
                {
                    "name": col.name,
                    "hyperfile_type": col.hyperfile_type,
                    "python_type": col.python_type,
                    "size": col.size,
                    "nullable": col.nullable,
                    "is_primary_key": col.is_primary_key,
                    "is_indexed": col.is_indexed,
                    "is_auto_increment": col.is_auto_increment,
                }
                for col in table.columns
            ],
            "indexes": [
                {
                    "name": idx.name,
                    "columns": idx.columns,
                    "is_unique": idx.is_unique,
                    "is_primary": idx.is_primary,
                }
                for idx in table.indexes
            ],
        }

    # Se nao houver Configuration, retorna TODAS as tabelas
    if not configuration_id:
        return [_table_to_dict(table) for table in schema.tables]

    # Busca elementos no escopo da Configuration
    elements = await Element.find(
        Element.project_id == project_id,
        {"excluded_from": {"$nin": [configuration_id]}}
    ).to_list()

    # Coleta nomes de tabelas das dependencias dos elementos
    table_names: set[str] = set()
    for elem in elements:
        if elem.dependencies:
            # Tabelas acessadas via codigo (HReadSeek, etc.)
            if elem.dependencies.data_files:
                table_names.update(elem.dependencies.data_files)
            # Tabelas vinculadas via DataBinding de controles UI
            if elem.dependencies.bound_tables:
                table_names.update(elem.dependencies.bound_tables)

    # Se nenhuma dependencia encontrada, retorna TODAS as tabelas (fallback)
    if not table_names:
        return [_table_to_dict(table) for table in schema.tables]

    # Filtra tabelas do schema para apenas as usadas
    tables = []
    for table in schema.tables:
        if table.name in table_names or table.physical_name in table_names:
            tables.append(_table_to_dict(table))

    return tables


async def get_element_count_for_configuration(
    project_id: PydanticObjectId,
    configuration_id: Optional[str],
) -> int:
    """
    Conta elementos no escopo da Configuration.

    Util para verificar se uma Configuration tem elementos antes
    de tentar extrair schema.

    Args:
        project_id: ID do Knowledge Base (Project)
        configuration_id: ID opcional da Configuration para scoping

    Returns:
        Contagem de elementos no escopo
    """
    if configuration_id:
        return await Element.find(
            Element.project_id == project_id,
            {"excluded_from": {"$nin": [configuration_id]}}
        ).count()
    return await Element.find(
        Element.project_id == project_id
    ).count()


async def extract_connections_for_project(
    project_id: PydanticObjectId,
) -> list:
    """
    Extrai todas as conexoes do schema do projeto.

    Diferente de tabelas (que podem ser filtradas por Configuration),
    conexoes sao configuracoes de projeto inteiro. Retorna todas as
    conexoes definidas no arquivo .xdd da Analysis.

    Args:
        project_id: ID do Knowledge Base (Project)

    Returns:
        Lista de SchemaConnection objects (pode ser vazia se nao houver schema)
    """
    schema = await DatabaseSchema.find_one(
        DatabaseSchema.project_id == project_id
    )
    if not schema:
        return []
    return schema.connections or []


async def extract_global_state_for_project(
    project_id: PydanticObjectId,
) -> GlobalStateContext:
    """
    Extrai variaveis globais de Project Code e elementos WDG.

    Consulta elementos com windevType em [0, 31] e usa GlobalStateExtractor
    para parsear declaracoes GLOBAL do codigo WLanguage.

    Args:
        project_id: ID do Knowledge Base (Project)

    Returns:
        GlobalStateContext com todas as variaveis globais agregadas
    """
    extractor = GlobalStateExtractor()
    all_variables = []
    all_init_blocks = []

    # Query Project Code (type_code: 0) e WDG (type_code: 31)
    elements = await Element.find(
        Element.project_id == project_id,
        {"windev_type": {"$in": [0, 31]}}
    ).to_list()

    for elem in elements:
        if not elem.raw_content:
            continue

        # Extrai variaveis globais
        variables = extractor.extract_variables(
            elem.raw_content,
            elem.windev_type or 0,
            elem.source_name,
        )
        all_variables.extend(variables)

        # Extrai blocos de inicializacao (apenas de Project Code)
        if elem.windev_type == 0:
            init_blocks = extractor.extract_initialization(elem.raw_content)
            all_init_blocks.extend(init_blocks)

    return GlobalStateContext.from_extractor_results(
        variables=all_variables,
        initialization_blocks=all_init_blocks,
    )