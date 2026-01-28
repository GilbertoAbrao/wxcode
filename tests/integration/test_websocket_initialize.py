"""Integration tests for WebSocket /initialize endpoint.

Tests verify that the initialization flow:
1. Calls extract_connections_for_project()
2. Calls extract_global_state_for_project()
3. Passes extracted data to PromptBuilder.write_context_file()
4. Writes CONTEXT.md to workspace
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocket

# Import the actual function to test
from wxcode.api.output_projects import initialize_output_project

# Import real OutputProjectStatus to use in mocks (it's a str, Enum that compares by value)
from wxcode.models.output_project import OutputProjectStatus


# === Mock Classes (dataclass-based, no MongoDB) ===


class MockScope(Enum):
    """Mock scope enum for global variables."""
    APP = "APP"
    MODULE = "MODULE"


@dataclass
class MockSchemaConnection:
    """Mock database connection from schema."""
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
    """Mock global variable from project."""
    name: str
    wlanguage_type: str
    default_value: str | None = None
    scope: MockScope = MockScope.APP
    source_element: str = "Project.wwp"


@dataclass
class MockInitializationBlock:
    """Mock initialization block from project code."""
    code: str
    dependencies: list[str] = field(default_factory=list)
    order: int = 0


@dataclass
class MockGlobalStateContext:
    """Mock global state context."""
    variables: list[MockGlobalVariable] = field(default_factory=list)
    initialization_blocks: list[MockInitializationBlock] = field(default_factory=list)


# === Fixtures ===


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket that tracks sent messages."""
    ws = MagicMock(spec=WebSocket)
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    ws.sent_messages = []

    async def track_send(data):
        ws.sent_messages.append(data)

    ws.send_json.side_effect = track_send
    return ws


@pytest.fixture
def mock_output_project(tmp_path):
    """Create a mock OutputProject with workspace path."""
    project = MagicMock()
    project.name = "TestProject"
    project.kb_id = "507f1f77bcf86cd799439011"
    project.stack_id = "fastapi-jinja2"
    project.configuration_id = "config123"
    project.status = OutputProjectStatus.CREATED  # Use real enum for comparison
    project.workspace_path = str(tmp_path / "workspace")
    project.save = AsyncMock()

    # Create workspace directory
    Path(project.workspace_path).mkdir(parents=True)

    return project


@pytest.fixture
def mock_stack():
    """Create a mock Stack."""
    stack = MagicMock()
    stack.name = "FastAPI + Jinja2"
    stack.language = "python"
    stack.framework = "FastAPI"
    stack.file_structure = {"app": {"routes": "API routes"}}
    stack.naming_conventions = {"files": "snake_case"}
    stack.type_mappings = {"string": "str"}
    stack.model_template = "class {name}(BaseModel): pass"
    stack.imports_template = "from fastapi import FastAPI"
    return stack


@pytest.fixture
def mock_connections():
    """Create mock database connections."""
    return [
        MockSchemaConnection(
            name="CNX_MAIN",
            type_code=1,
            database_type="sqlserver",
            driver_name="SQL Server",
            source="192.168.1.1",
            port="1433",
            database="MainDB",
            user="app_user",
        ),
        MockSchemaConnection(
            name="CNX_BACKUP",
            type_code=2,
            database_type="mysql",
            driver_name="MySQL",
            source="192.168.1.2",
            port="3306",
            database="BackupDB",
            user="backup_user",
        ),
    ]


@pytest.fixture
def mock_global_state():
    """Create mock global state context."""
    return MockGlobalStateContext(
        variables=[
            MockGlobalVariable(
                name="g_AppVersion",
                wlanguage_type="string",
                default_value="1.0.0",
            ),
            MockGlobalVariable(
                name="g_DebugMode",
                wlanguage_type="boolean",
                default_value="False",
            ),
        ],
        initialization_blocks=[
            MockInitializationBlock(
                code="g_AppVersion = GetAppVersion()",
                dependencies=["GetAppVersion"],
                order=0,
            ),
            MockInitializationBlock(
                code="g_DebugMode = IsDebugEnvironment()",
                dependencies=["IsDebugEnvironment"],
                order=1,
            ),
        ],
    )


@pytest.fixture
def mock_tables():
    """Create mock tables."""
    return [
        {
            "name": "USUARIO",
            "columns": [
                {"name": "id", "type": "int"},
                {"name": "nome", "type": "string"},
            ]
        },
        {
            "name": "CLIENTE",
            "columns": [
                {"name": "id", "type": "int"},
                {"name": "razao_social", "type": "string"},
            ]
        },
    ]


# === Test Class: WebSocket Initialize Extractors ===


class TestWebSocketInitializeExtractors:
    """Tests that /initialize endpoint calls all extractors correctly."""

    @pytest.mark.asyncio
    @patch("wxcode.api.output_projects.OutputProject")
    @patch("wxcode.api.output_projects.Stack")
    @patch("wxcode.api.output_projects.extract_schema_for_configuration")
    @patch("wxcode.api.output_projects.extract_connections_for_project")
    @patch("wxcode.api.output_projects.extract_global_state_for_project")
    @patch("wxcode.api.output_projects.PromptBuilder")
    @patch("wxcode.api.output_projects.GSDInvoker")
    async def test_calls_extract_connections_for_project(
        self,
        mock_gsd_invoker_class,
        mock_prompt_builder,
        mock_extract_global_state,
        mock_extract_connections,
        mock_extract_schema,
        mock_stack_model,
        mock_output_project_model,
        mock_websocket,
        mock_output_project,
        mock_stack,
        mock_connections,
        mock_global_state,
        mock_tables,
    ):
        """Verify extract_connections_for_project() is called with correct kb_id."""
        # Setup mocks
        mock_output_project_model.get = AsyncMock(return_value=mock_output_project)
        mock_stack_model.find_one = AsyncMock(return_value=mock_stack)
        mock_extract_schema.return_value = mock_tables
        mock_extract_connections.return_value = mock_connections
        mock_extract_global_state.return_value = mock_global_state
        mock_prompt_builder.write_context_file.return_value = Path(mock_output_project.workspace_path) / "CONTEXT.md"

        # Setup GSD invoker mock
        mock_invoker = MagicMock()
        mock_invoker.invoke_with_streaming = AsyncMock(return_value=0)
        mock_gsd_invoker_class.return_value = mock_invoker

        # Call endpoint
        await initialize_output_project(mock_websocket, "507f1f77bcf86cd799439011")

        # Verify extract_connections_for_project was called
        mock_extract_connections.assert_called_once_with(mock_output_project.kb_id)

    @pytest.mark.asyncio
    @patch("wxcode.api.output_projects.OutputProject")
    @patch("wxcode.api.output_projects.Stack")
    @patch("wxcode.api.output_projects.extract_schema_for_configuration")
    @patch("wxcode.api.output_projects.extract_connections_for_project")
    @patch("wxcode.api.output_projects.extract_global_state_for_project")
    @patch("wxcode.api.output_projects.PromptBuilder")
    @patch("wxcode.api.output_projects.GSDInvoker")
    async def test_calls_extract_global_state_for_project(
        self,
        mock_gsd_invoker_class,
        mock_prompt_builder,
        mock_extract_global_state,
        mock_extract_connections,
        mock_extract_schema,
        mock_stack_model,
        mock_output_project_model,
        mock_websocket,
        mock_output_project,
        mock_stack,
        mock_connections,
        mock_global_state,
        mock_tables,
    ):
        """Verify extract_global_state_for_project() is called with correct kb_id."""
        # Setup mocks
        mock_output_project_model.get = AsyncMock(return_value=mock_output_project)
        mock_stack_model.find_one = AsyncMock(return_value=mock_stack)
        mock_extract_schema.return_value = mock_tables
        mock_extract_connections.return_value = mock_connections
        mock_extract_global_state.return_value = mock_global_state
        mock_prompt_builder.write_context_file.return_value = Path(mock_output_project.workspace_path) / "CONTEXT.md"

        # Setup GSD invoker mock
        mock_invoker = MagicMock()
        mock_invoker.invoke_with_streaming = AsyncMock(return_value=0)
        mock_gsd_invoker_class.return_value = mock_invoker

        # Call endpoint
        await initialize_output_project(mock_websocket, "507f1f77bcf86cd799439011")

        # Verify extract_global_state_for_project was called
        mock_extract_global_state.assert_called_once_with(mock_output_project.kb_id)

    @pytest.mark.asyncio
    @patch("wxcode.api.output_projects.OutputProject")
    @patch("wxcode.api.output_projects.Stack")
    @patch("wxcode.api.output_projects.extract_schema_for_configuration")
    @patch("wxcode.api.output_projects.extract_connections_for_project")
    @patch("wxcode.api.output_projects.extract_global_state_for_project")
    @patch("wxcode.api.output_projects.PromptBuilder")
    @patch("wxcode.api.output_projects.GSDInvoker")
    async def test_calls_extractors_in_correct_order(
        self,
        mock_gsd_invoker_class,
        mock_prompt_builder,
        mock_extract_global_state,
        mock_extract_connections,
        mock_extract_schema,
        mock_stack_model,
        mock_output_project_model,
        mock_websocket,
        mock_output_project,
        mock_stack,
        mock_connections,
        mock_global_state,
        mock_tables,
    ):
        """Verify extractors are called before PromptBuilder."""
        # Track call order
        call_order = []

        async def track_extract_schema(*args, **kwargs):
            call_order.append("extract_schema")
            return mock_tables

        async def track_extract_connections(*args, **kwargs):
            call_order.append("extract_connections")
            return mock_connections

        async def track_extract_global_state(*args, **kwargs):
            call_order.append("extract_global_state")
            return mock_global_state

        def track_write_context(*args, **kwargs):
            call_order.append("write_context")
            return Path(mock_output_project.workspace_path) / "CONTEXT.md"

        # Setup mocks
        mock_output_project_model.get = AsyncMock(return_value=mock_output_project)
        mock_stack_model.find_one = AsyncMock(return_value=mock_stack)
        mock_extract_schema.side_effect = track_extract_schema
        mock_extract_connections.side_effect = track_extract_connections
        mock_extract_global_state.side_effect = track_extract_global_state
        mock_prompt_builder.write_context_file.side_effect = track_write_context

        # Setup GSD invoker mock
        mock_invoker = MagicMock()
        mock_invoker.invoke_with_streaming = AsyncMock(return_value=0)
        mock_gsd_invoker_class.return_value = mock_invoker

        # Call endpoint
        await initialize_output_project(mock_websocket, "507f1f77bcf86cd799439011")

        # Verify order: extractors before write_context
        assert "extract_schema" in call_order
        assert "extract_connections" in call_order
        assert "extract_global_state" in call_order
        assert "write_context" in call_order

        # write_context should be last
        assert call_order.index("write_context") > call_order.index("extract_schema")
        assert call_order.index("write_context") > call_order.index("extract_connections")
        assert call_order.index("write_context") > call_order.index("extract_global_state")


# === Test Class: WebSocket Initialize PromptBuilder ===


class TestWebSocketInitializePromptBuilder:
    """Tests that /initialize passes data to PromptBuilder correctly."""

    @pytest.mark.asyncio
    @patch("wxcode.api.output_projects.OutputProject")
    @patch("wxcode.api.output_projects.Stack")
    @patch("wxcode.api.output_projects.extract_schema_for_configuration")
    @patch("wxcode.api.output_projects.extract_connections_for_project")
    @patch("wxcode.api.output_projects.extract_global_state_for_project")
    @patch("wxcode.api.output_projects.PromptBuilder")
    @patch("wxcode.api.output_projects.GSDInvoker")
    async def test_passes_connections_to_prompt_builder(
        self,
        mock_gsd_invoker_class,
        mock_prompt_builder,
        mock_extract_global_state,
        mock_extract_connections,
        mock_extract_schema,
        mock_stack_model,
        mock_output_project_model,
        mock_websocket,
        mock_output_project,
        mock_stack,
        mock_connections,
        mock_global_state,
        mock_tables,
    ):
        """Verify PromptBuilder.write_context_file receives connections."""
        # Setup mocks
        mock_output_project_model.get = AsyncMock(return_value=mock_output_project)
        mock_stack_model.find_one = AsyncMock(return_value=mock_stack)
        mock_extract_schema.return_value = mock_tables
        mock_extract_connections.return_value = mock_connections
        mock_extract_global_state.return_value = mock_global_state
        mock_prompt_builder.write_context_file.return_value = Path(mock_output_project.workspace_path) / "CONTEXT.md"

        # Setup GSD invoker mock
        mock_invoker = MagicMock()
        mock_invoker.invoke_with_streaming = AsyncMock(return_value=0)
        mock_gsd_invoker_class.return_value = mock_invoker

        # Call endpoint
        await initialize_output_project(mock_websocket, "507f1f77bcf86cd799439011")

        # Verify PromptBuilder.write_context_file was called with connections
        mock_prompt_builder.write_context_file.assert_called_once()
        call_kwargs = mock_prompt_builder.write_context_file.call_args.kwargs
        assert call_kwargs["connections"] == mock_connections

    @pytest.mark.asyncio
    @patch("wxcode.api.output_projects.OutputProject")
    @patch("wxcode.api.output_projects.Stack")
    @patch("wxcode.api.output_projects.extract_schema_for_configuration")
    @patch("wxcode.api.output_projects.extract_connections_for_project")
    @patch("wxcode.api.output_projects.extract_global_state_for_project")
    @patch("wxcode.api.output_projects.PromptBuilder")
    @patch("wxcode.api.output_projects.GSDInvoker")
    async def test_passes_global_state_to_prompt_builder(
        self,
        mock_gsd_invoker_class,
        mock_prompt_builder,
        mock_extract_global_state,
        mock_extract_connections,
        mock_extract_schema,
        mock_stack_model,
        mock_output_project_model,
        mock_websocket,
        mock_output_project,
        mock_stack,
        mock_connections,
        mock_global_state,
        mock_tables,
    ):
        """Verify PromptBuilder.write_context_file receives global_state."""
        # Setup mocks
        mock_output_project_model.get = AsyncMock(return_value=mock_output_project)
        mock_stack_model.find_one = AsyncMock(return_value=mock_stack)
        mock_extract_schema.return_value = mock_tables
        mock_extract_connections.return_value = mock_connections
        mock_extract_global_state.return_value = mock_global_state
        mock_prompt_builder.write_context_file.return_value = Path(mock_output_project.workspace_path) / "CONTEXT.md"

        # Setup GSD invoker mock
        mock_invoker = MagicMock()
        mock_invoker.invoke_with_streaming = AsyncMock(return_value=0)
        mock_gsd_invoker_class.return_value = mock_invoker

        # Call endpoint
        await initialize_output_project(mock_websocket, "507f1f77bcf86cd799439011")

        # Verify PromptBuilder.write_context_file was called with global_state
        mock_prompt_builder.write_context_file.assert_called_once()
        call_kwargs = mock_prompt_builder.write_context_file.call_args.kwargs
        assert call_kwargs["global_state"] == mock_global_state

    @pytest.mark.asyncio
    @patch("wxcode.api.output_projects.OutputProject")
    @patch("wxcode.api.output_projects.Stack")
    @patch("wxcode.api.output_projects.extract_schema_for_configuration")
    @patch("wxcode.api.output_projects.extract_connections_for_project")
    @patch("wxcode.api.output_projects.extract_global_state_for_project")
    @patch("wxcode.api.output_projects.PromptBuilder")
    @patch("wxcode.api.output_projects.GSDInvoker")
    async def test_passes_all_parameters_to_prompt_builder(
        self,
        mock_gsd_invoker_class,
        mock_prompt_builder,
        mock_extract_global_state,
        mock_extract_connections,
        mock_extract_schema,
        mock_stack_model,
        mock_output_project_model,
        mock_websocket,
        mock_output_project,
        mock_stack,
        mock_connections,
        mock_global_state,
        mock_tables,
    ):
        """Verify PromptBuilder.write_context_file receives all required parameters."""
        # Setup mocks
        mock_output_project_model.get = AsyncMock(return_value=mock_output_project)
        mock_stack_model.find_one = AsyncMock(return_value=mock_stack)
        mock_extract_schema.return_value = mock_tables
        mock_extract_connections.return_value = mock_connections
        mock_extract_global_state.return_value = mock_global_state
        mock_prompt_builder.write_context_file.return_value = Path(mock_output_project.workspace_path) / "CONTEXT.md"

        # Setup GSD invoker mock
        mock_invoker = MagicMock()
        mock_invoker.invoke_with_streaming = AsyncMock(return_value=0)
        mock_gsd_invoker_class.return_value = mock_invoker

        # Call endpoint
        await initialize_output_project(mock_websocket, "507f1f77bcf86cd799439011")

        # Verify all parameters passed
        mock_prompt_builder.write_context_file.assert_called_once()
        call_kwargs = mock_prompt_builder.write_context_file.call_args.kwargs

        # Verify all required parameters
        assert "output_project" in call_kwargs
        assert "stack" in call_kwargs
        assert "tables" in call_kwargs
        assert "connections" in call_kwargs
        assert "global_state" in call_kwargs
        assert "workspace_path" in call_kwargs

        # Verify correct values
        assert call_kwargs["output_project"] == mock_output_project
        assert call_kwargs["stack"] == mock_stack
        assert call_kwargs["tables"] == mock_tables
        assert call_kwargs["connections"] == mock_connections
        assert call_kwargs["global_state"] == mock_global_state


# === Test Class: WebSocket Initialize Context File ===


class TestWebSocketInitializeContextFile:
    """Tests that /initialize writes CONTEXT.md to workspace."""

    @pytest.mark.asyncio
    @patch("wxcode.api.output_projects.OutputProject")
    @patch("wxcode.api.output_projects.Stack")
    @patch("wxcode.api.output_projects.extract_schema_for_configuration")
    @patch("wxcode.api.output_projects.extract_connections_for_project")
    @patch("wxcode.api.output_projects.extract_global_state_for_project")
    @patch("wxcode.api.output_projects.PromptBuilder")
    @patch("wxcode.api.output_projects.GSDInvoker")
    async def test_writes_context_md_to_workspace(
        self,
        mock_gsd_invoker_class,
        mock_prompt_builder,
        mock_extract_global_state,
        mock_extract_connections,
        mock_extract_schema,
        mock_stack_model,
        mock_output_project_model,
        mock_websocket,
        mock_output_project,
        mock_stack,
        mock_connections,
        mock_global_state,
        mock_tables,
    ):
        """Verify CONTEXT.md path is derived from workspace_path."""
        # Setup mocks
        mock_output_project_model.get = AsyncMock(return_value=mock_output_project)
        mock_stack_model.find_one = AsyncMock(return_value=mock_stack)
        mock_extract_schema.return_value = mock_tables
        mock_extract_connections.return_value = mock_connections
        mock_extract_global_state.return_value = mock_global_state

        expected_context_path = Path(mock_output_project.workspace_path) / "CONTEXT.md"
        mock_prompt_builder.write_context_file.return_value = expected_context_path

        # Setup GSD invoker mock
        mock_invoker = MagicMock()
        mock_invoker.invoke_with_streaming = AsyncMock(return_value=0)
        mock_gsd_invoker_class.return_value = mock_invoker

        # Call endpoint
        await initialize_output_project(mock_websocket, "507f1f77bcf86cd799439011")

        # Verify workspace_path passed to write_context_file
        call_kwargs = mock_prompt_builder.write_context_file.call_args.kwargs
        assert call_kwargs["workspace_path"] == Path(mock_output_project.workspace_path)

    @pytest.mark.asyncio
    @patch("wxcode.api.output_projects.OutputProject")
    @patch("wxcode.api.output_projects.Stack")
    @patch("wxcode.api.output_projects.extract_schema_for_configuration")
    @patch("wxcode.api.output_projects.extract_connections_for_project")
    @patch("wxcode.api.output_projects.extract_global_state_for_project")
    @patch("wxcode.api.output_projects.PromptBuilder")
    @patch("wxcode.api.output_projects.GSDInvoker")
    async def test_websocket_reports_context_created(
        self,
        mock_gsd_invoker_class,
        mock_prompt_builder,
        mock_extract_global_state,
        mock_extract_connections,
        mock_extract_schema,
        mock_stack_model,
        mock_output_project_model,
        mock_websocket,
        mock_output_project,
        mock_stack,
        mock_connections,
        mock_global_state,
        mock_tables,
    ):
        """Verify WebSocket receives message about CONTEXT.md creation."""
        # Setup mocks
        mock_output_project_model.get = AsyncMock(return_value=mock_output_project)
        mock_stack_model.find_one = AsyncMock(return_value=mock_stack)
        mock_extract_schema.return_value = mock_tables
        mock_extract_connections.return_value = mock_connections
        mock_extract_global_state.return_value = mock_global_state

        context_path = Path(mock_output_project.workspace_path) / "CONTEXT.md"
        mock_prompt_builder.write_context_file.return_value = context_path

        # Setup GSD invoker mock
        mock_invoker = MagicMock()
        mock_invoker.invoke_with_streaming = AsyncMock(return_value=0)
        mock_gsd_invoker_class.return_value = mock_invoker

        # Call endpoint
        await initialize_output_project(mock_websocket, "507f1f77bcf86cd799439011")

        # Check WebSocket messages include CONTEXT.md creation
        info_messages = [m for m in mock_websocket.sent_messages if m.get("type") == "info"]
        context_messages = [m for m in info_messages if "CONTEXT.md" in m.get("message", "")]
        assert len(context_messages) >= 1, "Expected at least one message about CONTEXT.md"

    @pytest.mark.asyncio
    @patch("wxcode.api.output_projects.OutputProject")
    @patch("wxcode.api.output_projects.Stack")
    @patch("wxcode.api.output_projects.extract_schema_for_configuration")
    @patch("wxcode.api.output_projects.extract_connections_for_project")
    @patch("wxcode.api.output_projects.extract_global_state_for_project")
    @patch("wxcode.api.output_projects.PromptBuilder")
    @patch("wxcode.api.output_projects.GSDInvoker")
    async def test_websocket_reports_connections_count(
        self,
        mock_gsd_invoker_class,
        mock_prompt_builder,
        mock_extract_global_state,
        mock_extract_connections,
        mock_extract_schema,
        mock_stack_model,
        mock_output_project_model,
        mock_websocket,
        mock_output_project,
        mock_stack,
        mock_connections,
        mock_global_state,
        mock_tables,
    ):
        """Verify WebSocket receives message about connections count."""
        # Setup mocks
        mock_output_project_model.get = AsyncMock(return_value=mock_output_project)
        mock_stack_model.find_one = AsyncMock(return_value=mock_stack)
        mock_extract_schema.return_value = mock_tables
        mock_extract_connections.return_value = mock_connections
        mock_extract_global_state.return_value = mock_global_state

        context_path = Path(mock_output_project.workspace_path) / "CONTEXT.md"
        mock_prompt_builder.write_context_file.return_value = context_path

        # Setup GSD invoker mock
        mock_invoker = MagicMock()
        mock_invoker.invoke_with_streaming = AsyncMock(return_value=0)
        mock_gsd_invoker_class.return_value = mock_invoker

        # Call endpoint
        await initialize_output_project(mock_websocket, "507f1f77bcf86cd799439011")

        # Check WebSocket messages include connections count
        info_messages = [m for m in mock_websocket.sent_messages if m.get("type") == "info"]
        connections_messages = [m for m in info_messages if "conexao" in m.get("message", "").lower() or "conexoes" in m.get("message", "").lower()]
        assert len(connections_messages) >= 1, "Expected at least one message about connections"

        # Verify count mentioned
        assert any("2" in m.get("message", "") for m in connections_messages), "Expected connections count in message"

    @pytest.mark.asyncio
    @patch("wxcode.api.output_projects.OutputProject")
    @patch("wxcode.api.output_projects.Stack")
    @patch("wxcode.api.output_projects.extract_schema_for_configuration")
    @patch("wxcode.api.output_projects.extract_connections_for_project")
    @patch("wxcode.api.output_projects.extract_global_state_for_project")
    @patch("wxcode.api.output_projects.PromptBuilder")
    @patch("wxcode.api.output_projects.GSDInvoker")
    async def test_websocket_reports_global_state_count(
        self,
        mock_gsd_invoker_class,
        mock_prompt_builder,
        mock_extract_global_state,
        mock_extract_connections,
        mock_extract_schema,
        mock_stack_model,
        mock_output_project_model,
        mock_websocket,
        mock_output_project,
        mock_stack,
        mock_connections,
        mock_global_state,
        mock_tables,
    ):
        """Verify WebSocket receives message about global state variable count."""
        # Setup mocks
        mock_output_project_model.get = AsyncMock(return_value=mock_output_project)
        mock_stack_model.find_one = AsyncMock(return_value=mock_stack)
        mock_extract_schema.return_value = mock_tables
        mock_extract_connections.return_value = mock_connections
        mock_extract_global_state.return_value = mock_global_state

        context_path = Path(mock_output_project.workspace_path) / "CONTEXT.md"
        mock_prompt_builder.write_context_file.return_value = context_path

        # Setup GSD invoker mock
        mock_invoker = MagicMock()
        mock_invoker.invoke_with_streaming = AsyncMock(return_value=0)
        mock_gsd_invoker_class.return_value = mock_invoker

        # Call endpoint
        await initialize_output_project(mock_websocket, "507f1f77bcf86cd799439011")

        # Check WebSocket messages include global state info
        info_messages = [m for m in mock_websocket.sent_messages if m.get("type") == "info"]
        global_messages = [m for m in info_messages if "global" in m.get("message", "").lower() or "variavel" in m.get("message", "").lower()]
        assert len(global_messages) >= 1, "Expected at least one message about global state"

        # Verify count mentioned
        assert any("2" in m.get("message", "") for m in global_messages), "Expected global variable count in message"


# === Test Class: WebSocket Initialize Edge Cases ===


class TestWebSocketInitializeEdgeCases:
    """Tests for edge cases in /initialize endpoint."""

    @pytest.mark.asyncio
    @patch("wxcode.api.output_projects.OutputProject")
    @patch("wxcode.api.output_projects.Stack")
    @patch("wxcode.api.output_projects.extract_schema_for_configuration")
    @patch("wxcode.api.output_projects.extract_connections_for_project")
    @patch("wxcode.api.output_projects.extract_global_state_for_project")
    @patch("wxcode.api.output_projects.PromptBuilder")
    @patch("wxcode.api.output_projects.GSDInvoker")
    async def test_handles_empty_connections(
        self,
        mock_gsd_invoker_class,
        mock_prompt_builder,
        mock_extract_global_state,
        mock_extract_connections,
        mock_extract_schema,
        mock_stack_model,
        mock_output_project_model,
        mock_websocket,
        mock_output_project,
        mock_stack,
        mock_global_state,
        mock_tables,
    ):
        """Verify endpoint handles empty connections list gracefully."""
        # Setup mocks with empty connections
        mock_output_project_model.get = AsyncMock(return_value=mock_output_project)
        mock_stack_model.find_one = AsyncMock(return_value=mock_stack)
        mock_extract_schema.return_value = mock_tables
        mock_extract_connections.return_value = []  # Empty connections
        mock_extract_global_state.return_value = mock_global_state
        mock_prompt_builder.write_context_file.return_value = Path(mock_output_project.workspace_path) / "CONTEXT.md"

        # Setup GSD invoker mock
        mock_invoker = MagicMock()
        mock_invoker.invoke_with_streaming = AsyncMock(return_value=0)
        mock_gsd_invoker_class.return_value = mock_invoker

        # Call endpoint - should not raise
        await initialize_output_project(mock_websocket, "507f1f77bcf86cd799439011")

        # Verify empty connections passed through
        call_kwargs = mock_prompt_builder.write_context_file.call_args.kwargs
        assert call_kwargs["connections"] == []

    @pytest.mark.asyncio
    @patch("wxcode.api.output_projects.OutputProject")
    @patch("wxcode.api.output_projects.Stack")
    @patch("wxcode.api.output_projects.extract_schema_for_configuration")
    @patch("wxcode.api.output_projects.extract_connections_for_project")
    @patch("wxcode.api.output_projects.extract_global_state_for_project")
    @patch("wxcode.api.output_projects.PromptBuilder")
    @patch("wxcode.api.output_projects.GSDInvoker")
    async def test_handles_empty_global_state(
        self,
        mock_gsd_invoker_class,
        mock_prompt_builder,
        mock_extract_global_state,
        mock_extract_connections,
        mock_extract_schema,
        mock_stack_model,
        mock_output_project_model,
        mock_websocket,
        mock_output_project,
        mock_stack,
        mock_connections,
        mock_tables,
    ):
        """Verify endpoint handles empty global state gracefully."""
        # Create empty global state
        empty_global_state = MockGlobalStateContext(variables=[], initialization_blocks=[])

        # Setup mocks
        mock_output_project_model.get = AsyncMock(return_value=mock_output_project)
        mock_stack_model.find_one = AsyncMock(return_value=mock_stack)
        mock_extract_schema.return_value = mock_tables
        mock_extract_connections.return_value = mock_connections
        mock_extract_global_state.return_value = empty_global_state
        mock_prompt_builder.write_context_file.return_value = Path(mock_output_project.workspace_path) / "CONTEXT.md"

        # Setup GSD invoker mock
        mock_invoker = MagicMock()
        mock_invoker.invoke_with_streaming = AsyncMock(return_value=0)
        mock_gsd_invoker_class.return_value = mock_invoker

        # Call endpoint - should not raise
        await initialize_output_project(mock_websocket, "507f1f77bcf86cd799439011")

        # Verify empty global state passed through
        call_kwargs = mock_prompt_builder.write_context_file.call_args.kwargs
        assert call_kwargs["global_state"] == empty_global_state

    @pytest.mark.asyncio
    @patch("wxcode.api.output_projects.OutputProject")
    async def test_invalid_project_id_returns_error(
        self,
        mock_output_project_model,
        mock_websocket,
    ):
        """Verify invalid project ID returns error via WebSocket."""
        # Call endpoint with invalid ID
        await initialize_output_project(mock_websocket, "invalid-id")

        # Check for error message
        error_messages = [m for m in mock_websocket.sent_messages if m.get("type") == "error"]
        assert len(error_messages) >= 1, "Expected error message for invalid ID"

    @pytest.mark.asyncio
    @patch("wxcode.api.output_projects.OutputProject")
    async def test_project_not_found_returns_error(
        self,
        mock_output_project_model,
        mock_websocket,
    ):
        """Verify non-existent project returns error via WebSocket."""
        # Setup mock to return None
        mock_output_project_model.get = AsyncMock(return_value=None)

        # Call endpoint
        await initialize_output_project(mock_websocket, "507f1f77bcf86cd799439011")

        # Check for error message
        error_messages = [m for m in mock_websocket.sent_messages if m.get("type") == "error"]
        assert len(error_messages) >= 1, "Expected error message for non-existent project"
        assert any("nao encontrado" in m.get("message", "").lower() for m in error_messages)


# === Test Class: Full Flow Integration ===


class TestWebSocketInitializeFullFlow:
    """Tests for complete initialization flow."""

    @pytest.mark.asyncio
    @patch("wxcode.api.output_projects.OutputProject")
    @patch("wxcode.api.output_projects.Stack")
    @patch("wxcode.api.output_projects.extract_schema_for_configuration")
    @patch("wxcode.api.output_projects.extract_connections_for_project")
    @patch("wxcode.api.output_projects.extract_global_state_for_project")
    @patch("wxcode.api.output_projects.PromptBuilder")
    @patch("wxcode.api.output_projects.GSDInvoker")
    async def test_full_flow_success(
        self,
        mock_gsd_invoker_class,
        mock_prompt_builder,
        mock_extract_global_state,
        mock_extract_connections,
        mock_extract_schema,
        mock_stack_model,
        mock_output_project_model,
        mock_websocket,
        mock_output_project,
        mock_stack,
        mock_connections,
        mock_global_state,
        mock_tables,
    ):
        """Verify complete successful flow from start to finish."""
        # Setup mocks
        mock_output_project_model.get = AsyncMock(return_value=mock_output_project)
        mock_stack_model.find_one = AsyncMock(return_value=mock_stack)
        mock_extract_schema.return_value = mock_tables
        mock_extract_connections.return_value = mock_connections
        mock_extract_global_state.return_value = mock_global_state
        mock_prompt_builder.write_context_file.return_value = Path(mock_output_project.workspace_path) / "CONTEXT.md"

        # Setup GSD invoker mock for success
        mock_invoker = MagicMock()
        mock_invoker.invoke_with_streaming = AsyncMock(return_value=0)
        mock_gsd_invoker_class.return_value = mock_invoker

        # Call endpoint
        await initialize_output_project(mock_websocket, "507f1f77bcf86cd799439011")

        # Verify all extractors called
        mock_extract_schema.assert_called_once()
        mock_extract_connections.assert_called_once()
        mock_extract_global_state.assert_called_once()

        # Verify PromptBuilder called
        mock_prompt_builder.write_context_file.assert_called_once()

        # Verify GSD invoker called
        mock_gsd_invoker_class.assert_called_once()
        mock_invoker.invoke_with_streaming.assert_called_once()

        # Verify WebSocket accept called
        mock_websocket.accept.assert_called_once()

        # Verify complete message sent
        complete_messages = [m for m in mock_websocket.sent_messages if m.get("type") == "complete"]
        assert len(complete_messages) == 1, "Expected one complete message"

    @pytest.mark.asyncio
    @patch("wxcode.api.output_projects.OutputProject")
    @patch("wxcode.api.output_projects.Stack")
    @patch("wxcode.api.output_projects.extract_schema_for_configuration")
    @patch("wxcode.api.output_projects.extract_connections_for_project")
    @patch("wxcode.api.output_projects.extract_global_state_for_project")
    @patch("wxcode.api.output_projects.PromptBuilder")
    @patch("wxcode.api.output_projects.GSDInvoker")
    async def test_gsd_failure_returns_error(
        self,
        mock_gsd_invoker_class,
        mock_prompt_builder,
        mock_extract_global_state,
        mock_extract_connections,
        mock_extract_schema,
        mock_stack_model,
        mock_output_project_model,
        mock_websocket,
        mock_output_project,
        mock_stack,
        mock_connections,
        mock_global_state,
        mock_tables,
    ):
        """Verify GSD failure returns error via WebSocket."""
        # Setup mocks
        mock_output_project_model.get = AsyncMock(return_value=mock_output_project)
        mock_stack_model.find_one = AsyncMock(return_value=mock_stack)
        mock_extract_schema.return_value = mock_tables
        mock_extract_connections.return_value = mock_connections
        mock_extract_global_state.return_value = mock_global_state
        mock_prompt_builder.write_context_file.return_value = Path(mock_output_project.workspace_path) / "CONTEXT.md"

        # Setup GSD invoker mock for failure
        mock_invoker = MagicMock()
        mock_invoker.invoke_with_streaming = AsyncMock(return_value=1)  # Non-zero exit code
        mock_gsd_invoker_class.return_value = mock_invoker

        # Call endpoint
        await initialize_output_project(mock_websocket, "507f1f77bcf86cd799439011")

        # Verify error message sent
        error_messages = [m for m in mock_websocket.sent_messages if m.get("type") == "error"]
        assert len(error_messages) >= 1, "Expected error message for GSD failure"
        assert any("codigo de erro" in m.get("message", "").lower() for m in error_messages)
