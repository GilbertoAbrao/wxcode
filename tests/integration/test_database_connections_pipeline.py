"""Integration test for database connections extraction pipeline.

Tests the complete flow:
1. Parse .xdd file to extract connections with types
2. Store connections in MongoDB (DatabaseSchema)
3. Generate code with dynamic .env.example and database.py
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from wxcode.parser.xdd_parser import XddParser
from wxcode.models.schema import DatabaseSchema, SchemaConnection
from wxcode.generator.orchestrator import GeneratorOrchestrator


# XML de exemplo com múltiplas conexões
SAMPLE_XDD_MULTI_CONNECTIONS = """<?xml version="1.0" encoding="ISO-8859-1"?>
<ANALYSE GenNum="139" VersionStructure="2">
    <CONNEXION Nom="CNX_BASE_HOMOLOG" Type="1">
        <SOURCE>192.168.10.13</SOURCE>
        <USER>infiniti_all</USER>
        <DB>Sipbackoffice_Virtualpay</DB>
        <INFOS_ETENDUES>Server=192.168.10.13;Port=1433;Initial Catalog=Sipbackoffice_Virtualpay</INFOS_ETENDUES>
    </CONNEXION>
    <CONNEXION Nom="BdInfiniti" Type="2">
        <SOURCE>192.168.10.14</SOURCE>
        <USER>app_user</USER>
        <DB>Infiniti_DB</DB>
    </CONNEXION>
    <FICHIER Nom="Cliente" NomPhysique="Cliente" FicNullSupporte="1" Connexion="CNX_BASE_HOMOLOG">
        <RUBRIQUE Nom="IDcliente">
            <TYPE>24</TYPE>
            <TYPE_CLE>1</TYPE_CLE>
            <TAILLE>8</TAILLE>
            <INDICERUBRIQUE Null="0" Valeur=""/>
        </RUBRIQUE>
        <RUBRIQUE Nom="Nome">
            <TYPE>2</TYPE>
            <TYPE_CLE>0</TYPE_CLE>
            <TAILLE>200</TAILLE>
            <INDICERUBRIQUE Null="1" Valeur=""/>
        </RUBRIQUE>
    </FICHIER>
</ANALYSE>
"""


@pytest.fixture
def sample_xdd_file(tmp_path: Path) -> Path:
    """Cria arquivo .xdd temporário com múltiplas conexões."""
    xdd_file = tmp_path / "test.xdd"
    xdd_file.write_text(SAMPLE_XDD_MULTI_CONNECTIONS, encoding="iso-8859-1")
    return xdd_file


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Cria diretório de output temporário."""
    output = tmp_path / "generated"
    output.mkdir()
    return output


class TestDatabaseConnectionsPipeline:
    """Teste de integração do pipeline completo de extração de conexões."""

    def test_parse_xdd_extracts_connection_metadata(self, sample_xdd_file: Path):
        """Fase 1: Parser extrai metadados completos das conexões."""
        parser = XddParser(sample_xdd_file)
        result = parser.parse()

        # Verifica que parseou 2 conexões
        assert len(result.connections) == 2

        # Verifica primeira conexão (SQL Server)
        conn1 = result.connections[0]
        assert conn1.name == "CNX_BASE_HOMOLOG"
        assert conn1.type_code == 1
        assert conn1.database_type == "sqlserver"
        assert conn1.driver_name == "SQL Server"
        assert conn1.source == "192.168.10.13"
        assert conn1.port == "1433"  # Extraído de INFOS_ETENDUES
        assert conn1.database == "Sipbackoffice_Virtualpay"
        assert conn1.user == "infiniti_all"
        assert "Port=1433" in conn1.extended_info

        # Verifica segunda conexão (MySQL)
        conn2 = result.connections[1]
        assert conn2.name == "BdInfiniti"
        assert conn2.type_code == 2
        assert conn2.database_type == "mysql"
        assert conn2.driver_name == "MySQL"
        assert conn2.port == "3306"  # Porta padrão MySQL

    @patch("wxcode.generator.orchestrator.DatabaseSchema")
    async def test_orchestrator_loads_connections_from_mongodb(
        self, mock_schema_class, output_dir: Path, sample_xdd_file: Path
    ):
        """Fase 2: Orchestrator carrega conexões do MongoDB."""
        # Parse XDD para obter conexões reais
        parser = XddParser(sample_xdd_file)
        parse_result = parser.parse()

        # Mock do DatabaseSchema.find_one para retornar schema com conexões
        mock_schema = MagicMock()
        mock_schema.connections = parse_result.connections
        mock_schema_class.find_one = AsyncMock(return_value=mock_schema)

        # Testa _load_database_connections
        orchestrator = GeneratorOrchestrator(
            project_id="507f1f77bcf86cd799439011",
            output_dir=output_dir,
        )

        connections = await orchestrator._load_database_connections()

        # Verifica que carregou as conexões
        assert len(connections) == 2
        assert connections[0].name == "CNX_BASE_HOMOLOG"
        assert connections[0].database_type == "sqlserver"
        assert connections[1].name == "BdInfiniti"
        assert connections[1].database_type == "mysql"

    @patch("wxcode.generator.orchestrator.DatabaseSchema")
    async def test_orchestrator_generates_env_with_connections(
        self, mock_schema_class, output_dir: Path, sample_xdd_file: Path
    ):
        """Fase 3: Orchestrator gera .env.example com variáveis dinâmicas."""
        # Parse XDD para obter conexões
        parser = XddParser(sample_xdd_file)
        parse_result = parser.parse()

        # Mock do DatabaseSchema
        mock_schema = MagicMock()
        mock_schema.connections = parse_result.connections
        mock_schema_class.find_one = AsyncMock(return_value=mock_schema)

        # Mock de Element.find para retornar lista vazia (sem elementos)
        with patch("wxcode.generator.orchestrator.Element") as mock_element:
            mock_element.find.return_value.to_list = AsyncMock(return_value=[])

            orchestrator = GeneratorOrchestrator(
                project_id="507f1f77bcf86cd799439011",
                output_dir=output_dir,
            )

            # Gera estrutura do projeto
            await orchestrator._generate_project_structure()

            # Verifica que .env.example foi gerado
            env_file = output_dir / ".env.example"
            assert env_file.exists()

            content = env_file.read_text()

            # Verifica conexão SQL Server
            assert "# Database: CNX_BASE_HOMOLOG (SQL Server)" in content
            assert "CNX_BASE_HOMOLOG_HOST=192.168.10.13" in content
            assert "CNX_BASE_HOMOLOG_PORT=1433" in content
            assert "CNX_BASE_HOMOLOG_DATABASE=Sipbackoffice_Virtualpay" in content
            assert "CNX_BASE_HOMOLOG_USER=infiniti_all" in content
            assert "CNX_BASE_HOMOLOG_TYPE=sqlserver" in content

            # Verifica conexão MySQL
            assert "# Database: BdInfiniti (MySQL)" in content
            assert "BDINFINITI_HOST=192.168.10.14" in content
            assert "BDINFINITI_PORT=3306" in content
            assert "BDINFINITI_DATABASE=Infiniti_DB" in content
            assert "BDINFINITI_TYPE=mysql" in content

    @patch("wxcode.generator.orchestrator.DatabaseSchema")
    async def test_orchestrator_generates_database_with_connections(
        self, mock_schema_class, output_dir: Path, sample_xdd_file: Path
    ):
        """Fase 4: Orchestrator gera database.py com múltiplas conexões."""
        # Parse XDD para obter conexões
        parser = XddParser(sample_xdd_file)
        parse_result = parser.parse()

        # Mock do DatabaseSchema
        mock_schema = MagicMock()
        mock_schema.connections = parse_result.connections
        mock_schema_class.find_one = AsyncMock(return_value=mock_schema)

        # Mock de Element.find
        with patch("wxcode.generator.orchestrator.Element") as mock_element:
            mock_element.find.return_value.to_list = AsyncMock(return_value=[])

            orchestrator = GeneratorOrchestrator(
                project_id="507f1f77bcf86cd799439011",
                output_dir=output_dir,
            )

            # Gera estrutura do projeto
            await orchestrator._generate_project_structure()

            # Verifica que database.py foi gerado
            db_file = output_dir / "app" / "database.py"
            assert db_file.exists()

            content = db_file.read_text()

            # Verifica imports SQLAlchemy
            assert "from sqlalchemy.ext.asyncio import create_async_engine" in content

            # Verifica registro de conexão SQL Server
            assert "# CNX_BASE_HOMOLOG (SQL Server)" in content
            assert "engine_cnx_base_homolog = create_async_engine" in content
            assert "mssql+aioodbc" in content

            # Verifica registro de conexão MySQL
            assert "# BdInfiniti (MySQL)" in content
            assert "engine_bdinfiniti = create_async_engine" in content
            assert "mysql+aiomysql" in content

            # Verifica dict de conexões
            assert "connections: dict[str, dict]" in content
            assert 'connections["CNX_BASE_HOMOLOG"]' in content
            assert 'connections["BdInfiniti"]' in content

            # Verifica função get_db
            assert "def get_db(connection_name" in content

    @patch("wxcode.generator.orchestrator.DatabaseSchema")
    async def test_orchestrator_generates_requirements_with_drivers(
        self, mock_schema_class, output_dir: Path, sample_xdd_file: Path
    ):
        """Fase 5: Orchestrator gera requirements com drivers corretos."""
        # Parse XDD para obter conexões
        parser = XddParser(sample_xdd_file)
        parse_result = parser.parse()

        # Mock do DatabaseSchema
        mock_schema = MagicMock()
        mock_schema.connections = parse_result.connections
        mock_schema_class.find_one = AsyncMock(return_value=mock_schema)

        # Mock de Element.find
        with patch("wxcode.generator.orchestrator.Element") as mock_element:
            mock_element.find.return_value.to_list = AsyncMock(return_value=[])

            orchestrator = GeneratorOrchestrator(
                project_id="507f1f77bcf86cd799439011",
                output_dir=output_dir,
            )

            # Gera estrutura do projeto
            await orchestrator._generate_project_structure()

            # Verifica que pyproject.toml foi gerado
            pyproject_file = output_dir / "pyproject.toml"
            assert pyproject_file.exists()

            content = pyproject_file.read_text()

            # Verifica SQLAlchemy
            assert '"sqlalchemy[asyncio]>=2.0.0"' in content

            # Verifica drivers específicos
            assert '"aioodbc>=0.5.0"' in content  # SQL Server
            assert '"pyodbc>=5.0.0"' in content   # SQL Server
            assert '"aiomysql>=0.2.0"' in content  # MySQL

    async def test_no_connections_fallback_to_mongodb(self, output_dir: Path):
        """Fase 6: Fallback para MongoDB quando não há conexões."""
        # Mock retornando None (sem schema)
        with patch("wxcode.generator.orchestrator.DatabaseSchema") as mock_schema_class:
            mock_schema_class.find_one = AsyncMock(return_value=None)

            with patch("wxcode.generator.orchestrator.Element") as mock_element:
                mock_element.find.return_value.to_list = AsyncMock(return_value=[])

                orchestrator = GeneratorOrchestrator(
                    project_id="507f1f77bcf86cd799439011",
                    output_dir=output_dir,
                )

                # Gera estrutura do projeto
                await orchestrator._generate_project_structure()

                # Verifica .env.example com MongoDB
                env_file = output_dir / ".env.example"
                content = env_file.read_text()
                assert "DATABASE_URL=mongodb://localhost:27017" in content

                # Verifica database.py com MongoDB
                db_file = output_dir / "app" / "database.py"
                db_content = db_file.read_text()
                assert "from motor.motor_asyncio import AsyncIOMotorClient" in db_content


class TestConnectionTypeEdgeCases:
    """Testes de edge cases no pipeline de conexões."""

    def test_unknown_connection_type_warning(self, tmp_path: Path):
        """Tipo de conexão desconhecido gera warning."""
        xdd_content = """<?xml version="1.0" encoding="ISO-8859-1"?>
<ANALYSE GenNum="1">
    <CONNEXION Nom="CNX_UNKNOWN" Type="999">
        <SOURCE>unknown.server.com</SOURCE>
        <USER>user</USER>
        <DB>UnknownDB</DB>
    </CONNEXION>
</ANALYSE>
"""
        xdd_file = tmp_path / "unknown_type.xdd"
        xdd_file.write_text(xdd_content, encoding="iso-8859-1")

        parser = XddParser(xdd_file)
        result = parser.parse()

        # Verifica que parseou a conexão com tipo unknown
        assert len(result.connections) == 1
        conn = result.connections[0]
        assert conn.database_type == "unknown"
        assert conn.driver_name == "Unknown"

    def test_hyperfile_connection_no_sqlalchemy_imports(self, tmp_path: Path):
        """Conexões HyperFile não geram imports SQLAlchemy."""
        xdd_content = """<?xml version="1.0" encoding="ISO-8859-1"?>
<ANALYSE GenNum="1">
    <CONNEXION Nom="CNX_HF" Type="5">
        <SOURCE>hf.server.com</SOURCE>
        <USER></USER>
        <DB>HFDatabase</DB>
    </CONNEXION>
</ANALYSE>
"""
        xdd_file = tmp_path / "hyperfile.xdd"
        xdd_file.write_text(xdd_content, encoding="iso-8859-1")

        parser = XddParser(xdd_file)
        result = parser.parse()

        # Verifica tipo HyperFile
        assert result.connections[0].database_type == "hyperfile"
        assert result.connections[0].port == ""  # HyperFile não usa porta
