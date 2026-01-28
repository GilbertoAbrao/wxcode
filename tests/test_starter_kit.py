"""Tests for StarterKitGenerator.

Tests dynamic generation of .env.example, requirements.txt, and database.py
based on database connections from the schema.
"""

import tempfile
from pathlib import Path
from dataclasses import dataclass

import pytest

from wxcode.generator.starter_kit import (
    StarterKitGenerator,
    StarterKitConfig,
    StarterKitResult,
)


# Mock SchemaConnection para testes
@dataclass
class MockSchemaConnection:
    """Mock de SchemaConnection para testes."""
    name: str
    type_code: int
    database_type: str
    driver_name: str
    source: str
    port: str
    database: str
    user: str
    extended_info: str = ""


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    """Cria diretório temporário para output."""
    output_dir = tmp_path / "generated"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sqlserver_connection() -> MockSchemaConnection:
    """Mock de conexão SQL Server."""
    return MockSchemaConnection(
        name="CNX_BASE_HOMOLOG",
        type_code=1,
        database_type="sqlserver",
        driver_name="SQL Server",
        source="192.168.10.13",
        port="1433",
        database="Sipbackoffice_Virtualpay",
        user="infiniti_all",
    )


@pytest.fixture
def mysql_connection() -> MockSchemaConnection:
    """Mock de conexão MySQL."""
    return MockSchemaConnection(
        name="BdInfiniti",
        type_code=2,
        database_type="mysql",
        driver_name="MySQL",
        source="192.168.10.14",
        port="3306",
        database="Infiniti_DB",
        user="app_user",
    )


@pytest.fixture
def postgresql_connection() -> MockSchemaConnection:
    """Mock de conexão PostgreSQL."""
    return MockSchemaConnection(
        name="CNX_POSTGRES",
        type_code=3,
        database_type="postgresql",
        driver_name="PostgreSQL",
        source="localhost",
        port="5432",
        database="myapp",
        user="postgres",
    )


class TestGenerateEnvExample:
    """Testes de geração do .env.example."""

    def test_generate_env_single_connection(self, tmp_output_dir: Path, sqlserver_connection: MockSchemaConnection):
        """Gera .env.example com uma única conexão."""
        config = StarterKitConfig(
            project_name="TestApp",
            connections=[sqlserver_connection],
        )
        generator = StarterKitGenerator(tmp_output_dir, config)
        generator._generate_env_example()

        env_file = tmp_output_dir / ".env.example"
        assert env_file.exists()

        content = env_file.read_text()

        # Verifica cabeçalho da aplicação
        assert "APP_NAME=TestApp" in content
        assert "DEBUG=false" in content

        # Verifica variáveis da conexão
        assert "# Database: CNX_BASE_HOMOLOG (SQL Server)" in content
        assert "CNX_BASE_HOMOLOG_HOST=192.168.10.13" in content
        assert "CNX_BASE_HOMOLOG_PORT=1433" in content
        assert "CNX_BASE_HOMOLOG_DATABASE=Sipbackoffice_Virtualpay" in content
        assert "CNX_BASE_HOMOLOG_USER=infiniti_all" in content
        assert "CNX_BASE_HOMOLOG_PASSWORD=" in content
        assert "CNX_BASE_HOMOLOG_TYPE=sqlserver" in content

        # Verifica secret key
        assert "SECRET_KEY=change-me-in-production" in content

    def test_generate_env_multiple_connections(
        self,
        tmp_output_dir: Path,
        sqlserver_connection: MockSchemaConnection,
        mysql_connection: MockSchemaConnection,
        postgresql_connection: MockSchemaConnection,
    ):
        """Gera .env.example com múltiplas conexões."""
        config = StarterKitConfig(
            project_name="MultiDBApp",
            connections=[sqlserver_connection, mysql_connection, postgresql_connection],
        )
        generator = StarterKitGenerator(tmp_output_dir, config)
        generator._generate_env_example()

        env_file = tmp_output_dir / ".env.example"
        content = env_file.read_text()

        # Verifica conexão SQL Server
        assert "CNX_BASE_HOMOLOG_HOST=192.168.10.13" in content
        assert "CNX_BASE_HOMOLOG_TYPE=sqlserver" in content

        # Verifica conexão MySQL
        assert "BDINFINITI_HOST=192.168.10.14" in content
        assert "BDINFINITI_PORT=3306" in content
        assert "BDINFINITI_TYPE=mysql" in content

        # Verifica conexão PostgreSQL
        assert "CNX_POSTGRES_HOST=localhost" in content
        assert "CNX_POSTGRES_PORT=5432" in content
        assert "CNX_POSTGRES_TYPE=postgresql" in content

    def test_generate_env_no_connections_fallback(self, tmp_output_dir: Path):
        """Gera .env.example padrão quando não há conexões."""
        config = StarterKitConfig(
            project_name="DefaultApp",
            use_mongodb=True,
        )
        generator = StarterKitGenerator(tmp_output_dir, config)
        generator._generate_env_example()

        env_file = tmp_output_dir / ".env.example"
        content = env_file.read_text()

        # Verifica fallback para MongoDB
        assert "DATABASE_URL=mongodb://localhost:27017" in content
        assert "DATABASE_NAME=DefaultApp_db" in content


class TestGenerateRequirementsTxt:
    """Testes de geração do requirements.txt."""

    def test_generate_requirements_with_sqlserver_driver(
        self, tmp_output_dir: Path, sqlserver_connection: MockSchemaConnection
    ):
        """Inclui drivers SQL Server no requirements.txt."""
        config = StarterKitConfig(
            project_name="TestApp",
            connections=[sqlserver_connection],
        )
        generator = StarterKitGenerator(tmp_output_dir, config)
        generator._generate_requirements_txt()

        req_file = tmp_output_dir / "requirements.txt"
        content = req_file.read_text()

        # Verifica SQLAlchemy
        assert "sqlalchemy[asyncio]>=2.0.0" in content

        # Verifica drivers SQL Server
        assert "aioodbc>=0.5.0" in content
        assert "pyodbc>=5.0.0" in content

    def test_generate_requirements_with_multiple_drivers(
        self,
        tmp_output_dir: Path,
        sqlserver_connection: MockSchemaConnection,
        mysql_connection: MockSchemaConnection,
        postgresql_connection: MockSchemaConnection,
    ):
        """Inclui drivers para múltiplos bancos."""
        config = StarterKitConfig(
            project_name="MultiDBApp",
            connections=[sqlserver_connection, mysql_connection, postgresql_connection],
        )
        generator = StarterKitGenerator(tmp_output_dir, config)
        generator._generate_requirements_txt()

        req_file = tmp_output_dir / "requirements.txt"
        content = req_file.read_text()

        # Verifica SQLAlchemy (comum)
        assert "sqlalchemy[asyncio]>=2.0.0" in content

        # Verifica drivers específicos
        assert "aioodbc>=0.5.0" in content
        assert "pyodbc>=5.0.0" in content
        assert "aiomysql>=0.2.0" in content
        assert "asyncpg>=0.29.0" in content

        # Verifica que não há duplicação de SQLAlchemy
        assert content.count("sqlalchemy[asyncio]") == 1

    def test_generate_requirements_no_connections_fallback(self, tmp_output_dir: Path):
        """Gera requirements.txt padrão quando não há conexões."""
        config = StarterKitConfig(
            project_name="DefaultApp",
            use_mongodb=True,
        )
        generator = StarterKitGenerator(tmp_output_dir, config)
        generator._generate_requirements_txt()

        req_file = tmp_output_dir / "requirements.txt"
        content = req_file.read_text()

        # Verifica fallback para MongoDB
        assert "motor>=3.3.0" in content
        assert "beanie>=1.25.0" in content


class TestGenerateDatabasePy:
    """Testes de geração do database.py."""

    def test_generate_database_single_connection(
        self, tmp_output_dir: Path, sqlserver_connection: MockSchemaConnection
    ):
        """Gera database.py com uma única conexão."""
        config = StarterKitConfig(
            project_name="TestApp",
            connections=[sqlserver_connection],
        )
        generator = StarterKitGenerator(tmp_output_dir, config)
        generator._generate_database_py()

        db_file = tmp_output_dir / "app" / "database.py"
        assert db_file.exists()

        content = db_file.read_text()

        # Verifica imports
        assert "from sqlalchemy.ext.asyncio import create_async_engine" in content
        assert "from sqlalchemy.orm import sessionmaker" in content

        # Verifica registro de conexão
        assert "# CNX_BASE_HOMOLOG (SQL Server)" in content
        assert "engine_cnx_base_homolog = create_async_engine" in content
        assert "mssql+aioodbc" in content
        assert 'connections["CNX_BASE_HOMOLOG"]' in content

        # Verifica função get_db
        assert "def get_db(connection_name" in content

    def test_generate_database_multiconn(
        self,
        tmp_output_dir: Path,
        sqlserver_connection: MockSchemaConnection,
        mysql_connection: MockSchemaConnection,
    ):
        """Gera database.py com múltiplas conexões."""
        config = StarterKitConfig(
            project_name="MultiDBApp",
            connections=[sqlserver_connection, mysql_connection],
        )
        generator = StarterKitGenerator(tmp_output_dir, config)
        generator._generate_database_py()

        db_file = tmp_output_dir / "app" / "database.py"
        content = db_file.read_text()

        # Verifica ambas conexões
        assert "# CNX_BASE_HOMOLOG (SQL Server)" in content
        assert "# BdInfiniti (MySQL)" in content

        # Verifica engines
        assert "engine_cnx_base_homolog" in content
        assert "engine_bdinfiniti" in content

        # Verifica drivers corretos
        assert "mssql+aioodbc" in content
        assert "mysql+aiomysql" in content

        # Verifica dict de conexões
        assert "connections: dict[str, dict]" in content

    def test_generate_database_no_connections_mongodb_fallback(self, tmp_output_dir: Path):
        """Gera database.py padrão MongoDB quando não há conexões."""
        config = StarterKitConfig(
            project_name="DefaultApp",
            use_mongodb=True,
        )
        generator = StarterKitGenerator(tmp_output_dir, config)
        generator._generate_database_py()

        db_file = tmp_output_dir / "app" / "database.py"
        content = db_file.read_text()

        # Verifica imports MongoDB
        assert "from motor.motor_asyncio import AsyncIOMotorClient" in content

        # Verifica não tem SQLAlchemy
        assert "sqlalchemy" not in content.lower()

    def test_generate_database_hyperfile_connection_commented(self, tmp_output_dir: Path):
        """Gera comentário para conexões HyperFile (não suportadas)."""
        hyperfile_conn = MockSchemaConnection(
            name="CNX_HF",
            type_code=5,
            database_type="hyperfile",
            driver_name="HyperFile Classic",
            source="hf.server.com",
            port="",
            database="HFDatabase",
            user="",
        )

        config = StarterKitConfig(
            project_name="HFApp",
            connections=[hyperfile_conn],
        )
        generator = StarterKitGenerator(tmp_output_dir, config)
        generator._generate_database_py()

        db_file = tmp_output_dir / "app" / "database.py"
        content = db_file.read_text()

        # Verifica comentário de HyperFile
        assert "# CNX_HF (HyperFile Classic)" in content
        assert "# HyperFile connections not yet supported" in content


class TestGenerateConfigPy:
    """Testes para geração de config.py com conexões."""

    def test_generate_config_with_single_connection(
        self, tmp_output_dir: Path, sqlserver_connection: MockSchemaConnection
    ):
        """Config.py deve incluir campos para conexão única."""
        config = StarterKitConfig(
            project_name="TestApp",
            connections=[sqlserver_connection],
        )
        generator = StarterKitGenerator(tmp_output_dir, config)
        generator._generate_config_py()

        config_file = tmp_output_dir / "app" / "config.py"
        content = config_file.read_text()

        # Verifica campos da conexão
        assert "cnx_base_homolog_host: str" in content
        assert "cnx_base_homolog_port: str" in content
        assert "cnx_base_homolog_database: str" in content
        assert "cnx_base_homolog_user: str" in content
        assert "cnx_base_homolog_password: str" in content
        # Verifica valores default
        assert '"192.168.10.13"' in content
        assert '"1433"' in content
        assert '"Sipbackoffice_Virtualpay"' in content

    def test_generate_config_with_multiple_connections(
        self, tmp_output_dir: Path, sqlserver_connection: MockSchemaConnection
    ):
        """Config.py deve incluir campos para múltiplas conexões."""
        mysql_conn = MockSchemaConnection(
            name="CNX_LOG",
            type_code=2,
            database_type="mysql",
            driver_name="MySQL",
            source="mysql.server.com",
            port="3306",
            database="LogDB",
            user="log_user",
        )

        config = StarterKitConfig(
            project_name="TestApp",
            connections=[sqlserver_connection, mysql_conn],
        )
        generator = StarterKitGenerator(tmp_output_dir, config)
        generator._generate_config_py()

        config_file = tmp_output_dir / "app" / "config.py"
        content = config_file.read_text()

        # Verifica campos de ambas as conexões
        assert "cnx_base_homolog_host: str" in content
        assert "cnx_log_host: str" in content
        assert "cnx_log_port: str" in content
        assert '"mysql.server.com"' in content
        assert '"3306"' in content

    def test_generate_config_no_connections_fallback(self, tmp_output_dir: Path):
        """Sem conexões, config.py usa fallback MongoDB."""
        config = StarterKitConfig(
            project_name="TestApp",
            use_mongodb=True,
        )
        generator = StarterKitGenerator(tmp_output_dir, config)
        generator._generate_config_py()

        config_file = tmp_output_dir / "app" / "config.py"
        content = config_file.read_text()

        # Verifica fallback para MongoDB
        assert "database_url: str = 'mongodb://localhost:27017'" in content
        assert "database_name: str" in content


class TestStarterKitConfig:
    """Testes da classe StarterKitConfig."""

    def test_config_with_connections(self, sqlserver_connection: MockSchemaConnection):
        """Config aceita lista de conexões."""
        config = StarterKitConfig(
            project_name="TestApp",
            connections=[sqlserver_connection],
        )

        assert len(config.connections) == 1
        assert config.connections[0].name == "CNX_BASE_HOMOLOG"

    def test_config_default_empty_connections(self):
        """Config tem lista vazia de conexões por padrão."""
        config = StarterKitConfig(project_name="TestApp")

        assert config.connections == []


class TestStarterKitResult:
    """Testes da classe StarterKitResult."""

    def test_result_summary(self, tmp_output_dir: Path):
        """Summary contém informações corretas."""
        result = StarterKitResult(
            output_dir=tmp_output_dir,
            files_created=["app/main.py", "app/config.py"],
            directories_created=["app", "tests"],
        )

        summary = result.summary()

        assert str(tmp_output_dir) in summary
        assert "Directories: 2" in summary
        assert "Files: 2" in summary
