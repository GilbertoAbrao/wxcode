"""Schema Generator - Generates Pydantic models from DatabaseSchema.

Converts HyperFile database schema extracted from WinDev/WebDev projects
into Pydantic models for use with FastAPI.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bson import ObjectId

from wxcode.models.schema import DatabaseSchema, SchemaColumn, SchemaTable

from .base import BaseGenerator, ElementFilter


@dataclass
class DetectedRelationship:
    """Represents a detected relationship between tables."""

    source_table: str
    source_column: str
    target_table: str
    target_column: str
    relationship_type: str  # "foreign_key", "inferred"


class SchemaGenerator(BaseGenerator):
    """Generates Pydantic models from DatabaseSchema.

    Reads the database schema from MongoDB and generates:
    - One Pydantic model per table
    - __init__.py with all model exports
    - Proper type mappings from HyperFile to Python

    Attributes:
        TYPE_MAP: Mapping of HyperFile type codes to Python type strings
    """

    # Mapping HyperFile type codes to Python types
    # Based on WinDev HyperFile documentation
    TYPE_MAP: dict[int, str] = {
        1: "bytes",         # Binary
        2: "str",           # Text/String
        3: "str",           # Text (16-bit)
        4: "int",           # Integer (4 bytes)
        5: "int",           # Integer (2 bytes)
        6: "int",           # Integer (1 byte)
        7: "int",           # Integer (8 bytes - long)
        8: "float",         # Real (4 bytes)
        9: "float",         # Real (8 bytes - double)
        10: "datetime",     # DateTime
        11: "date",         # Date
        12: "time",         # Time
        13: "bool",         # Boolean
        14: "Decimal",      # Currency
        15: "str",          # Memo (text)
        16: "str",          # Memo text
        17: "bytes",        # Memo binary
        18: "str",          # Memo HFSQL
        19: "int",          # Duration
        20: "str",          # Character
        21: "str",          # Unicode string
        22: "str",          # Unicode memo
        23: "str",          # JSON
        24: "int",          # Auto-increment
        25: "int",          # Auto-increment (8 bytes)
        26: "UUID",         # UUID
        27: "str",          # Password
        28: "str",          # Secure password
    }

    # Imports needed for specific types
    TYPE_IMPORTS: dict[str, str] = {
        "datetime": "from datetime import datetime",
        "date": "from datetime import date",
        "time": "from datetime import time",
        "Decimal": "from decimal import Decimal",
        "UUID": "from uuid import UUID",
    }

    template_subdir: str = "python"

    def __init__(
        self,
        project_id: str,
        output_dir: Path,
        element_filter: ElementFilter | None = None,
    ):
        """Initialize SchemaGenerator.

        Args:
            project_id: MongoDB ObjectId string for the project
            output_dir: Root directory where files will be written
            element_filter: Optional filter (not used for schema, kept for consistency)
        """
        super().__init__(project_id, output_dir, element_filter)
        self._relationships: list[DetectedRelationship] = []
        self._table_names: set[str] = set()

    async def generate(self) -> list[Path]:
        """Generate Pydantic models from database schema.

        Returns:
            List of generated file paths
        """
        # Fetch schema from MongoDB
        schema = await DatabaseSchema.find_one(
            {"project_id": ObjectId(self.project_id)}
        )

        if not schema:
            return []

        # Collect table names for relationship detection
        self._table_names = {table.name.lower() for table in schema.tables}

        # Detect relationships across all tables
        self._detect_relationships(schema.tables)

        generated_models: list[dict[str, str]] = []

        # Generate model for each table
        for table in schema.tables:
            content = self._generate_model(table)
            filename = self._table_to_filename(table.name)
            self.write_file(f"app/models/{filename}.py", content)

            generated_models.append({
                "filename": filename,
                "class_name": self._table_to_classname(table.name),
            })

        # Generate __init__.py
        if generated_models:
            init_content = self._generate_init(generated_models)
            self.write_file("app/models/__init__.py", init_content)

        return self.generated_files

    def _detect_relationships(self, tables: list[SchemaTable]) -> None:
        """Detect relationships between tables based on naming conventions.

        Looks for columns ending with _id that match table names.

        Args:
            tables: List of tables from schema
        """
        self._relationships = []

        for table in tables:
            for column in table.columns:
                col_name_lower = column.name.lower()

                # Check for foreign key pattern: <table_name>_id or id_<table_name>
                if col_name_lower.endswith("_id"):
                    # Extract potential table name
                    potential_table = col_name_lower[:-3]  # Remove _id

                    if potential_table in self._table_names:
                        self._relationships.append(DetectedRelationship(
                            source_table=table.name,
                            source_column=column.name,
                            target_table=potential_table.upper(),
                            target_column="id",
                            relationship_type="foreign_key",
                        ))
                elif col_name_lower.startswith("id_"):
                    # id_cliente pattern
                    potential_table = col_name_lower[3:]  # Remove id_

                    if potential_table in self._table_names:
                        self._relationships.append(DetectedRelationship(
                            source_table=table.name,
                            source_column=column.name,
                            target_table=potential_table.upper(),
                            target_column="id",
                            relationship_type="foreign_key",
                        ))

    def _get_relationship_for_column(
        self, table_name: str, column_name: str
    ) -> DetectedRelationship | None:
        """Get relationship for a specific column if one exists.

        Args:
            table_name: Name of the table
            column_name: Name of the column

        Returns:
            DetectedRelationship if found, None otherwise
        """
        for rel in self._relationships:
            if (
                rel.source_table.lower() == table_name.lower()
                and rel.source_column.lower() == column_name.lower()
            ):
                return rel
        return None

    def _generate_model(self, table: SchemaTable) -> str:
        """Generate Pydantic model for a table.

        Args:
            table: SchemaTable from database schema

        Returns:
            Python code string for the model
        """
        fields = []
        used_types: set[str] = set()

        for column in table.columns:
            field_info = self._column_to_field(table.name, column)
            fields.append(field_info)

            # Track which types need imports
            base_type = field_info["type"].replace("Optional[", "").rstrip("]")
            if base_type in self.TYPE_IMPORTS:
                used_types.add(base_type)

        # Check for email fields (using EmailStr validator)
        has_email_field = any(
            self._is_email_field(f["name"]) for f in fields
        )

        context = {
            "table_name": table.name,
            "original_table_name": table.physical_name or table.name,
            "class_name": self._table_to_classname(table.name),
            "fields": fields,
            "has_email_field": has_email_field,
            "docstring": f"Pydantic model for table {table.name}",
        }

        return self.render_template("model.py.j2", context)

    def _is_email_field(self, field_name: str) -> bool:
        """Check if a field is an email field by name.

        Args:
            field_name: Name of the field

        Returns:
            True if the field appears to be an email field
        """
        name_lower = field_name.lower()
        return "email" in name_lower or "e_mail" in name_lower

    def _column_to_field(
        self, table_name: str, column: SchemaColumn
    ) -> dict[str, Any]:
        """Convert SchemaColumn to field dictionary for template.

        Args:
            table_name: Name of the table containing this column
            column: Column from schema

        Returns:
            Dictionary with name, type, default, comment
        """
        python_type = self._get_python_type(column)
        field_name = self._to_snake_case(column.name)

        # Check if this is an email field and use EmailStr
        if self._is_email_field(column.name):
            python_type = "EmailStr"

        # Determine default value
        default: Any = None
        if column.default_value is not None:
            default = self._format_default(column.default_value, python_type)
        elif column.nullable:
            python_type = f"Optional[{python_type}]"
            default = "None"
        elif column.is_auto_increment:
            # Auto-increment fields don't need default in create models
            pass

        # Generate comment including relationship info
        comment = self._generate_field_comment(table_name, column)

        return {
            "name": field_name,
            "type": python_type,
            "default": default,
            "comment": comment,
        }

    def _get_python_type(self, column: SchemaColumn) -> str:
        """Get Python type for a column.

        Args:
            column: Column from schema

        Returns:
            Python type string
        """
        # Use pre-computed python_type if available
        if column.python_type and column.python_type != "Any":
            return column.python_type

        # Fall back to TYPE_MAP
        return self.TYPE_MAP.get(column.hyperfile_type, "Any")

    def _format_default(self, value: str, python_type: str) -> str:
        """Format default value for Python code.

        Args:
            value: Default value string from schema
            python_type: Target Python type

        Returns:
            Formatted default value string
        """
        if python_type == "str":
            return f'"{value}"'
        elif python_type == "bool":
            return "True" if value.lower() in ("true", "1", "yes") else "False"
        elif python_type in ("int", "float", "Decimal"):
            return value
        else:
            return f'"{value}"'

    def _generate_field_comment(
        self, table_name: str, column: SchemaColumn
    ) -> str | None:
        """Generate comment for a field.

        Args:
            table_name: Name of the table containing this column
            column: Column from schema

        Returns:
            Comment string or None
        """
        parts = []

        # Check for relationship (FK)
        relationship = self._get_relationship_for_column(table_name, column.name)
        if relationship:
            parts.append(f"FK: {relationship.target_table}.{relationship.target_column}")

        # Add key info
        if column.is_primary_key:
            parts.append("PK")
        elif column.is_unique:
            parts.append("Unique")
        elif column.is_indexed:
            parts.append("Indexed")

        # Add special field markers
        if column.is_auto_increment:
            parts.append("Auto-increment")

        # Add TODO for special validators
        field_name_lower = column.name.lower()
        if "cpf" in field_name_lower:
            parts.append("TODO: Add CPF validator")
        elif "cnpj" in field_name_lower:
            parts.append("TODO: Add CNPJ validator")
        elif "telefone" in field_name_lower or "phone" in field_name_lower:
            parts.append("TODO: Add phone validator")
        elif "cep" in field_name_lower:
            parts.append("TODO: Add CEP validator")

        return " | ".join(parts) if parts else None

    def _generate_init(self, models: list[dict[str, str]]) -> str:
        """Generate __init__.py with model exports.

        Args:
            models: List of dicts with filename and class_name

        Returns:
            Python code string for __init__.py
        """
        return self.render_template("init_models.py.j2", {"models": models})

    def _table_to_filename(self, table_name: str) -> str:
        """Convert table name to Python filename.

        Args:
            table_name: Table name from schema

        Returns:
            Snake case filename (without .py)
        """
        return self._to_snake_case(table_name)

    def _table_to_classname(self, table_name: str) -> str:
        """Convert table name to Python class name.

        Args:
            table_name: Table name from schema

        Returns:
            PascalCase class name
        """
        return self._to_pascal_case(table_name)
