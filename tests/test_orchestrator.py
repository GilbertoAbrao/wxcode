"""Tests for GeneratorOrchestrator.

Tests the orchestration of all generators and project structure generation.
"""

import tempfile
from pathlib import Path

import pytest

from wxcode.generator.orchestrator import GeneratorOrchestrator, OrchestratorResult


class TestOrchestratorResult:
    """Tests for OrchestratorResult class."""

    def test_summary_success(self):
        """Test summary for successful generation."""
        result = OrchestratorResult(
            project_id="test123",
            output_dir=Path("/tmp/test"),
            success=True,
            total_files=10,
        )
        result.generators = [
            type("Progress", (), {"name": "schema", "status": "completed", "files_generated": 3, "error": None})(),
            type("Progress", (), {"name": "domain", "status": "completed", "files_generated": 7, "error": None})(),
        ]

        summary = result.summary()

        assert "completed" in summary
        assert "10" in summary
        assert "schema" in summary
        assert "domain" in summary

    def test_summary_with_errors(self):
        """Test summary with errors."""
        result = OrchestratorResult(
            project_id="test123",
            output_dir=Path("/tmp/test"),
            success=False,
            total_files=5,
            errors=["schema: Database error", "domain: Parse error"],
        )

        summary = result.summary()

        assert "failed" in summary
        assert "Database error" in summary
        assert "Parse error" in summary


class TestGeneratorOrchestrator:
    """Tests for GeneratorOrchestrator class."""

    @pytest.fixture
    def output_dir(self) -> Path:
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def orchestrator(self, output_dir: Path) -> GeneratorOrchestrator:
        """Create a GeneratorOrchestrator instance."""
        return GeneratorOrchestrator("507f1f77bcf86cd799439011", output_dir)

    # Test initialization
    def test_init(self, orchestrator: GeneratorOrchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.project_id == "507f1f77bcf86cd799439011"
        assert orchestrator.output_dir is not None

    def test_generator_order(self, orchestrator: GeneratorOrchestrator):
        """Test generator order is correct."""
        order = [name for name, _ in orchestrator.GENERATOR_ORDER]

        assert order == ["schema", "domain", "service", "route", "api", "template"]

    # Test project structure generation
    def test_generate_main_py(self, orchestrator: GeneratorOrchestrator):
        """Test main.py generation."""
        orchestrator._generate_project_structure()

        main_path = orchestrator.output_dir / "app/main.py"
        assert main_path.exists()

        content = main_path.read_text()
        assert "FastAPI" in content
        assert "lifespan" in content
        assert "static" in content
        assert "templates" in content

    def test_generate_config_py(self, orchestrator: GeneratorOrchestrator):
        """Test config.py generation."""
        orchestrator._generate_project_structure()

        config_path = orchestrator.output_dir / "app/config.py"
        assert config_path.exists()

        content = config_path.read_text()
        assert "Settings" in content
        assert "database_url" in content
        assert "secret_key" in content

    def test_generate_database_py(self, orchestrator: GeneratorOrchestrator):
        """Test database.py generation."""
        orchestrator._generate_project_structure()

        db_path = orchestrator.output_dir / "app/database.py"
        assert db_path.exists()

        content = db_path.read_text()
        assert "AsyncIOMotorClient" in content
        assert "init_db" in content
        assert "close_db" in content

    def test_generate_pyproject_toml(self, orchestrator: GeneratorOrchestrator):
        """Test pyproject.toml generation."""
        orchestrator._generate_project_structure()

        toml_path = orchestrator.output_dir / "pyproject.toml"
        assert toml_path.exists()

        content = toml_path.read_text()
        assert "fastapi" in content
        assert "uvicorn" in content
        assert "motor" in content
        assert "beanie" in content
        assert "jinja2" in content

    def test_generate_dockerfile(self, orchestrator: GeneratorOrchestrator):
        """Test Dockerfile generation."""
        orchestrator._generate_project_structure()

        dockerfile_path = orchestrator.output_dir / "Dockerfile"
        assert dockerfile_path.exists()

        content = dockerfile_path.read_text()
        assert "python:3.11" in content
        assert "uvicorn" in content
        assert "8000" in content

    def test_generate_docker_compose(self, orchestrator: GeneratorOrchestrator):
        """Test docker-compose.yml generation."""
        orchestrator._generate_project_structure()

        compose_path = orchestrator.output_dir / "docker-compose.yml"
        assert compose_path.exists()

        content = compose_path.read_text()
        assert "mongo" in content
        assert "8000:8000" in content
        assert "mongo_data" in content

    def test_generate_env_example(self, orchestrator: GeneratorOrchestrator):
        """Test .env.example generation."""
        orchestrator._generate_project_structure()

        env_path = orchestrator.output_dir / ".env.example"
        assert env_path.exists()

        content = env_path.read_text()
        assert "DATABASE_URL" in content
        assert "SECRET_KEY" in content

    def test_generate_init_files(self, orchestrator: GeneratorOrchestrator):
        """Test __init__.py files generation."""
        orchestrator._generate_project_structure()

        app_init = orchestrator.output_dir / "app/__init__.py"
        tests_init = orchestrator.output_dir / "tests/__init__.py"

        assert app_init.exists()
        assert tests_init.exists()

    def test_directory_structure(self, orchestrator: GeneratorOrchestrator):
        """Test correct directory structure is created."""
        orchestrator._generate_project_structure()

        expected_dirs = [
            "app",
            "app/api",
            "app/models",
            "app/routes",
            "app/services",
            "app/templates",
            "app/templates/pages",
            "app/static",
            "app/static/css",
            "app/static/js",
            "tests",
        ]

        for dir_name in expected_dirs:
            dir_path = orchestrator.output_dir / dir_name
            assert dir_path.exists(), f"Directory {dir_name} should exist"
            assert dir_path.is_dir(), f"{dir_name} should be a directory"

    # Test layer generation
    def test_generate_layer_invalid(self, orchestrator: GeneratorOrchestrator):
        """Test error for invalid layer."""
        with pytest.raises(ValueError) as exc_info:
            import asyncio
            asyncio.run(orchestrator.generate_layer("invalid_layer"))

        assert "Unknown layer" in str(exc_info.value)

    def test_valid_layers(self, orchestrator: GeneratorOrchestrator):
        """Test all valid layer names."""
        valid_layers = ["schema", "domain", "service", "route", "api", "template"]

        for layer in valid_layers:
            # Just check that the layer is recognized (don't actually run)
            layer_map = dict(orchestrator.GENERATOR_ORDER)
            assert layer in layer_map, f"Layer {layer} should be valid"


class TestGeneratorOrchestratorFiles:
    """Test generated file contents."""

    @pytest.fixture
    def output_dir(self) -> Path:
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def orchestrator(self, output_dir: Path) -> GeneratorOrchestrator:
        """Create a GeneratorOrchestrator instance."""
        orch = GeneratorOrchestrator("507f1f77bcf86cd799439011", output_dir)
        orch._generate_project_structure()
        return orch

    def test_main_py_has_routers(self, orchestrator: GeneratorOrchestrator):
        """Test main.py includes routers."""
        content = (orchestrator.output_dir / "app/main.py").read_text()

        assert "from app.routes import" in content
        assert "from app.api import" in content
        assert "include_router" in content

    def test_main_py_has_health_endpoint(self, orchestrator: GeneratorOrchestrator):
        """Test main.py has health check."""
        content = (orchestrator.output_dir / "app/main.py").read_text()

        assert '@app.get("/health")' in content
        assert '"status": "healthy"' in content

    def test_config_uses_pydantic_settings(self, orchestrator: GeneratorOrchestrator):
        """Test config uses pydantic-settings."""
        content = (orchestrator.output_dir / "app/config.py").read_text()

        assert "from pydantic_settings import" in content
        assert "BaseSettings" in content
        assert ".env" in content

    def test_database_is_async(self, orchestrator: GeneratorOrchestrator):
        """Test database module is async."""
        content = (orchestrator.output_dir / "app/database.py").read_text()

        assert "async def init_db" in content
        assert "async def close_db" in content
        assert "AsyncIOMotorClient" in content

    def test_pyproject_has_dev_dependencies(self, orchestrator: GeneratorOrchestrator):
        """Test pyproject.toml has dev dependencies."""
        content = (orchestrator.output_dir / "pyproject.toml").read_text()

        assert "[project.optional-dependencies]" in content
        assert "pytest" in content
        assert "ruff" in content
        assert "mypy" in content

    def test_pyproject_has_tool_configs(self, orchestrator: GeneratorOrchestrator):
        """Test pyproject.toml has tool configurations."""
        content = (orchestrator.output_dir / "pyproject.toml").read_text()

        assert "[tool.pytest.ini_options]" in content
        assert "[tool.ruff]" in content
        assert "[tool.mypy]" in content

    def test_dockerfile_is_multi_stage_ready(self, orchestrator: GeneratorOrchestrator):
        """Test Dockerfile uses slim base image."""
        content = (orchestrator.output_dir / "Dockerfile").read_text()

        assert "python:3.11-slim" in content
        assert "--no-cache-dir" in content

    def test_docker_compose_has_volumes(self, orchestrator: GeneratorOrchestrator):
        """Test docker-compose has persistent volumes."""
        content = (orchestrator.output_dir / "docker-compose.yml").read_text()

        assert "volumes:" in content
        assert "mongo_data" in content
        assert "/data/db" in content


class TestOrchestratorResultCounts:
    """Test that OrchestratorResult correctly tracks file counts."""

    @pytest.fixture
    def output_dir(self) -> Path:
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_write_file_increments_count(self, output_dir: Path):
        """Test that _write_file increments total_files."""
        orchestrator = GeneratorOrchestrator("test123", output_dir)

        initial_count = orchestrator.result.total_files

        orchestrator._write_file("test.txt", "content")

        assert orchestrator.result.total_files == initial_count + 1

    def test_project_structure_file_count(self, output_dir: Path):
        """Test file count after generating project structure."""
        orchestrator = GeneratorOrchestrator("test123", output_dir)

        orchestrator._generate_project_structure()

        # Should have generated: main.py, config.py, database.py, pyproject.toml,
        # Dockerfile, docker-compose.yml, .env.example, and 2 __init__.py files
        assert orchestrator.result.total_files >= 9
