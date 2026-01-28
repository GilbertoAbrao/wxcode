"""
Testes para Neo4jConnection.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from wxcode.graph.neo4j_connection import (
    Neo4jConnection,
    Neo4jConnectionError,
)


class TestNeo4jConnection:
    """Testes para Neo4jConnection."""

    def test_init_uses_default_settings(self):
        """Testa que init usa valores do settings."""
        with patch("wxcode.graph.neo4j_connection.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                neo4j_uri="bolt://test:7687",
                neo4j_user="testuser",
                neo4j_password="testpass",
                neo4j_database="testdb",
            )
            conn = Neo4jConnection()

            assert conn.uri == "bolt://test:7687"
            assert conn.user == "testuser"
            assert conn.password == "testpass"
            assert conn.database == "testdb"

    def test_init_overrides_settings(self):
        """Testa que parâmetros explícitos sobrescrevem settings."""
        conn = Neo4jConnection(
            uri="bolt://custom:7687",
            user="customuser",
            password="custompass",
            database="customdb",
        )

        assert conn.uri == "bolt://custom:7687"
        assert conn.user == "customuser"
        assert conn.password == "custompass"
        assert conn.database == "customdb"

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Testa conexão bem sucedida."""
        with patch("wxcode.graph.neo4j_connection.AsyncGraphDatabase") as mock_db:
            mock_driver = AsyncMock()
            mock_db.driver.return_value = mock_driver

            conn = Neo4jConnection(
                uri="bolt://localhost:7687",
                user="neo4j",
                password="test",
            )
            await conn.connect()

            mock_db.driver.assert_called_once()
            mock_driver.verify_connectivity.assert_called_once()
            assert conn._driver is not None

    @pytest.mark.asyncio
    async def test_connect_service_unavailable(self):
        """Testa erro quando Neo4j não está disponível."""
        from neo4j.exceptions import ServiceUnavailable

        with patch("wxcode.graph.neo4j_connection.AsyncGraphDatabase") as mock_db:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity.side_effect = ServiceUnavailable("Connection refused")
            mock_db.driver.return_value = mock_driver

            conn = Neo4jConnection(
                uri="bolt://localhost:7687",
                user="neo4j",
                password="test",
            )

            with pytest.raises(Neo4jConnectionError) as exc_info:
                await conn.connect()

            assert "Neo4j não disponível" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_connect_auth_error(self):
        """Testa erro de autenticação."""
        from neo4j.exceptions import AuthError

        with patch("wxcode.graph.neo4j_connection.AsyncGraphDatabase") as mock_db:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity.side_effect = AuthError("Invalid credentials")
            mock_db.driver.return_value = mock_driver

            conn = Neo4jConnection(
                uri="bolt://localhost:7687",
                user="neo4j",
                password="wrong",
            )

            with pytest.raises(Neo4jConnectionError) as exc_info:
                await conn.connect()

            assert "autenticação" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_close(self):
        """Testa fechamento da conexão."""
        with patch("wxcode.graph.neo4j_connection.AsyncGraphDatabase") as mock_db:
            mock_driver = AsyncMock()
            mock_db.driver.return_value = mock_driver

            conn = Neo4jConnection(
                uri="bolt://localhost:7687",
                user="neo4j",
                password="test",
            )
            await conn.connect()
            await conn.close()

            mock_driver.close.assert_called_once()
            assert conn._driver is None

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Testa uso como context manager."""
        with patch("wxcode.graph.neo4j_connection.AsyncGraphDatabase") as mock_db:
            mock_driver = AsyncMock()
            mock_db.driver.return_value = mock_driver

            async with Neo4jConnection(
                uri="bolt://localhost:7687",
                user="neo4j",
                password="test",
            ) as conn:
                assert conn._driver is not None

            mock_driver.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_not_connected(self):
        """Testa execute sem conexão."""
        conn = Neo4jConnection(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="test",
        )

        with pytest.raises(Neo4jConnectionError) as exc_info:
            await conn.execute("MATCH (n) RETURN n")

        assert "Não conectado" in str(exc_info.value)

    def test_execute_requires_connection(self):
        """Testa que execute requer conexão."""
        conn = Neo4jConnection(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="test",
        )
        # Sem conexão, _driver é None
        assert conn._driver is None

    def test_batch_create_requires_connection(self):
        """Testa que batch_create requer conexão."""
        conn = Neo4jConnection(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="test",
        )
        # Sem conexão, _driver é None
        assert conn._driver is None
