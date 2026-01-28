"""API Generator - Generates FastAPI routes from REST APIs.

Converts WinDev REST API definitions (.wdrest) into FastAPI API routes.
"""

from pathlib import Path
from typing import Any

from bson import ObjectId

from wxcode.models.element import Element

from .base import BaseGenerator, ElementFilter


class APIGenerator(BaseGenerator):
    """Generates FastAPI API routes from WinDev REST definitions.

    Reads REST API elements from MongoDB and generates:
    - One route file per REST API
    - GET/POST/PUT/DELETE routes based on API definition
    - __init__.py with router includes

    Supports selective element conversion via ElementFilter.
    """

    # HTTP method mapping
    METHOD_MAP = {
        "GET": "get",
        "POST": "post",
        "PUT": "put",
        "DELETE": "delete",
        "PATCH": "patch",
    }

    template_subdir: str = "python"

    def __init__(
        self,
        project_id: str,
        output_dir: Path,
        element_filter: ElementFilter | None = None,
    ):
        """Initialize APIGenerator.

        Args:
            project_id: MongoDB ObjectId string for the project
            output_dir: Root directory where files will be written
            element_filter: Optional filter for selective element conversion
        """
        super().__init__(project_id, output_dir, element_filter)

    async def generate(self) -> list[Path]:
        """Generate FastAPI API routes from REST definitions.

        Supports selective conversion via element_filter.
        Idempotent: cleans previous files before regenerating.

        Returns:
            List of generated file paths
        """
        # Find REST API elements with filter applied
        query = self.get_element_query("rest_api")
        elements = await Element.find(query).to_list()

        if not elements:
            return []

        generated_apis: list[dict[str, str]] = []

        # Generate route for each REST API
        for element in elements:
            # Clean previous API files only (not routes or other types)
            await self.clean_previous_files(element, file_types=["api"])

            content = self._generate_api(element)
            filename = self._element_to_filename(element.source_name)

            # Write file and track for element
            self.write_file_for_element(
                element, f"app/api/{filename}.py", content, "api"
            )

            generated_apis.append({
                "filename": filename,
                "route_prefix": self._element_to_route_prefix(element.source_name),
                "tag": self._element_to_tag(element.source_name),
            })

        # Generate __init__.py with router includes
        if generated_apis:
            init_content = self._generate_init(generated_apis)
            self.write_file("app/api/__init__.py", init_content)

        # Update conversion status for all converted elements
        await self.update_all_converted_elements()

        return self.generated_files

    def _generate_api(self, element: Element) -> str:
        """Generate API route file for a REST definition.

        Args:
            element: Element representing the REST API

        Returns:
            Python code string for the route file
        """
        api_name = self._to_snake_case(element.source_name)

        # Extract endpoints from AST if available
        routes = self._extract_routes_from_ast(element)

        # If no routes found, create default CRUD routes
        if not routes:
            routes = self._create_default_routes(element)

        # Collect dependencies and imports
        imports = self._collect_imports(routes)

        context = {
            "route_name": api_name,
            "original_page": element.source_file,
            "routes": routes,
            "imports": imports,
        }

        return self.render_template("route.py.j2", context)

    def _extract_routes_from_ast(self, element: Element) -> list[dict[str, Any]]:
        """Extract route definitions from element AST.

        Args:
            element: Element with AST data

        Returns:
            List of route dictionaries
        """
        routes = []

        if not element.ast or not element.ast.procedures:
            return routes

        for proc in element.ast.procedures:
            # Try to extract HTTP method from procedure name
            name = proc.get("name", "")
            method = self._detect_http_method(name)

            if method:
                routes.append(self._create_api_route(
                    element=element,
                    method=method,
                    handler_name=self._to_snake_case(name),
                    path=self._element_to_route_path(element.source_name),
                    return_type="dict",
                ))

        return routes

    def _detect_http_method(self, name: str) -> str | None:
        """Detect HTTP method from procedure name.

        Args:
            name: Procedure name

        Returns:
            HTTP method or None
        """
        name_upper = name.upper()

        for prefix in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            if name_upper.startswith(prefix):
                return prefix.lower()

        # Check for CRUD patterns
        if any(kw in name_upper for kw in ["LIST", "BUSCAR", "LISTAR", "FETCH"]):
            return "get"
        if any(kw in name_upper for kw in ["CREATE", "ADD", "CRIAR", "INCLUIR", "ADICIONAR"]):
            return "post"
        if any(kw in name_upper for kw in ["UPDATE", "MODIFY", "ALTERAR", "ATUALIZAR"]):
            return "put"
        if any(kw in name_upper for kw in ["DELETE", "REMOVE", "EXCLUIR", "DELETAR"]):
            return "delete"

        return None

    def _create_default_routes(self, element: Element) -> list[dict[str, Any]]:
        """Create default CRUD routes for an API.

        Args:
            element: Element representing the API

        Returns:
            List of default route dictionaries
        """
        base_path = self._element_to_route_path(element.source_name)
        base_name = self._to_snake_case(element.source_name)

        # Remove 'api' prefix if present
        for prefix in ["api_", "API_", "rest_", "REST_"]:
            if base_name.startswith(prefix.lower()):
                base_name = base_name[len(prefix):]
                break

        routes = [
            # GET list
            self._create_api_route(
                element=element,
                method="get",
                handler_name=f"list_{base_name}",
                path=base_path,
                return_type="list[dict]",
                docstring=f"List all {base_name}.",
            ),
            # GET single
            self._create_api_route(
                element=element,
                method="get",
                handler_name=f"get_{base_name}",
                path=f"{base_path}/{{item_id}}",
                path_params=[{"name": "item_id", "type": "int"}],
                return_type="dict",
                docstring=f"Get a single {base_name} by ID.",
            ),
            # POST create
            self._create_api_route(
                element=element,
                method="post",
                handler_name=f"create_{base_name}",
                path=base_path,
                status_code=201,
                return_type="dict",
                docstring=f"Create a new {base_name}.",
            ),
            # PUT update
            self._create_api_route(
                element=element,
                method="put",
                handler_name=f"update_{base_name}",
                path=f"{base_path}/{{item_id}}",
                path_params=[{"name": "item_id", "type": "int"}],
                return_type="dict",
                docstring=f"Update a {base_name} by ID.",
            ),
            # DELETE
            self._create_api_route(
                element=element,
                method="delete",
                handler_name=f"delete_{base_name}",
                path=f"{base_path}/{{item_id}}",
                path_params=[{"name": "item_id", "type": "int"}],
                status_code=204,
                return_type="None",
                docstring=f"Delete a {base_name} by ID.",
            ),
        ]

        return routes

    def _create_api_route(
        self,
        element: Element,
        method: str,
        handler_name: str,
        path: str,
        path_params: list[dict] | None = None,
        query_params: list[dict] | None = None,
        return_type: str = "dict",
        status_code: int | None = None,
        docstring: str | None = None,
    ) -> dict[str, Any]:
        """Create an API route dictionary.

        Args:
            element: Source element
            method: HTTP method (get, post, etc.)
            handler_name: Name for the handler function
            path: URL path
            path_params: Path parameters
            query_params: Query parameters
            return_type: Return type annotation
            status_code: HTTP status code
            docstring: Documentation string

        Returns:
            Route dictionary for template
        """
        # Build body based on method
        body = None
        if method == "get":
            body = "# TODO: Implement GET logic\nreturn []" if "list" in return_type else "# TODO: Implement GET logic\nreturn {}"
        elif method == "post":
            body = "# TODO: Implement POST logic\nreturn {}"
        elif method in ("put", "patch"):
            body = "# TODO: Implement UPDATE logic\nreturn {}"
        elif method == "delete":
            body = "# TODO: Implement DELETE logic\nreturn None"

        return {
            "method": method,
            "path": path,
            "handler_name": handler_name,
            "response_class": None,  # JSON response by default
            "status_code": status_code,
            "return_type": return_type,
            "path_params": path_params or [],
            "query_params": query_params or [],
            "dependencies": [],
            "template_path": None,
            "body": body,
            "docstring": docstring or f"API endpoint for {element.source_name}.",
        }

    def _collect_imports(self, routes: list[dict]) -> list[str]:
        """Collect required imports.

        Args:
            routes: List of route dictionaries

        Returns:
            List of import statements
        """
        imports: set[str] = set()

        # Check for list return types
        for route in routes:
            if "list" in (route.get("return_type") or ""):
                imports.add("from typing import Any")
                break

        return sorted(imports)

    def _element_to_filename(self, source_name: str) -> str:
        """Convert element name to Python filename.

        Args:
            source_name: Source name from element

        Returns:
            Snake case filename (without .py)
        """
        name = source_name

        # Remove prefixes
        for prefix in ["API_", "REST_"]:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break

        # Remove suffixes
        for suffix in [".wdrest", "REST", "Api", "API"]:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break

        return self._to_snake_case(name) + "_api"

    def _element_to_route_path(self, source_name: str) -> str:
        """Convert element name to API path.

        Args:
            source_name: Source name from element

        Returns:
            API path (e.g., "/api/clientes")
        """
        name = source_name
        for prefix in ["API_", "REST_", "API", "REST"]:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break
        for suffix in [".wdrest", "REST", "Api", "API"]:
            if name.endswith(suffix):
                name = name[:-len(suffix)]

        snake = self._to_snake_case(name)
        kebab = snake.replace("_", "-")

        return f"/api/{kebab}"

    def _element_to_route_prefix(self, source_name: str) -> str:
        """Convert element name to route prefix."""
        return self._element_to_route_path(source_name)

    def _element_to_tag(self, source_name: str) -> str:
        """Convert element name to OpenAPI tag."""
        name = source_name
        for prefix in ["API_", "REST_"]:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break
        for suffix in [".wdrest"]:
            if name.endswith(suffix):
                name = name[:-len(suffix)]

        return self._to_snake_case(name)

    def _generate_init(self, apis: list[dict[str, str]]) -> str:
        """Generate __init__.py with router includes.

        Args:
            apis: List of API dicts with filename, route_prefix, tag

        Returns:
            Python code string for __init__.py
        """
        lines = [
            '"""API routes generated by wxcode."""',
            "",
            "from fastapi import APIRouter",
            "",
        ]

        # Import routers
        for api in apis:
            lines.append(f"from .{api['filename']} import router as {api['filename']}_router")

        lines.append("")
        lines.append("api_router = APIRouter()")
        lines.append("")

        # Include routers
        for api in apis:
            lines.append(
                f'api_router.include_router({api["filename"]}_router, '
                f'prefix="{api["route_prefix"]}", tags=["{api["tag"]}"])'
            )

        lines.append("")
        return "\n".join(lines)
