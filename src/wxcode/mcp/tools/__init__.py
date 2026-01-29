"""MCP Tools for wxcode Knowledge Base.

All tools are registered on import by using the @mcp.tool decorator.
Import this module to register all tools with the MCP server.

Tools available (29 tools):
- elements: get_element, list_elements, search_code
- controls: get_controls, get_data_bindings
- procedures: get_procedures, get_procedure
- schema: get_schema, get_table
- graph: get_dependencies, get_impact, get_path, find_hubs, find_dead_code, find_cycles
- conversion: get_conversion_candidates, get_topological_order, mark_converted, mark_project_initialized, get_conversion_stats
- stack: get_stack_conventions
- planes: get_element_planes
- wlanguage: get_wlanguage_reference, list_wlanguage_functions, get_wlanguage_pattern
- similarity: search_converted_similar
- pdf: get_element_pdf_slice
- system: health_check, list_tools
"""

# Import all tool modules to register them with @mcp.tool
from wxcode.mcp.tools import elements  # noqa: F401
from wxcode.mcp.tools import controls  # noqa: F401
from wxcode.mcp.tools import procedures  # noqa: F401
from wxcode.mcp.tools import schema  # noqa: F401
from wxcode.mcp.tools import graph  # noqa: F401
from wxcode.mcp.tools import conversion  # noqa: F401
from wxcode.mcp.tools import stack  # noqa: F401
from wxcode.mcp.tools import planes  # noqa: F401
from wxcode.mcp.tools import wlanguage  # noqa: F401
from wxcode.mcp.tools import similarity  # noqa: F401
from wxcode.mcp.tools import pdf  # noqa: F401
from wxcode.mcp.tools import system  # noqa: F401

__all__ = [
    "elements",
    "controls",
    "procedures",
    "schema",
    "graph",
    "conversion",
    "stack",
    "planes",
    "wlanguage",
    "similarity",
    "pdf",
    "system",
]
