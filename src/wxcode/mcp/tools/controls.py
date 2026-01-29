"""MCP tools for Control queries.

Provides tools to query UI control hierarchies and data bindings for
WinDev pages. Essential for understanding page structure during conversion.
"""

from bson import DBRef
from fastmcp import Context

from wxcode.config import get_settings
from wxcode.mcp.instance import mcp
from wxcode.models.control import Control
from wxcode.models.control_type import ControlTypeDefinition
from wxcode.models.element import Element
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
async def get_controls(
    ctx: Context,
    element_name: str,
    project_name: str | None = None,
    include_events: bool = True,
    include_properties: bool = True
) -> dict:
    """
    Get control hierarchy for a WinDev page element.

    Returns all controls (buttons, inputs, cells, etc.) with their
    properties, events, and parent-child relationships. The hierarchy
    is sorted by full_path which encodes depth-first tree order.

    Use this to understand the UI structure of a page before conversion.

    Args:
        element_name: Name of the page element (e.g., PAGE_Login)
        project_name: Optional project name to scope the search
        include_events: Include event handlers (OnClick, etc.) - default True
        include_properties: Include control properties (width, height, etc.) - default True

    Returns:
        Control hierarchy with type names, depth, events, and properties
    """
    try:
        # Find the element first
        element, error = await _find_element(ctx, element_name, project_name)

        if error:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": error,
                "suggestion": "Use list_elements to see available elements"
            }

        # Query controls sorted by full_path (encodes hierarchy)
        controls = await Control.find({"element_id": element.id}).sort("+full_path").to_list()

        if not controls:
            return {
                "error": False,
                "element": element_name,
                "total_controls": 0,
                "controls": [],
                "message": "No controls found for this element"
            }

        # Get type definitions for readable type names
        type_codes = list(set(c.type_code for c in controls if c.type_code))
        if type_codes:
            type_defs = await ControlTypeDefinition.find(
                {"type_code": {"$in": type_codes}}
            ).to_list()
            type_map = {
                td.type_code: td.type_name or td.inferred_name or f"type_{td.type_code}"
                for td in type_defs
            }
        else:
            type_map = {}

        # Build response
        controls_data = []
        for ctrl in controls:
            control_info = {
                "name": ctrl.name,
                "type_code": ctrl.type_code,
                "type_name": type_map.get(ctrl.type_code, f"type_{ctrl.type_code}"),
                "full_path": ctrl.full_path,
                "depth": ctrl.depth,
                "has_code": ctrl.has_code,
                "is_container": ctrl.is_container,
                "is_bound": bool(ctrl.data_binding),
            }

            # Include properties if requested
            if include_properties and ctrl.properties:
                control_info["properties"] = ctrl.properties.model_dump(mode="json")
            elif include_properties:
                control_info["properties"] = None

            # Include events if requested
            if include_events and ctrl.events:
                control_info["events"] = [
                    {
                        "event_name": e.event_name,
                        "type_code": e.type_code,
                        "has_code": bool(e.code),
                        "role": e.role
                    }
                    for e in ctrl.events
                ]
            elif include_events:
                control_info["events"] = []

            controls_data.append(control_info)

        return {
            "error": False,
            "element": element_name,
            "total_controls": len(controls),
            "controls": controls_data
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__
        }


@mcp.tool
async def get_data_bindings(
    ctx: Context,
    element_name: str,
    project_name: str | None = None
) -> dict:
    """
    Get data bindings for a WinDev page element.

    Returns the mapping between UI controls and database table fields.
    Essential for understanding how the page reads/writes data and for
    generating correct form handling code during conversion.

    In WinDev, controls can be bound to database fields via FileToScreen()
    and ScreenToFile() for automatic data synchronization.

    Args:
        element_name: Name of the page element (e.g., PAGE_Login)
        project_name: Optional project name to scope the search

    Returns:
        List of bindings showing control -> table.field mappings
    """
    try:
        # Find the element first
        element, error = await _find_element(ctx, element_name, project_name)

        if error:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": error,
                "suggestion": "Use list_elements to see available elements"
            }

        # Find controls with data bindings
        # Query both by data_binding existence and is_bound flag
        controls = await Control.find({
            "element_id": element.id,
            "$or": [
                {"data_binding": {"$ne": None}},
                {"is_bound": True}
            ]
        }).to_list()

        # Extract bindings and collect referenced tables
        bindings = []
        tables: set[str] = set()

        for ctrl in controls:
            if ctrl.data_binding:
                # Get binding type as string value
                binding_type = "simple"
                if hasattr(ctrl.data_binding, 'binding_type') and ctrl.data_binding.binding_type:
                    binding_type = ctrl.data_binding.binding_type.value

                binding = {
                    "control_name": ctrl.name,
                    "control_path": ctrl.full_path,
                    "binding_type": binding_type,
                    "table_name": ctrl.data_binding.table_name,
                    "field_name": ctrl.data_binding.field_name,
                }

                # Add variable binding if present
                if ctrl.data_binding.variable_name:
                    binding["variable_name"] = ctrl.data_binding.variable_name

                # Add complex binding path if present
                if ctrl.data_binding.binding_path:
                    binding["binding_path"] = ctrl.data_binding.binding_path

                bindings.append(binding)

                # Track referenced tables
                if ctrl.data_binding.table_name:
                    tables.add(ctrl.data_binding.table_name)

        return {
            "error": False,
            "element": element_name,
            "total_bindings": len(bindings),
            "bindings": bindings,
            "tables_referenced": sorted(list(tables))
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__
        }
