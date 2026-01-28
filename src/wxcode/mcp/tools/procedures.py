"""MCP tools for Procedure queries.

Provides tools to query WinDev procedures - both global procedures from .wdg
files and local procedures from pages/windows. Essential for understanding
business logic during conversion.
"""

from bson import DBRef
from fastmcp import Context

from wxcode.config import get_settings
from wxcode.mcp.server import mcp
from wxcode.models.element import Element
from wxcode.models.procedure import Procedure
from wxcode.models.project import Project


async def _find_element(
    ctx: Context,
    element_name: str,
    project_name: str | None
) -> tuple[Element | None, str | None]:
    """
    Find element by name, optionally scoped to project.

    Returns:
        (element, error_message) - element is None if not found
    """
    if project_name:
        project = await Project.find_one(Project.name == project_name)
        if not project:
            return None, f"Project '{project_name}' not found"

        # DBRef query via raw Motor
        settings = get_settings()
        mongo_client = ctx.request_context.lifespan_context["mongo_client"]
        db = mongo_client[settings.mongodb_database]
        collection = db["elements"]

        project_dbref = DBRef("projects", project.id)
        elem_dict = await collection.find_one({
            "source_name": element_name,
            "project_id": project_dbref
        })

        if not elem_dict:
            return None, f"Element '{element_name}' not found in project '{project_name}'"

        element = await Element.get(elem_dict["_id"])
        return element, None
    else:
        elements = await Element.find(Element.source_name == element_name).to_list()

        if not elements:
            return None, f"Element '{element_name}' not found"

        if len(elements) > 1:
            return None, f"Element '{element_name}' found in multiple projects. Use project_name to specify."

        return elements[0], None


@mcp.tool
async def get_procedures(
    ctx: Context,
    element_name: str,
    project_name: str | None = None,
    include_code: bool = False
) -> dict:
    """
    List all procedures defined in a WinDev element.

    Returns procedure names, signatures, and optionally full code.
    Use this to understand what functions/methods an element provides.

    Args:
        element_name: Name of the element (e.g., ServerProcedures, PAGE_Login)
        project_name: Optional project name to scope the search
        include_code: Include full procedure code (default: False for performance)

    Returns:
        List of procedures with signatures and metadata
    """
    try:
        # Find element first
        element, error = await _find_element(ctx, element_name, project_name)

        if error:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": error,
                "suggestion": "Use list_elements to see available elements"
            }

        # Query procedures for this element
        procedures = await Procedure.find({"element_id": element.id}).sort("+name").to_list()

        if not procedures:
            return {
                "error": False,
                "element": element_name,
                "total_procedures": 0,
                "procedures": [],
                "message": "No procedures found for this element"
            }

        # Build response
        procedures_data = []
        for proc in procedures:
            proc_info = {
                "name": proc.name,
                "signature": proc.signature,
                "is_public": proc.is_public,
                "is_local": proc.is_local,
                "is_internal": proc.is_internal,
                "code_lines": proc.code_lines or (len(proc.code.split('\n')) if proc.code else 0),
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type,
                        "is_local": p.is_local,
                        "default_value": p.default_value
                    }
                    for p in (proc.parameters or [])
                ],
                "return_type": proc.return_type
            }

            # Include code if requested
            if include_code:
                proc_info["code"] = proc.code

            procedures_data.append(proc_info)

        return {
            "error": False,
            "element": element_name,
            "total_procedures": len(procedures),
            "procedures": procedures_data
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__
        }


@mcp.tool
async def get_procedure(
    ctx: Context,
    procedure_name: str,
    element_name: str | None = None,
    project_name: str | None = None
) -> dict:
    """
    Get a specific procedure by name with full details.

    Returns the complete procedure definition including code and dependencies.
    If procedure exists in multiple elements, use element_name to specify.

    Args:
        procedure_name: Name of the procedure (e.g., ValidaCPF)
        element_name: Optional element to scope the search
        project_name: Optional project name

    Returns:
        Complete procedure definition with code and dependencies
    """
    try:
        query: dict = {"name": procedure_name}
        resolved_element_name = element_name

        # If element_name provided, scope to that element
        if element_name:
            element, error = await _find_element(ctx, element_name, project_name)
            if error:
                return {
                    "error": True,
                    "code": "NOT_FOUND",
                    "message": error,
                    "suggestion": "Use list_elements to see available elements"
                }
            query["element_id"] = element.id
        elif project_name:
            # Project scope without element - need to add project constraint
            project = await Project.find_one(Project.name == project_name)
            if not project:
                return {
                    "error": True,
                    "code": "NOT_FOUND",
                    "message": f"Project '{project_name}' not found"
                }
            query["project_id"] = project.id

        procedures = await Procedure.find(query).to_list()

        if not procedures:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"Procedure '{procedure_name}' not found"
            }

        if len(procedures) > 1 and not element_name:
            # Found in multiple elements - need to fetch element names
            settings = get_settings()
            mongo_client = ctx.request_context.lifespan_context["mongo_client"]
            db = mongo_client[settings.mongodb_database]
            elements_coll = db["elements"]

            element_names = []
            for proc in procedures:
                elem_dict = await elements_coll.find_one({"_id": proc.element_id})
                if elem_dict:
                    element_names.append(elem_dict.get("source_name", "unknown"))

            return {
                "error": True,
                "code": "AMBIGUOUS",
                "message": f"Procedure '{procedure_name}' found in multiple elements",
                "suggestion": f"Use element_name to specify. Found in: {', '.join(element_names)}"
            }

        proc = procedures[0]

        # Fetch element name if not provided
        if not resolved_element_name:
            settings = get_settings()
            mongo_client = ctx.request_context.lifespan_context["mongo_client"]
            db = mongo_client[settings.mongodb_database]
            elements_coll = db["elements"]
            elem_dict = await elements_coll.find_one({"_id": proc.element_id})
            resolved_element_name = elem_dict.get("source_name", "unknown") if elem_dict else "unknown"

        # Build dependencies dict
        deps = None
        if proc.dependencies:
            deps = {
                "calls_procedures": proc.dependencies.calls_procedures or [],
                "uses_files": proc.dependencies.uses_files or [],
                "uses_apis": proc.dependencies.uses_apis or [],
                "uses_queries": proc.dependencies.uses_queries or []
            }

        return {
            "error": False,
            "data": {
                "name": proc.name,
                "element": resolved_element_name,
                "signature": proc.signature,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type,
                        "is_local": p.is_local,
                        "default_value": p.default_value
                    }
                    for p in (proc.parameters or [])
                ],
                "return_type": proc.return_type,
                "code": proc.code,
                "code_lines": proc.code_lines or (len(proc.code.split('\n')) if proc.code else 0),
                "is_public": proc.is_public,
                "is_local": proc.is_local,
                "is_internal": proc.is_internal,
                "scope": proc.scope,
                "has_error_handling": proc.has_error_handling,
                "has_documentation": proc.has_documentation,
                "dependencies": deps
            }
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__
        }
