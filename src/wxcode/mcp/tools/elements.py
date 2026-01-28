"""MCP tools for Element queries.

Provides tools to retrieve, list, and search WinDev elements (pages, procedures,
classes, queries) from the wxcode knowledge base.
"""

import re
from typing import Any

from bson import DBRef
from fastmcp import Context

from wxcode.config import get_settings
from wxcode.mcp.server import mcp
from wxcode.models import Element, Project


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


def _serialize_element(element: Element, include_raw: bool = True) -> dict[str, Any]:
    """
    Serialize Element to JSON-safe dict.

    Handles enums, ObjectIds, and nested Pydantic models.

    Args:
        element: Element document to serialize
        include_raw: Whether to include raw_content field

    Returns:
        JSON-serializable dictionary
    """
    data: dict[str, Any] = {
        "id": str(element.id),
        "name": element.source_name,
        "type": element.source_type.value,
        "file": element.source_file,
        "layer": element.layer.value if element.layer else None,
        "topological_order": element.topological_order,
        "conversion_status": element.conversion.status.value,
    }

    if include_raw and element.raw_content:
        data["raw_content"] = element.raw_content

    if element.ast:
        data["ast"] = element.ast.model_dump(mode="json")

    if element.dependencies:
        data["dependencies"] = element.dependencies.model_dump(mode="json")

    return data


def _extract_match_preview(content: str, pattern: str, context_chars: int = 100) -> str:
    """
    Extract preview around first regex match.

    Args:
        content: Full content to search
        pattern: Regex pattern to match
        context_chars: Number of characters of context before/after match

    Returns:
        Preview string with ellipses for truncation
    """
    try:
        match = re.search(pattern, content, re.IGNORECASE)
        if not match:
            return ""
        start = max(0, match.start() - context_chars)
        end = min(len(content), match.end() + context_chars)
        preview = content[start:end]
        if start > 0:
            preview = "..." + preview
        if end < len(content):
            preview = preview + "..."
        return preview
    except re.error:
        # Invalid regex pattern
        return ""


@mcp.tool
async def get_element(
    ctx: Context,
    element_name: str,
    project_name: str | None = None,
    include_raw_content: bool = True,
) -> dict[str, Any]:
    """
    Get complete definition of a WinDev element.

    Returns source code, AST, dependencies, and conversion status.
    Use this to understand what a page, procedure group, class, or query does.

    Args:
        element_name: Name of the element (e.g., PAGE_Login, ServerProcedures)
        project_name: Optional project name to scope the search
        include_raw_content: Whether to include the full source code (default: True)

    Returns:
        Complete element definition including AST and dependencies
    """
    try:
        element, error = await _find_element(ctx, element_name, project_name)

        if error:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": error,
                "suggestion": "Use list_elements to see available elements",
            }

        return {
            "error": False,
            "data": _serialize_element(element, include_raw=include_raw_content),
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }


@mcp.tool
async def list_elements(
    ctx: Context,
    project_name: str | None = None,
    element_type: str | None = None,
    layer: str | None = None,
    conversion_status: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """
    List elements with optional filters.

    Use this to discover what elements exist in a project or find elements
    that need conversion.

    Args:
        project_name: Filter by project name
        element_type: Filter by type (page, procedure_group, class, query, report)
        layer: Filter by layer (schema, domain, business, api, ui)
        conversion_status: Filter by status (pending, in_progress, converted, validated)
        limit: Maximum number of results (default: 100)

    Returns:
        List of elements matching filters with summary info (no raw_content)
    """
    try:
        query: dict[str, Any] = {}

        if project_name:
            project = await Project.find_one(Project.name == project_name)
            if not project:
                return {
                    "error": True,
                    "code": "NOT_FOUND",
                    "message": f"Project '{project_name}' not found",
                }
            # Use raw query for DBRef comparison
            query["project_id.$id"] = project.id

        if element_type:
            query["source_type"] = element_type

        if layer:
            query["layer"] = layer

        if conversion_status:
            query["conversion.status"] = conversion_status

        # Count total before limit
        total = await Element.find(query).count()

        # Get limited results
        elements = await Element.find(query).limit(limit).to_list()

        return {
            "error": False,
            "total": total,
            "returned": len(elements),
            "elements": [
                {
                    "name": e.source_name,
                    "type": e.source_type.value,
                    "file": e.source_file,
                    "layer": e.layer.value if e.layer else None,
                    "conversion_status": e.conversion.status.value,
                }
                for e in elements
            ],
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }


@mcp.tool
async def search_code(
    ctx: Context,
    pattern: str,
    project_name: str | None = None,
    element_types: list[str] | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """
    Search code patterns across elements using regex.

    Use this to find elements containing specific code patterns like function calls,
    variable usage, or SQL statements.

    Args:
        pattern: Regex pattern to search for in element source code
        project_name: Optional project name to scope the search
        element_types: Optional list of element types to search (page, procedure_group, etc.)
        limit: Maximum number of results (default: 50)

    Returns:
        Matching elements with preview showing context around the match
    """
    try:
        query: dict[str, Any] = {}

        if project_name:
            project = await Project.find_one(Project.name == project_name)
            if not project:
                return {
                    "error": True,
                    "code": "NOT_FOUND",
                    "message": f"Project '{project_name}' not found",
                }
            query["project_id.$id"] = project.id

        if element_types:
            query["source_type"] = {"$in": element_types}

        # Regex search in raw_content - case-insensitive
        query["raw_content"] = {"$regex": pattern, "$options": "i"}

        # Execute with limit
        elements = await Element.find(query).limit(limit).to_list()

        return {
            "error": False,
            "pattern": pattern,
            "matches": len(elements),
            "results": [
                {
                    "name": e.source_name,
                    "type": e.source_type.value,
                    "file": e.source_file,
                    "preview": _extract_match_preview(e.raw_content or "", pattern),
                }
                for e in elements
            ],
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }
