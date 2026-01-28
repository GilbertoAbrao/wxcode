"""Route Generator - Generates FastAPI routes from pages.

Converts WinDev pages (.wwh) into FastAPI route files
with GET handlers for rendering templates.
"""

from pathlib import Path
from typing import Any

from bson import ObjectId

from wxcode.models.control import Control
from wxcode.models.element import Element

from .base import BaseGenerator, ElementFilter


class RouteGenerator(BaseGenerator):
    """Generates FastAPI routes from WinDev pages.

    Reads page elements from MongoDB and generates:
    - One route file per page
    - GET route for page display
    - POST route for form submission (if page has form controls)
    - __init__.py with router includes

    Supports selective element conversion via ElementFilter.
    """

    template_subdir: str = "python"

    def __init__(
        self,
        project_id: str,
        output_dir: Path,
        element_filter: ElementFilter | None = None,
    ):
        """Initialize RouteGenerator.

        Args:
            project_id: MongoDB ObjectId string for the project
            output_dir: Root directory where files will be written
            element_filter: Optional filter for selective element conversion
        """
        super().__init__(project_id, output_dir, element_filter)
        self._service_map: dict[str, str] = {}  # service_name -> class_name

    async def generate(self) -> list[Path]:
        """Generate FastAPI routes from pages.

        Supports selective conversion via element_filter.
        Idempotent: cleans previous files before regenerating.

        Returns:
            List of generated file paths
        """
        # Find page elements with filter applied
        query = self.get_element_query(["page", "window"])
        elements = await Element.find(query).to_list()

        if not elements:
            return []

        generated_routes: list[dict[str, str]] = []

        # Generate route for each page
        for element in elements:
            # Clean previous route files only (not templates or other types)
            await self.clean_previous_files(element, file_types=["route"])

            # Get controls for this page
            controls = await Control.find(
                {"element_id": element.id}
            ).to_list()

            content = self._generate_route(element, controls)
            filename = self._element_to_filename(element.source_name)

            # Write file and track for element
            self.write_file_for_element(
                element, f"app/routes/{filename}.py", content, "route"
            )

            generated_routes.append({
                "filename": filename,
                "route_prefix": self._element_to_route_prefix(element.source_name),
                "tag": self._element_to_tag(element.source_name),
            })

        # Generate __init__.py with router includes
        if generated_routes:
            init_content = self._generate_init(generated_routes)
            self.write_file("app/routes/__init__.py", init_content)

        # Update conversion status for all converted elements
        await self.update_all_converted_elements()

        return self.generated_files

    def _generate_route(
        self, element: Element, controls: list[Control]
    ) -> str:
        """Generate route file for a page.

        Args:
            element: Element representing the page
            controls: List of controls in the page

        Returns:
            Python code string for the route file
        """
        route_name = self._to_snake_case(element.source_name)
        page_type = self._detect_page_type(element, controls)

        routes = []

        # Always add GET route for page display
        routes.append(self._create_get_route(element, page_type))

        # Add POST route if page has form
        if page_type == "form":
            routes.append(self._create_post_route(element, controls))

        # Collect dependencies and imports
        dependencies = self._detect_dependencies(element, controls)
        imports = self._collect_imports(routes, dependencies)

        context = {
            "route_name": route_name,
            "original_page": element.source_file,
            "routes": routes,
            "imports": imports,
        }

        return self.render_template("route.py.j2", context)

    def _detect_page_type(
        self, element: Element, controls: list[Control]
    ) -> str:
        """Detect the type of page based on controls.

        Args:
            element: Page element
            controls: List of controls

        Returns:
            Page type: "form", "list", "dashboard", or "simple"
        """
        # Count control types
        edit_count = 0
        button_count = 0
        table_count = 0

        for control in controls:
            type_code = control.type_code
            name_lower = control.name.lower() if control.name else ""

            # Edit controls (type 8)
            if type_code == 8 or name_lower.startswith("edt_"):
                edit_count += 1
            # Button controls
            elif name_lower.startswith("btn_"):
                button_count += 1
            # Table controls
            elif name_lower.startswith("table_") or name_lower.startswith("tbl_"):
                table_count += 1

        # Detect page type by control composition
        if table_count > 0:
            return "list"
        elif edit_count >= 2 and button_count >= 1:
            return "form"
        elif edit_count > 5:
            return "dashboard"
        else:
            return "simple"

    def _create_get_route(self, element: Element, page_type: str) -> dict[str, Any]:
        """Create GET route for page display.

        Args:
            element: Page element
            page_type: Detected page type

        Returns:
            Route dictionary for template
        """
        # Use the filename (without prefix) for handler name
        route_name = self._element_to_filename(element.source_name)
        handler_name = f"{route_name}_page"

        # Route path is empty because prefix already defines the base path
        path = ""

        # Determine template path
        template_path = f"pages/{route_name}.html"

        return {
            "method": "get",
            "path": path,
            "handler_name": handler_name,
            "response_class": "HTMLResponse",
            "status_code": None,
            "return_type": None,
            "path_params": [],
            "query_params": [],
            "dependencies": [],
            "template_path": template_path,
            "body": None,
            "docstring": f"Display {element.source_name} page.",
        }

    def _create_post_route(
        self, element: Element, controls: list[Control]
    ) -> dict[str, Any]:
        """Create POST route for form submission.

        Args:
            element: Page element
            controls: List of controls

        Returns:
            Route dictionary for template
        """
        # Use the filename (without prefix) for handler name
        route_name = self._element_to_filename(element.source_name)
        handler_name = f"{route_name}_submit"
        # Route path is empty because prefix already defines the base path
        path = ""
        template_path = f"pages/{route_name}.html"

        # Build body for form handling
        body_lines = [
            "form_data = await request.form()",
            "# TODO: Process form data",
            "# TODO: Call appropriate service method",
            f'return templates.TemplateResponse(',
            f'    "{template_path}",',
            f'    {{"request": request, "success": True}}',
            f')',
        ]

        return {
            "method": "post",
            "path": path,
            "handler_name": handler_name,
            "response_class": "HTMLResponse",
            "status_code": None,
            "return_type": None,
            "path_params": [],
            "query_params": [],
            "dependencies": [],
            "template_path": template_path,
            "body": "\n".join(body_lines),
            "docstring": f"Handle form submission for {element.source_name}.",
        }

    def _detect_dependencies(
        self, element: Element, controls: list[Control]
    ) -> list[dict[str, str]]:
        """Detect service dependencies for the page.

        Args:
            element: Page element
            controls: List of controls

        Returns:
            List of dependency dictionaries
        """
        dependencies = []

        # Check element dependencies if available
        if element.dependencies:
            for dep_name in element.dependencies.uses or []:
                # Convert to service reference
                if "service" in dep_name.lower() or "procedures" in dep_name.lower():
                    service_class = self._to_pascal_case(dep_name)
                    if not service_class.endswith("Service"):
                        service_class += "Service"

                    dependencies.append({
                        "name": self._to_snake_case(service_class),
                        "type": service_class,
                        "factory": service_class,
                    })

        return dependencies

    def _collect_imports(
        self, routes: list[dict], dependencies: list[dict]
    ) -> list[str]:
        """Collect required imports.

        Args:
            routes: List of route dictionaries
            dependencies: List of dependencies

        Returns:
            List of import statements
        """
        imports: set[str] = set()

        # Add service imports
        for dep in dependencies:
            imports.add(f"from app.services import {dep['type']}")

        return sorted(imports)

    def _element_to_filename(self, source_name: str) -> str:
        """Convert element name to Python filename.

        Args:
            source_name: Source name from element (e.g., "PAGE_Login")

        Returns:
            Snake case filename (without .py)
        """
        # Remove common prefixes
        name = source_name
        for prefix in ["PAGE_", "PAGE", "page_", "FEN_", "WIN_"]:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break

        return self._to_snake_case(name)

    def _element_to_route_path(self, source_name: str) -> str:
        """Convert element name to route path.

        Args:
            source_name: Source name from element

        Returns:
            Route path (e.g., "/login", "/clientes")
        """
        # Remove common prefixes
        name = source_name
        for prefix in ["PAGE_", "PAGE", "page_", "FEN_", "WIN_"]:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break

        # Convert to kebab-case
        snake = self._to_snake_case(name)
        kebab = snake.replace("_", "-")

        return f"/{kebab}"

    def _element_to_route_prefix(self, source_name: str) -> str:
        """Convert element name to route prefix.

        Args:
            source_name: Source name from element

        Returns:
            Route prefix for grouping (e.g., "/auth", "/clientes")
        """
        return self._element_to_route_path(source_name)

    def _element_to_tag(self, source_name: str) -> str:
        """Convert element name to OpenAPI tag.

        Args:
            source_name: Source name from element

        Returns:
            Tag name for OpenAPI docs
        """
        name = source_name
        for prefix in ["PAGE_", "PAGE", "page_", "FEN_", "WIN_"]:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break

        return self._to_snake_case(name)

    def _generate_init(self, routes: list[dict[str, str]]) -> str:
        """Generate __init__.py with router includes.

        Args:
            routes: List of route dicts with filename, route_prefix, tag

        Returns:
            Python code string for __init__.py
        """
        lines = [
            '"""Routes generated by wxcode."""',
            "",
            "from fastapi import APIRouter",
            "",
        ]

        # Import routers
        for route in routes:
            lines.append(f"from .{route['filename']} import router as {route['filename']}_router")

        lines.append("")
        lines.append("router = APIRouter()")
        lines.append("")

        # Include routers
        for route in routes:
            lines.append(
                f'router.include_router({route["filename"]}_router, '
                f'prefix="{route["route_prefix"]}", tags=["{route["tag"]}"])'
            )

        lines.append("")
        return "\n".join(lines)
