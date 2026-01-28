# Testing Patterns

**Analysis Date:** 2026-01-21

## Test Framework

**Runner:**
- Framework: `pytest` (configured in `pytest.ini`)
- Version: Latest (no explicit version pin in pyproject.toml)
- Config file: `pytest.ini` at project root

**Pytest Configuration:**
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
```

**Key Settings:**
- `asyncio_mode = auto` - Automatically runs async tests without decorators
- Test discovery: Files matching `test_*.py`, functions matching `test_*`
- Output: Verbose (`-v`), short tracebacks (`--tb=short`)

**Type Checking:**
- Framework: `mypy`
- Config: `mypy.ini` at project root
- Mode: `strict = True` - Maximum strictness

**Mypy Configuration:**
```ini
[mypy]
python_version = 3.11
strict = True
warn_return_any = True
warn_unused_ignores = True
```

**Run Commands:**
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_analyzer.py

# Run specific test class
pytest tests/test_analyzer.py::TestNodeType

# Run with verbose output
pytest -v

# Watch mode (requires pytest-watch)
ptw

# Coverage report
pytest --cov=src/wxcode --cov-report=html

# Specific pattern
pytest -k "test_procedure_call"
```

## Test File Organization

**Location Pattern:**
- Source: `src/wxcode/<module>/<file>.py`
- Tests: `tests/test_<file>.py` (flat structure) OR `tests/<module>/test_<file>.py` (mirrored structure)

**Actual Layout:**
```
tests/
├── test_analyzer.py                    # Tests for src/wxcode/analyzer
├── test_chat_agent.py                  # Tests for src/wxcode/services
├── test_dependency_extractor.py        # Tests for src/wxcode/parser
├── test_wdg_parser.py                  # Tests for src/wxcode/parser/wdg_parser.py
├── test_schema_generator.py            # Tests for src/wxcode/generator
├── integration/
│   ├── test_binding_extraction.py
│   ├── test_dashlite_theme.py
│   └── test_database_connections_pipeline.py
└── parser/
    └── test_project_mapper.py          # Tests for src/wxcode/parser/project_mapper.py
```

**Naming Convention:**
- Test class: `Test<ComponentName>` (e.g., `TestNodeType`, `TestGraphEdge`, `TestSchemaGenerator`)
- Test method: `test_<behavior_or_condition>` (e.g., `test_node_types_exist`, `test_simple_procedure_call`)
- Parametrized tests: Use `@pytest.mark.parametrize`

## Test Structure

**Test Class Organization:**
```python
class TestComponentName:
    """Testes para ComponentName."""

    @pytest.fixture
    def component(self):
        """Create component instance."""
        return ComponentName(...)

    def test_feature_1(self, component):
        """Describes what is tested."""
        # Arrange (setup)
        expected = "value"

        # Act
        result = component.method()

        # Assert
        assert result == expected

    def test_feature_2_with_edge_case(self):
        """Test edge case."""
        # Standalone test without fixture
        obj = TestClass()
        assert obj.property == "expected"
```

**File-Level Fixtures:**
```python
# tests/test_schema_generator.py
class TestSchemaGenerator:
    @pytest.fixture
    def output_dir(self) -> Path:
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def generator(self, output_dir: Path) -> SchemaGenerator:
        """Create a SchemaGenerator instance."""
        return SchemaGenerator("507f1f77bcf86cd799439011", output_dir)
```

**Docstring Style:**
- Short: `"""Test description in Portuguese."""`
- Long: Include context and what is tested
- Example: `"""Testa criação de parâmetro simples."""`

## Test Patterns

**Setup Method Pattern:**
```python
class TestDependencyExtractor:
    """Testes para o DependencyExtractor."""

    def setup_method(self):
        """Inicializa o extrator."""
        self.extractor = DependencyExtractor()

    def test_simple_procedure_call(self):
        """Testa chamada de procedure simples."""
        code = "resultado = BuscaCEP(sCEP)"
        deps = self.extractor.extract(code)
        assert "BuscaCEP" in deps.calls_procedures
```

**Fixture with Parameters:**
```python
@pytest.fixture
def schema_table() -> SchemaTable:
    """Create a test schema table."""
    return SchemaTable(
        name="CLIENTE",
        table_code=1,
        columns=[
            SchemaColumn(name="id", column_code=1, type_code=4),
            SchemaColumn(name="nome", column_code=2, type_code=2),
        ]
    )
```

**Parametrized Tests:**
```python
@pytest.mark.parametrize("input_val,expected", [
    ("ClienteService", "cliente_service"),
    ("HTTPClient", "h_t_t_p_client"),
    ("PAGE_Login", "page_login"),
])
def test_to_snake_case(self, generator, input_val, expected):
    """Test snake_case conversion."""
    assert generator._to_snake_case(input_val) == expected
```

**Async Test Pattern:**
```python
# With asyncio_mode=auto, no decorator needed
async def test_async_operation(self):
    """Test async method."""
    result = await some_async_function()
    assert result is not None

# Or in a class
class TestAsyncOperations:
    async def test_save_element(self, element):
        """Test saving element."""
        await element.save()
        retrieved = await Element.find_one({"source_name": element.source_name})
        assert retrieved is not None
```

## Mocking & Test Doubles

**Framework:** `unittest.mock` (standard library)

**Import Pattern:**
```python
from unittest.mock import AsyncMock, MagicMock, patch, Mock
```

**Mock Control Type:**
```python
# tests/test_template_generator.py
def test_get_control_type_name_edit(self, generator):
    """Test Edit control type detection."""
    control = MagicMock()
    control.name = "EDT_Nome"
    control.type_code = 8

    result = generator._get_control_type_name(control)
    assert result == "Edit"
```

**Async Mock:**
```python
@pytest.fixture
def mock_db_client():
    """Mock async MongoDB client."""
    client = AsyncMock()
    client.find_one.return_value = Element(...)
    return client

async def test_with_async_mock(self, mock_db_client):
    """Test with async mock."""
    result = await mock_db_client.find_one(...)
    assert result is not None
```

**Patching Pattern:**
```python
from unittest.mock import patch

def test_with_patch(self):
    """Test with patched dependency."""
    with patch('wxcode.parser.wwh_parser.WdhParser') as MockParser:
        MockParser.return_value.parse.return_value = {"controls": []}
        # Test logic using mocked parser
```

**What to Mock:**
- External I/O: Database, filesystem, HTTP (unless integration test)
- Complex dependencies: Large parsers, generator orchestrators
- Time/random: Use `monkeypatch` or `freezegun` if time-dependent

**What NOT to Mock:**
- Simple value objects (dataclasses, Pydantic models)
- Pure functions with no side effects
- Internal helper methods (test through public interface)
- Constants and enums

## Fixtures and Factories

**Test Data Factories:**

**Element Factory:**
```python
# Used in multiple test files
def create_test_element(
    project_id: ObjectId,
    source_type: ElementType = ElementType.PAGE,
    source_name: str = "TEST_PAGE"
) -> Element:
    """Create a test Element."""
    return Element(
        project_id=project_id,
        source_type=source_type,
        source_name=source_name,
        source_file=f"{source_name}.wwh",
        raw_content="test content",
        dependencies=ElementDependencies(),
        conversion=ElementConversion()
    )
```

**Project Fixture:**
```python
@pytest.fixture
def sample_project():
    """Create a sample project."""
    return Project(
        name="TestProject",
        source_path="/path/to/test.wwp",
        major_version=26,
        project_type=4097
    )
```

**Parsed Data Structures:**
```python
# tests/test_wdg_parser.py - used for parsed procedure tests
class TestParsedProcedureSet:
    def test_total_procedures(self):
        """Testa contagem de procedures."""
        proc_set = ParsedProcedureSet(
            name="Util",
            procedures=[
                ParsedProcedure(name="Proc1", code_lines=10),
                ParsedProcedure(name="Proc2", code_lines=20),
                ParsedProcedure(name="Proc3", code_lines=15),
            ]
        )
        assert proc_set.total_procedures == 3
```

**Fixture Location:**
- **File-scoped**: `@pytest.fixture` in test file
- **Module-scoped**: `@pytest.fixture(scope="module")` for expensive setup
- **Global**: `conftest.py` (not found in this project - can be added if needed)

## Coverage

**Requirements:** No explicit coverage target enforced (no `.coveragerc`)

**View Coverage:**
```bash
# Generate coverage report
pytest --cov=src/wxcode --cov-report=html

# View HTML report
open htmlcov/index.html

# Terminal report
pytest --cov=src/wxcode --cov-report=term-missing
```

**Coverage Configuration File:**
Currently not enforced. Coverage is tracked but not gated.

## Test Types

**Unit Tests:**
- Scope: Individual functions, methods, small classes
- File pattern: `tests/test_<module>.py`
- Examples:
  - `test_dependency_extractor.py` - Tests individual extraction functions
  - `test_analyzer.py` - Tests graph node/edge models
  - `test_schema_generator.py` - Tests type mapping functions
- Setup: Minimal dependencies (mocked when needed)
- Speed: Fast (< 1s per test)

**Integration Tests:**
- Scope: Multiple components working together
- Location: `tests/integration/`
- Examples:
  - `test_database_connections_pipeline.py` - End-to-end DB connection parsing
  - `test_binding_extraction.py` - Control binding with PDF data
  - `test_dashlite_theme.py` - Full theme application
- Setup: May use real databases, file systems
- Speed: Slower (1-10s per test)

**E2E Tests:**
- Status: Not found in codebase
- Possible candidates: Full import-parse-analyze-convert pipeline

## Common Test Patterns

**Enum Value Testing:**
```python
# tests/test_analyzer.py
class TestNodeType:
    """Testes para NodeType enum."""

    def test_node_types_exist(self):
        """Verifica que todos os tipos de nó existem."""
        assert NodeType.TABLE.value == "table"
        assert NodeType.CLASS.value == "class"
        assert NodeType.PROCEDURE.value == "procedure"
        assert NodeType.PAGE.value == "page"
```

**String Conversion Testing:**
```python
# tests/test_schema_generator.py
@pytest.mark.parametrize("input_val,expected", [
    ("ClienteService", "cliente_service"),
    ("HTTPClient", "h_t_t_p_client"),
])
def test_to_snake_case(self, generator, input_val, expected):
    """Test snake_case conversion."""
    assert generator._to_snake_case(input_val) == expected
```

**Collection Testing:**
```python
def test_with_dependencies(self):
    """Testa dependências preenchidas."""
    deps = ExtractedDependencies(
        calls_procedures=["ValidaCPF", "FormataCNPJ"],
        uses_files=["CLIENTE", "PEDIDO"],
    )
    assert len(deps.calls_procedures) == 2
    assert "CLIENTE" in deps.uses_files
    assert deps.is_empty() is False
```

**Async Collection Testing:**
```python
async def test_process_elements(self):
    """Test processing multiple elements."""
    elements = [
        Element(source_name="PAGE_1", ...),
        Element(source_name="PAGE_2", ...),
    ]
    results = await process_batch(elements)
    assert len(results) == 2
```

**Exception Testing:**
```python
def test_parser_missing_file(self):
    """Testa que parser lança erro para arquivo inexistente."""
    with pytest.raises(FileNotFoundError):
        parser = WdgParser(Path("/nonexistent/file.wdg"))
```

**Property Testing:**
```python
def test_element_needs_chunking(self):
    """Testa se elemento precisa de chunking."""
    element = Element(
        raw_content="x" * 15000,  # ~3750 tokens
        ...
    )
    assert element.needs_chunking is True
```

**Dictionary/JSON Testing:**
```python
def test_type_map_coverage(self, generator):
    """Ensure TYPE_MAP covers common HyperFile types."""
    essential_types = [2, 4, 8, 10, 11, 13, 14, 24, 26]
    for type_code in essential_types:
        assert type_code in generator.TYPE_MAP, f"Type {type_code} not in TYPE_MAP"
```

## Test Statistics

**Total Test Count:** ~810 test functions across 35 files
- Files: `tests/test_*.py` (main), `tests/integration/*` (integration), `tests/parser/*` (specialized)
- Coverage: Parser, analyzer, generator, models, services

**Test Distribution:**
- Parser tests: `test_wdg_parser.py`, `test_xdd_parser.py`, `test_wwh_parser.py`, etc.
- Generator tests: `test_schema_generator.py`, `test_template_generator.py`, `test_route_generator.py`, `test_domain_generator.py`, `test_service_generator.py`
- Analyzer tests: `test_analyzer.py`, `test_impact_analyzer.py`
- Model tests: `test_configuration_models.py`, `test_data_binding.py`
- Integration tests: `tests/integration/` (3 files)
- Service tests: `test_chat_agent.py`, `test_theme_skill_loader.py`

## Error Handling in Tests

**FileNotFoundError:**
```python
def test_parser_file_not_found(self):
    """Test error handling for missing files."""
    with pytest.raises(FileNotFoundError):
        parser = WdgParser(Path("/nonexistent.wdg"))
```

**ValueError:**
```python
def test_invalid_type_conversion(self):
    """Test handling of invalid type."""
    with pytest.raises(ValueError):
        TypeConverter.convert("invalid", 4)
```

**Expected Test Failures:**
```python
@pytest.mark.xfail(reason="Feature not yet implemented")
def test_future_feature():
    """This test is expected to fail."""
    pass
```

---

*Testing analysis: 2026-01-21*
