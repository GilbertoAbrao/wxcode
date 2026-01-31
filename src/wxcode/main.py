"""
Aplicação FastAPI do WXCODE.

Fornece API REST para operações de conversão e interface web.
"""

from dotenv import load_dotenv

load_dotenv()  # Carregar variáveis de ambiente do .env

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from wxcode import __version__
from wxcode.config import get_settings, PROJECT_ROOT
from wxcode.database import init_db, close_db
from wxcode.services import seed_stacks
from wxcode.api import (
    projects,
    elements,
    conversions,
    websocket,
    import_wizard,
    import_wizard_ws,
    tree,
    products,
    workspace,
    stacks,
    output_projects,
    milestones,
    schema,
)


# Contexto de vida da aplicação
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Gerencia conexão com banco de dados e inicializa dados."""
    # Startup
    client = await init_db()
    app.state.db_client = client

    # Seed stack configurations (non-blocking on failure)
    await seed_stacks()

    yield

    # Shutdown
    await close_db(client)


# Cria aplicação FastAPI
app = FastAPI(
    title="WXCODE",
    description="Conversor universal de projetos WinDev/WebDev/WinDev Mobile",
    version=__version__,
    lifespan=lifespan,
)

# Configurar CORS para aceitar requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3052", "http://127.0.0.1:3052"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra rotas da API
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(elements.router, prefix="/api/elements", tags=["Elements"])
app.include_router(conversions.router, prefix="/api/conversions", tags=["Conversions"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(websocket.router, prefix="/api", tags=["Chat"])
app.include_router(import_wizard.router, tags=["Import Wizard"])
app.include_router(import_wizard_ws.router, tags=["Import Wizard WebSocket"])
app.include_router(tree.router, prefix="/api/tree", tags=["Tree"])
app.include_router(workspace.router, prefix="/api/workspace", tags=["Workspace"])
app.include_router(stacks.router, prefix="/api/stacks", tags=["Stacks"])
app.include_router(output_projects.router, prefix="/api/output-projects", tags=["Output Projects"])
app.include_router(milestones.router, prefix="/api/milestones", tags=["Milestones"])
app.include_router(schema.router, prefix="/api/schema", tags=["Schema"])


@app.get("/")
async def root() -> dict:
    """Endpoint raiz."""
    return {
        "name": "wxcode",
        "version": __version__,
        "description": "Conversor universal de projetos WinDev/WebDev/WinDev Mobile",
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> dict:
    """Health check."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "wxcode.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        reload_dirs=[str(PROJECT_ROOT / "src" / "wxcode")],
        reload_includes=["*.py"],
        reload_excludes=[
            "**/__pycache__/**",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.log",
            "**/*.tmp",
            "**/.pytest_cache/**",
        ],
    )
