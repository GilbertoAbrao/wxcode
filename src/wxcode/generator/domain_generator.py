"""Domain Generator - Generates Python classes from ClassDefinition.

Converts WinDev class definitions extracted from .wdc files
into Python dataclasses for use with FastAPI.
"""

from pathlib import Path
from typing import Any

from bson import ObjectId

from wxcode.models.class_definition import (
    ClassConstant,
    ClassDefinition,
    ClassMember,
    ClassMethod,
)
from wxcode.models.procedure import ProcedureParameter

from .base import BaseGenerator, ElementFilter
from .wlanguage_converter import WLanguageConverter, ConversionResult


class DomainGenerator(BaseGenerator):
    """Generates Python classes from ClassDefinition.

    Reads class definitions from MongoDB and generates:
    - One Python dataclass per WinDev class
    - __init__.py with all class exports
    - Proper type mappings and inheritance

    Supports selective class conversion via ElementFilter.
    Note: For DomainGenerator, element_names in filter are matched against class names.

    Attributes:
        TYPE_MAP: Mapping of WLanguage types to Python type strings
    """

    # Mapping WLanguage types to Python types
    TYPE_MAP: dict[str, str] = {
        # Basic types
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
        # Date/Time types
        "date": "date",
        "datetime": "datetime",
        "time": "time",
        "duration": "int",
        "durée": "int",
        # Complex types
        "variant": "Any",
        "json": "dict",
        "buffer": "bytes",
        "array": "list",
        "tableau": "list",
        "associative array": "dict",
        # Special types
        "currency": "Decimal",
        "monétaire": "Decimal",
        "monetaire": "Decimal",
    }

    # Default values for types
    TYPE_DEFAULTS: dict[str, str] = {
        "str": '""',
        "int": "0",
        "float": "0.0",
        "bool": "False",
        "date": "None",
        "datetime": "None",
        "time": "None",
        "Any": "None",
        "dict": "field(default_factory=dict)",
        "list": "field(default_factory=list)",
        "bytes": 'b""',
        "Decimal": "Decimal(0)",
    }

    template_subdir: str = "python"

    def __init__(
        self,
        project_id: str,
        output_dir: Path,
        element_filter: ElementFilter | None = None,
    ):
        """Initialize DomainGenerator.

        Args:
            project_id: MongoDB ObjectId string for the project
            output_dir: Root directory where files will be written
            element_filter: Optional filter for selective class conversion.
                           element_names are matched against class names.
        """
        super().__init__(project_id, output_dir, element_filter)
        self._class_names: dict[str, str] = {}  # original_name -> python_class_name

    def _get_class_query(self) -> dict[str, Any]:
        """Get MongoDB query for classes with filter applied.

        Returns:
            MongoDB query dictionary
        """
        import fnmatch
        import re

        query: dict[str, Any] = {"project_id": ObjectId(self.project_id)}

        if not self.element_filter:
            return query

        # Filter by IDs (element_ids filter)
        if self.element_filter.element_ids:
            query["_id"] = {"$in": [ObjectId(eid) for eid in self.element_filter.element_ids]}

        # Filter by names (element_names filter applied to class names)
        if self.element_filter.element_names and not self.element_filter.element_ids:
            patterns = []
            for name in self.element_filter.element_names:
                # Convert wildcard to regex
                regex = "^" + re.escape(name).replace(r"\*", ".*") + "$"
                patterns.append({"name": {"$regex": regex, "$options": "i"}})
            if len(patterns) == 1:
                query.update(patterns[0])
            else:
                query["$or"] = patterns

        return query

    async def generate(self) -> list[Path]:
        """Generate Python classes from class definitions.

        Supports selective conversion via element_filter.

        Returns:
            List of generated file paths
        """
        # Fetch class definitions with filter applied
        query = self._get_class_query()
        class_defs = await ClassDefinition.find(query).to_list()

        if not class_defs:
            return []

        # Build map of class names for inheritance resolution
        for class_def in class_defs:
            python_name = self._to_pascal_case(class_def.name)
            self._class_names[class_def.name.lower()] = python_name

        generated_classes: list[dict[str, str]] = []

        # Generate Python class for each definition
        for class_def in class_defs:
            content = self._generate_class(class_def)
            filename = self._class_to_filename(class_def.name)
            self.write_file(f"app/domain/{filename}.py", content)

            generated_classes.append({
                "filename": filename,
                "class_name": self._to_pascal_case(class_def.name),
            })

        # Generate __init__.py
        if generated_classes:
            init_content = self._generate_init(generated_classes)
            self.write_file("app/domain/__init__.py", init_content)

        return self.generated_files

    def _generate_class(self, class_def: ClassDefinition) -> str:
        """Generate Python class for a ClassDefinition.

        Args:
            class_def: ClassDefinition from MongoDB

        Returns:
            Python code string for the class
        """
        class_name = self._to_pascal_case(class_def.name)

        # Resolve base class
        base_class = None
        if class_def.inherits_from:
            base_key = class_def.inherits_from.lower()
            if base_key in self._class_names:
                base_class = self._class_names[base_key]
            else:
                # External class - use as-is
                base_class = self._to_pascal_case(class_def.inherits_from)

        # Convert constants
        constants = [self._convert_constant(c) for c in class_def.constants]

        # Convert members
        members = [self._convert_member(m) for m in class_def.members]

        # Convert methods
        methods = []
        init_code = None

        for method in class_def.methods:
            if method.method_type == "constructor":
                # Extract constructor code for __post_init__
                init_code = self._convert_method_body(method.code)
            else:
                methods.append(self._convert_method(method, class_def.is_abstract))

        # Collect imports
        imports = self._collect_imports(class_def, members, methods)

        context = {
            "class_name": class_name,
            "original_file": f"{class_def.name}.wdc",
            "docstring": f"Class converted from {class_def.name}.wdc",
            "is_abstract": class_def.is_abstract,
            "base_class": base_class,
            "constants": constants,
            "members": members,
            "methods": methods,
            "init_code": init_code,
            "imports": imports,
        }

        return self.render_template("domain_class.py.j2", context)

    def _convert_constant(self, constant: ClassConstant) -> dict[str, Any]:
        """Convert ClassConstant to template dict.

        Args:
            constant: Constant from class definition

        Returns:
            Dictionary with name, type, value
        """
        # Infer type from value
        value = constant.value
        inferred_type = constant.type or self._infer_type(value)
        python_type = self._get_python_type(inferred_type)

        # Format value for Python
        formatted_value = self._format_constant_value(value, python_type)

        return {
            "name": constant.name.upper(),  # Constants are uppercase
            "type": python_type,
            "value": formatted_value,
        }

    def _convert_member(self, member: ClassMember) -> dict[str, Any]:
        """Convert ClassMember to template dict.

        Args:
            member: Member from class definition

        Returns:
            Dictionary with name, type, default, is_private
        """
        python_type = self._get_python_type(member.type)
        member_name = self._to_snake_case(member.name)

        # Determine default value
        if member.default_value:
            default = self._format_default_value(member.default_value, python_type)
        else:
            default = self.TYPE_DEFAULTS.get(python_type, "None")

        return {
            "name": member_name,
            "type": python_type,
            "default": default,
            "is_private": member.visibility.lower() == "private",
        }

    def _convert_method(
        self, method: ClassMethod, is_abstract_class: bool = False
    ) -> dict[str, Any]:
        """Convert ClassMethod to template dict.

        Args:
            method: Method from class definition
            is_abstract_class: True if parent class is abstract

        Returns:
            Dictionary with method info for template
        """
        method_name = self._to_snake_case(method.name)

        # Convert parameters
        params = []
        for param in method.parameters:
            params.append(self._convert_parameter(param))

        # Determine return type
        return_type = "None"
        if method.return_type:
            return_type = self._get_python_type(method.return_type)

        # Build original signature for docstring
        original_params = ", ".join(
            f"{p.name} is {p.type}" + (f" = {p.default_value}" if p.default_value else "")
            for p in method.parameters
        )
        return_str = f": {method.return_type}" if method.return_type else ""
        original_signature = f"PROCEDURE {method.name}({original_params}){return_str}"

        # Convert method body
        body = None
        if method.code and method.code.strip():
            body = self._convert_method_body(method.code)

        return {
            "name": method_name,
            "params": params,
            "return_type": return_type,
            "docstring": f"Method converted from WLanguage.",
            "original_signature": original_signature,
            "body": body,
            "is_abstract": is_abstract_class and method.visibility.lower() == "public",
            "is_static": method.is_static,
        }

    def _convert_parameter(self, param: ProcedureParameter) -> dict[str, Any]:
        """Convert ProcedureParameter to template dict.

        Args:
            param: Parameter from method

        Returns:
            Dictionary with name, type, default
        """
        python_type = self._get_python_type(param.type)
        param_name = self._to_snake_case(param.name)

        default = None
        if param.default_value:
            default = self._format_default_value(param.default_value, python_type)

        return {
            "name": param_name,
            "type": python_type,
            "default": default,
        }

    def _convert_method_body(self, code: str) -> str | None:
        """Convert WLanguage method body to Python.

        Uses WLanguageConverter to convert H* functions and common patterns.

        Args:
            code: WLanguage code string

        Returns:
            Python code string or None
        """
        if not code or not code.strip():
            return None

        # Use WLanguageConverter for conversion
        converter = WLanguageConverter(db_var="self.db")
        result = converter.convert(code)

        # Build output
        output_lines = []

        # Add warnings as comments if any
        if result.warnings:
            for warning in result.warnings:
                output_lines.append(f"# WARNING: {warning}")

        # Add review marker if needed
        if result.requires_manual_review:
            output_lines.append("# TODO: [WXCODE] Manual review required")
            if result.review_reasons:
                for reason in result.review_reasons:
                    output_lines.append(f"#   - {reason}")

        # Add converted code
        output_lines.append(result.python_code)

        return "\n".join(output_lines)

    def _get_python_type(self, wlang_type: str) -> str:
        """Get Python type from WLanguage type.

        Args:
            wlang_type: WLanguage type string

        Returns:
            Python type string
        """
        if not wlang_type:
            return "Any"

        # Normalize type name
        type_lower = wlang_type.lower().strip()

        # Check direct mapping
        if type_lower in self.TYPE_MAP:
            return self.TYPE_MAP[type_lower]

        # Check for class reference (starts with 'class' prefix)
        if type_lower.startswith("class"):
            # Convert camelCase to PascalCase (first snake_case, then PascalCase)
            snake = self._to_snake_case(wlang_type)
            return self._to_pascal_case(snake)

        # Check for array types
        if "array" in type_lower or "tableau" in type_lower:
            return "list"

        # Default to Any for unknown types
        return "Any"

    def _infer_type(self, value: str) -> str:
        """Infer WLanguage type from value.

        Args:
            value: Value string

        Returns:
            Inferred type string
        """
        if not value:
            return "string"

        # Try to parse as number
        try:
            if "." in value:
                float(value)
                return "real"
            else:
                int(value)
                return "int"
        except ValueError:
            pass

        # Check for boolean
        if value.lower() in ("true", "false", "vrai", "faux"):
            return "boolean"

        # Default to string
        return "string"

    def _format_constant_value(self, value: str, python_type: str) -> str:
        """Format constant value for Python code.

        Args:
            value: Original value string
            python_type: Target Python type

        Returns:
            Formatted value string
        """
        if python_type == "str":
            # Escape quotes in string
            escaped = value.replace('"', '\\"')
            return f'"{escaped}"'
        elif python_type == "bool":
            return "True" if value.lower() in ("true", "1", "vrai") else "False"
        else:
            return value

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
        elif python_type in ("int", "float", "Decimal"):
            return value
        elif python_type == "None":
            return "None"
        else:
            return f'"{value}"'

    def _collect_imports(
        self,
        class_def: ClassDefinition,
        members: list[dict],
        methods: list[dict],
    ) -> list[str]:
        """Collect required imports for the class.

        Args:
            class_def: Class definition
            members: Converted members
            methods: Converted methods

        Returns:
            List of import statements
        """
        imports: set[str] = set()

        # Check member types
        for member in members:
            self._add_type_import(member["type"], imports)

        # Check method return types and parameters
        for method in methods:
            self._add_type_import(method["return_type"], imports)
            for param in method["params"]:
                self._add_type_import(param["type"], imports)

        # Check for Decimal in defaults
        for member in members:
            if "Decimal" in str(member.get("default", "")):
                imports.add("from decimal import Decimal")

        return sorted(imports)

    def _add_type_import(self, type_str: str, imports: set[str]) -> None:
        """Add import statement for a type if needed.

        Args:
            type_str: Type string
            imports: Set of import statements to update
        """
        type_imports = {
            "datetime": "from datetime import datetime",
            "date": "from datetime import date",
            "time": "from datetime import time",
            "Decimal": "from decimal import Decimal",
            "UUID": "from uuid import UUID",
        }

        if type_str in type_imports:
            imports.add(type_imports[type_str])

    def _class_to_filename(self, class_name: str) -> str:
        """Convert class name to Python filename.

        Args:
            class_name: Class name from definition

        Returns:
            Snake case filename (without .py)
        """
        return self._to_snake_case(class_name)

    def _generate_init(self, classes: list[dict[str, str]]) -> str:
        """Generate __init__.py with class exports.

        Args:
            classes: List of dicts with filename and class_name

        Returns:
            Python code string for __init__.py
        """
        lines = ['"""Domain classes generated by wxcode."""', ""]

        # Import statements
        for cls in classes:
            lines.append(f"from .{cls['filename']} import {cls['class_name']}")

        lines.append("")

        # __all__ export
        all_classes = ", ".join(f'"{cls["class_name"]}"' for cls in classes)
        lines.append(f"__all__ = [{all_classes}]")
        lines.append("")

        return "\n".join(lines)
