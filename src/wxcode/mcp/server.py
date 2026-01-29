"""
MCP Server for wxcode Knowledge Base.

Exposes MongoDB + Neo4j data to Claude Code via MCP tools.

Transports:
- STDIO (default): For local Claude Code integration
- HTTP/SSE (--http): For remote access with API key auth

Usage:
    python -m wxcode.mcp.server          # STDIO mode
    python -m wxcode.mcp.server --http   # HTTP mode on port 8152

IMPORTANT: All logging goes to stderr - stdout is reserved for JSON-RPC.
"""
import argparse
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

from wxcode.config import get_settings
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


def run_http_server():
    """Run MCP server in HTTP/SSE mode with API key authentication."""
    import asyncio
    from starlette.middleware import Middleware
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import JSONResponse

    settings = get_settings()

    if not settings.mcp_api_key:
        logger.error("MCP_API_KEY must be set for HTTP mode")
        logger.error("Set it in .env or as environment variable")
        sys.exit(1)

    logger.info(f"Starting HTTP server on port {settings.mcp_http_port}")
    logger.info("API key authentication enabled")

    # API Key middleware class
    class APIKeyMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            # Validate API key header
            provided_key = request.headers.get("X-API-Key")
            if not provided_key or provided_key != settings.mcp_api_key:
                return JSONResponse(
                    status_code=401,
                    content={"error": "Invalid or missing API key"}
                )
            return await call_next(request)

    async def run():
        await mcp.run_http_async(
            host="0.0.0.0",
            port=settings.mcp_http_port,
            middleware=[Middleware(APIKeyMiddleware)],
        )

    asyncio.run(run())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="wxcode MCP Server")
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run in HTTP mode (default: STDIO for Claude Code)"
    )
    parser.add_argument(
        "--port",
        type=int,
        help="HTTP port (default: from MCP_HTTP_PORT or 8152)"
    )
    args = parser.parse_args()

    if args.http:
        if args.port:
            # Override port if specified
            import os
            os.environ["MCP_HTTP_PORT"] = str(args.port)
        run_http_server()
    else:
        mcp.run()  # STDIO transport by default
