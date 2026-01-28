"""MCP tools for Stack conventions and configuration.

Provides tools to query stack conventions for consistent code generation
during WinDev to modern stack conversion.
"""

from typing import Any

from fastmcp import Context

from wxcode.mcp.server import mcp
from wxcode.models.output_project import OutputProject
from wxcode.models.stack import Stack


def _format_naming_conventions(stack: Stack) -> dict[str, Any]:
    """Format naming conventions with examples."""
    conventions = {}

    examples = {
        "class": ["UserService", "ClienteModel"],
        "file": ["user_service.py", "auth_routes.py"],
        "variable": ["user_id", "cliente_nome"],
        "constant": ["MAX_LOGIN_ATTEMPTS", "DEFAULT_PAGE_SIZE"],
        "database_table": ["users", "clientes"],
        "route": ["/api/users", "/clientes/{id}"],
        "partial": ["_user_card.html", "_form_field.html"],
    }

    for key, pattern in stack.naming_conventions.items():
        conventions[key] = {
            "pattern": pattern,
            "examples": examples.get(key, []),
        }

    return conventions


def _format_patterns(stack: Stack) -> dict[str, Any]:
    """Format common patterns based on stack characteristics."""
    patterns = {}

    # Dependency injection pattern based on framework
    if stack.framework == "fastapi":
        patterns["dependency_injection"] = {
            "enabled": True,
            "method": "FastAPI Depends",
            "example": "def get_service(db: Session = Depends(get_db)): ...",
        }
    elif stack.framework == "django":
        patterns["dependency_injection"] = {
            "enabled": False,
            "method": "Django views receive request directly",
        }
    elif stack.framework in ("nextjs", "nuxt3", "remix", "sveltekit"):
        patterns["dependency_injection"] = {
            "enabled": True,
            "method": "React/Vue context or hooks",
        }

    # Database session pattern based on ORM
    if stack.orm == "sqlalchemy":
        patterns["database_session"] = {
            "pattern": "scoped_session",
            "example": "db: Session = Depends(get_db)",
        }
    elif stack.orm == "django-orm":
        patterns["database_session"] = {
            "pattern": "implicit",
            "example": "Model.objects.filter(...)",
        }
    elif stack.orm == "prisma":
        patterns["database_session"] = {
            "pattern": "client",
            "example": "const user = await prisma.user.findUnique(...)",
        }
    elif stack.orm == "drizzle":
        patterns["database_session"] = {
            "pattern": "client",
            "example": "const user = await db.select().from(users).where(...)",
        }

    # Error handling pattern
    if stack.language == "python":
        patterns["error_handling"] = {
            "use_exceptions": True,
            "exception_class": "HTTPException" if stack.framework == "fastapi" else "Http404",
        }
    elif stack.language == "typescript":
        patterns["error_handling"] = {
            "use_exceptions": True,
            "exception_class": "Error or custom error classes",
        }

    # Validation pattern
    if stack.language == "python" and stack.framework in ("fastapi", "django"):
        patterns["validation"] = {
            "library": "pydantic" if stack.framework == "fastapi" else "django forms",
            "location": "schemas/" if stack.framework == "fastapi" else "forms/",
        }
    elif stack.language == "typescript":
        patterns["validation"] = {
            "library": "zod",
            "location": "schemas/ or lib/validations/",
        }

    return patterns


def _format_legacy_mapping(stack: Stack) -> dict[str, str]:
    """Format legacy WinDev to modern stack mapping suggestions."""
    mapping = {
        "global_variables": "session or dependency injection",
        "hungarian_notation": "remove prefixes (gn, gs, gc)",
        "procedures": f"functions in {stack.file_structure.get('services', 'services/')}",
        "classes": f"models in {stack.file_structure.get('models', 'models/')}",
        "pages": f"routes + templates in {stack.file_structure.get('routes', 'routes/')}",
    }

    # Add framework-specific mappings
    if stack.framework == "fastapi":
        mapping["HyperFile_buffer"] = "Pydantic model instance"
        mapping["FileToScreen"] = "Form with model_validate()"
        mapping["ScreenToFile"] = "model.model_dump()"
    elif stack.framework == "django":
        mapping["HyperFile_buffer"] = "Django model instance"
        mapping["FileToScreen"] = "Form with instance=obj"
        mapping["ScreenToFile"] = "form.save()"
    elif stack.language == "typescript":
        mapping["HyperFile_buffer"] = "TypeScript interface/type"
        mapping["FileToScreen"] = "React state or form library"
        mapping["ScreenToFile"] = "API call with form data"

    return mapping


def _get_template_extension(engine: str) -> str:
    """Get file extension for template engine."""
    extensions = {
        "jinja2": ".html",
        "blade": ".blade.php",
        "erb": ".html.erb",
        "jsx": ".jsx",
        "tsx": ".tsx",
        "vue": ".vue",
        "svelte": ".svelte",
    }
    return extensions.get(engine, ".html")


@mcp.tool
async def get_stack_conventions(
    ctx: Context,
    output_project_id: str,
    category: str | None = None,
) -> dict[str, Any]:
    """
    Get stack conventions and patterns for consistent code generation.

    Returns naming conventions, file structure, patterns, and legacy mapping
    suggestions for the target stack of an Output Project.

    Use this during execute-phase to generate code following project conventions.

    Args:
        output_project_id: ID of the Output Project
        category: Optional filter: "naming", "structure", "patterns", "templates",
                  "legacy_mapping", "types", "examples", or "all" (default: "all")

    Returns:
        Stack conventions organized by category with examples and suggestions
    """
    try:
        # Find Output Project
        output_project = await OutputProject.get(output_project_id)
        if not output_project:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"Output Project '{output_project_id}' not found",
            }

        # Find Stack
        stack = await Stack.find_one(Stack.stack_id == output_project.stack_id)
        if not stack:
            return {
                "error": True,
                "code": "NOT_FOUND",
                "message": f"Stack '{output_project.stack_id}' not found",
            }

        # Build response based on category filter
        category = category or "all"

        response: dict[str, Any] = {
            "error": False,
            "output_project_id": output_project_id,
            "stack_id": stack.stack_id,
            "stack_name": stack.name,
        }

        conventions: dict[str, Any] = {}

        if category in ("all", "naming"):
            conventions["naming"] = _format_naming_conventions(stack)

        if category in ("all", "structure"):
            conventions["structure"] = {
                "directories": stack.file_structure,
                "file_organization": {
                    "one_model_per_file": True,
                    "group_routes_by_domain": True,
                },
            }

        if category in ("all", "patterns"):
            conventions["patterns"] = _format_patterns(stack)

        if category in ("all", "templates"):
            conventions["templates"] = {
                "engine": stack.template_engine,
                "extension": _get_template_extension(stack.template_engine),
                "base_template": "base.html"
                if stack.template_engine in ("jinja2", "blade", "erb")
                else "layout.tsx",
                "naming": stack.naming_conventions.get("file", "snake_case"),
            }

        if category in ("all", "legacy_mapping"):
            conventions["legacy_mapping"] = _format_legacy_mapping(stack)

        response["conventions"] = conventions

        # Add type mappings
        if category in ("all", "types"):
            response["type_mappings"] = stack.type_mappings

        # Add code examples
        if category in ("all", "examples"):
            response["examples"] = {
                "model_template": stack.model_template or "# No model template defined",
                "imports_template": stack.imports_template or "# No imports template defined",
            }

            # Add HTMX patterns if available
            if stack.htmx_patterns:
                response["examples"]["htmx_patterns"] = stack.htmx_patterns

            # Add TypeScript types if available
            if stack.typescript_types:
                response["examples"]["typescript_types"] = stack.typescript_types

        return response

    except Exception as e:
        return {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(e),
            "type": type(e).__name__,
        }
