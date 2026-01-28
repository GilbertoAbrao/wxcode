"""Service Generator - Generates FastAPI services from Procedures.

Converts WinDev procedure groups extracted from .wdg files
into FastAPI service classes.
"""

from pathlib import Path
from typing import Any

from bson import ObjectId

from wxcode.models.element import Element
from wxcode.models.procedure import Procedure, ProcedureParameter

from .base import BaseGenerator, ElementFilter
from .wlanguage_converter import WLanguageConverter


class ServiceGenerator(BaseGenerator):
    """Generates FastAPI services from Procedure groups.

    Reads procedures from MongoDB grouped by their source element (.wdg file)
    and generates:
    - One service class per procedure group
    - Methods for each procedure
    - __init__.py with all service exports

    Uses WLanguageConverter for code conversion.
    Supports selective element conversion via ElementFilter.
    """

    # WLanguage to Python type mapping (same as DomainGenerator)
    TYPE_MAP: dict[str, str] = {
        "string": "str",
        "chaîne": "str",
        "chaine": "str",
        "int": "int",
        "entier": "int",
        "integer": "int",
        "real": "float",
        "réel": "float",
        "reel": "float",
        "numeric": "float",
        "numérique": "float",
        "boolean": "bool",
        "booléen": "bool",
        "booleen": "bool",
        "date": "date",
        "datetime": "datetime",
        "time": "time",
        "variant": "Any",
        "json": "dict",
        "buffer": "bytes",
        "array": "list",
        "tableau": "list",
    }

    template_subdir: str = "python"

    def __init__(
        self,
        project_id: str,
        output_dir: Path,
        element_filter: ElementFilter | None = None,
    ):
        """Initialize ServiceGenerator.

        Args:
            project_id: MongoDB ObjectId string for the project
            output_dir: Root directory where files will be written
            element_filter: Optional filter for selective element conversion
        """
        super().__init__(project_id, output_dir, element_filter)
        self._converter = WLanguageConverter(db_var="self.db")

    async def generate(self) -> list[Path]:
        """Generate FastAPI services from procedures.

        Supports selective conversion via element_filter.
        Idempotent: cleans previous files before regenerating.

        Returns:
            List of generated file paths
        """
        # Find procedure group elements with filter applied
        query = self.get_element_query("procedure_group")
        elements = await Element.find(query).to_list()

        if not elements:
            return []

        generated_services: list[dict[str, str]] = []

        # Generate service for each procedure group
        for element in elements:
            # Clean previous generated files for idempotency
            await self.clean_previous_files(element, file_types=["service"])

            procedures = await Procedure.find(
                {
                    "element_id": element.id,
                    "is_local": False,  # Only global procedures
                }
            ).to_list()

            if not procedures:
                continue

            content = self._generate_service(element, procedures)
            filename = self._element_to_filename(element.source_name)

            # Write file and track for element
            self.write_file_for_element(
                element, f"app/services/{filename}.py", content, "service"
            )

            generated_services.append({
                "filename": filename,
                "class_name": self._element_to_classname(element.source_name),
            })

        # Generate __init__.py
        if generated_services:
            init_content = self._generate_init(generated_services)
            self.write_file("app/services/__init__.py", init_content)

        # Update conversion status for all converted elements
        await self.update_all_converted_elements()

        return self.generated_files

    def _generate_service(
        self, element: Element, procedures: list[Procedure]
    ) -> str:
        """Generate service class for a procedure group.

        Args:
            element: Element representing the .wdg file
            procedures: List of procedures in this group

        Returns:
            Python code string for the service
        """
        class_name = self._element_to_classname(element.source_name)
        service_name = self._to_snake_case(element.source_name)

        # Convert all procedures to methods
        methods = []
        for proc in procedures:
            if proc.is_public:  # Skip internal/private procedures
                methods.append(self._convert_procedure(proc))

        # Collect required imports
        imports = self._collect_imports(methods)

        context = {
            "class_name": class_name,
            "service_name": service_name,
            "original_file": element.source_file,
            "docstring": f"Service converted from {element.source_file}",
            "methods": methods,
            "imports": imports,
        }

        return self.render_template("service.py.j2", context)

    def _convert_procedure(self, proc: Procedure) -> dict[str, Any]:
        """Convert Procedure to method dictionary for template.

        Args:
            proc: Procedure from MongoDB

        Returns:
            Dictionary with method info for template
        """
        method_name = self._to_snake_case(proc.name)

        # Convert parameters
        params = []
        for param in proc.parameters:
            if not param.is_local:  # Skip LOCAL parameters
                params.append(self._convert_parameter(param))

        # Determine return type
        return_type = "None"
        if proc.return_type:
            return_type = self._get_python_type(proc.return_type)

        # Build original signature for docstring
        original_signature = proc.signature if proc.signature else f"PROCEDURE {proc.name}()"

        # Convert code
        body = None
        needs_manual_conversion = False
        conversion_reason = None
        original_code = None

        if proc.code and proc.code.strip():
            result = self._converter.convert(proc.code)
            body = result.python_code

            if result.requires_manual_review:
                needs_manual_conversion = True
                conversion_reason = ", ".join(result.review_reasons) if result.review_reasons else "Complex code"
                original_code = proc.code[:500]  # First 500 chars

                # Add warnings to body
                if result.warnings:
                    warnings_comment = "\n".join(f"# WARNING: {w}" for w in result.warnings)
                    body = warnings_comment + "\n" + body

        return {
            "name": method_name,
            "params": params,
            "return_type": return_type,
            "docstring": f"Procedure converted from WLanguage.",
            "original_signature": original_signature,
            "body": body,
            "needs_manual_conversion": needs_manual_conversion,
            "conversion_reason": conversion_reason,
            "original_code": original_code,
        }

    def _convert_parameter(self, param: ProcedureParameter) -> dict[str, Any]:
        """Convert ProcedureParameter to template dict.

        Args:
            param: Parameter from procedure

        Returns:
            Dictionary with name, type, default
        """
        python_type = self._get_python_type(param.type) if param.type else "Any"
        param_name = self._to_snake_case(param.name)

        default = None
        if param.default_value:
            default = self._format_default_value(param.default_value, python_type)

        return {
            "name": param_name,
            "type": python_type,
            "default": default,
        }

    def _get_python_type(self, wlang_type: str) -> str:
        """Get Python type from WLanguage type.

        Args:
            wlang_type: WLanguage type string

        Returns:
            Python type string
        """
        if not wlang_type:
            return "Any"

        type_lower = wlang_type.lower().strip()

        if type_lower in self.TYPE_MAP:
            return self.TYPE_MAP[type_lower]

        # Check for array types
        if "array" in type_lower or "tableau" in type_lower:
            return "list"

        return "Any"

    def _format_default_value(self, value: str, python_type: str) -> str:
        """Format default value for Python code.

        Args:
            value: Default value string
            python_type: Target Python type

        Returns:
            Formatted default value
        """
        if python_type == "str":
            escaped = value.replace('"', '\\"')
            return f'"{escaped}"'
        elif python_type == "bool":
            return "True" if value.lower() in ("true", "1", "vrai", "yes") else "False"
        elif python_type in ("int", "float"):
            return value
        elif python_type == "None":
            return "None"
        else:
            return f'"{value}"'

    def _collect_imports(self, methods: list[dict]) -> list[str]:
        """Collect required imports for the service.

        Args:
            methods: List of method dictionaries

        Returns:
            List of import statements
        """
        imports: set[str] = set()

        type_imports = {
            "datetime": "from datetime import datetime",
            "date": "from datetime import date",
            "time": "from datetime import time",
            "Decimal": "from decimal import Decimal",
            "UUID": "from uuid import UUID",
        }

        for method in methods:
            # Check return type
            if method["return_type"] in type_imports:
                imports.add(type_imports[method["return_type"]])

            # Check parameter types
            for param in method["params"]:
                if param["type"] in type_imports:
                    imports.add(type_imports[param["type"]])

        return sorted(imports)

    def _element_to_filename(self, source_name: str) -> str:
        """Convert element source name to Python filename.

        Args:
            source_name: Source name from element (e.g., "ServerProcedures")

        Returns:
            Snake case filename (without .py)
        """
        # Remove common suffixes
        name = source_name
        for suffix in [".wdg", "Procedures", "Service"]:
            if name.endswith(suffix):
                name = name[:-len(suffix)]

        return self._to_snake_case(name) + "_service"

    def _element_to_classname(self, source_name: str) -> str:
        """Convert element source name to class name.

        Args:
            source_name: Source name from element

        Returns:
            PascalCase class name ending with Service
        """
        # Remove common suffixes
        name = source_name
        for suffix in [".wdg", "Procedures"]:
            if name.endswith(suffix):
                name = name[:-len(suffix)]

        # Convert to PascalCase and add Service suffix
        snake = self._to_snake_case(name)
        pascal = self._to_pascal_case(snake)

        if not pascal.endswith("Service"):
            pascal += "Service"

        return pascal

    def _generate_init(self, services: list[dict[str, str]]) -> str:
        """Generate __init__.py with service exports.

        Args:
            services: List of dicts with filename and class_name

        Returns:
            Python code string for __init__.py
        """
        lines = ['"""Services generated by wxcode."""', ""]

        # Import statements
        for svc in services:
            lines.append(f"from .{svc['filename']} import {svc['class_name']}")

        lines.append("")

        # __all__ export
        all_services = ", ".join(f'"{svc["class_name"]}"' for svc in services)
        lines.append(f"__all__ = [{all_services}]")
        lines.append("")

        return "\n".join(lines)
