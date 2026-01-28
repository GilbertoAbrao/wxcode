"""
Gerenciamento de conexão com Neo4j.
"""

from typing import Any, Optional
import logging

from neo4j import GraphDatabase, AsyncGraphDatabase
from neo4j.exceptions import (
    ServiceUnavailable,
    AuthError,
    Neo4jError,
)

from wxcode.config import get_settings

logger = logging.getLogger(__name__)


class Neo4jConnectionError(Exception):
    """Erro de conexão com Neo4j."""

    pass


class Neo4jConnection:
    """
    Gerencia conexão com Neo4j.

    Configuração via settings ou environment:
    - NEO4J_URI: bolt://localhost:7687
    - NEO4J_USER: neo4j
    - NEO4J_PASSWORD: ****
    - NEO4J_DATABASE: neo4j

    Uso:
        async with Neo4jConnection() as conn:
            result = await conn.execute("MATCH (n) RETURN count(n)")
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        """
        Inicializa conexão com Neo4j.

        Args:
            uri: URI do Neo4j (bolt://localhost:7687)
            user: Usuário
            password: Senha
            database: Nome do banco de dados
        """
        settings = get_settings()
        self.uri = uri or settings.neo4j_uri
        self.user = user or settings.neo4j_user
        self.password = password or settings.neo4j_password
        self.database = database or settings.neo4j_database
        self._driver = None

    async def __aenter__(self) -> "Neo4jConnection":
        """Abre conexão ao entrar no context manager."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Fecha conexão ao sair do context manager."""
        await self.close()

    async def connect(self) -> None:
        """
        Estabelece conexão com Neo4j.

        Raises:
            Neo4jConnectionError: Se não conseguir conectar
        """
        try:
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_pool_size=50,
                connection_acquisition_timeout=60,
            )
            # Verifica conectividade
            await self._driver.verify_connectivity()
            logger.info(f"Conectado ao Neo4j em {self.uri}")
        except ServiceUnavailable as e:
            raise Neo4jConnectionError(
                f"Neo4j não disponível em {self.uri}. "
                "Verifique se o Neo4j está rodando.\n"
                "Para iniciar: docker run -p 7474:7474 -p 7687:7687 neo4j:5"
            ) from e
        except AuthError as e:
            raise Neo4jConnectionError(
                f"Falha de autenticação no Neo4j. "
                "Verifique NEO4J_USER e NEO4J_PASSWORD."
            ) from e
        except Exception as e:
            raise Neo4jConnectionError(f"Erro ao conectar ao Neo4j: {e}") from e

    async def close(self) -> None:
        """Fecha conexão com Neo4j."""
        if self._driver:
            await self._driver.close()
            self._driver = None
            logger.info("Conexão Neo4j fechada")

    async def execute(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """
        Executa query Cypher.

        Args:
            query: Query Cypher
            parameters: Parâmetros da query

        Returns:
            Lista de registros como dicts

        Raises:
            Neo4jConnectionError: Se não estiver conectado
            Neo4jError: Se query falhar
        """
        if not self._driver:
            raise Neo4jConnectionError("Não conectado ao Neo4j")

        async with self._driver.session(database=self.database) as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records

    async def execute_write(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Executa query de escrita (CREATE, MERGE, DELETE).

        Args:
            query: Query Cypher
            parameters: Parâmetros da query

        Returns:
            Resumo da execução (counters)

        Raises:
            Neo4jConnectionError: Se não estiver conectado
        """
        if not self._driver:
            raise Neo4jConnectionError("Não conectado ao Neo4j")

        async with self._driver.session(database=self.database) as session:
            result = await session.run(query, parameters or {})
            summary = await result.consume()
            return {
                "nodes_created": summary.counters.nodes_created,
                "nodes_deleted": summary.counters.nodes_deleted,
                "relationships_created": summary.counters.relationships_created,
                "relationships_deleted": summary.counters.relationships_deleted,
                "properties_set": summary.counters.properties_set,
            }

    async def batch_create(
        self,
        items: list[dict[str, Any]],
        query: str,
        batch_size: int = 1000,
    ) -> int:
        """
        Cria itens em batch para performance.

        Args:
            items: Lista de dicts com dados dos itens
            query: Query Cypher usando UNWIND $items
            batch_size: Tamanho do batch (default: 1000)

        Returns:
            Total de nós/relacionamentos criados

        Example:
            query = '''
            UNWIND $items as item
            CREATE (n:Node {name: item.name})
            '''
            count = await conn.batch_create(nodes, query)
        """
        if not self._driver:
            raise Neo4jConnectionError("Não conectado ao Neo4j")

        total_created = 0

        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            async with self._driver.session(database=self.database) as session:
                result = await session.run(query, {"items": batch})
                summary = await result.consume()
                total_created += (
                    summary.counters.nodes_created
                    + summary.counters.relationships_created
                )

            logger.debug(
                f"Batch {i // batch_size + 1}: "
                f"{len(batch)} items processados"
            )

        return total_created

    async def clear_project(self, project_name: str) -> int:
        """
        Remove todos os nós de um projeto.

        Args:
            project_name: Nome do projeto

        Returns:
            Número de nós removidos
        """
        query = """
        MATCH (n {project: $project})
        DETACH DELETE n
        RETURN count(n) as deleted
        """
        result = await self.execute(query, {"project": project_name})
        deleted = result[0]["deleted"] if result else 0
        logger.info(f"Removidos {deleted} nós do projeto {project_name}")
        return deleted

    async def create_indexes(self) -> None:
        """
        Cria indexes para queries frequentes.
        """
        indexes = [
            "CREATE INDEX node_name_table IF NOT EXISTS FOR (n:Table) ON (n.name)",
            "CREATE INDEX node_name_class IF NOT EXISTS FOR (n:Class) ON (n.name)",
            "CREATE INDEX node_name_procedure IF NOT EXISTS FOR (n:Procedure) ON (n.name)",
            "CREATE INDEX node_name_page IF NOT EXISTS FOR (n:Page) ON (n.name)",
            "CREATE INDEX node_name_window IF NOT EXISTS FOR (n:Window) ON (n.name)",
            "CREATE INDEX node_name_query IF NOT EXISTS FOR (n:Query) ON (n.name)",
            "CREATE INDEX node_project IF NOT EXISTS FOR (n:Table) ON (n.project)",
        ]

        for index_query in indexes:
            try:
                await self.execute_write(index_query)
            except Neo4jError as e:
                # Ignora se index já existe
                if "equivalent index" not in str(e).lower():
                    logger.warning(f"Erro ao criar index: {e}")

        logger.info("Indexes criados/verificados")

    async def get_stats(self) -> dict[str, int]:
        """
        Retorna estatísticas do banco.

        Returns:
            Dict com contagens por label
        """
        query = """
        CALL db.labels() YIELD label
        CALL {
            WITH label
            MATCH (n)
            WHERE label IN labels(n)
            RETURN count(n) as count
        }
        RETURN label, count
        ORDER BY count DESC
        """
        result = await self.execute(query)
        return {r["label"]: r["count"] for r in result}
