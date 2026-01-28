# Phase 4: Core Infrastructure - Research

**Researched:** 2026-01-21
**Domain:** MCP Server with FastMCP, MongoDB/Neo4j connections, STDIO transport
**Confidence:** HIGH

## Summary

Phase 4 establishes the foundational MCP Server that exposes the wxcode Knowledge Base to Claude Code. The research confirms that **FastMCP v2.x** is the correct choice for production (v3 is beta), with **STDIO transport** as the default for Claude Code integration. The existing codebase already has well-established patterns for MongoDB initialization (`init_db()`) and Neo4j graceful fallback that should be reused.

Key findings:
1. FastMCP provides `@lifespan` decorator for async database initialization with `try/finally` cleanup
2. STDIO transport requires all logging to stderr (stdout is reserved for JSON-RPC messages)
3. The `.mcp.json` format uses `mcpServers` object with `command`, `args`, and `env` fields
4. Neo4j graceful fallback pattern already exists in `gsd_context_collector.py` and should be adapted

**Primary recommendation:** Use FastMCP v2.14.x with lifespan for database initialization, Python logging configured to stderr, and existing Neo4j connection pattern with try/except fallback.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastmcp | 2.14.x (`<3`) | MCP server framework | Official high-level SDK, 70% of MCP servers use FastMCP |
| motor | 3.7.x | Async MongoDB driver | Already in project, required by Beanie |
| beanie | 2.0.x | MongoDB ODM | Already in project, models defined |
| neo4j | 5.28.x | Neo4j driver | Already in project, async support |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic-settings | 2.12.x | Configuration management | Already used via `Settings` class |
| python-dotenv | 1.2.x | Environment file loading | Already used in project |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| FastMCP | Raw `mcp` SDK | Lower-level, more boilerplate, less Pythonic |
| STDIO transport | HTTP transport | HTTP better for multi-client but Claude Code uses STDIO |
| FastMCP v3.0 | FastMCP v2.14 | v3 is beta, may have breaking changes |

**Installation:**
```bash
pip install "fastmcp<3"
# OR add to requirements.txt:
# fastmcp<3
```

Note: Project already has all database dependencies in requirements.txt.

## Architecture Patterns

### Recommended Project Structure
```
src/wxcode/
├── mcp/
│   ├── __init__.py          # Package marker
│   ├── server.py            # FastMCP server with lifespan
│   ├── tools/               # Tool modules (Phase 5+)
│   │   ├── __init__.py
│   │   └── ...
│   └── context.py           # Shared context/dependencies
└── ...
```

### Pattern 1: Lifespan for Database Initialization
**What:** Use FastMCP's `@lifespan` decorator to initialize databases at startup
**When to use:** Always - databases must be initialized before tools can query them
**Example:**
```python
# Source: https://gofastmcp.com/servers/lifespan
from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan
from wxcode.database import init_db, close_db
from wxcode.graph.neo4j_connection import Neo4jConnection, Neo4jConnectionError

@lifespan
async def db_lifespan(server):
    """Initialize MongoDB and optionally Neo4j at startup."""
    # MongoDB (required)
    mongo_client = await init_db()

    # Neo4j (optional, graceful fallback)
    neo4j_conn = None
    neo4j_available = False
    try:
        neo4j_conn = Neo4jConnection()
        await neo4j_conn.connect()
        neo4j_available = True
    except Neo4jConnectionError as e:
        import sys
        print(f"[MCP] Neo4j unavailable: {e}, using MongoDB only", file=sys.stderr)

    try:
        yield {
            "mongo_client": mongo_client,
            "neo4j_conn": neo4j_conn,
            "neo4j_available": neo4j_available,
        }
    finally:
        # Cleanup
        await close_db(mongo_client)
        if neo4j_conn:
            await neo4j_conn.close()

mcp = FastMCP("wxcode-kb", lifespan=db_lifespan)
```

### Pattern 2: Accessing Lifespan Context in Tools
**What:** Use `ctx.lifespan_context` to access initialized resources
**When to use:** In every tool that needs database access
**Example:**
```python
# Source: https://gofastmcp.com/servers/lifespan
from fastmcp import Context

@mcp.tool
async def example_tool(ctx: Context, param: str) -> dict:
    """Example tool accessing database."""
    neo4j_available = ctx.lifespan_context["neo4j_available"]
    neo4j_conn = ctx.lifespan_context["neo4j_conn"]

    if neo4j_available and neo4j_conn:
        # Use Neo4j
        result = await neo4j_conn.execute("MATCH (n) RETURN n LIMIT 1")
    else:
        # Fallback to MongoDB-only
        result = {"fallback": True}

    return result
```

### Pattern 3: Logging to stderr Only
**What:** Configure Python logging to use stderr exclusively
**When to use:** Always - stdout is reserved for JSON-RPC in STDIO transport
**Example:**
```python
# Source: https://docs.python.org/3/howto/logging.html
import logging
import sys

def configure_logging():
    """Configure logging to stderr only for MCP STDIO transport."""
    # Remove any existing handlers
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # Add stderr handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(logging.INFO)

# Call before server starts
configure_logging()
```

### Pattern 4: Server Entry Point
**What:** Module entry point for `python -m wxcode.mcp.server`
**When to use:** Standard pattern for runnable module
**Example:**
```python
# src/wxcode/mcp/server.py
from fastmcp import FastMCP
# ... imports and lifespan definition ...

mcp = FastMCP("wxcode-kb", lifespan=db_lifespan)

# Tools will be registered here in Phase 5+

if __name__ == "__main__":
    configure_logging()
    mcp.run()  # STDIO transport by default
```

### Anti-Patterns to Avoid
- **print() in tools:** Never use `print()` - it writes to stdout and corrupts JSON-RPC
- **Global database connections:** Don't initialize databases at module load - use lifespan
- **Blocking Neo4j check:** Don't let Neo4j failure block server startup - fail gracefully
- **Forgetting cleanup:** Always use `try/finally` in lifespan for proper resource release

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MCP protocol handling | Custom JSON-RPC | FastMCP | Protocol is complex, versioned, evolving |
| Tool schema generation | Manual OpenAPI | `@mcp.tool` decorator | FastMCP generates from type hints |
| MongoDB async connection | Raw pymongo | Beanie + Motor | Already configured in project |
| Neo4j async connection | Custom driver | `Neo4jConnection` class | Already exists in `graph/neo4j_connection.py` |
| Graceful fallback | Custom try/except | Existing pattern | See `gsd_context_collector.py` lines 96-137 |

**Key insight:** The project already has battle-tested patterns for database connections and graceful Neo4j fallback. Phase 4 should adapt these patterns to FastMCP's lifespan model, not reinvent them.

## Common Pitfalls

### Pitfall 1: Writing to stdout
**What goes wrong:** Any `print()` or stdout logging corrupts JSON-RPC messages, breaking the MCP connection
**Why it happens:** Developers forget STDIO transport uses stdout for protocol messages
**How to avoid:** Configure all logging to stderr before server starts; use `ctx.info()` for MCP-aware logging
**Warning signs:** Connection drops, garbled responses, "invalid JSON" errors from client

### Pitfall 2: Database Not Initialized
**What goes wrong:** Tools fail with "collection not found" or ODM errors
**Why it happens:** Beanie requires `init_beanie()` before any queries; skipping lifespan means silent failures
**How to avoid:** Always use lifespan; verify Beanie initialization in lifespan before yielding
**Warning signs:** First tool call fails, "Document class is not initialized" errors

### Pitfall 3: Neo4j Blocking Server Start
**What goes wrong:** Server hangs or crashes when Neo4j is unavailable
**Why it happens:** Neo4j connection attempt without timeout/exception handling
**How to avoid:** Wrap Neo4j connection in try/except, set `neo4j_available` flag, continue without Neo4j
**Warning signs:** Server doesn't respond, timeout on first request

### Pitfall 4: FastMCP v3 Breaking Changes
**What goes wrong:** Server fails after `pip install --upgrade fastmcp`
**Why it happens:** v3.0 is beta with breaking API changes
**How to avoid:** Pin to `fastmcp<3` in requirements.txt
**Warning signs:** Import errors, missing methods, changed signatures

### Pitfall 5: Wrong .mcp.json Format
**What goes wrong:** Claude Code doesn't discover or can't start the server
**Why it happens:** Missing `mcpServers` wrapper, wrong `command`/`args` format
**How to avoid:** Follow exact format; use absolute paths; test with `claude mcp list`
**Warning signs:** Server not listed in Claude Code, "command not found" errors

## Code Examples

Verified patterns from official sources:

### Complete Server Template
```python
# src/wxcode/mcp/server.py
# Source: https://gofastmcp.com/servers/lifespan + project patterns
"""
MCP Server for wxcode Knowledge Base.

Exposes MongoDB + Neo4j data to Claude Code via MCP tools.
"""
import logging
import sys
from typing import Any

from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan

from wxcode.database import init_db, close_db
from wxcode.graph.neo4j_connection import Neo4jConnection, Neo4jConnectionError

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure logging to stderr only (stdout reserved for MCP JSON-RPC)."""
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(logging.INFO)


@lifespan
async def app_lifespan(server) -> dict[str, Any]:
    """Initialize database connections at startup."""
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

# Tools will be registered here in Phase 5+
# from wxcode.mcp.tools import register_tools
# register_tools(mcp)


if __name__ == "__main__":
    configure_logging()
    mcp.run()  # STDIO transport by default
```

### .mcp.json Configuration
```json
{
  "mcpServers": {
    "wxcode-kb": {
      "command": "python",
      "args": ["-m", "wxcode.mcp.server"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/wxcode/src"
      }
    }
  }
}
```

Alternative using uv (if project uses uv):
```json
{
  "mcpServers": {
    "wxcode-kb": {
      "command": "uv",
      "args": [
        "run",
        "--project", "/absolute/path/to/wxcode",
        "python", "-m", "wxcode.mcp.server"
      ]
    }
  }
}
```

### Testing the Server
```bash
# Verify server starts without errors
python -m wxcode.mcp.server

# Check Claude Code sees the server
claude mcp list

# Test a specific server
claude mcp get wxcode-kb
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom JSON-RPC | FastMCP | 2024 | Massive boilerplate reduction |
| Sync database | Async lifespan | FastMCP 2.0 | Proper resource management |
| HTTP transport | STDIO default | MCP standard | Better Claude Code integration |
| FastMCP v1 | FastMCP v2 | 2025 | v1 deprecated, v2 stable |

**Deprecated/outdated:**
- FastMCP v1.x: Superseded by v2, different API
- SSE transport: Deprecated in favor of streamable-http for network use
- Sync database initialization: Use async lifespan

**Upcoming (not recommended yet):**
- FastMCP v3.0: Currently beta (3.0.0b1), breaking changes expected
- MCP Python SDK v2: Expected Q1 2026, pin to v1.x for now

## Open Questions

Things that couldn't be fully resolved:

1. **Environment Variable Loading in MCP Context**
   - What we know: FastMCP supports `FASTMCP_` prefix for settings
   - What's unclear: Does `.env` file loading work in STDIO subprocess context?
   - Recommendation: Explicitly load dotenv at module start, pass env vars in .mcp.json

2. **Beanie Initialization in Subprocess**
   - What we know: `init_beanie()` must be called before queries
   - What's unclear: Any issues with Beanie when server is spawned by Claude Code?
   - Recommendation: Test early; if issues, may need to initialize on first tool call

3. **Neo4j Connection Timeout**
   - What we know: Current `Neo4jConnection` has 60s acquisition timeout
   - What's unclear: Is 60s too long for MCP startup? Will client timeout first?
   - Recommendation: Consider reducing timeout for MCP context, or make async with early yield

## Sources

### Primary (HIGH confidence)
- [FastMCP official docs](https://gofastmcp.com/) - lifespan, logging, server running
- [FastMCP lifespan](https://gofastmcp.com/servers/lifespan) - database connection pattern
- [FastMCP logging](https://gofastmcp.com/servers/logging) - stderr requirement
- [FastMCP MCP JSON config](https://gofastmcp.com/integrations/mcp-json-configuration) - .mcp.json format
- [PyPI fastmcp](https://pypi.org/project/fastmcp/) - version 2.14.3, Python 3.10+
- Project source: `src/wxcode/database.py` - existing init_db() pattern
- Project source: `src/wxcode/graph/neo4j_connection.py` - existing Neo4j pattern
- Project source: `src/wxcode/services/gsd_context_collector.py` - graceful fallback pattern

### Secondary (MEDIUM confidence)
- [MCP Python SDK GitHub](https://github.com/modelcontextprotocol/python-sdk) - SDK structure, relationship to FastMCP
- [Python logging docs](https://docs.python.org/3/howto/logging.html) - stderr handler configuration

### Tertiary (LOW confidence)
- Web search results on STDIO transport - implementation details vary by source

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - FastMCP is official, versions verified on PyPI
- Architecture: HIGH - lifespan pattern from official docs, existing project patterns
- Pitfalls: HIGH - well-documented in MCP ecosystem (stdout/stderr issue is canonical)
- Configuration: MEDIUM - .mcp.json format is standard but Claude Code specifics may vary

**Research date:** 2026-01-21
**Valid until:** 2026-02-21 (30 days - FastMCP v2 is stable, but v3 may release)
