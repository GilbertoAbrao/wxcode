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

# Import mcp from instance module to avoid __main__ vs module identity issue
from wxcode.mcp.instance import mcp

# Register all tools by importing the tools package
from wxcode.mcp import tools  # noqa: F401 - import for side effects

# Re-export mcp for backwards compatibility
__all__ = ["mcp"]

logger = logging.getLogger(__name__)


def run_http_server():
    """Run MCP server in HTTP/SSE mode with API key authentication."""
    import asyncio
    from starlette.middleware import Middleware
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import JSONResponse

    from wxcode.config import get_settings

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
