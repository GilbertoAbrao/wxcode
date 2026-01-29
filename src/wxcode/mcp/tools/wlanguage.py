"""MCP tools for WLanguage function reference.

Provides tools to query WLanguage H* function documentation and get
modern stack equivalents during code conversion.
"""

from pathlib import Path
from typing import Any

import yaml
from fastmcp import Context

from wxcode.mcp.instance import mcp
from wxcode.models.output_project import OutputProject
from wxcode.models.stack import Stack

# Cache for loaded reference data
_reference_cache: dict[str, Any] | None = None


def _load_reference() -> dict[str, Any]:
    """Load WLanguage reference YAML file (cached)."""
    global _reference_cache

    if _reference_cache is not None:
        return _reference_cache

    # Find the reference file
    reference_path = Path(__file__).parent.parent.parent / "data" / "wlanguage_reference.yaml"

    if not reference_path.exists():
        return {"functions": {}, "patterns": {}}

    with open(reference_path, "r", encoding="utf-8") as f:
        _reference_cache = yaml.safe_load(f)

    return _reference_cache or {"functions": {}, "patterns": {}}


def _get_stack_key(stack: Stack) -> str:
    """
    Get the key to use for stack-specific equivalents.

    Maps stack configuration to reference file keys.
    """
    # Direct framework matches
    if stack.framework in ("fastapi",) and stack.orm == "sqlalchemy":
        return "fastapi-sqlalchemy"
    if stack.framework == "django":
        return "django"

    # ORM-based matches for TypeScript stacks
    if stack.orm == "prisma":
        return "prisma"
    if stack.orm == "drizzle":
        return "drizzle"

    # Fallback based on language
    if stack.language == "python":
        return "fastapi-sqlalchemy"
    if stack.language == "typescript":
        return "prisma"

    return "fastapi-sqlalchemy"


def _format_function_info(
    func_name: str, func_data: dict[str, Any], stack_key: str | None = None
) -> dict[str, Any]:
    """Format function information for response."""
    info = {
        "function": func_name,
        "category": func_data.get("category", "unknown"),
        "description": func_data.get("description", ""),
        "parameters": func_data.get("parameters", []),
        "returns": func_data.get("returns"),
        "returns_description": func_data.get("returns_description"),
        "related": func_data.get("related", []),
    }

    if func_data.get("notes"):
        info["notes"] = func_data["notes"]

    # Add equivalents
    equivalents = func_data.get("equivalents", {})
    if stack_key and stack_key in equivalents:
        info["equivalent"] = equivalents[stack_key].strip()
        info["stack_used"] = stack_key
    else:
        # Include all equivalents if no specific stack
        info["equivalents"] = {k: v.strip() for k, v in equivalents.items()}

    return info


@mcp.tool
async def get_wlanguage_reference(
    ctx: Context,
    function_name: str,
    output_project_id: str | None = None,
    stack_id: str | None = None,
    include_related: bool = True,
) -> dict[str, Any]:
    """
    Get WLanguage H* function documentation with modern stack equivalents.

    Returns documentation for WLanguage data access functions (HReadSeek,
    HAdd, HModify, etc.) along with equivalent code for the target stack.

    Use this during conversion to understand WLanguage patterns and generate
    appropriate modern code.

    Args:
        function_name: Name of the WLanguage function (e.g., "HReadSeek", "HAdd")
        output_project_id: Optional Output Project ID to determine target stack
        stack_id: Optional stack ID (alternative to output_project_id)
        include_related: Include documentation for related functions (default True)

    Returns:
        Function documentation with parameters, returns, notes, and stack-specific
        equivalent code
    """
    try:
        # Load reference data
        reference = _load_reference()
        functions = reference.get("functions", {})

        if not functions:
            return {
                "error": True,
                "code": "NO_REFERENCE",
                "message": "WLanguage reference data not found",
                "suggestion": "Ensure wlanguage_reference.yaml exists in data directory",
            }

        # Normalize function name (remove leading H if present for search)
        search_name = function_name.strip()
        if (
            not search_name.startswith("H")
            and not search_name.startswith("File")
            and not search_name.startswith("Screen")
        ):
            search_name = "H" + search_name

        # Try exact match first
        func_data = functions.get(search_name)

        # Try case-insensitive match
        if not func_data:
            for name, data in functions.items():
                if name.lower() == search_name.lower():
                    func_data = data
                    search_name = name
                    break

        if not func_data:
            # Suggest similar functions
            similar = [
                name
                for name in functions.keys()
                if search_name.lower() in name.lower() or name.lower() in search_name.lower()
            ]
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"Function '{function_name}' not found in reference",
                "similar_functions": similar[:5] if similar else None,
                "available_categories": list(
                    set(f.get("category", "unknown") for f in functions.values())
                ),
            }

        # Determine target stack
        stack_key = None
        stack_name = None

        if output_project_id:
            output_project = await OutputProject.get(output_project_id)
            if output_project:
                stack = await Stack.find_one(Stack.stack_id == output_project.stack_id)
                if stack:
                    stack_key = _get_stack_key(stack)
                    stack_name = stack.name
        elif stack_id:
            stack = await Stack.find_one(Stack.stack_id == stack_id)
            if stack:
                stack_key = _get_stack_key(stack)
                stack_name = stack.name

        # Build response
        response: dict[str, Any] = {
            "error": False,
        }

        if stack_name:
            response["target_stack"] = stack_name

        # Main function info
        response["function"] = _format_function_info(search_name, func_data, stack_key)

        # Include related functions if requested
        if include_related and func_data.get("related"):
            related_docs = []
            for related_name in func_data["related"]:
                related_data = functions.get(related_name)
                if related_data:
                    related_docs.append(
                        _format_function_info(related_name, related_data, stack_key)
                    )
            if related_docs:
                response["related_functions"] = related_docs

        return response

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }


@mcp.tool
async def list_wlanguage_functions(ctx: Context, category: str | None = None) -> dict[str, Any]:
    """
    List available WLanguage functions in the reference.

    Returns functions grouped by category (navigation, crud, search, etc.).

    Args:
        category: Optional filter by category (navigation, crud, search,
                  transaction, status, locking, aggregate, utility)

    Returns:
        List of functions grouped by category with brief descriptions
    """
    try:
        reference = _load_reference()
        functions = reference.get("functions", {})

        if not functions:
            return {
                "error": True,
                "code": "NO_REFERENCE",
                "message": "WLanguage reference data not found",
            }

        # Group by category
        by_category: dict[str, list[dict[str, str]]] = {}

        for func_name, func_data in functions.items():
            func_category = func_data.get("category", "unknown")

            # Apply filter if specified
            if category and func_category.lower() != category.lower():
                continue

            if func_category not in by_category:
                by_category[func_category] = []

            by_category[func_category].append(
                {"name": func_name, "description": func_data.get("description", "")[:100]}
            )

        if category and not by_category:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"No functions found in category '{category}'",
                "available_categories": list(
                    set(f.get("category", "unknown") for f in functions.values())
                ),
            }

        return {
            "error": False,
            "total_functions": sum(len(funcs) for funcs in by_category.values()),
            "categories": by_category,
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }


@mcp.tool
async def get_wlanguage_pattern(ctx: Context, pattern_name: str) -> dict[str, Any]:
    """
    Get a common WLanguage code pattern with modern equivalent.

    Returns documented WLanguage patterns (cursor iteration, search and modify,
    transaction block) with both WLanguage code and modern equivalents.

    Args:
        pattern_name: Name of the pattern (cursor_iteration, search_and_modify,
                      transaction_block)

    Returns:
        Pattern documentation with WLanguage code and modern equivalents
    """
    try:
        reference = _load_reference()
        patterns = reference.get("patterns", {})

        if not patterns:
            return {
                "error": True,
                "code": "NO_PATTERNS",
                "message": "No patterns found in reference",
            }

        # Try exact match
        pattern_data = patterns.get(pattern_name)

        # Try with underscores/dashes
        if not pattern_data:
            normalized = pattern_name.lower().replace("-", "_").replace(" ", "_")
            pattern_data = patterns.get(normalized)

        if not pattern_data:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"Pattern '{pattern_name}' not found",
                "available_patterns": list(patterns.keys()),
            }

        return {
            "error": False,
            "pattern": pattern_name,
            "description": pattern_data.get("description", ""),
            "windev_code": pattern_data.get("windev", "").strip(),
            "modern_code": pattern_data.get("modern", "").strip(),
        }

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }
