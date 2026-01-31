"""MCP tools for system operations.

Provides health check and tool listing capabilities for the MCP server.
"""

from datetime import datetime
from typing import Any

from fastmcp import Context

from wxcode.mcp.instance import mcp
from wxcode.models import Project, Element


@mcp.tool
async def health_check(ctx: Context) -> dict[str, Any]:
    """
    Check MCP server health and database connectivity.

    Returns status of all services: MongoDB, Neo4j, and general server info.
    Use this to verify the MCP server is working correctly.

    Returns:
        Health status with connection details and statistics
    """
    lifespan_ctx = ctx.request_context.lifespan_context

    result = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "server": "wxcode-kb",
        "services": {},
    }

    # Check MongoDB
    try:
        mongo_client = lifespan_ctx.get("mongo_client")
        if mongo_client:
            # Quick ping
            await mongo_client.admin.command("ping")

            # Get some stats
            project_count = await Project.count()
            element_count = await Element.count()

            result["services"]["mongodb"] = {
                "status": "connected",
                "projects": project_count,
                "elements": element_count,
            }
        else:
            result["services"]["mongodb"] = {"status": "not_initialized"}
            result["status"] = "degraded"
    except Exception as e:
        result["services"]["mongodb"] = {
            "status": "error",
            "error": str(e),
        }
        result["status"] = "unhealthy"

    # Check Neo4j
    neo4j_available = lifespan_ctx.get("neo4j_available", False)
    neo4j_conn = lifespan_ctx.get("neo4j_conn")

    if neo4j_available and neo4j_conn:
        try:
            # Quick connectivity check
            async with neo4j_conn.driver.session() as session:
                neo4j_result = await session.run("RETURN 1 as n")
                await neo4j_result.consume()

            result["services"]["neo4j"] = {"status": "connected"}
        except Exception as e:
            result["services"]["neo4j"] = {
                "status": "error",
                "error": str(e),
            }
    else:
        result["services"]["neo4j"] = {
            "status": "unavailable",
            "note": "Neo4j is optional - graph analysis features disabled",
        }

    return result


@mcp.tool
async def list_tools(
    ctx: Context,
    category: str | None = None,
) -> dict[str, Any]:
    """
    List all available MCP tools with descriptions.

    Returns a categorized list of all tools exposed by the wxcode-kb MCP server.
    Use this to discover available functionality.

    Args:
        category: Optional filter by category. Options:
                  "elements", "controls", "procedures", "schema", "graph",
                  "conversion", "stack", "wlanguage", "system", or None for all.

    Returns:
        Categorized list of tools with descriptions
    """
    # Tool definitions organized by category
    tools_by_category = {
        "elements": {
            "description": "Access WinDev source code elements",
            "tools": [
                {"name": "get_element", "description": "Get complete element data (AST, raw_content, dependencies)"},
                {"name": "list_elements", "description": "List elements with optional filters (type, layer, status)"},
                {"name": "search_code", "description": "Search for patterns in element code"},
            ],
        },
        "controls": {
            "description": "UI controls and data bindings",
            "tools": [
                {"name": "get_controls", "description": "Get control hierarchy for an element"},
                {"name": "get_data_bindings", "description": "Get data bindings between controls and data sources"},
            ],
        },
        "procedures": {
            "description": "Global and local procedures",
            "tools": [
                {"name": "get_procedures", "description": "List procedures for a project or element"},
                {"name": "get_procedure", "description": "Get detailed procedure information"},
            ],
        },
        "schema": {
            "description": "Database schema information",
            "tools": [
                {"name": "list_kb_connections", "description": "List database connections from KB schema"},
                {"name": "get_schema", "description": "Get complete database schema for a project"},
                {"name": "get_table", "description": "Get detailed table information (columns, indexes)"},
            ],
        },
        "graph": {
            "description": "Dependency analysis (requires Neo4j for some features)",
            "tools": [
                {"name": "get_dependencies", "description": "Get dependencies for an element"},
                {"name": "get_impact", "description": "Analyze impact of changing an element"},
                {"name": "get_path", "description": "Find dependency path between two elements"},
                {"name": "find_hubs", "description": "Find highly connected elements (hubs)"},
                {"name": "find_dead_code", "description": "Find potentially unused elements"},
                {"name": "find_cycles", "description": "Detect dependency cycles"},
            ],
        },
        "conversion": {
            "description": "Conversion workflow management",
            "tools": [
                {"name": "get_conversion_candidates", "description": "Get elements ready for conversion"},
                {"name": "get_topological_order", "description": "Get elements in conversion order"},
                {"name": "get_conversion_stats", "description": "Get conversion progress statistics"},
                {"name": "mark_converted", "description": "Mark an element as converted"},
                {"name": "mark_project_initialized", "description": "Mark output project as initialized"},
                {"name": "create_milestone", "description": "Create a milestone for element conversion"},
                {"name": "list_connections_outputproject", "description": "List connections of an OutputProject"},
                {"name": "add_connection_outputproject", "description": "Add a connection to an OutputProject"},
                {"name": "update_connection_outputproject", "description": "Update a connection in an OutputProject"},
            ],
        },
        "stack": {
            "description": "Target stack conventions",
            "tools": [
                {"name": "get_stack_conventions", "description": "Get naming, patterns, and structure for target stack"},
            ],
        },
        "planes": {
            "description": "UI plane detection (tabs, wizards, views)",
            "tools": [
                {"name": "get_element_planes", "description": "Detect multi-plane UI patterns"},
            ],
        },
        "wlanguage": {
            "description": "WLanguage reference and patterns",
            "tools": [
                {"name": "get_wlanguage_reference", "description": "Get WLanguage function documentation"},
                {"name": "list_wlanguage_functions", "description": "List WLanguage functions by category"},
                {"name": "get_wlanguage_pattern", "description": "Get conversion pattern for WLanguage construct"},
            ],
        },
        "similarity": {
            "description": "Find similar converted elements",
            "tools": [
                {"name": "search_converted_similar", "description": "Find similar already-converted elements"},
            ],
        },
        "pdf": {
            "description": "PDF documentation access",
            "tools": [
                {"name": "get_element_pdf_slice", "description": "Get PDF documentation slice for an element"},
            ],
        },
        "system": {
            "description": "System and server operations",
            "tools": [
                {"name": "health_check", "description": "Check server health and database connectivity"},
                {"name": "list_tools", "description": "List all available MCP tools"},
            ],
        },
    }

    # Filter by category if specified
    if category:
        category = category.lower()
        if category not in tools_by_category:
            return {
                "error": True,
                "code": "INVALID_CATEGORY",
                "message": f"Unknown category: {category}",
                "valid_categories": list(tools_by_category.keys()),
            }

        return {
            "error": False,
            "category": category,
            "description": tools_by_category[category]["description"],
            "tools": tools_by_category[category]["tools"],
            "tool_count": len(tools_by_category[category]["tools"]),
        }

    # Return all tools
    total_tools = sum(len(cat["tools"]) for cat in tools_by_category.values())

    return {
        "error": False,
        "total_tools": total_tools,
        "categories": tools_by_category,
    }
