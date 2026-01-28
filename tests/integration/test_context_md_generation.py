"""Integration tests for complete CONTEXT.md generation.

Tests the complete flow from extractors to CONTEXT.md generation,
ensuring all sections present and token budget maintained.
"""

from dataclasses import dataclass, field
from enum import Enum
from unittest.mock import MagicMock

import pytest
import tiktoken

from wxcode.services.prompt_builder import PromptBuilder


# Mock Scope enum (matches parser/global_state_extractor.py)
class MockScope(Enum):
    APP = "app"
    MODULE = "module"
    REQUEST = "request"


@dataclass
class MockSchemaConnection:
    """Mock for SchemaConnection without MongoDB dependency."""

    name: str
    type_code: int
    database_type: str
    driver_name: str
    source: str
    port: str
    database: str
    user: str
    extended_info: str = ""


@dataclass
class MockGlobalVariable:
    """Mock for GlobalVariable without MongoDB dependency."""

    name: str
    wlanguage_type: str
    default_value: str | None = None
    scope: MockScope = MockScope.APP
    source_element: str = "Project.wwp"
    source_type_code: int = 0


@dataclass
class MockInitializationBlock:
    """Mock for InitializationBlock without MongoDB dependency."""

    code: str
    dependencies: list[str] = field(default_factory=list)
    order: int = 0


@dataclass
class MockGlobalStateContext:
    """Mock for GlobalStateContext without MongoDB dependency."""

    variables: list[MockGlobalVariable] = field(default_factory=list)
    initialization_blocks: list[MockInitializationBlock] = field(default_factory=list)


def count_tokens(text: str) -> int:
    """Count tokens using tiktoken cl100k_base encoding (GPT-4 compatible)."""
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


@pytest.fixture
def mock_output_project() -> MagicMock:
    """Create mock OutputProject."""
    project = MagicMock()
    project.name = "TestProject"
    project.kb_id = "507f1f77bcf86cd799439011"
    return project


@pytest.fixture
def mock_stack() -> MagicMock:
    """Create mock Stack with all required fields."""
    stack = MagicMock()
    stack.name = "FastAPI + Jinja2"
    stack.language = "python"
    stack.framework = "FastAPI"
    stack.file_structure = {
        "root": ".",
        "app": "app/",
        "templates": "templates/",
        "static": "static/",
    }
    stack.naming_conventions = {
        "files": "snake_case",
        "classes": "PascalCase",
        "functions": "snake_case",
    }
    stack.type_mappings = {
        "string": "str",
        "int": "int",
        "real": "float",
        "boolean": "bool",
        "date": "datetime.date",
    }
    stack.model_template = """from pydantic import BaseModel

class MyModel(BaseModel):
    id: int
    name: str
"""
    stack.imports_template = """from fastapi import FastAPI, Depends
from pydantic import BaseModel
"""
    return stack


@pytest.fixture
def mock_connections() -> list[MockSchemaConnection]:
    """Create list of 2 mock database connections."""
    return [
        MockSchemaConnection(
            name="CNX_BASE_PROD",
            type_code=1,
            database_type="sqlserver",
            driver_name="SQL Server",
            source="192.168.1.100",
            port="1433",
            database="ProdDB",
            user="app_user",
            extended_info="Server=192.168.1.100;Port=1433",
        ),
        MockSchemaConnection(
            name="CNX_MYSQL",
            type_code=2,
            database_type="mysql",
            driver_name="MySQL",
            source="mysql.server.com",
            port="3306",
            database="AppDB",
            user="mysql_user",
            extended_info="",
        ),
    ]


@pytest.fixture
def mock_global_state() -> MockGlobalStateContext:
    """Create mock GlobalStateContext with 3 variables and 1 init block."""
    variables = [
        MockGlobalVariable(
            name="gCnn",
            wlanguage_type="Connection",
            default_value=None,
            scope=MockScope.APP,
            source_element="Project.wwp",
        ),
        MockGlobalVariable(
            name="gnTimeout",
            wlanguage_type="int",
            default_value="30",
            scope=MockScope.APP,
            source_element="Project.wwp",
        ),
        MockGlobalVariable(
            name="gsAccessToken",
            wlanguage_type="string",
            default_value="secret123",
            scope=MockScope.MODULE,
            source_element="ServerProcs.wdg",
        ),
    ]
    init_blocks = [
        MockInitializationBlock(
            code="""IF HOpenConnection(gCnn) = False THEN
    EndProgram("Database connection failed")
END

gnTimeout = Global_PegaInfoINI("config.ini", "Timeout")""",
            dependencies=["gCnn", "gnTimeout"],
            order=0,
        )
    ]
    return MockGlobalStateContext(variables=variables, initialization_blocks=init_blocks)


@pytest.fixture
def mock_tables() -> list[dict]:
    """Create list of 2 mock database tables."""
    return [
        {
            "name": "USUARIO",
            "physical_name": "USUARIO",
            "columns": [
                {
                    "name": "IDusuario",
                    "python_type": "int",
                    "is_primary_key": True,
                    "is_indexed": True,
                    "nullable": False,
                    "is_auto_increment": True,
                },
                {
                    "name": "Nome",
                    "python_type": "str",
                    "is_primary_key": False,
                    "is_indexed": False,
                    "nullable": True,
                    "is_auto_increment": False,
                },
                {
                    "name": "Email",
                    "python_type": "str",
                    "is_primary_key": False,
                    "is_indexed": True,
                    "nullable": False,
                    "is_auto_increment": False,
                },
            ],
            "indexes": [
                {"name": "PK_USUARIO", "columns": ["IDusuario"], "is_unique": True, "is_primary": True}
            ],
        },
        {
            "name": "CLIENTE",
            "physical_name": "CLIENTE",
            "columns": [
                {
                    "name": "IDcliente",
                    "python_type": "int",
                    "is_primary_key": True,
                    "is_indexed": True,
                    "nullable": False,
                    "is_auto_increment": True,
                },
                {
                    "name": "CPF",
                    "python_type": "str",
                    "is_primary_key": False,
                    "is_indexed": True,
                    "nullable": False,
                    "is_auto_increment": False,
                },
            ],
            "indexes": [],
        },
    ]


class TestBuildContextComplete:
    """Tests for complete build_context with all sections."""

    def test_build_context_with_all_sections(
        self,
        mock_output_project: MagicMock,
        mock_stack: MagicMock,
        mock_tables: list[dict],
        mock_connections: list[MockSchemaConnection],
        mock_global_state: MockGlobalStateContext,
    ):
        """Verify all 6 section headers are present in generated CONTEXT.md."""
        content = PromptBuilder.build_context(
            output_project=mock_output_project,
            stack=mock_stack,
            tables=mock_tables,
            connections=mock_connections,
            global_state=mock_global_state,
        )

        # All 6 required sections must be present
        assert "## Database Schema" in content
        assert "## Database Connections" in content
        assert "## Environment Variables" in content
        assert "## Global State" in content
        assert "## Initialization Code" in content
        assert "## MCP Server Integration" in content

    def test_build_context_sections_in_order(
        self,
        mock_output_project: MagicMock,
        mock_stack: MagicMock,
        mock_tables: list[dict],
        mock_connections: list[MockSchemaConnection],
        mock_global_state: MockGlobalStateContext,
    ):
        """Verify sections appear in correct order."""
        content = PromptBuilder.build_context(
            output_project=mock_output_project,
            stack=mock_stack,
            tables=mock_tables,
            connections=mock_connections,
            global_state=mock_global_state,
        )

        # Get positions of each section
        schema_pos = content.find("## Database Schema")
        connections_pos = content.find("## Database Connections")
        env_pos = content.find("## Environment Variables")
        global_state_pos = content.find("## Global State")
        init_pos = content.find("## Initialization Code")
        mcp_pos = content.find("## MCP Server Integration")

        # Verify order: Schema -> Connections -> Env -> Global State -> Init -> MCP
        assert schema_pos < connections_pos, "Schema must come before Connections"
        assert connections_pos < env_pos, "Connections must come before Env"
        assert env_pos < global_state_pos, "Env must come before Global State"
        assert global_state_pos < init_pos, "Global State must come before Init"
        assert init_pos < mcp_pos, "Init must come before MCP"

    def test_build_context_empty_connections(
        self,
        mock_output_project: MagicMock,
        mock_stack: MagicMock,
        mock_tables: list[dict],
        mock_global_state: MockGlobalStateContext,
    ):
        """Verify default message when connections=None."""
        content = PromptBuilder.build_context(
            output_project=mock_output_project,
            stack=mock_stack,
            tables=mock_tables,
            connections=None,
            global_state=mock_global_state,
        )

        # Should have default message for connections
        assert "## Database Connections" in content
        assert "*No external database connections defined.*" in content
        # .env.example should still exist but with default content
        assert "## Environment Variables" in content
        assert "# No database connections" in content

    def test_build_context_empty_global_state(
        self,
        mock_output_project: MagicMock,
        mock_stack: MagicMock,
        mock_tables: list[dict],
        mock_connections: list[MockSchemaConnection],
    ):
        """Verify default message when global_state=None."""
        content = PromptBuilder.build_context(
            output_project=mock_output_project,
            stack=mock_stack,
            tables=mock_tables,
            connections=mock_connections,
            global_state=None,
        )

        # Should have default message for global state
        assert "## Global State" in content
        assert "*No global variables defined.*" in content
        # Init code section should also have default message
        assert "## Initialization Code" in content
        assert "*No initialization code found.*" in content
        # Lifespan pattern should NOT appear when no init blocks
        assert "FastAPI Lifespan Pattern" not in content

    def test_build_context_empty_both(
        self,
        mock_output_project: MagicMock,
        mock_stack: MagicMock,
        mock_tables: list[dict],
    ):
        """Verify valid CONTEXT.md generated when both connections and global_state are None."""
        content = PromptBuilder.build_context(
            output_project=mock_output_project,
            stack=mock_stack,
            tables=mock_tables,
            connections=None,
            global_state=None,
        )

        # All sections should still exist
        assert "## Database Schema" in content
        assert "## Database Connections" in content
        assert "## Environment Variables" in content
        assert "## Global State" in content
        assert "## Initialization Code" in content
        assert "## MCP Server Integration" in content

        # Default messages for empty sections
        assert "*No external database connections defined.*" in content
        assert "*No global variables defined.*" in content
        assert "*No initialization code found.*" in content

        # Project name and stack should be present
        assert "TestProject" in content
        assert "FastAPI" in content


class TestTokenBudget:
    """Tests for token budget validation."""

    def test_minimal_context_token_count(
        self,
        mock_output_project: MagicMock,
        mock_stack: MagicMock,
    ):
        """Empty data should produce < 2000 tokens (instructions only)."""
        content = PromptBuilder.build_context(
            output_project=mock_output_project,
            stack=mock_stack,
            tables=[],
            connections=None,
            global_state=None,
        )

        token_count = count_tokens(content)
        print(f"Minimal context token count: {token_count}")

        assert token_count < 2000, f"Minimal context too large: {token_count} tokens"

    def test_realistic_context_token_count(
        self,
        mock_output_project: MagicMock,
        mock_stack: MagicMock,
        mock_tables: list[dict],
        mock_connections: list[MockSchemaConnection],
        mock_global_state: MockGlobalStateContext,
    ):
        """With 2 connections, 3 variables, 1 init block should be < 8000 tokens."""
        content = PromptBuilder.build_context(
            output_project=mock_output_project,
            stack=mock_stack,
            tables=mock_tables,
            connections=mock_connections,
            global_state=mock_global_state,
        )

        token_count = count_tokens(content)
        print(f"Realistic context token count: {token_count}")

        assert token_count < 8000, f"Realistic context too large: {token_count} tokens"

    def test_large_init_block_truncated(
        self,
        mock_output_project: MagicMock,
        mock_stack: MagicMock,
        mock_tables: list[dict],
    ):
        """Init block with 200 lines should be truncated, still under budget."""
        # Create init block with 200 lines
        large_code = "\n".join([f"// Line {i}: HExecuteQuery(gQuery{i})" for i in range(200)])
        large_init = MockInitializationBlock(
            code=large_code,
            dependencies=["gCnn"],
            order=0,
        )
        global_state = MockGlobalStateContext(
            variables=[
                MockGlobalVariable(name="gCnn", wlanguage_type="Connection", scope=MockScope.APP)
            ],
            initialization_blocks=[large_init],
        )

        content = PromptBuilder.build_context(
            output_project=mock_output_project,
            stack=mock_stack,
            tables=mock_tables,
            connections=None,
            global_state=global_state,
        )

        token_count = count_tokens(content)
        print(f"Large init block token count: {token_count}")

        # Verify truncation indicator present
        assert "// ... (" in content, "Truncation indicator should be present"
        assert "more lines)" in content, "Truncation indicator should show remaining lines"

        # Still under budget
        assert token_count < 8000, f"Large init block context too large: {token_count} tokens"

    def test_many_variables_token_impact(
        self,
        mock_output_project: MagicMock,
        mock_stack: MagicMock,
        mock_tables: list[dict],
    ):
        """20 variables should still be under budget."""
        # Create 20 variables with various types
        variables = [
            MockGlobalVariable(
                name=f"gVar{i}",
                wlanguage_type="string" if i % 3 == 0 else ("int" if i % 3 == 1 else "boolean"),
                default_value=str(i) if i % 2 == 0 else None,
                scope=MockScope.APP if i % 2 == 0 else MockScope.MODULE,
                source_element="Project.wwp",
            )
            for i in range(20)
        ]
        global_state = MockGlobalStateContext(variables=variables, initialization_blocks=[])

        content = PromptBuilder.build_context(
            output_project=mock_output_project,
            stack=mock_stack,
            tables=mock_tables,
            connections=None,
            global_state=global_state,
        )

        token_count = count_tokens(content)
        print(f"20 variables token count: {token_count}")

        assert token_count < 8000, f"20 variables context too large: {token_count} tokens"


class TestContextContentValidation:
    """Tests for validating content in generated CONTEXT.md."""

    def test_project_name_in_context(
        self,
        mock_output_project: MagicMock,
        mock_stack: MagicMock,
        mock_tables: list[dict],
    ):
        """Verify project_name appears in generated content."""
        content = PromptBuilder.build_context(
            output_project=mock_output_project,
            stack=mock_stack,
            tables=mock_tables,
        )

        assert "TestProject" in content

    def test_stack_details_in_context(
        self,
        mock_output_project: MagicMock,
        mock_stack: MagicMock,
        mock_tables: list[dict],
    ):
        """Verify stack.name and stack.language in content."""
        content = PromptBuilder.build_context(
            output_project=mock_output_project,
            stack=mock_stack,
            tables=mock_tables,
        )

        assert "FastAPI + Jinja2" in content
        assert "python" in content

    def test_table_names_in_context(
        self,
        mock_output_project: MagicMock,
        mock_stack: MagicMock,
        mock_tables: list[dict],
    ):
        """Verify table names from mock_tables appear in content."""
        content = PromptBuilder.build_context(
            output_project=mock_output_project,
            stack=mock_stack,
            tables=mock_tables,
        )

        assert "USUARIO" in content
        assert "CLIENTE" in content
        # Also check column names
        assert "IDusuario" in content
        assert "Email" in content
        assert "CPF" in content

    def test_connection_hosts_in_context(
        self,
        mock_output_project: MagicMock,
        mock_stack: MagicMock,
        mock_tables: list[dict],
        mock_connections: list[MockSchemaConnection],
    ):
        """Verify connection hosts/ports appear in content."""
        content = PromptBuilder.build_context(
            output_project=mock_output_project,
            stack=mock_stack,
            tables=mock_tables,
            connections=mock_connections,
        )

        # Check hosts
        assert "192.168.1.100" in content
        assert "mysql.server.com" in content
        # Check ports
        assert "1433" in content
        assert "3306" in content
        # Check connection names
        assert "CNX_BASE_PROD" in content
        assert "CNX_MYSQL" in content

    def test_variable_names_in_context(
        self,
        mock_output_project: MagicMock,
        mock_stack: MagicMock,
        mock_tables: list[dict],
        mock_global_state: MockGlobalStateContext,
    ):
        """Verify variable names appear in content."""
        content = PromptBuilder.build_context(
            output_project=mock_output_project,
            stack=mock_stack,
            tables=mock_tables,
            global_state=mock_global_state,
        )

        # Check variable names
        assert "gCnn" in content
        assert "gnTimeout" in content
        assert "gsAccessToken" in content
        # Check sensitive value is redacted
        assert "*[REDACTED]*" in content  # gsAccessToken has "secret" pattern


class TestRealisticDataVolume:
    """Tests with data volumes similar to real Linkpay_ADM project."""

    @pytest.fixture
    def large_mock_tables(self) -> list[dict]:
        """Create 20 tables, each with 5-10 columns."""
        tables = []
        table_names = [
            "USUARIO", "CLIENTE", "PEDIDO", "PRODUTO", "ESTOQUE",
            "PAGAMENTO", "FATURA", "NOTA_FISCAL", "TRANSPORTADORA", "ENTREGA",
            "CATEGORIA", "SUBCATEGORIA", "FORNECEDOR", "COMPRA", "ITEM_COMPRA",
            "ITEM_PEDIDO", "HISTORICO", "LOG_ACESSO", "CONFIGURACAO", "PARAMETRO",
        ]
        for i, name in enumerate(table_names):
            num_columns = 5 + (i % 6)  # 5 to 10 columns
            columns = [
                {
                    "name": f"ID{name.lower()}",
                    "python_type": "int",
                    "is_primary_key": True,
                    "is_indexed": True,
                    "nullable": False,
                    "is_auto_increment": True,
                }
            ]
            for j in range(1, num_columns):
                columns.append({
                    "name": f"Campo{j}",
                    "python_type": "str" if j % 2 == 0 else "int",
                    "is_primary_key": False,
                    "is_indexed": j < 3,
                    "nullable": j > 2,
                    "is_auto_increment": False,
                })
            tables.append({
                "name": name,
                "physical_name": name,
                "columns": columns,
                "indexes": [
                    {"name": f"PK_{name}", "columns": [f"ID{name.lower()}"], "is_unique": True, "is_primary": True}
                ],
            })
        return tables

    @pytest.fixture
    def many_mock_variables(self) -> list[MockGlobalVariable]:
        """Create 15 global variables with various scopes."""
        var_types = ["string", "int", "boolean", "Connection", "JSON", "array of string"]
        variables = []
        for i in range(15):
            variables.append(
                MockGlobalVariable(
                    name=f"gVar{i:02d}",
                    wlanguage_type=var_types[i % len(var_types)],
                    default_value=str(i * 10) if i % 3 == 0 else None,
                    scope=MockScope.APP if i < 5 else (MockScope.MODULE if i < 10 else MockScope.REQUEST),
                    source_element="Project.wwp" if i < 5 else "ServerProcs.wdg",
                )
            )
        return variables

    @pytest.fixture
    def complex_init_block(self) -> MockInitializationBlock:
        """Create init block with 80 lines of code and 10 dependencies."""
        lines = [
            "// Inicializacao do projeto",
            "COMPILE IF Configuration = \"PROD\"",
            "    gsCnxString = Global_PegaInfoINI(\"config.ini\", \"PROD_CNX\")",
            "ELSE",
            "    gsCnxString = Global_PegaInfoINI(\"config.ini\", \"DEV_CNX\")",
            "END",
            "",
            "IF HOpenConnection(gCnn) = False THEN",
            "    EndProgram(\"Erro ao conectar\")",
            "END",
        ]
        # Add more lines to reach 80
        for i in range(70):
            lines.append(f"// Linha adicional {i}: Configuracao {chr(65 + i % 26)}")

        return MockInitializationBlock(
            code="\n".join(lines),
            dependencies=["gCnn", "gsCnxString", "gnTimeout", "gbDebug", "gsServer",
                         "gnPorta", "gsUsuario", "gsSenha", "gjConfig", "gaLogs"],
            order=0,
        )

    def test_realistic_volume_completes(
        self,
        mock_output_project: MagicMock,
        mock_stack: MagicMock,
        large_mock_tables: list[dict],
        many_mock_variables: list[MockGlobalVariable],
        complex_init_block: MockInitializationBlock,
        mock_connections: list[MockSchemaConnection],
    ):
        """build_context() should complete without error with realistic data."""
        global_state = MockGlobalStateContext(
            variables=many_mock_variables,
            initialization_blocks=[complex_init_block],
        )

        # Should not raise any exception
        content = PromptBuilder.build_context(
            output_project=mock_output_project,
            stack=mock_stack,
            tables=large_mock_tables,
            connections=mock_connections,
            global_state=global_state,
        )

        # Verify content is non-empty
        assert len(content) > 0

    def test_realistic_volume_token_budget(
        self,
        mock_output_project: MagicMock,
        mock_stack: MagicMock,
        large_mock_tables: list[dict],
        many_mock_variables: list[MockGlobalVariable],
        complex_init_block: MockInitializationBlock,
        mock_connections: list[MockSchemaConnection],
    ):
        """Realistic volume should stay under 8000 tokens."""
        global_state = MockGlobalStateContext(
            variables=many_mock_variables,
            initialization_blocks=[complex_init_block],
        )

        content = PromptBuilder.build_context(
            output_project=mock_output_project,
            stack=mock_stack,
            tables=large_mock_tables,
            connections=mock_connections,
            global_state=global_state,
        )

        token_count = count_tokens(content)
        print(f"Token count with realistic data: {token_count}")

        assert token_count < 8000, f"Realistic volume exceeds budget: {token_count} tokens"

    def test_realistic_volume_all_sections_present(
        self,
        mock_output_project: MagicMock,
        mock_stack: MagicMock,
        large_mock_tables: list[dict],
        many_mock_variables: list[MockGlobalVariable],
        complex_init_block: MockInitializationBlock,
        mock_connections: list[MockSchemaConnection],
    ):
        """All 6 sections should exist with realistic data."""
        global_state = MockGlobalStateContext(
            variables=many_mock_variables,
            initialization_blocks=[complex_init_block],
        )

        content = PromptBuilder.build_context(
            output_project=mock_output_project,
            stack=mock_stack,
            tables=large_mock_tables,
            connections=mock_connections,
            global_state=global_state,
        )

        # All 6 required sections
        assert "## Database Schema" in content
        assert "## Database Connections" in content
        assert "## Environment Variables" in content
        assert "## Global State" in content
        assert "## Initialization Code" in content
        assert "## MCP Server Integration" in content

    def test_realistic_volume_no_truncation_except_init(
        self,
        mock_output_project: MagicMock,
        mock_stack: MagicMock,
        large_mock_tables: list[dict],
        many_mock_variables: list[MockGlobalVariable],
        complex_init_block: MockInitializationBlock,
        mock_connections: list[MockSchemaConnection],
    ):
        """Tables and variables should not be truncated, only init code if over 100 lines."""
        global_state = MockGlobalStateContext(
            variables=many_mock_variables,
            initialization_blocks=[complex_init_block],
        )

        content = PromptBuilder.build_context(
            output_project=mock_output_project,
            stack=mock_stack,
            tables=large_mock_tables,
            connections=mock_connections,
            global_state=global_state,
        )

        # All 20 tables should be present
        for table in large_mock_tables:
            assert table["name"] in content, f"Table {table['name']} missing"

        # All 15 variables should be present
        for var in many_mock_variables:
            assert var.name in content, f"Variable {var.name} missing"

        # Init block is 80 lines, under 100 limit, so no truncation
        assert "// ... (" not in content, "Init block under 100 lines should not be truncated"
