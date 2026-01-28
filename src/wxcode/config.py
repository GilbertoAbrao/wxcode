"""
Configurações da aplicação.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# Caminho absoluto para o diretório raiz do projeto
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "wxcode"

    # Anthropic API
    anthropic_api_key: Optional[str] = None

    # Aplicação
    debug: bool = False
    log_level: str = "INFO"

    # FastAPI
    api_host: str = "0.0.0.0"
    api_port: int = 8052

    # Conversão
    default_target_stack: str = "fastapi-jinja2"
    max_tokens_per_chunk: int = 3500
    chunk_overlap_tokens: int = 200
    conversion_output_base: str = "./output/openspec"
    conversion_provider: str = "anthropic"
    conversion_model: Optional[str] = None

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"

    # File deletion safety - base directory for allowed deletions
    allowed_deletion_base: str = str(PROJECT_ROOT / "project-refs")


@lru_cache
def get_settings() -> Settings:
    """Retorna as configurações (cached)."""
    return Settings()
