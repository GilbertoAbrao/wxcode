# Technology Stack

**Analysis Date:** 2026-01-21

## Languages

**Primary:**
- Python 3.11+ - Backend, CLI, all core logic and parsers

**Secondary:**
- TypeScript/JavaScript - Frontend only (Next.js based on config files found)
- WLanguage - Source format (WinDev project files being analyzed and converted)

## Runtime

**Environment:**
- Python 3.11 or higher (from `setup.py`)
- Node.js - for frontend development and Claude Code CLI integration

**Package Manager:**
- pip - Python package management
- npm/pnpm - JavaScript dependencies (frontend)

**Lockfile:**
- requirements.txt - frozen Python dependencies (present)
- requirements-dev.txt - development dependencies (present)
- package-lock.json or yarn.lock - frontend dependencies (assumed based on Next.js)

## Frameworks

**Core Web:**
- FastAPI 0.128.0 - REST API framework (`src/wxcode/main.py`)
- Uvicorn 0.40.0 - ASGI server for FastAPI
- Jinja2 3.1.6 - Template engine for code generation and rendering

**CLI:**
- Typer 0.21.0 - CLI framework with Rich formatting (`src/wxcode/cli.py`)
- Rich 14.2.0 - Terminal output formatting and progress bars

**Frontend:**
- Next.js - React framework (detected from config: `frontend/next.config.ts`)
- ESLint - Linting configuration (`frontend/eslint.config.mjs`)
- PostCSS - CSS processing (`frontend/postcss.config.mjs`)

**Async Support:**
- asyncio (Python standard library) - Async runtime
- Motor 3.7.1 - Async MongoDB driver
- httpx 0.28.1 - Async HTTP client

## Key Dependencies

**Critical:**
- Pydantic 2.12.5 - Data validation and settings management
- Pydantic-Settings 2.12.0 - Environment-based configuration
- Beanie 2.0.1 - Async MongoDB ODM (why it matters: provides async document models with validation)

**Database:**
- Motor 3.7.1 - Async MongoDB driver (AsyncIOMotorClient)
- PyMongo 4.15.5 - MongoDB Python driver (underlying Motor dependency)
- Neo4j 5.28.1 - Graph database client for dependency analysis

**LLM Integration:**
- anthropic 0.75.0 - Anthropic Claude API client (primary LLM provider)
- openai (optional) - OpenAI API client via provider plugin system
- httpx 0.28.1 - HTTP client for LLM calls and n8n webhooks

**Document Processing:**
- pdfplumber 0.11.8 - PDF parsing for documentation
- pdfminer.six 20251107 - PDF extraction
- PyMuPDF 1.26.7 - Alternative PDF library
- pypdfium2 5.2.0 - PDF utilities
- Pillow 12.0.0 - Image processing

**Code Analysis:**
- NetworkX 3.6.1 - Graph algorithms for dependency analysis
- ast (Python standard library) - Abstract syntax tree parsing

**Utilities:**
- python-dotenv 1.2.1 - .env file loading
- PyYAML 6.0.3 - YAML parsing
- Requests 2.32.5 - HTTP requests
- python-multipart 0.0.21 - Form data parsing in FastAPI

**Token/Model Analysis:**
- tiktoken 0.12.0 - Token counting for Claude API (for cost estimation)
- docstring_parser 0.17.1 - Parse Python docstrings

## Configuration

**Environment:**
- Loaded via Pydantic Settings from `.env` file
- `.env.example` provided as template
- Key variables:
  - `MONGODB_URL` - MongoDB connection string
  - `MONGODB_DATABASE` - Database name
  - `ANTHROPIC_API_KEY` - Claude API key
  - `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE` - Neo4j settings
  - `N8N_WEBHOOK_URL` - n8n ChatAgent webhook for message processing
  - `API_HOST`, `API_PORT` - FastAPI server settings
  - `DEBUG`, `LOG_LEVEL` - Application settings
  - `DEFAULT_TARGET_STACK` - Target conversion stack (default: fastapi-jinja2)
  - `MAX_TOKENS_PER_CHUNK`, `CHUNK_OVERLAP_TOKENS` - For semantic chunking
  - `CONVERSION_PROVIDER`, `CONVERSION_MODEL` - LLM provider selection

**Build:**
- setup.py - Package configuration with entry point: `wxcode=wxcode.cli:app`
- FastAPI app runs on configurable host/port (default 0.0.0.0:8000)

## Development Tools

**Testing:**
- pytest 9.0.2 - Test runner
- pytest-asyncio - Async test support
- pytest-cov - Coverage reporting

**Linting & Type Checking:**
- ruff >= 0.2.0 - Fast Python linter
- mypy >= 1.8.0 - Static type checker

**Git Hooks:**
- pre-commit >= 3.6.0 - Git hook framework (configuration file likely in .pre-commit-config.yaml)

## External Services Integration

**LLM Providers (pluggable architecture):**
- Location: `src/wxcode/llm_converter/providers/`
- Anthropic Claude (primary) - via `anthropic` package
- OpenAI GPT - optional via `openai` package
- Ollama (local models) - via `httpx` calls to local server

**Database Services:**
- MongoDB (async via Motor) - stores elements, controls, procedures, schema
- Neo4j (graph database) - stores dependency graphs for impact analysis

**External APIs:**
- n8n ChatAgent webhook - for message processing and agent responses
  - URL: `N8N_WEBHOOK_URL` environment variable
  - Used in: `src/wxcode/services/gsd_invoker.py`
  - Called via httpx for async HTTP POST

**Claude Code CLI Integration:**
- Invokes local Claude Code CLI (`claude` command)
- For GSD (Get Stuff Done) workflow execution
- Streaming output via PTY and WebSocket
- Location: `src/wxcode/services/gsd_invoker.py`

## Platform Requirements

**Development:**
- Python 3.11+
- Node.js (for frontend and Claude Code CLI)
- MongoDB 4.0+ (for document storage)
- Neo4j 5.0+ (optional, for dependency analysis features)
- Docker recommended for MongoDB and Neo4j

**Production:**
- Python 3.11+ runtime
- MongoDB deployment
- Neo4j deployment (optional)
- FastAPI-capable ASGI server (Uvicorn or similar)
- Environment variables properly configured
- Anthropic API key provisioned
- Optional: n8n instance for ChatAgent workflow

**Port Requirements:**
- 8000/8035 (FastAPI API) - configurable via `API_PORT`
- 3000/3020 (Next.js frontend) - CORS allowed
- 27017 (MongoDB) - if running locally
- 7687 (Neo4j Bolt) - if running locally
- 11434 (Ollama) - if using local LLM provider

## Deployment Stack

**API Server:**
- FastAPI + Uvicorn (Python async ASGI)
- CORS configured for localhost frontend development

**Frontend:**
- Next.js on Node.js runtime

**Databases:**
- MongoDB (primary data store)
- Neo4j (dependency graphs)

---

*Stack analysis: 2026-01-21*
