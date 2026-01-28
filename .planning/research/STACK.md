# Stack Research: MCP Server

**Project:** wxcode MCP Server Integration
**Researched:** 2026-01-21
**Overall confidence:** HIGH

## Executive Summary

The wxcode project already has a robust async Python stack (FastAPI, Beanie/MongoDB, Neo4j). Adding MCP Server capability requires minimal new dependencies. The official MCP Python SDK (`mcp>=1.25,<2`) includes FastMCP, which provides decorator-based server construction that aligns perfectly with the existing FastAPI patterns.

**Key decision:** Use the official MCP Python SDK's built-in FastMCP, NOT the standalone `fastmcp` package or `fastapi-mcp`. This minimizes dependencies while providing all needed functionality.

## Recommended Stack

### Core MCP Library

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `mcp[cli]` | `>=1.25,<2` | MCP Server SDK | Official SDK with FastMCP included. Pin to v1.x until v2 stabilizes (Q1 2026). The `[cli]` extra adds development/debugging tools. |

**Installation:**
```bash
pip install "mcp[cli]>=1.25,<2"
```

**Import pattern:**
```python
from mcp.server.fastmcp import FastMCP
```

### Why This Version

- **v1.25.0** (Dec 2024): Latest stable v1.x release
- **v2.0 in Q1 2026**: Breaking changes expected, especially transport layer
- **Pin strategy**: `>=1.25,<2` gets bug fixes but avoids v2 breakage
- FastMCP 1.0 was incorporated into the official SDK in 2024

**Source:** [MCP Python SDK Releases](https://github.com/modelcontextprotocol/python-sdk/releases)

### No Additional Dependencies Required

The existing wxcode stack already provides everything MCP needs:

| Existing Dependency | Version | MCP Usage |
|---------------------|---------|-----------|
| `pydantic` | 2.12.5 | Tool input/output validation (FastMCP uses Pydantic natively) |
| `starlette` | 0.50.0 | ASGI app mounting (FastMCP creates Starlette apps) |
| `uvicorn` | 0.40.0 | HTTP server for MCP transport |
| `motor` / `beanie` | 3.7.1 / 2.0.1 | Async MongoDB access for MCP tools |
| `neo4j` | 5.28.1 | Async Neo4j for dependency graph tools |

## Integration Points

### 1. ASGI Mounting Strategy

Mount MCP server alongside existing FastAPI app:

```python
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Create MCP server
mcp = FastMCP("wxcode-kb")

# Get ASGI app from MCP
mcp_app = mcp.http_app(path="/mcp")

# Combine lifespans (CRITICAL)
@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    # Existing wxcode startup
    client = await init_db()
    app.state.db_client = client

    # MCP lifespan (session manager initialization)
    async with mcp_app.lifespan(app):
        yield

    # Existing wxcode shutdown
    await close_db(client)

# Mount MCP on existing app
app = FastAPI(
    title="WXCODE",
    lifespan=combined_lifespan,
)
app.mount("/mcp", mcp_app)
```

**Key insight:** Must combine lifespans or MCP session manager won't initialize.

**Source:** [FastMCP + FastAPI Integration](https://gofastmcp.com/integrations/fastapi)

### 2. Transport Protocol

**Recommended:** Streamable HTTP (`transport="streamable-http"`)

| Transport | Use Case | Claude Code Support |
|-----------|----------|---------------------|
| `streamable-http` | Production, remote access | YES (recommended) |
| `sse` | Legacy, being deprecated | YES (but deprecated) |
| `stdio` | Local CLI tools | YES |

Configure for HTTP:
```python
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)
```

Or when mounted on FastAPI, it inherits the host/port from uvicorn.

**Source:** [Claude Code MCP Docs](https://code.claude.com/docs/en/mcp)

### 3. Database Access Pattern

MCP tools will use existing Beanie models and Neo4j connection:

```python
from wxcode.models import Element, Project
from wxcode.graph.neo4j_connection import Neo4jConnection

@mcp.tool()
async def get_element(element_name: str, project_name: str) -> dict:
    """Get element details from Knowledge Base."""
    element = await Element.find_one(
        Element.source_name == element_name,
        Element.project.name == project_name
    )
    return element.model_dump() if element else {"error": "Not found"}

@mcp.tool()
async def get_dependencies(element_name: str) -> list[dict]:
    """Get element dependencies from Neo4j graph."""
    async with Neo4jConnection() as conn:
        return await conn.execute(
            "MATCH (n {name: $name})-[:DEPENDS_ON]->(m) RETURN m.name",
            {"name": element_name}
        )
```

### 4. Configuration Extension

Add MCP settings to existing `Settings` class:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # MCP Server
    mcp_enabled: bool = True
    mcp_path: str = "/mcp"
    mcp_server_name: str = "wxcode-kb"
```

## What NOT to Use

### 1. Standalone `fastmcp` Package

| Package | Version | Why NOT |
|---------|---------|---------|
| `fastmcp` | 2.14.3 | Adds unnecessary dependency. FastMCP is already in `mcp` SDK. Would need to manage two update cycles. |

**Exception:** If you need FastMCP 3.0 beta features (January 2026), install standalone. But for production, stick with SDK's bundled version.

### 2. `fastapi-mcp` Package

| Package | Version | Why NOT |
|---------|---------|---------|
| `fastapi-mcp` | 0.4.0 | Auto-converts FastAPI endpoints to MCP tools. But wxcode needs CUSTOM tools for KB queries, not generic endpoint exposure. Over-engineering for this use case. |

**When it would be useful:** If you wanted to expose ALL existing `/api/*` endpoints as MCP tools without custom logic. That's not our goal.

### 3. MongoDB MCP Server (Official)

| Package | Why NOT |
|---------|---------|
| `mongodb-mcp-server` | Generic MongoDB access. We need wxcode-specific tools (get element with AST, get conversion status, update conversion). Generic CRUD is insufficient. |

### 4. SSE Transport

| Why NOT |
|---------|
| Being deprecated in favor of Streamable HTTP. SSE is unidirectional (server-to-client only). Streamable HTTP provides full bidirectional communication. |

## Architecture Decision

### Separate Process vs Same Process

**Recommendation:** Same process (mounted on FastAPI app)

| Approach | Pros | Cons |
|----------|------|------|
| **Same process** (mount) | Shares DB connections, simpler deployment, single port | Slightly coupled |
| **Separate process** | Independent scaling, isolation | Extra port, duplicated DB setup |

For wxcode's use case (local development tool, single-user), same-process mounting is simpler and sufficient. The MCP server shares the existing Beanie/MongoDB and Neo4j connections.

### Stateful vs Stateless

**Recommendation:** Stateless for HTTP transport

```python
mcp = FastMCP("wxcode-kb", stateless_http=True)
```

- Stateless is simpler for read-heavy KB queries
- No session persistence needed for our tools
- Better for potential future scaling

## Claude Code Configuration

After implementation, users configure Claude Code:

**.mcp.json (project scope):**
```json
{
  "mcpServers": {
    "wxcode-kb": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

Or via CLI:
```bash
claude mcp add --transport http wxcode-kb http://localhost:8000/mcp
```

**Source:** [Claude Code MCP Configuration](https://code.claude.com/docs/en/mcp)

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| MCP SDK choice (`mcp>=1.25,<2`) | HIGH | Verified with PyPI, GitHub releases, official docs |
| FastAPI mounting pattern | HIGH | Verified with gofastmcp.com integration docs |
| Transport recommendation | HIGH | Verified with Claude Code docs and MCP spec |
| No additional deps needed | HIGH | Cross-referenced existing requirements.txt |
| Version pinning strategy | MEDIUM | v2 timeline is estimated (Q1 2026), monitor releases |

## Sources

### HIGH Confidence (Official Documentation)
- [MCP Python SDK - GitHub](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Python SDK - PyPI (v1.25.0)](https://pypi.org/project/mcp/)
- [FastMCP + FastAPI Integration](https://gofastmcp.com/integrations/fastapi)
- [FastMCP Deployment Guide](https://gofastmcp.com/deployment/running-server)
- [Claude Code MCP Documentation](https://code.claude.com/docs/en/mcp)

### MEDIUM Confidence (Verified Sources)
- [Streamable HTTP Transport - Cloudflare Blog](https://blog.cloudflare.com/streamable-http-mcp-servers-python/)
- [MCP Python SDK Releases](https://github.com/modelcontextprotocol/python-sdk/releases)

## Installation Command

```bash
# Add to requirements.txt
echo 'mcp[cli]>=1.25,<2' >> requirements.txt

# Or install directly
pip install "mcp[cli]>=1.25,<2"
```

No other dependencies needed - the existing wxcode stack (pydantic, starlette, uvicorn, beanie, neo4j) provides everything MCP requires.
