"""FastMCP instance for wxcode Knowledge Base.

This module exists to break circular imports. The mcp instance is defined
here and imported by both server.py and all tool modules.

IMPORTANT: This module should NOT import anything that imports from it,
otherwise we get the __main__ vs module identity issue when running
python -m wxcode.mcp.server.
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastmcp import FastMCP

# Configure logging to stderr (stdout reserved for MCP JSON-RPC)
def _configure_logging() -> None:
    """Configure logging to stderr only."""
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(logging.INFO)


_configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """
    Initialize database connections at startup.

    MongoDB is required - failure will prevent server startup.
    Neo4j is optional - failure will be logged and server continues.

    Yields:
        Context dict with:
        - mongo_client: Motor AsyncIOMotorClient
        - neo4j_conn: Neo4jConnection or None
        - neo4j_available: bool indicating Neo4j status
    """
    # Import here to avoid circular imports
    from wxcode.database import init_db, close_db
    from wxcode.graph.neo4j_connection import Neo4jConnection, Neo4jConnectionError

    logger.info("Starting wxcode MCP Server...")

    # MongoDB (required)
    mongo_client = await init_db()
    logger.info("MongoDB connected and Beanie initialized")

    # Neo4j (optional)
    neo4j_conn = None
    neo4j_available = False

    try:
        neo4j_conn = Neo4jConnection()
        await neo4j_conn.connect()
        neo4j_available = True
        logger.info("Neo4j connected")
    except Neo4jConnectionError as e:
        logger.warning(f"Neo4j unavailable: {e}, using MongoDB only")
    except Exception as e:
        logger.warning(f"Neo4j connection failed: {e}, using MongoDB only")

    try:
        yield {
            "mongo_client": mongo_client,
            "neo4j_conn": neo4j_conn,
            "neo4j_available": neo4j_available,
        }
    finally:
        logger.info("Shutting down wxcode MCP Server...")
        await close_db(mongo_client)
        if neo4j_conn:
            await neo4j_conn.close()
        logger.info("Shutdown complete")


# Create the single mcp instance - this is imported by all tool modules
mcp = FastMCP("wxcode-kb", lifespan=app_lifespan)

__all__ = ["mcp", "app_lifespan"]
