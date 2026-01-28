"""MCP tools for conversion workflow tracking.

Provides tools to track conversion progress, determine optimal conversion order,
identify elements ready for conversion, and mark elements/projects as converted.

Write operations:
- mark_converted: Mark an element as converted
- mark_project_initialized: Mark an OutputProject as initialized
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
from wxcode.mcp.server import mcp
from wxcode.models import Element, Project
from wxcode.models.element import ConversionStatus
from wxcode.models.output_project import OutputProject, OutputProjectStatus


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