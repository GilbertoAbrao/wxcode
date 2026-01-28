"""
Configuração de conexão com MongoDB.
"""

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from wxcode.config import get_settings
from wxcode.models import (
    Project,
    Element,
    Conversion,
    Control,
    ControlTypeDefinition,
    Procedure,
    DatabaseSchema,
    ClassDefinition,
    Product,
    ConversionHistoryEntry,
    Stack,
    OutputProject,
    Milestone,
)
from wxcode.models.token_usage import TokenUsageLog
from wxcode.models.import_session import ImportSession


async def init_db() -> AsyncIOMotorClient:
    """
    Inicializa a conexão com MongoDB e o Beanie ODM.

    Returns:
        Cliente MongoDB conectado.
    """
    settings = get_settings()

    # Cria cliente MongoDB
    client = AsyncIOMotorClient(settings.mongodb_url)

    # Inicializa Beanie com os models
    await init_beanie(
        database=client[settings.mongodb_database],
        document_models=[
            Project,
            Element,
            Conversion,
            Control,
            ControlTypeDefinition,
            Procedure,
            DatabaseSchema,
            ClassDefinition,
            TokenUsageLog,
            ImportSession,
            Product,
            ConversionHistoryEntry,
            Stack,
            OutputProject,
            Milestone,
        ]
    )

    return client


async def close_db(client: AsyncIOMotorClient) -> None:
    """Fecha a conexão com MongoDB."""
    client.close()
