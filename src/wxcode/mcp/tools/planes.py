"""MCP tools for Plane detection in WinDev pages.

Provides tools to detect and analyze planes (tabs, wizard views, conditional
visibility layers) in WinDev/WebDev page elements. Essential for understanding
complex UI navigation patterns during conversion.
"""

import re
from collections import defaultdict
from typing import Any

from bson import DBRef
from fastmcp import Context

from wxcode.config import get_settings
from wxcode.mcp.server import mcp
from wxcode.models.control import Control
from wxcode.models.element import Element
from wxcode.models.project import Project


async def _find_element(
    ctx: Context, element_name: str, project_name: str | None
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

        settings = get_settings()
        mongo_client = ctx.request_context.lifespan_context["mongo_client"]
        db = mongo_client[settings.mongodb_database]
        collection = db["elements"]

        project_dbref = DBRef("projects", project.id)
        elem_dict = await collection.find_one(
            {"source_name": element_name, "project_id": project_dbref}
        )

        if not elem_dict:
            return None, f"Element '{element_name}' not found in project '{project_name}'"

        element = await Element.get(elem_dict["_id"])
        return element, None
    else:
        elements = await Element.find(Element.source_name == element_name).to_list()

        if not elements:
            return None, f"Element '{element_name}' not found"

        if len(elements) > 1:
            return (
                None,
                f"Element '{element_name}' found in multiple projects. Use project_name to specify.",
            )

        return elements[0], None


def _parse_plane_value(plane_str: str | None) -> list[int]:
    """
    Parse plane property value into list of plane numbers.

    WinDev planes can be:
    - Single: "1"
    - Multiple: "1,2,3"
    - Range-like: "1-3" (rare)

    Returns:
        List of plane numbers (0 means "all planes" / base layer)
    """
    if not plane_str:
        return [0]  # No plane = base layer

    planes = []
    plane_str = str(plane_str).strip()

    # Handle comma-separated
    for part in plane_str.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            planes.append(int(part))
        except ValueError:
            # Try range format "1-3"
            if "-" in part:
                try:
                    start, end = part.split("-")
                    planes.extend(range(int(start.strip()), int(end.strip()) + 1))
                except (ValueError, IndexError):
                    pass

    return planes if planes else [0]


def _extract_plane_operations(raw_content: str) -> list[dict[str, Any]]:
    """
    Extract plane-related WLanguage operations from raw content.

    Looks for:
    - Plane(N) or Plane(N, control) - switch to plane
    - PlaneEnable(N, True/False) - enable/disable plane
    - PlaneVisible(N) - check visibility
    - CurrentPlane - get current plane
    - CONTROL..Plane - property access

    Returns:
        List of operations with type, plane number, context
    """
    operations = []

    # Patterns for plane operations
    patterns = [
        # Plane(N) or Plane(N, control)
        (r"Plane\s*\(\s*(\d+)(?:\s*,\s*([^)]+))?\)", "plane_switch"),
        # PlaneEnable(N, bool)
        (r"PlaneEnable\s*\(\s*(\d+)\s*,\s*(True|False|true|false)", "plane_enable"),
        # PlaneVisible(N)
        (r"PlaneVisible\s*\(\s*(\d+)\s*\)", "plane_visible_check"),
        # ..Plane = N (property assignment)
        (r"\.\.Plane\s*=\s*(\d+)", "plane_assign"),
        # ..Plane (property read, capture context)
        (r"(\w+)\.\.Plane(?!\s*=)", "plane_read"),
    ]

    for pattern, op_type in patterns:
        for match in re.finditer(pattern, raw_content, re.IGNORECASE):
            operation = {
                "type": op_type,
                "line_position": match.start(),
            }

            if op_type == "plane_switch":
                operation["plane_number"] = int(match.group(1))
                if match.group(2):
                    operation["target_control"] = match.group(2).strip()
            elif op_type == "plane_enable":
                operation["plane_number"] = int(match.group(1))
                operation["enabled"] = match.group(2).lower() == "true"
            elif op_type == "plane_visible_check":
                operation["plane_number"] = int(match.group(1))
            elif op_type == "plane_assign":
                operation["plane_number"] = int(match.group(1))
            elif op_type == "plane_read":
                operation["control_name"] = match.group(1)

            operations.append(operation)

    return operations


def _infer_navigation_pattern(
    planes: dict[int, list[str]], operations: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Infer navigation pattern from planes and operations.

    Patterns:
    - wizard: Sequential plane switches (1->2->3), typically with Next/Previous buttons
    - tabs: Non-sequential access to any plane, tab-like controls
    - conditional: Planes shown/hidden based on logic, no clear navigation
    - simple: 2 planes or less, likely show/hide pattern
    """
    num_planes = len(planes)

    if num_planes <= 1:
        return {
            "pattern": "none",
            "description": "No planes detected - single view",
            "confidence": "high",
        }

    if num_planes == 2:
        return {
            "pattern": "simple",
            "description": "Two planes - likely show/hide or toggle pattern",
            "confidence": "medium",
        }

    # Check for sequential switch patterns (wizard)
    switch_ops = [op for op in operations if op["type"] == "plane_switch"]
    if switch_ops:
        plane_numbers = [op["plane_number"] for op in switch_ops]
        # Check if switches are sequential
        is_sequential = (
            all(
                plane_numbers[i] + 1 == plane_numbers[i + 1]
                or plane_numbers[i] - 1 == plane_numbers[i + 1]
                for i in range(len(plane_numbers) - 1)
            )
            if len(plane_numbers) > 1
            else False
        )

        if is_sequential:
            return {
                "pattern": "wizard",
                "description": f"Sequential navigation through {num_planes} steps",
                "confidence": "high",
                "step_count": num_planes,
            }

    # Check for tab-like patterns (multiple direct accesses)
    direct_switches = len([op for op in operations if op["type"] == "plane_switch"])
    if direct_switches >= num_planes:
        return {
            "pattern": "tabs",
            "description": f"Tab-like navigation with {num_planes} views",
            "confidence": "medium",
            "tab_count": num_planes,
        }

    # Default to conditional
    return {
        "pattern": "conditional",
        "description": f"Conditional visibility with {num_planes} planes",
        "confidence": "low",
    }


def _suggest_modern_implementation(
    pattern: dict[str, Any], planes: dict[int, list[str]]
) -> dict[str, Any]:
    """
    Suggest modern stack implementation for the detected pattern.
    """
    pattern_type = pattern["pattern"]

    suggestions = {
        "none": {
            "component": "single view",
            "approach": "Direct component rendering",
            "state_needed": False,
        },
        "simple": {
            "component": "conditional render or toggle",
            "approach": "Use boolean state for visibility",
            "state_needed": True,
            "example_state": "const [isExpanded, setIsExpanded] = useState(false)",
            "example_render": "{isExpanded && <ExpandedContent />}",
        },
        "wizard": {
            "component": "stepper or multi-step form",
            "approach": "Use step state with next/previous handlers",
            "state_needed": True,
            "example_state": "const [currentStep, setCurrentStep] = useState(1)",
            "example_render": "{currentStep === 1 && <Step1 />}",
            "libraries": ["react-hook-form (multi-step)", "formik wizard", "shadcn stepper"],
        },
        "tabs": {
            "component": "tabs component",
            "approach": "Use tab state or native tabs component",
            "state_needed": True,
            "example_state": "const [activeTab, setActiveTab] = useState('tab1')",
            "libraries": ["shadcn/ui Tabs", "radix-ui Tabs", "headlessui Tab"],
        },
        "conditional": {
            "component": "conditional rendering",
            "approach": "Use multiple boolean states or computed visibility",
            "state_needed": True,
            "example_state": "Multiple visibility flags based on business logic",
        },
    }

    return suggestions.get(pattern_type, suggestions["conditional"])


@mcp.tool
async def get_element_planes(
    ctx: Context,
    element_name: str,
    project_name: str | None = None,
    include_controls: bool = True,
    include_code_analysis: bool = True,
) -> dict[str, Any]:
    """
    Detect and analyze planes (tabs/wizard views) in a WinDev page element.

    In WinDev/WebDev, planes are layers of controls that can be shown/hidden
    to create tabbed interfaces, wizards, or conditional views. This tool
    analyzes both control plane properties and code patterns to understand
    the navigation structure.

    Use this during conversion planning to determine the appropriate modern
    component (tabs, stepper, conditional render, etc.).

    Args:
        element_name: Name of the page element (e.g., PAGE_Cadastro)
        project_name: Optional project name to scope the search
        include_controls: Include control details per plane (default True)
        include_code_analysis: Analyze raw_content for plane operations (default True)

    Returns:
        Plane analysis with:
        - planes: Dict mapping plane number to control names
        - navigation_pattern: Detected pattern (wizard, tabs, conditional, simple, none)
        - operations: Plane-related code operations found
        - modern_suggestion: Suggested modern implementation approach
    """
    try:
        # Find the element
        element, error = await _find_element(ctx, element_name, project_name)

        if error:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": error,
                "suggestion": "Use list_elements to see available elements",
            }

        # Get all controls for this element
        controls = await Control.find({"element_id": element.id}).to_list()

        # Group controls by plane
        planes: dict[int, list[dict[str, Any]]] = defaultdict(list)
        plane_names: dict[int, list[str]] = defaultdict(list)  # Just names for pattern detection

        for ctrl in controls:
            plane_value = None
            if ctrl.properties and ctrl.properties.plane:
                plane_value = ctrl.properties.plane

            plane_numbers = _parse_plane_value(plane_value)

            for plane_num in plane_numbers:
                control_info = {"name": ctrl.name, "type_code": ctrl.type_code}
                if include_controls:
                    control_info["full_path"] = ctrl.full_path
                    control_info["depth"] = ctrl.depth
                    control_info["has_code"] = ctrl.has_code
                planes[plane_num].append(control_info)
                plane_names[plane_num].append(ctrl.name)

        # Analyze code for plane operations
        operations = []
        if include_code_analysis and element.raw_content:
            operations = _extract_plane_operations(element.raw_content)

        # Infer navigation pattern
        navigation_pattern = _infer_navigation_pattern(plane_names, operations)

        # Get modern implementation suggestion
        modern_suggestion = _suggest_modern_implementation(navigation_pattern, plane_names)

        # Build response
        response: dict[str, Any] = {
            "error": False,
            "element": element_name,
            "total_planes": len(planes),
            "total_controls": len(controls),
        }

        # Format planes output
        planes_output = {}
        for plane_num in sorted(planes.keys()):
            plane_key = f"plane_{plane_num}" if plane_num > 0 else "base_layer"
            planes_output[plane_key] = {
                "plane_number": plane_num,
                "control_count": len(planes[plane_num]),
            }
            if include_controls:
                planes_output[plane_key]["controls"] = planes[plane_num]

        response["planes"] = planes_output
        response["navigation_pattern"] = navigation_pattern

        if include_code_analysis:
            response["plane_operations"] = operations
            response["operation_count"] = len(operations)

        response["modern_suggestion"] = modern_suggestion

        # Add helpful summary
        if navigation_pattern["pattern"] != "none":
            response["summary"] = (
                f"Page uses {navigation_pattern['pattern']} pattern with "
                f"{len(planes)} planes. "
                f"Suggested modern approach: {modern_suggestion['component']}"
            )
        else:
            response["summary"] = "Page uses single view, no plane-based navigation detected"

        return response

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }
