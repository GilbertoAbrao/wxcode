"""MCP tools for Neo4j graph analysis.

Provides tools for dependency analysis, impact assessment, and graph traversal.
All tools require Neo4j to be running and synced with MongoDB.
"""

from fastmcp import Context

from wxcode.mcp.instance import mcp
from wxcode.graph.impact_analyzer import ImpactAnalyzer
from wxcode.graph.neo4j_connection import Neo4jConnection


def _check_neo4j(ctx: Context) -> tuple[Neo4jConnection | None, dict | None]:
    """
    Check Neo4j availability and return connection or error dict.

    Args:
        ctx: FastMCP context with lifespan context

    Returns:
        (connection, None) if available
        (None, error_dict) if unavailable
    """
    neo4j_available = ctx.request_context.lifespan_context.get("neo4j_available", False)
    if not neo4j_available:
        return None, {
            "error": True,
            "code": "NEO4J_UNAVAILABLE",
            "message": "Neo4j is not available. Graph analysis requires Neo4j.",
            "suggestion": (
                "Start Neo4j with: docker run -d -p 7474:7474 -p 7687:7687 "
                "-e NEO4J_AUTH=neo4j/password neo4j:5"
            ),
        }
    return ctx.request_context.lifespan_context["neo4j_conn"], None


@mcp.tool
async def get_dependencies(
    ctx: Context,
    element_name: str,
    direction: str = "both",
    project_name: str | None = None,
) -> dict:
    """
    Get direct dependencies (uses/used_by) for an element.

    Returns immediate relationships without transitive traversal.
    Use get_impact for full transitive impact analysis.

    Args:
        element_name: Name of the element (e.g., PAGE_Login, ValidaCPF)
        direction: "uses" (outgoing), "used_by" (incoming), or "both" (default)
        project_name: Optional project name to filter results

    Returns:
        Direct dependencies with relationship types
    """
    try:
        conn, error = _check_neo4j(ctx)
        if error:
            return error

        params: dict = {"name": element_name}
        if project_name:
            params["project"] = project_name

        project_filter = "WHERE n.project = $project" if project_name else ""

        uses = []
        used_by = []

        if direction in ("uses", "both"):
            query = f"""
            MATCH (n {{name: $name}})
            {project_filter}
            OPTIONAL MATCH (n)-[r]->(target)
            WHERE target IS NOT NULL
            RETURN type(r) as rel_type, target.name as name, labels(target)[0] as type
            """
            records = await conn.execute(query, params)
            uses = [
                {"name": r["name"], "type": r["type"], "relationship": r["rel_type"]}
                for r in records
                if r["name"]
            ]

        if direction in ("used_by", "both"):
            query = f"""
            MATCH (n {{name: $name}})
            {project_filter}
            OPTIONAL MATCH (source)-[r]->(n)
            WHERE source IS NOT NULL
            RETURN type(r) as rel_type, source.name as name, labels(source)[0] as type
            """
            records = await conn.execute(query, params)
            used_by = [
                {"name": r["name"], "type": r["type"], "relationship": r["rel_type"]}
                for r in records
                if r["name"]
            ]

        return {"error": False, "element": element_name, "uses": uses, "used_by": used_by}

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }


@mcp.tool
async def get_impact(
    ctx: Context,
    element_name: str,
    max_depth: int = 5,
    project_name: str | None = None,
) -> dict:
    """
    Analyze impact of changes to an element.

    Finds all elements that would be affected if the specified element changes.
    Uses transitive traversal to find indirect dependencies.

    Args:
        element_name: Element name, optionally prefixed with type (e.g., "TABLE:CLIENTE")
        max_depth: Maximum traversal depth (default: 5, recommend 2-3 for initial analysis)
        project_name: Optional project name to filter results

    Returns:
        Affected elements grouped by depth and type
    """
    try:
        conn, error = _check_neo4j(ctx)
        if error:
            return error

        analyzer = ImpactAnalyzer(conn)
        result = await analyzer.get_impact(
            node_id=element_name,
            max_depth=max_depth,
            project=project_name,
        )

        if result.error:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": result.error,
                "suggestion": "Ensure Neo4j is synced: wxcode sync-neo4j <project>",
            }

        return {
            "error": False,
            "data": {
                "source_name": result.source_name,
                "source_type": result.source_type,
                "total_affected": result.total_affected,
                "max_depth": result.max_depth,
                "affected": [
                    {"name": a.name, "type": a.node_type, "depth": a.depth}
                    for a in result.affected
                ],
                "by_depth": {
                    str(d): [{"name": n.name, "type": n.node_type} for n in nodes]
                    for d, nodes in result.by_depth().items()
                },
                "by_type": {
                    t: [{"name": n.name, "depth": n.depth} for n in nodes]
                    for t, nodes in result.by_type().items()
                },
            },
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }


@mcp.tool
async def get_path(
    ctx: Context,
    source: str,
    target: str,
    project_name: str | None = None,
) -> dict:
    """
    Find paths between two elements in the dependency graph.

    Uses Neo4j shortest path algorithm to find how elements are connected.

    Args:
        source: Source element name
        target: Target element name
        project_name: Optional project name to filter results

    Returns:
        Paths connecting the elements, sorted by length
    """
    try:
        conn, error = _check_neo4j(ctx)
        if error:
            return error

        analyzer = ImpactAnalyzer(conn)
        result = await analyzer.get_path(
            source=source,
            target=target,
            project=project_name,
        )

        if result.error:
            return {
                "error": True,
                "code": "NO_PATH",
                "message": result.error,
            }

        return {
            "error": False,
            "data": {
                "source": result.source,
                "target": result.target,
                "path_count": len(result.paths),
                "shortest_length": result.shortest_length,
                "paths": [
                    [{"name": n.name, "type": n.node_type} for n in path]
                    for path in result.paths
                ],
            },
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }


@mcp.tool
async def find_hubs(
    ctx: Context,
    min_connections: int = 10,
    project_name: str | None = None,
) -> dict:
    """
    Find hub nodes with many dependencies.

    Hubs are critical elements with many connections (both incoming and outgoing).
    Changes to hub elements have high impact across the codebase and should be
    reviewed carefully. These are often core utilities, shared services, or
    central data structures.

    Args:
        min_connections: Minimum total connections (in + out) to be considered a hub
        project_name: Optional project name to filter results

    Returns:
        Hub nodes sorted by total connections (highest first)
    """
    try:
        conn, error = _check_neo4j(ctx)
        if error:
            return error

        analyzer = ImpactAnalyzer(conn)
        result = await analyzer.find_hubs(
            min_connections=min_connections,
            project=project_name,
        )

        if result.error:
            return {
                "error": True,
                "code": "ANALYSIS_ERROR",
                "message": result.error,
            }

        return {
            "error": False,
            "data": {
                "min_connections": result.min_connections,
                "hub_count": len(result.hubs),
                "hubs": [
                    {
                        "name": hub.name,
                        "type": hub.node_type,
                        "incoming": hub.incoming,
                        "outgoing": hub.outgoing,
                        "total": hub.total_connections,
                    }
                    for hub in result.hubs
                ],
            },
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }


@mcp.tool
async def find_dead_code(
    ctx: Context,
    project_name: str | None = None,
    exclude_prefixes: list[str] | None = None,
) -> dict:
    """
    Find potentially unused procedures and classes.

    Dead code candidates are elements with no incoming calls or uses.
    Entry points like APIs, Pages, Windows, and Tasks are excluded by default
    since they are invoked externally (not from within the codebase).

    Note: Results are candidates - manual verification recommended before removal.

    Args:
        project_name: Optional project name to filter results
        exclude_prefixes: Entry point prefixes to exclude (default: API, Task, PAGE_, WIN_)

    Returns:
        Potentially unused procedures and classes
    """
    try:
        conn, error = _check_neo4j(ctx)
        if error:
            return error

        analyzer = ImpactAnalyzer(conn)
        result = await analyzer.find_dead_code(
            project=project_name,
            entry_point_prefixes=exclude_prefixes,
        )

        if result.error:
            return {
                "error": True,
                "code": "ANALYSIS_ERROR",
                "message": result.error,
            }

        # Default prefixes used when none provided
        default_prefixes = ["API", "Task", "PAGE_", "WIN_"]
        used_prefixes = exclude_prefixes if exclude_prefixes is not None else default_prefixes

        return {
            "error": False,
            "data": {
                "total": result.total,
                "procedures": result.procedures,
                "classes": result.classes,
                "excluded_prefixes": used_prefixes,
            },
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }


@mcp.tool
async def find_cycles(
    ctx: Context,
    node_type: str = "Procedure",
    max_length: int = 10,
    project_name: str | None = None,
) -> dict:
    """
    Find circular dependencies in the codebase.

    Cycles are circular dependencies where A depends on B which depends on A
    (or longer chains). These can cause:
    - Initialization order problems
    - Difficulty in testing and mocking
    - Tight coupling between components

    Results are limited to 100 cycles to prevent explosion.
    Lower max_length values improve performance.

    Args:
        node_type: Type of nodes to check (default: Procedure)
        max_length: Maximum cycle length to detect (default: 10)
        project_name: Optional project name to filter results

    Returns:
        Cycles found in the dependency graph
    """
    try:
        conn, error = _check_neo4j(ctx)
        if error:
            return error

        analyzer = ImpactAnalyzer(conn)
        cycles = await analyzer.find_cycles(
            node_type=node_type,
            max_length=max_length,
            project=project_name,
        )

        return {
            "error": False,
            "data": {
                "node_type": node_type,
                "cycle_count": len(cycles),
                "cycles": cycles,
            },
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }