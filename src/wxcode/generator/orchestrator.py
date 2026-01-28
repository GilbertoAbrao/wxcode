"""Generator Orchestrator - Coordinates all code generators.

Runs all generators in the correct order and produces a complete
FastAPI + Jinja2 application.

Supports selective element conversion via ElementFilter and
configuration-aware conversion via ConversionConfig.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from wxcode.models.conversion_config import ConversionConfig
from wxcode.models.configuration_context import ConfigurationContext
from wxcode.models.element import Element
from wxcode.models.global_state_context import GlobalStateContext
from wxcode.parser.compile_if_extractor import CompileIfExtractor
from wxcode.parser.global_state_extractor import GlobalStateExtractor

from .api_generator import APIGenerator
from .base import ElementFilter
from .domain_generator import DomainGenerator
from .python_config_generator import PythonConfigGenerator
from .python.state_generator import PythonStateGenerator
from .result import GenerationResult
from .route_generator import RouteGenerator
from .schema_generator import SchemaGenerator
from .service_generator import ServiceGenerator
from .state_generator import BaseStateGenerator
from .template_generator import TemplateGenerator


@dataclass
class GeneratorProgress:
    """Tracks progress of a single generator."""

    name: str
    status: str = "pending"  # pending, running, completed, failed
    files_generated: int = 0
    error: str | None = None


@dataclass
class OrchestratorResult:
    """Result of running all generators."""

    project_id: str
    output_dir: Path
    success: bool = True
    generators: list[GeneratorProgress] = field(default_factory=list)
    total_files: int = 0
    errors: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Generate a summary of the orchestration result."""
        lines = [
            f"Generation {'completed' if self.success else 'failed'}",
            f"Output: {self.output_dir}",
            f"Total files: {self.total_files}",
            "",
            "Generators:",
        ]

        for gen in self.generators:
            status_icon = (
                "[OK]" if gen.status == "completed" else
                "[FAIL]" if gen.status == "failed" else
                "[...]"
            )
            lines.append(f"  {status_icon} {gen.name}: {gen.files_generated} files")
            if gen.error:
                lines.append(f"       Error: {gen.error}")

        if self.errors:
            lines.append("")
            lines.append("Errors:")
            for err in self.errors:
                lines.append(f"  - {err}")

        return "\n".join(lines)


class GeneratorOrchestrator:
    """Orchestrates all code generators for a project.

    Runs generators in topological order to respect dependencies:
    1. Schema (database models)
    2. Domain (business entities)
    3. Service (business logic)
    4. Route (page routes)
    5. API (REST endpoints)
    6. Template (HTML templates)

    Also generates project structure files (main.py, config, docker, etc.)

    Supports selective element conversion via ElementFilter.
    """

    # Generator order based on dependencies
    GENERATOR_ORDER = [
        ("schema", SchemaGenerator),
        ("domain", DomainGenerator),
        ("service", ServiceGenerator),
        ("route", RouteGenerator),
        ("api", APIGenerator),
        ("template", TemplateGenerator),
    ]

    # State generators registry by stack name
    STATE_GENERATORS: dict[str, type[BaseStateGenerator]] = {
        "python": PythonStateGenerator,
        # Future: "node": NodeStateGenerator,
        # Future: "go": GoStateGenerator,
    }

    def __init__(
        self,
        project_id: str,
        output_dir: Path,
        element_filter: ElementFilter | None = None,
        stack: str = "python",
    ):
        """Initialize orchestrator.

        Args:
            project_id: MongoDB ObjectId string for the project
            output_dir: Root directory where files will be written
            element_filter: Optional filter for selective element conversion
            stack: Target stack for generation (default: "python")
        """
        self.project_id = project_id
        self.output_dir = Path(output_dir)
        self.element_filter = element_filter
        self.stack = stack
        self.result = OrchestratorResult(
            project_id=project_id,
            output_dir=self.output_dir,
        )

        # Validate stack
        if stack not in self.STATE_GENERATORS:
            available = ", ".join(self.STATE_GENERATORS.keys())
            raise ValueError(
                f"Unsupported stack '{stack}'. Available stacks: {available}"
            )

    async def generate_all(self) -> OrchestratorResult:
        """Run all generators and produce complete application.

        Passes element_filter to all generators for selective conversion.

        Returns:
            OrchestratorResult with details of the generation
        """
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Extract and generate global state files FIRST
        try:
            global_state_context = await self._extract_global_state()
            if global_state_context:
                state_files = await self._generate_state_files(global_state_context)
                self.result.total_files += len(state_files)
        except Exception as e:
            self.result.success = False
            self.result.errors.append(f"global_state: {e}")
            # Continue with other generators even if state generation fails

        # When doing selective conversion, we need to include converted elements
        # because the first generator may mark the element as converted,
        # and subsequent generators would not find it.
        filter_for_generators = self.element_filter
        if self.element_filter and not self.element_filter.include_converted:
            filter_for_generators = ElementFilter(
                element_ids=self.element_filter.element_ids,
                element_names=self.element_filter.element_names,
                include_converted=True,  # Force include converted for selective
            )

        # Run each generator in order
        for name, generator_class in self.GENERATOR_ORDER:
            progress = GeneratorProgress(name=name)
            self.result.generators.append(progress)

            try:
                progress.status = "running"
                # Pass element_filter to each generator
                generator = generator_class(
                    self.project_id, self.output_dir, filter_for_generators
                )
                files = await generator.generate()
                progress.files_generated = len(files)
                progress.status = "completed"
                self.result.total_files += len(files)

            except Exception as e:
                progress.status = "failed"
                progress.error = str(e)
                self.result.success = False
                self.result.errors.append(f"{name}: {e}")

        # Generate project structure files (only if no filter or full generation)
        if self.result.success and not self.element_filter:
            try:
                await self._generate_project_structure()
            except Exception as e:
                self.result.success = False
                self.result.errors.append(f"project_structure: {e}")

        return self.result

    async def generate_layer(
        self, layer: str, element_filter: ElementFilter | None = None
    ) -> list[Path]:
        """Generate only a specific layer.

        Args:
            layer: Layer name (schema, domain, service, route, api, template)
            element_filter: Optional filter for selective element conversion.
                           If None, uses instance's element_filter.

        Returns:
            List of generated file paths
        """
        generator_map = dict(self.GENERATOR_ORDER)

        if layer not in generator_map:
            raise ValueError(f"Unknown layer: {layer}. Valid: {list(generator_map.keys())}")

        # Use provided filter or instance's filter
        filter_to_use = element_filter if element_filter is not None else self.element_filter

        generator_class = generator_map[layer]
        generator = generator_class(self.project_id, self.output_dir, filter_to_use)
        return await generator.generate()

    async def _extract_global_state(self) -> GlobalStateContext | None:
        """
        Extrai declarações GLOBAL de Project Code e WDGs.

        Returns:
            GlobalStateContext consolidado ou None se nenhuma variável global
        """
        from bson import ObjectId

        from wxcode.models.element import Element

        extractor = GlobalStateExtractor()
        all_variables = []
        all_init_blocks = []

        # Busca Project Code (type_code: 0)
        project_elements = await Element.find(
            Element.projectId == ObjectId(self.project_id),
            Element.windevType == 0,  # Project Code
        ).to_list()

        for elem in project_elements:
            if elem.rawContent:
                variables = extractor.extract_variables(
                    elem.rawContent, elem.windevType, elem.sourceName
                )
                init_blocks = extractor.extract_initialization(elem.rawContent)
                all_variables.extend(variables)
                all_init_blocks.extend(init_blocks)

        # Busca WDGs (type_code: 31 = Set of Procedures)
        wdg_elements = await Element.find(
            Element.projectId == ObjectId(self.project_id),
            Element.windevType == 31,  # WDG
        ).to_list()

        for elem in wdg_elements:
            if elem.rawContent:
                variables = extractor.extract_variables(
                    elem.rawContent, elem.windevType, elem.sourceName
                )
                init_blocks = extractor.extract_initialization(elem.rawContent)
                all_variables.extend(variables)
                all_init_blocks.extend(init_blocks)

        # Retorna None se nenhuma variável global encontrada
        if not all_variables:
            return None

        return GlobalStateContext.from_extractor_results(all_variables, all_init_blocks)

    async def _generate_state_files(
        self, context: GlobalStateContext
    ) -> list[Path]:
        """
        Gera arquivos de estado usando StateGenerator do stack.

        Args:
            context: Contexto de estado global

        Returns:
            Lista de arquivos gerados
        """
        # Seleciona generator apropriado
        generator_class = self.STATE_GENERATORS[self.stack]
        generator = generator_class()

        # Gera arquivos
        return generator.generate(context, self.output_dir)

    async def _load_database_connections(self) -> list:
        """
        Carrega conexões de banco de dados do DatabaseSchema.

        Returns:
            Lista de SchemaConnection ou lista vazia se não houver schema
        """
        from bson import ObjectId
        from wxcode.models.schema import DatabaseSchema

        # Busca schema do projeto
        schema = await DatabaseSchema.find_one(
            DatabaseSchema.project_id == ObjectId(self.project_id)
        )

        if schema and schema.connections:
            return schema.connections

        return []

    async def _generate_project_structure(self) -> None:
        """Generate project structure files."""
        # Load database connections from schema
        connections = await self._load_database_connections()

        # Create directory structure
        dirs = [
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
        for dir_name in dirs:
            (self.output_dir / dir_name).mkdir(parents=True, exist_ok=True)

        # Generate main.py
        self._generate_main_py()

        # Generate config.py with connections
        self._generate_config_py(connections)

        # Generate database.py with connections
        self._generate_database_py(connections)

        # Generate __init__.py files
        self._generate_init_files()

        # Generate pyproject.toml with database drivers
        self._generate_pyproject_toml(connections)

        # Generate Dockerfile
        self._generate_dockerfile()

        # Generate docker-compose.yml
        self._generate_docker_compose()

        # Generate .env.example with connections
        self._generate_env_example(connections)

        # Generate run scripts (Windows and Linux)
        self._generate_run_scripts()

        # Generate README.md
        self._generate_readme(connections)

    def _generate_main_py(self) -> None:
        """Generate main.py FastAPI application."""
        content = '''"""FastAPI application generated by wxcode."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
from app.routes import router as page_router
from app.api import api_router

app.include_router(page_router)
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the application"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
'''
        self._write_file("app/main.py", content)

    def _generate_config_py(self, connections: list) -> None:
        """Generate config.py settings with database connections.

        Args:
            connections: List of SchemaConnection objects
        """
        # Generate database settings based on connections
        if connections:
            db_settings_lines = []
            for conn in connections:
                conn_var = conn.name.lower()
                db_settings_lines.append(f"    # {conn.name} ({conn.driver_name})")
                db_settings_lines.append(f'    {conn_var}_host: str = "{conn.source or "localhost"}"')
                db_settings_lines.append(f'    {conn_var}_port: str = "{conn.port or "5432"}"')
                db_settings_lines.append(f'    {conn_var}_database: str = "{conn.database or "app_db"}"')
                db_settings_lines.append(f'    {conn_var}_user: str = "{conn.user or "user"}"')
                db_settings_lines.append(f'    {conn_var}_password: str = ""')
                db_settings_lines.append("")
            db_settings = "\n".join(db_settings_lines)
        else:
            db_settings = '''    # Database
    database_url: str = "mongodb://localhost:27017"
    database_name: str = "app_db"'''

        content = f'''"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    app_name: str = "Application"
    debug: bool = False

{db_settings}

    # Security
    secret_key: str = "change-me-in-production"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
'''
        self._write_file("app/config.py", content)

    def _generate_database_py(self, connections: list) -> None:
        """Generate database.py with support for multiple connections.

        Args:
            connections: List of SchemaConnection objects
        """
        # If no connections, generate default MongoDB code
        if not connections:
            content = '''"""Database connection and initialization."""

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.config import settings

# Import all models here
# from app.models import Model1, Model2

client: AsyncIOMotorClient = None
db = None


async def init_db():
    """Initialize database connection."""
    global client, db

    client = AsyncIOMotorClient(settings.database_url)
    db = client[settings.database_name]

    # Initialize Beanie with document models
    # await init_beanie(
    #     database=db,
    #     document_models=[Model1, Model2],
    # )


async def close_db():
    """Close database connection."""
    global client
    if client:
        client.close()


def get_db():
    """Get database instance."""
    return db
'''
            self._write_file("app/database.py", content)
            return

        # Generate multi-connection database.py
        # Group by database type to generate appropriate imports
        types_needed = {conn.database_type for conn in connections if conn.database_type not in ("hyperfile", "hyperfile_cs", "unknown")}

        imports = []
        if any(t in types_needed for t in ("sqlserver", "mysql", "postgresql", "oracle")):
            imports.append("from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession")
            imports.append("from sqlalchemy.orm import sessionmaker")

        imports_str = "\n".join(imports) if imports else ""

        # Generate connection dict
        connections_init = []
        connections_close = []

        for conn in connections:
            conn_var = conn.name.lower()

            if conn.database_type in ("sqlserver", "mysql", "postgresql", "oracle"):
                # SQLAlchemy connection
                driver_map = {
                    "sqlserver": "mssql+aioodbc",
                    "mysql": "mysql+aiomysql",
                    "postgresql": "postgresql+asyncpg",
                    "oracle": "oracle+oracledb"
                }
                driver = driver_map.get(conn.database_type, conn.database_type)

                connections_init.append(f'''    # {conn.name} ({conn.driver_name})
    engine_{conn_var} = create_async_engine(
        f"{driver}://{{settings.{conn_var}_user}}:{{settings.{conn_var}_password}}@{{settings.{conn_var}_host}}:{{settings.{conn_var}_port}}/{{settings.{conn_var}_database}}"
    )
    session_factory_{conn_var} = sessionmaker(engine_{conn_var}, class_=AsyncSession, expire_on_commit=False)
    connections["{conn.name}"] = {{"engine": engine_{conn_var}, "session_factory": session_factory_{conn_var}}}''')

                connections_close.append(f'    await connections["{conn.name}"]["engine"].dispose()')

            elif conn.database_type in ("hyperfile", "hyperfile_cs"):
                # HyperFile - just a comment
                connections_init.append(f'''    # {conn.name} ({conn.driver_name})
    # HyperFile connections not yet supported - TODO: Implement HyperFile REST API client''')

        connections_init_str = "\n".join(connections_init)
        connections_close_str = "\n".join(connections_close) if connections_close else "    pass"

        content = f'''"""Database connections."""

{imports_str}
from app.config import settings

# Connection registry
connections: dict[str, dict] = {{}}


async def init_db() -> None:
    """Initialize all database connections."""
{connections_init_str}


async def close_db() -> None:
    """Close all database connections."""
{connections_close_str}


def get_db(connection_name: str = "{connections[0].name if connections else 'default'}"):
    """Get database session for specific connection.

    Args:
        connection_name: Name of the connection (default: first connection)

    Returns:
        Session factory for the requested connection
    """
    if connection_name not in connections:
        raise ValueError(f"Unknown connection: {{connection_name}}")

    return connections[connection_name]["session_factory"]
'''
        self._write_file("app/database.py", content)

    def _generate_init_files(self) -> None:
        """Generate __init__.py files."""
        # app/__init__.py
        self._write_file("app/__init__.py", '"""Application package."""\n')

        # tests/__init__.py
        self._write_file("tests/__init__.py", '"""Test package."""\n')

    def _generate_pyproject_toml(self, connections: list) -> None:
        """Generate pyproject.toml with database drivers.

        Args:
            connections: List of SchemaConnection objects
        """
        # Determine required database drivers
        db_deps = []
        types_needed = {conn.database_type for conn in connections} if connections else set()

        if not connections or not types_needed:
            # Default: MongoDB
            db_deps = [
                '    "motor>=3.3.0",',
                '    "beanie>=1.25.0",',
            ]
        else:
            # Add SQLAlchemy if any SQL database
            if any(t in types_needed for t in ("sqlserver", "mysql", "postgresql", "oracle")):
                db_deps.append('    "sqlalchemy[asyncio]>=2.0.0",')

            # Add specific drivers
            if "sqlserver" in types_needed:
                db_deps.append('    "aioodbc>=0.5.0",')
                db_deps.append('    "pyodbc>=5.0.0",')
            if "mysql" in types_needed:
                db_deps.append('    "aiomysql>=0.2.0",')
            if "postgresql" in types_needed:
                db_deps.append('    "asyncpg>=0.29.0",')
            if "oracle" in types_needed:
                db_deps.append('    "oracledb>=2.0.0",')

        db_deps_str = "\n".join(db_deps)

        content = f'''[project]
name = "app"
version = "1.0.0"
description = "Application generated by wxcode"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
{db_deps_str}
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "jinja2>=3.1.0",
    "python-multipart>=0.0.6",
    "httpx>=0.26.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
'''
        self._write_file("pyproject.toml", content)

    def _generate_dockerfile(self) -> None:
        """Generate Dockerfile."""
        content = '''FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application
COPY app/ app/
COPY tests/ tests/

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
        self._write_file("Dockerfile", content)

    def _generate_docker_compose(self) -> None:
        """Generate docker-compose.yml."""
        content = '''version: "3.8"

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mongodb://mongo:27017
      - DATABASE_NAME=app_db
    depends_on:
      - mongo

  mongo:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
'''
        self._write_file("docker-compose.yml", content)

    def _generate_env_example(self, connections: list) -> None:
        """Generate .env.example with dynamic database connections.

        Args:
            connections: List of SchemaConnection objects
        """
        content = "# Application settings\nAPP_NAME=Application\nDEBUG=false\n\n"

        if not connections:
            # Default MongoDB connection
            content += "# Database\nDATABASE_URL=mongodb://localhost:27017\nDATABASE_NAME=app_db\n\n"
        else:
            # Generate environment variables for each connection
            for conn in connections:
                conn_var = conn.name.upper()
                content += f"# Database: {conn.name} ({conn.driver_name})\n"
                content += f"{conn_var}_HOST={conn.source or 'localhost'}\n"
                content += f"{conn_var}_PORT={conn.port or '5432'}\n"
                content += f"{conn_var}_DATABASE={conn.database or 'app_db'}\n"
                content += f"{conn_var}_USER={conn.user or 'user'}\n"
                content += f"{conn_var}_PASSWORD=\n"
                content += f"{conn_var}_TYPE={conn.database_type}\n"
                content += "\n"

        content += "# Security\nSECRET_KEY=change-me-in-production\n"

        self._write_file(".env.example", content)

    def _generate_run_scripts(self) -> None:
        """Generate run scripts for Windows and Linux."""
        # Linux/macOS script
        linux_script = '''#!/bin/bash
# Run script for Linux/macOS
# Generated by wxcode

set -e

echo "=== Application Setup ==="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q fastapi uvicorn[standard] sqlalchemy[asyncio] aioodbc pyodbc pydantic pydantic-settings jinja2 python-multipart httpx

# Copy .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "IMPORTANT: Edit .env with your database credentials!"
fi

echo ""
echo "=== Starting Application ==="
echo "URL: http://127.0.0.1:8000"
echo "Press Ctrl+C to stop"
echo ""

# Run application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
'''
        self._write_file("run.sh", linux_script)

        # Windows script
        windows_script = '''@echo off
REM Run script for Windows
REM Generated by wxcode

echo === Application Setup ===

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\\Scripts\\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -q fastapi uvicorn[standard] sqlalchemy[asyncio] aioodbc pyodbc pydantic pydantic-settings jinja2 python-multipart httpx

REM Copy .env if not exists
if not exist ".env" (
    echo Creating .env from .env.example...
    copy .env.example .env
    echo IMPORTANT: Edit .env with your database credentials!
)

echo.
echo === Starting Application ===
echo URL: http://127.0.0.1:8000
echo Press Ctrl+C to stop
echo.

REM Run application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
'''
        self._write_file("run.bat", windows_script)

    def _generate_readme(self, connections: list) -> None:
        """Generate README.md with project documentation.

        Args:
            connections: List of SchemaConnection objects
        """
        # Build database info section
        if connections:
            db_info = "### Database Connections\n\n"
            db_info += "| Connection | Type | Host | Database |\n"
            db_info += "|------------|------|------|----------|\n"
            for conn in connections:
                db_info += f"| {conn.name} | {conn.driver_name} | {conn.source}:{conn.port} | {conn.database} |\n"
        else:
            db_info = "### Database\n\nMongoDB (default configuration)\n"

        content = f'''# Application

FastAPI application generated by [wxcode](https://github.com/wxcode/wxcode).

## Quick Start

### Windows

```batch
run.bat
```

### Linux/macOS

```bash
chmod +x run.sh
./run.sh
```

## Manual Setup

### 1. Create virtual environment

```bash
# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\\Scripts\\activate
```

### 2. Install dependencies

```bash
pip install fastapi uvicorn[standard] sqlalchemy[asyncio] aioodbc pyodbc pydantic pydantic-settings jinja2 python-multipart httpx
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 4. Run application

```bash
uvicorn app.main:app --reload
```

The application will be available at http://127.0.0.1:8000

## Project Structure

```
├── app/
│   ├── main.py          # FastAPI application entry point
│   ├── config.py        # Application settings (from .env)
│   ├── database.py      # Database connections
│   ├── api/             # REST API endpoints
│   ├── routes/          # HTML page routes
│   ├── models/          # Pydantic models
│   ├── services/        # Business logic
│   ├── templates/       # Jinja2 HTML templates
│   └── static/          # CSS, JS, images
├── tests/               # Test files
├── .env.example         # Environment variables template
├── run.sh               # Linux/macOS run script
├── run.bat              # Windows run script
├── Dockerfile
└── docker-compose.yml
```

{db_info}

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description |
|----------|-------------|
| `APP_NAME` | Application name |
| `DEBUG` | Enable debug mode (true/false) |
| `SECRET_KEY` | Secret key for sessions |
| `*_HOST` | Database host |
| `*_PORT` | Database port |
| `*_DATABASE` | Database name |
| `*_USER` | Database user |
| `*_PASSWORD` | Database password |

## Docker

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# Stop
docker-compose down
```

## API Documentation

When running, access:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

---

Generated by wxcode
'''
        self._write_file("README.md", content)

    def _write_file(self, relative_path: str, content: str) -> Path:
        """Write content to a file.

        Args:
            relative_path: Path relative to output_dir
            content: File content

        Returns:
            Full path to created file
        """
        full_path = self.output_dir / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        self.result.total_files += 1
        return full_path

    # Configuration-aware conversion methods (Tasks 14-16)

    async def _get_elements_for_config(
        self, config: ConversionConfig
    ) -> list[Element]:
        """Filtra elementos que não estão excluídos da configuration (Task 14).

        Args:
            config: Configuração de conversão.

        Returns:
            Lista de elementos incluídos na configuration.
        """
        # Query elementos que NÃO estão excluídos desta configuration
        elements = await Element.find(
            {
                "project_id": config.project_id,
                "excluded_from": {"$nin": [config.configuration_id]}
            }
        ).to_list()

        return elements

    async def _build_config_context(
        self,
        elements: list[Element],
        config_name: str
    ) -> ConfigurationContext:
        """Constrói ConfigurationContext agregando COMPILE IF de todos elementos (Task 15).

        Args:
            elements: Lista de elementos do projeto.
            config_name: Nome da configuration.

        Returns:
            ConfigurationContext consolidado.
        """
        extractor = CompileIfExtractor()
        all_blocks = []
        all_variables = []

        # Extrai COMPILE IF de cada elemento
        for element in elements:
            if not element.raw_content:
                continue

            # Extrai blocos
            blocks = extractor.extract(element.raw_content)
            all_blocks.extend(blocks)

            # Extrai variáveis dos blocos
            variables = extractor.extract_variables(blocks)
            all_variables.extend(variables)

        # Constrói contexto consolidado
        context = ConfigurationContext.from_blocks(all_blocks, all_variables)
        return context

    async def convert_with_config(
        self, config: ConversionConfig
    ) -> OrchestratorResult:
        """Converte projeto usando ConversionConfig específica (Task 16).

        Args:
            config: Configuração de conversão.

        Returns:
            OrchestratorResult com detalhes da geração.
        """
        # Atualizar output_dir e project_id do orchestrator
        self.output_dir = config.output_dir
        self.project_id = str(config.project_id)
        self.result = OrchestratorResult(
            project_id=str(config.project_id),
            output_dir=self.output_dir,
        )

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Filtrar elementos pela configuration
        elements = await self._get_elements_for_config(config)

        # 2. Extrair COMPILE IF e construir ConfigurationContext
        context = await self._build_config_context(elements, config.configuration_name)

        # 3. Gerar config files
        config_gen = PythonConfigGenerator()
        config_files = config_gen.generate(
            context,
            config.configuration_name,
            self.output_dir
        )
        self.result.total_files += len(config_files)

        # 4. Executar generators (condicionado ao tipo)
        generators_to_run = [
            ("schema", SchemaGenerator),
            ("domain", DomainGenerator),
            ("service", ServiceGenerator),
        ]

        # Routes só se for Site ou API
        if config.should_generate_routes:
            generators_to_run.append(("route", RouteGenerator))
            generators_to_run.append(("api", APIGenerator))

        # Templates só se for Site
        if config.should_generate_templates:
            generators_to_run.append(("template", TemplateGenerator))

        # Run each generator in order
        for name, generator_class in generators_to_run:
            progress = GeneratorProgress(name=name)
            self.result.generators.append(progress)

            try:
                progress.status = "running"
                # TODO: Passar ConfigurationContext para generators
                # (requer modificação nos generators - change futuro)
                generator = generator_class(
                    str(config.project_id),
                    self.output_dir,
                    None  # element_filter
                )
                files = await generator.generate()
                progress.files_generated = len(files)
                progress.status = "completed"
                self.result.total_files += len(files)

            except Exception as e:
                progress.status = "failed"
                progress.error = str(e)
                self.result.success = False
                self.result.errors.append(f"{name}: {e}")

        # Generate project structure files
        if self.result.success:
            try:
                await self._generate_project_structure()
            except Exception as e:
                self.result.success = False
                self.result.errors.append(f"project_structure: {e}")

        return self.result
