"""MCP tools for conversion workflow tracking.

Provides tools to track conversion progress, determine optimal conversion order,
identify elements ready for conversion, and mark elements/projects as converted.

Write operations:
- mark_converted: Mark an element as converted
- mark_project_initialized: Mark an OutputProject as initialized
- create_milestone: Create a milestone associated with WXCODE structure
"""

import logging
from datetime import datetime
from typing import Any

from bson import DBRef

# Audit logger for write operations
audit_logger = logging.getLogger("wxcode.mcp.audit")
from fastmcp import Context

from wxcode.analyzer.dependency_analyzer import DependencyAnalyzer
from wxcode.config import get_settings
from wxcode.mcp.instance import mcp
from wxcode.models import Element, Project
from wxcode.models.element import ConversionStatus
from wxcode.models.milestone import Milestone, MilestoneStatus
from wxcode.models.output_project import (
    OutputProject,
    OutputProjectConnection,
    OutputProjectStatus,
)
from wxcode.models.schema import DatabaseSchema


async def _find_element(
    ctx: Context,
    element_name: str,
    project_name: str | None,
) -> tuple[Element | None, str | None]:
    """
    Find element by name, optionally scoped to project.

    Uses DBRef pattern for project-scoped queries (workaround for Beanie Link fields).

    Args:
        ctx: FastMCP context with lifespan context
        element_name: Name of the element to find
        project_name: Optional project name to scope the search

    Returns:
        Tuple of (element, error_message) - element is None if not found
    """
    if project_name:
        project = await Project.find_one(Project.name == project_name)
        if not project:
            return None, f"Project '{project_name}' not found"

        # DBRef query via raw Motor - workaround for Beanie Link fields
        settings = get_settings()
        mongo_client = ctx.request_context.lifespan_context["mongo_client"]
        db = mongo_client[settings.mongodb_database]
        collection = db["elements"]

        project_dbref = DBRef("projects", project.id)
        elem_dict = await collection.find_one({
            "source_name": element_name,
            "project_id": project_dbref,
        })

        if not elem_dict:
            return None, f"Element '{element_name}' not found in project '{project_name}'"

        element = await Element.get(elem_dict["_id"])
        return element, None
    else:
        # Search across all projects
        elements = await Element.find(Element.source_name == element_name).to_list()

        if not elements:
            return None, f"Element '{element_name}' not found"

        if len(elements) > 1:
            # Ambiguous - need to look up project names
            settings = get_settings()
            mongo_client = ctx.request_context.lifespan_context["mongo_client"]
            db = mongo_client[settings.mongodb_database]
            projects_coll = db["projects"]

            project_names = []
            for elem in elements:
                if hasattr(elem, "project_id") and elem.project_id:
                    proj_dict = await projects_coll.find_one({"_id": elem.project_id.ref.id})
                    if proj_dict:
                        project_names.append(proj_dict["name"])

            return None, (
                f"Element '{element_name}' found in multiple projects: "
                f"{', '.join(project_names)}. Use project_name to specify."
            )

        return elements[0], None


@mcp.tool
async def get_conversion_candidates(
    ctx: Context,
    project_name: str,
    layer: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Get elements ready for conversion based on dependency analysis.

    Returns pending elements whose dependencies have already been converted.
    Use this to identify the next batch of elements to convert while
    respecting the topological dependency order.

    Args:
        project_name: Name of the project to analyze
        layer: Optional layer filter (schema, domain, business, api, ui)
        limit: Maximum number of candidates to return (default: 20)

    Returns:
        List of conversion-ready elements sorted by topological order
    """
    try:
        # Find project
        project = await Project.find_one(Project.name == project_name)
        if not project:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"Project '{project_name}' not found",
            }

        # Build query for pending elements
        settings = get_settings()
        mongo_client = ctx.request_context.lifespan_context["mongo_client"]
        db = mongo_client[settings.mongodb_database]
        collection = db["elements"]

        project_dbref = DBRef("projects", project.id)

        # Query pending elements
        query: dict[str, Any] = {
            "project_id": project_dbref,
            "conversion.status": ConversionStatus.PENDING.value,
        }

        if layer:
            query["layer"] = layer

        # Get all pending elements
        cursor = collection.find(query).sort("topological_order", 1)
        pending_elements = await cursor.to_list(length=None)

        # Get all converted/validated element names for dependency checking
        converted_query = {
            "project_id": project_dbref,
            "conversion.status": {
                "$in": [
                    ConversionStatus.CONVERTED.value,
                    ConversionStatus.VALIDATED.value,
                ]
            },
        }
        converted_cursor = collection.find(converted_query, {"source_name": 1})
        converted_docs = await converted_cursor.to_list(length=None)
        converted_names = {doc["source_name"] for doc in converted_docs}

        # Filter candidates: dependencies.uses must all be converted
        candidates = []
        for elem in pending_elements:
            if len(candidates) >= limit:
                break

            # Check if all dependencies are converted
            deps = elem.get("dependencies", {})
            uses = deps.get("uses", [])

            # Element is ready if all its dependencies are converted
            all_deps_converted = all(dep in converted_names for dep in uses)

            if all_deps_converted:
                candidates.append({
                    "name": elem["source_name"],
                    "type": elem.get("source_type"),
                    "file": elem.get("source_file"),
                    "layer": elem.get("layer"),
                    "topological_order": elem.get("topological_order"),
                    "dependencies_count": len(uses),
                    "blocking_count": len([u for u in uses if u not in converted_names]),
                })

        return {
            "error": False,
            "data": {
                "project": project_name,
                "filter_layer": layer,
                "total_pending": len(pending_elements),
                "total_converted": len(converted_names),
                "candidates_count": len(candidates),
                "candidates": candidates,
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
async def get_topological_order(
    ctx: Context,
    project_name: str,
    layer: str | None = None,
    include_converted: bool = False,
) -> dict[str, Any]:
    """
    Get recommended conversion order based on dependency analysis.

    Uses DependencyAnalyzer to compute fresh topological ordering that
    respects element dependencies. Elements without dependencies come first.

    Args:
        project_name: Name of the project to analyze
        layer: Optional layer filter (schema, domain, business, api, ui)
        include_converted: Include already converted elements (default: False)

    Returns:
        Ordered list of elements with layer groupings
    """
    try:
        # Find project
        project = await Project.find_one(Project.name == project_name)
        if not project:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"Project '{project_name}' not found",
            }

        # Run fresh dependency analysis (without persisting)
        analyzer = DependencyAnalyzer(project.id)
        result = await analyzer.analyze(persist=False)

        # Get status info for filtering
        settings = get_settings()
        mongo_client = ctx.request_context.lifespan_context["mongo_client"]
        db = mongo_client[settings.mongodb_database]
        collection = db["elements"]

        project_dbref = DBRef("projects", project.id)

        # Build name -> status mapping
        status_cursor = collection.find(
            {"project_id": project_dbref},
            {"source_name": 1, "conversion.status": 1, "layer": 1},
        )
        status_docs = await status_cursor.to_list(length=None)
        name_to_info = {
            doc["source_name"]: {
                "status": doc.get("conversion", {}).get("status", "pending"),
                "layer": doc.get("layer"),
            }
            for doc in status_docs
        }

        # Filter and transform topological_order
        # node_id format is "type:name" - extract name
        filtered_order = []
        by_layer: dict[str, list[dict[str, Any]]] = {}

        for idx, node_id in enumerate(result.topological_order):
            # Extract name from node_id (e.g., "page:PAGE_Login" -> "PAGE_Login")
            if ":" in node_id:
                node_type, name = node_id.split(":", 1)
            else:
                node_type = "unknown"
                name = node_id

            # Get element info
            info = name_to_info.get(name, {})
            elem_status = info.get("status", "unknown")
            elem_layer = info.get("layer")

            # Filter by conversion status
            if not include_converted:
                if elem_status in [
                    ConversionStatus.CONVERTED.value,
                    ConversionStatus.VALIDATED.value,
                ]:
                    continue

            # Filter by layer if specified
            if layer and elem_layer != layer:
                continue

            entry = {
                "position": idx,
                "node_id": node_id,
                "name": name,
                "node_type": node_type,
                "status": elem_status,
                "layer": elem_layer,
            }

            filtered_order.append(entry)

            # Group by layer
            layer_key = elem_layer or "unassigned"
            if layer_key not in by_layer:
                by_layer[layer_key] = []
            by_layer[layer_key].append(entry)

        return {
            "error": False,
            "data": {
                "project": project_name,
                "filter_layer": layer,
                "include_converted": include_converted,
                "total_nodes": result.total_nodes,
                "total_edges": result.total_edges,
                "cycles_count": len(result.cycles),
                "order_count": len(filtered_order),
                "order": filtered_order,
                "by_layer": by_layer,
                "layer_stats": result.layer_stats,
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
async def get_conversion_stats(
    ctx: Context,
    project_name: str,
) -> dict[str, Any]:
    """
    Get conversion progress statistics for a project.

    Uses MongoDB aggregation to efficiently compute conversion status
    breakdown by status and by layer+status combination.

    Args:
        project_name: Name of the project to analyze

    Returns:
        Conversion statistics with progress percentage and breakdowns
    """
    try:
        # Find project
        project = await Project.find_one(Project.name == project_name)
        if not project:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"Project '{project_name}' not found",
            }

        # Get MongoDB collection for aggregation
        settings = get_settings()
        mongo_client = ctx.request_context.lifespan_context["mongo_client"]
        db = mongo_client[settings.mongodb_database]
        collection = db["elements"]

        project_dbref = DBRef("projects", project.id)

        # Aggregation pipeline for status counts
        status_pipeline = [
            {"$match": {"project_id": project_dbref}},
            {
                "$group": {
                    "_id": "$conversion.status",
                    "count": {"$sum": 1},
                }
            },
        ]
        status_results = await collection.aggregate(status_pipeline).to_list(length=None)

        # Build status totals
        by_status: dict[str, int] = {}
        total = 0
        for doc in status_results:
            status = doc["_id"] or "pending"  # Handle null status
            count = doc["count"]
            by_status[status] = count
            total += count

        # Aggregation pipeline for layer+status counts
        layer_status_pipeline = [
            {"$match": {"project_id": project_dbref}},
            {
                "$group": {
                    "_id": {
                        "layer": "$layer",
                        "status": "$conversion.status",
                    },
                    "count": {"$sum": 1},
                }
            },
        ]
        layer_status_results = await collection.aggregate(
            layer_status_pipeline
        ).to_list(length=None)

        # Build layer breakdown
        by_layer: dict[str, dict[str, int]] = {}
        for doc in layer_status_results:
            layer = doc["_id"]["layer"] or "unassigned"
            status = doc["_id"]["status"] or "pending"
            count = doc["count"]

            if layer not in by_layer:
                by_layer[layer] = {}
            by_layer[layer][status] = count

        # Calculate progress
        converted_count = by_status.get(ConversionStatus.CONVERTED.value, 0)
        validated_count = by_status.get(ConversionStatus.VALIDATED.value, 0)
        completed = converted_count + validated_count

        progress_percentage = (completed / total * 100) if total > 0 else 0.0

        return {
            "error": False,
            "data": {
                "project": project_name,
                "total_elements": total,
                "completed": completed,
                "progress_percentage": round(progress_percentage, 2),
                "by_status": by_status,
                "by_layer": by_layer,
                "status_descriptions": {
                    "pending": "Not yet started",
                    "in_progress": "Currently being converted",
                    "proposal_generated": "GSD proposal created",
                    "converted": "Code generated",
                    "validated": "Tested and verified",
                    "error": "Conversion failed",
                    "skipped": "Intentionally excluded",
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
async def mark_converted(
    ctx: Context,
    element_name: str,
    project_name: str,
    confirm: bool = False,
    notes: str | None = None,
) -> dict[str, Any]:
    """
    Mark an element as converted with explicit confirmation required.

    This is the ONLY write operation in the MCP server. All state changes
    require explicit confirm=True to execute - calling with confirm=False
    returns a preview of the change without executing it.

    Implements the confirmation pattern for safe state mutations:
    1. First call with confirm=False to preview the change
    2. Review the preview and call again with confirm=True to execute

    Args:
        element_name: Name of the element to mark as converted
        project_name: Name of the project containing the element
        confirm: Set to True to execute the change (default: False for preview)
        notes: Optional notes about the conversion (appended to issues)

    Returns:
        Preview dict (confirm=False) or execution result (confirm=True)
    """
    try:
        # Find element using helper
        element, error = await _find_element(ctx, element_name, project_name)
        if error:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": error,
            }

        # Get current status for preview/logging
        current_status = element.conversion.status.value
        new_status = ConversionStatus.CONVERTED.value

        # Preview mode - return what would happen
        if not confirm:
            return {
                "error": False,
                "requires_confirmation": True,
                "preview": {
                    "element": element_name,
                    "project": project_name,
                    "current_status": current_status,
                    "new_status": new_status,
                    "notes": notes,
                    "instruction": (
                        "Call mark_converted again with confirm=True to execute this change"
                    ),
                },
            }

        # Execute mode - apply the change
        element.conversion.status = ConversionStatus.CONVERTED
        element.conversion.converted_at = datetime.utcnow()

        # Append timestamped note if provided
        if notes:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            element.conversion.issues.append(f"[{timestamp}] {notes}")

        # Persist the change
        await element.save()

        # Audit log
        audit_logger.info(
            "mark_converted executed: project=%s element=%s old_status=%s new_status=%s",
            project_name,
            element_name,
            current_status,
            new_status,
        )

        return {
            "error": False,
            "executed": True,
            "data": {
                "element": element_name,
                "project": project_name,
                "old_status": current_status,
                "new_status": new_status,
                "converted_at": element.conversion.converted_at.isoformat(),
                "notes_added": notes is not None,
            },
        }

    except Exception as e:
        audit_logger.error(
            "mark_converted failed: project=%s element=%s error=%s",
            project_name,
            element_name,
            str(e),
        )
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }


@mcp.tool
async def mark_project_initialized(
    ctx: Context,
    output_project_id: str,
    confirm: bool = False,
    notes: str | None = None,
) -> dict[str, Any]:
    """
    Mark an OutputProject as initialized after project structure is created.

    Use this after completing Phase 1 (project initialization):
    - Project structure created (directories, config files)
    - Database models generated for all tables
    - Main application entry point created
    - PROJECT.md and ROADMAP.md created

    This is a write operation that requires explicit confirm=True to execute.
    Calling with confirm=False returns a preview of the change.

    Args:
        output_project_id: ID of the OutputProject to mark as initialized
        confirm: Set to True to execute the change (default: False for preview)
        notes: Optional notes about the initialization (e.g., what was created)

    Returns:
        Preview dict (confirm=False) or execution result (confirm=True)
    """
    try:
        # Find OutputProject
        output_project = await OutputProject.get(output_project_id)
        if not output_project:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"OutputProject '{output_project_id}' not found",
            }

        # Get current status
        current_status = output_project.status.value
        new_status = OutputProjectStatus.INITIALIZED.value

        # Validate transition
        if output_project.status == OutputProjectStatus.INITIALIZED:
            return {
                "error": True,
                "code": "ALREADY_INITIALIZED",
                "message": f"OutputProject is already initialized",
                "current_status": current_status,
            }

        if output_project.status == OutputProjectStatus.ACTIVE:
            return {
                "error": True,
                "code": "INVALID_TRANSITION",
                "message": "Cannot mark as initialized - project is already active",
                "current_status": current_status,
            }

        # Preview mode
        if not confirm:
            return {
                "error": False,
                "requires_confirmation": True,
                "preview": {
                    "output_project_id": output_project_id,
                    "project_name": output_project.name,
                    "current_status": current_status,
                    "new_status": new_status,
                    "notes": notes,
                    "instruction": (
                        "Call mark_project_initialized again with confirm=True to execute this change"
                    ),
                },
            }

        # Execute mode - apply the change
        output_project.status = OutputProjectStatus.INITIALIZED
        output_project.updated_at = datetime.utcnow()
        await output_project.save()

        # Audit log
        audit_logger.info(
            "mark_project_initialized executed: output_project_id=%s name=%s old_status=%s new_status=%s notes=%s",
            output_project_id,
            output_project.name,
            current_status,
            new_status,
            notes,
        )

        return {
            "error": False,
            "executed": True,
            "data": {
                "output_project_id": output_project_id,
                "project_name": output_project.name,
                "old_status": current_status,
                "new_status": new_status,
                "updated_at": output_project.updated_at.isoformat(),
                "notes": notes,
            },
        }

    except Exception as e:
        audit_logger.error(
            "mark_project_initialized failed: output_project_id=%s error=%s",
            output_project_id,
            str(e),
        )
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }


@mcp.tool
async def create_milestone(
    ctx: Context,
    output_project_id: str,
    element_name: str,
    wxcode_version: str,
    milestone_folder_name: str,
    element_id: str | None = None,
    confirm: bool = False,
) -> dict[str, Any]:
    """
    Create a milestone associated with WXCODE structure.

    Creates a new Milestone record linking an OutputProject to a KB Element,
    with WXCODE version and folder name metadata. Unlike the REST API endpoint,
    this allows multiple milestones for the same element (different versions).

    This is a write operation that requires explicit confirm=True to execute.
    Calling with confirm=False returns a preview of the change.

    Args:
        output_project_id: ID of the OutputProject
        element_name: Name of the element to convert
        wxcode_version: WXCODE milestone version (e.g., v1.0, v1.1)
        milestone_folder_name: Name of the milestone folder in .planning/milestones/
        element_id: Optional element ID (if not provided, searches by name)
        confirm: Set to True to execute the change (default: False for preview)

    Returns:
        Preview dict (confirm=False) or execution result (confirm=True)
    """
    try:
        # Validate OutputProject exists
        output_project = await OutputProject.get(output_project_id)
        if not output_project:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"OutputProject '{output_project_id}' not found",
            }

        # Find element by ID or name
        element = None
        if element_id:
            element = await Element.get(element_id)
            if not element:
                return {
                    "error": True,
                    "code": "NOT_FOUND",
                    "message": f"Element with ID '{element_id}' not found",
                }
        else:
            # Search by name using helper
            element, error = await _find_element(ctx, element_name, project_name=None)
            if error:
                return {
                    "error": True,
                    "code": "NOT_FOUND",
                    "message": error,
                }

        # Preview mode
        if not confirm:
            return {
                "error": False,
                "requires_confirmation": True,
                "preview": {
                    "output_project_id": output_project_id,
                    "output_project_name": output_project.name,
                    "element_id": str(element.id),
                    "element_name": element.source_name,
                    "wxcode_version": wxcode_version,
                    "milestone_folder_name": milestone_folder_name,
                    "status": MilestoneStatus.IN_PROGRESS.value,
                    "instruction": (
                        "Call create_milestone again with confirm=True to execute this change"
                    ),
                },
            }

        # Execute mode - create the milestone
        milestone = Milestone(
            output_project_id=output_project.id,
            element_id=element.id,
            element_name=element.source_name,
            status=MilestoneStatus.IN_PROGRESS,
            wxcode_version=wxcode_version,
            milestone_folder_name=milestone_folder_name,
        )
        await milestone.insert()

        # Audit log
        audit_logger.info(
            "create_milestone executed: output_project_id=%s element=%s version=%s folder=%s milestone_id=%s",
            output_project_id,
            element.source_name,
            wxcode_version,
            milestone_folder_name,
            str(milestone.id),
        )

        return {
            "error": False,
            "milestone_id": str(milestone.id),
            "element_name": element.source_name,
            "wxcode_version": wxcode_version,
            "milestone_folder_name": milestone_folder_name,
            "status": MilestoneStatus.IN_PROGRESS.value,
            "created": True,
        }

    except Exception as e:
        audit_logger.error(
            "create_milestone failed: output_project_id=%s element=%s error=%s",
            output_project_id,
            element_name,
            str(e),
        )
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }


def _generate_connection_string(conn: dict[str, Any]) -> str:
    """
    Generate SQLAlchemy connection string based on database type.

    Args:
        conn: Connection dict with database_type, source, port, database, user

    Returns:
        SQLAlchemy connection string
    """
    db_type = conn.get("database_type", "").lower()
    source = conn.get("source", "")
    port = conn.get("port", "")
    database = conn.get("database", "")
    user = conn.get("user", "")

    # Password placeholder - real password should come from env vars
    password_placeholder = "{password}"

    if db_type == "sqlserver":
        port_str = f":{port}" if port else ":1433"
        return (
            f"mssql+pyodbc://{user}:{password_placeholder}@{source}{port_str}/{database}"
            "?driver=ODBC+Driver+17+for+SQL+Server"
        )
    elif db_type == "mysql":
        port_str = f":{port}" if port else ":3306"
        return f"mysql+pymysql://{user}:{password_placeholder}@{source}{port_str}/{database}"
    elif db_type in ("postgresql", "postgres"):
        port_str = f":{port}" if port else ":5432"
        return f"postgresql+asyncpg://{user}:{password_placeholder}@{source}{port_str}/{database}"
    elif db_type == "sqlite":
        return f"sqlite:///{source}"
    else:
        # Generic fallback
        return f"{db_type}://{user}:{password_placeholder}@{source}:{port}/{database}"


@mcp.tool
async def list_connections_outputproject(
    ctx: Context,
    output_project_id: str,
) -> dict[str, Any]:
    """
    List database connections configured for an OutputProject.

    Returns all connections with their configuration details.
    Use this to see current connections before adding or updating.

    Args:
        output_project_id: ID of the OutputProject

    Returns:
        List of connections with all configuration details
    """
    try:
        # Find OutputProject
        output_project = await OutputProject.get(output_project_id)
        if not output_project:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"OutputProject '{output_project_id}' not found",
            }

        # Build connections list
        connections_data = []
        for conn in output_project.connections or []:
            connections_data.append({
                "name": conn.name,
                "type_code": conn.type_code,
                "database_type": conn.database_type,
                "driver_name": conn.driver_name,
                "source": conn.source,
                "port": conn.port,
                "database": conn.database,
                "user": conn.user,
                "is_editable": conn.is_editable,
                "is_dev_connection": conn.is_dev_connection,
                "connection_string": conn.connection_string,
                "source_connection_name": conn.source_connection_name,
            })

        return {
            "error": False,
            "output_project_id": output_project_id,
            "output_project_name": output_project.name,
            "total_connections": len(connections_data),
            "connections": connections_data,
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }


@mcp.tool
async def add_connection_outputproject(
    ctx: Context,
    output_project_id: str,
    name: str,
    database_type: str,
    source: str,
    database: str,
    port: str | None = None,
    user: str | None = None,
    driver_name: str | None = None,
    is_dev_connection: bool = False,
    source_connection_name: str | None = None,
    confirm: bool = False,
) -> dict[str, Any]:
    """
    Add a database connection to an OutputProject.

    Adds a single connection to the OutputProject's connections list.
    The connection will be editable unless is_dev_connection=True.

    This is a write operation that requires explicit confirm=True to execute.
    Calling with confirm=False returns a preview of the change.

    Args:
        output_project_id: ID of the OutputProject
        name: Connection name (e.g., "main", "dev_sqlite")
        database_type: Type of database (sqlserver, mysql, postgresql, sqlite)
        source: Database server/host or file path for SQLite
        database: Database name
        port: Database port (optional, uses default for type)
        user: Database user (optional)
        driver_name: Driver name (optional)
        is_dev_connection: Mark as dev connection (not editable)
        source_connection_name: Name of KB connection this was copied from
        confirm: Set to True to execute (default: False for preview)

    Returns:
        Preview or execution result with connection details
    """
    try:
        # Find OutputProject
        output_project = await OutputProject.get(output_project_id)
        if not output_project:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"OutputProject '{output_project_id}' not found",
            }

        # Check for duplicate name
        existing_names = [c.name for c in output_project.connections or []]
        if name in existing_names:
            return {
                "error": True,
                "code": "DUPLICATE_NAME",
                "message": f"Connection with name '{name}' already exists",
                "existing_connections": existing_names,
            }

        # Build connection dict for string generation
        conn_dict = {
            "database_type": database_type,
            "source": source,
            "port": port or "",
            "database": database,
            "user": user or "",
        }

        # Create connection object
        new_connection = OutputProjectConnection(
            name=name,
            type_code=0,
            database_type=database_type,
            driver_name=driver_name or database_type.capitalize(),
            source=source,
            port=port or "",
            database=database,
            user=user,
            is_editable=not is_dev_connection,
            is_dev_connection=is_dev_connection,
            connection_string=_generate_connection_string(conn_dict),
            source_connection_name=source_connection_name,
        )

        # Preview mode
        if not confirm:
            return {
                "error": False,
                "requires_confirmation": True,
                "preview": {
                    "output_project_id": output_project_id,
                    "output_project_name": output_project.name,
                    "new_connection": {
                        "name": new_connection.name,
                        "database_type": new_connection.database_type,
                        "source": new_connection.source,
                        "port": new_connection.port,
                        "database": new_connection.database,
                        "user": new_connection.user,
                        "is_editable": new_connection.is_editable,
                        "is_dev_connection": new_connection.is_dev_connection,
                        "connection_string": new_connection.connection_string,
                    },
                    "existing_connections_count": len(existing_names),
                    "instruction": (
                        "Call add_connection_outputproject again with confirm=True to execute"
                    ),
                },
            }

        # Execute mode - add connection
        if output_project.connections is None:
            output_project.connections = []
        output_project.connections.append(new_connection)
        output_project.updated_at = datetime.utcnow()
        await output_project.save()

        # Audit log
        audit_logger.info(
            "add_connection_outputproject executed: output_project_id=%s name=%s connection=%s",
            output_project_id,
            output_project.name,
            name,
        )

        return {
            "error": False,
            "executed": True,
            "data": {
                "output_project_id": output_project_id,
                "output_project_name": output_project.name,
                "connection_added": {
                    "name": new_connection.name,
                    "database_type": new_connection.database_type,
                    "connection_string": new_connection.connection_string,
                },
                "total_connections": len(output_project.connections),
                "updated_at": output_project.updated_at.isoformat(),
            },
        }

    except Exception as e:
        audit_logger.error(
            "add_connection_outputproject failed: output_project_id=%s error=%s",
            output_project_id,
            str(e),
        )
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }


@mcp.tool
async def update_connection_outputproject(
    ctx: Context,
    output_project_id: str,
    connection_name: str,
    source: str | None = None,
    port: str | None = None,
    database: str | None = None,
    user: str | None = None,
    driver_name: str | None = None,
    confirm: bool = False,
) -> dict[str, Any]:
    """
    Update an existing database connection in an OutputProject.

    Only connections with is_editable=True can be updated.
    Pass only the fields you want to change.

    This is a write operation that requires explicit confirm=True to execute.
    Calling with confirm=False returns a preview of the change.

    Args:
        output_project_id: ID of the OutputProject
        connection_name: Name of the connection to update
        source: New database server/host (optional)
        port: New database port (optional)
        database: New database name (optional)
        user: New database user (optional)
        driver_name: New driver name (optional)
        confirm: Set to True to execute (default: False for preview)

    Returns:
        Preview or execution result with updated connection details
    """
    try:
        # Find OutputProject
        output_project = await OutputProject.get(output_project_id)
        if not output_project:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"OutputProject '{output_project_id}' not found",
            }

        # Find connection by name
        connection = None
        connection_index = -1
        for idx, conn in enumerate(output_project.connections or []):
            if conn.name == connection_name:
                connection = conn
                connection_index = idx
                break

        if connection is None:
            existing_names = [c.name for c in output_project.connections or []]
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"Connection '{connection_name}' not found",
                "existing_connections": existing_names,
            }

        # Check if editable
        if not connection.is_editable:
            return {
                "error": True,
                "code": "NOT_EDITABLE",
                "message": f"Connection '{connection_name}' is not editable",
                "is_dev_connection": connection.is_dev_connection,
            }

        # Build changes dict
        changes = {}
        if source is not None:
            changes["source"] = source
        if port is not None:
            changes["port"] = port
        if database is not None:
            changes["database"] = database
        if user is not None:
            changes["user"] = user
        if driver_name is not None:
            changes["driver_name"] = driver_name

        if not changes:
            return {
                "error": True,
                "code": "NO_CHANGES",
                "message": "No fields provided to update",
            }

        # Build preview of new values
        new_values = {
            "source": changes.get("source", connection.source),
            "port": changes.get("port", connection.port),
            "database": changes.get("database", connection.database),
            "user": changes.get("user", connection.user),
            "driver_name": changes.get("driver_name", connection.driver_name),
            "database_type": connection.database_type,
        }

        # Generate new connection string
        new_connection_string = _generate_connection_string(new_values)

        # Preview mode
        if not confirm:
            return {
                "error": False,
                "requires_confirmation": True,
                "preview": {
                    "output_project_id": output_project_id,
                    "output_project_name": output_project.name,
                    "connection_name": connection_name,
                    "changes": changes,
                    "current_values": {
                        "source": connection.source,
                        "port": connection.port,
                        "database": connection.database,
                        "user": connection.user,
                        "driver_name": connection.driver_name,
                        "connection_string": connection.connection_string,
                    },
                    "new_values": {
                        **new_values,
                        "connection_string": new_connection_string,
                    },
                    "instruction": (
                        "Call update_connection_outputproject again with confirm=True to execute"
                    ),
                },
            }

        # Execute mode - apply changes
        if "source" in changes:
            connection.source = changes["source"]
        if "port" in changes:
            connection.port = changes["port"]
        if "database" in changes:
            connection.database = changes["database"]
        if "user" in changes:
            connection.user = changes["user"]
        if "driver_name" in changes:
            connection.driver_name = changes["driver_name"]

        # Update connection string
        connection.connection_string = new_connection_string

        # Update in list
        output_project.connections[connection_index] = connection
        output_project.updated_at = datetime.utcnow()
        await output_project.save()

        # Audit log
        audit_logger.info(
            "update_connection_outputproject executed: output_project_id=%s connection=%s changes=%s",
            output_project_id,
            connection_name,
            list(changes.keys()),
        )

        return {
            "error": False,
            "executed": True,
            "data": {
                "output_project_id": output_project_id,
                "output_project_name": output_project.name,
                "connection_name": connection_name,
                "changes_applied": list(changes.keys()),
                "new_connection_string": new_connection_string,
                "updated_at": output_project.updated_at.isoformat(),
            },
        }

    except Exception as e:
        audit_logger.error(
            "update_connection_outputproject failed: output_project_id=%s connection=%s error=%s",
            output_project_id,
            connection_name,
            str(e),
        )
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }