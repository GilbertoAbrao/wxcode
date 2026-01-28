"""
MCP Server for wxcode Knowledge Base.

Exposes MongoDB + Neo4j data to Claude Code via MCP tools.
Uses STDIO transport (default for Claude Code integration).

IMPORTANT: All logging goes to stderr - stdout is reserved for JSON-RPC.
"""
import logging
import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

# Configure logging to stderr BEFORE any other imports that might log
def configure_logging() -> None:
    """Configure logging to stderr only (stdout reserved for MCP JSON-RPC)."""
    root = logging.getLogger()
    # Remove any existing handlers
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # Add stderr handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(logging.INFO)


# Configure logging early
configure_logging()

from fastmcp import FastMCP

from wxcode.database import init_db, close_db
from wxcode.graph.neo4j_connection import Neo4jConnection, Neo4jConnectionError

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
    logger.info("Starting wxcode MCP Server...")

    # MongoDB (required) - uses existing init_db()
    mongo_client = await init_db()
    logger.info("MongoDB connected and Beanie initialized")

    # Neo4j (optional) - graceful fallback pattern from gsd_context_collector.py
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


# Create server with lifespan
mcp = FastMCP("wxcode-kb", lifespan=app_lifespan)

# Register all tools by importing the tools package
from wxcode.mcp import tools  # noqa: F401 - import for side effects


if __name__ == "__main__":
    mcp.run()  # STDIO transport by default
